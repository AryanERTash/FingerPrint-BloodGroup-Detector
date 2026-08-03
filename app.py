import io
import os
from contextlib import asynccontextmanager

import numpy as np
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from PIL import Image

from fastapi.staticfiles import StaticFiles


from tensorflow.keras.layers import Dense
from tensorflow.keras.models import load_model


MODEL_PATH = os.path.join("model", "bg-fe-default.h5")
IMG_TARGET_SIZE = (256, 256)  
MAX_UPLOAD_DIMENSIONS = (256, 256) 
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {
	"image/png",
	"image/jpeg",
	"image/jpg",
	"image/bmp",
	"image/x-ms-bmp",
}



CLASS_LABELS = ['A+', 'A-', 'AB+', 'AB-', 'B+', 'B-', 'O+', 'O-']




model_state: dict = {"model": None}




class SafeDense(Dense):
	# for newer version of tensorflow
	# might cause loading problem if not used in load_model
	def __init__(self, *args, quantization_config=None, **kwargs):
		super().__init__(*args, **kwargs)


@asynccontextmanager
async def lifespan(app: FastAPI):
	print("[INFO] Loading blood group model...")

	model_state["model"] = load_model(
		MODEL_PATH, compile=False, custom_objects={"Dense": SafeDense}
	)
	
	print("[INFO] Model loaded successfully. Ready to serve requests.")

	yield
	

	# shuting down logic
	print("[INFO] Server shutting down.")
	
	model_state["model"] = None




# init fastapi

app = FastAPI(title="Blood Group Detection using finger print", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")





def preprocess_image(file_bytes: bytes) -> np.ndarray:
	try:
		img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
	except Exception:
		raise HTTPException(
			status_code=400, detail="Uploaded file is not a valid image."
		)


	img = img.resize(IMG_TARGET_SIZE)
	arr = np.array(img, dtype="float32")
	arr = arr / 255.0 # to match training inputs
	arr = np.expand_dims(arr, axis=0)
	
	return arr



@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
	return templates.TemplateResponse(request=request, name="index.html")



DATASET_DIR = os.path.abspath(os.path.join("model", "dataset"))

@app.get("/download/{image_path:path}")
async def download_dataset_image(image_path: str):
	file_path = os.path.abspath(os.path.join(DATASET_DIR, image_path))
	

	if not file_path.startswith(DATASET_DIR):
		raise HTTPException(status_code=400, detail="Invalid image path.")

	if not os.path.isfile(file_path):
		raise HTTPException(status_code=404, detail="Image not found.")

	filename = os.path.basename(file_path)

	# print(filename)


	return FileResponse(
		path=file_path,
		filename=filename,
		media_type="image/bmp"
	)




@app.post("/api")
async def predict(file: UploadFile = File(...)):
	model = model_state["model"]
	if model is None:
		raise HTTPException(
			status_code=503, detail="Model is not ready yet. Try again shortly."
		)

	if file.content_type not in ALLOWED_CONTENT_TYPES:
		raise HTTPException(
			status_code=400,
			detail="Only PNG, JPG, or BMP images are supported.",
		)

	contents = await file.read()
	if len(contents) > MAX_FILE_SIZE_BYTES:
		raise HTTPException(status_code=400, detail="File too large. Max size is 5 MB.")
	if len(contents) == 0:
		raise HTTPException(status_code=400, detail="Uploaded file is empty.")

	x = preprocess_image(contents)
	preds = model.predict(x, verbose=0)[0]

	pred_idx = int(np.argmax(preds))
	probabilities = [
		{"label": CLASS_LABELS[i], "probability": float(preds[i])}
		for i in range(len(CLASS_LABELS))
	]
	probabilities.sort(key=lambda item: item["probability"], reverse=True)

	result = {
		"predicted_class": CLASS_LABELS[pred_idx],
		"confidence": float(preds[pred_idx]),
		"probabilities": probabilities,
	}
	return JSONResponse(content=result)


if __name__ == "__main__":
	import uvicorn

	uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)
