import os


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


MODEL_PATH = os.path.join("model", "blood_group_detection1.keras")
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


CLASS_LABELS = ["A+", "A-", "AB+", "AB-", "B+", "B-", "O+", "O-"]


model_state: dict = {"model": None}





_original_dense_init = Dense.__init__


def _safe_dense_init(self, *args, **kwargs):
    
    kwargs.pop("quantization_config", None)
    _original_dense_init(self, *args, **kwargs)

Dense.__init__ = _safe_dense_init




class SafeDense(Dense):
    # for newer version of tensorflow
    # might cause loading problem if not used in load_model
    def __init__(self, *args, quantization_config=None, **kwargs):
        super().__init__(*args, **kwargs)


from tensorflow.keras.utils import custom_object_scope


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[INFO] Loading blood group model...")

    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Model file not found at: {os.path.abspath(MODEL_PATH)}"
        )


    with custom_object_scope({"Dense": SafeDense, "SafeDense": SafeDense}):
        model_state["model"] = load_model(MODEL_PATH, compile=False)

    print("[INFO] Model loaded successfully. Ready to serve requests.")

    yield

    print("[INFO] Server shutting down.")
    model_state["model"] = None


# init fastapi

app = FastAPI(title="Blood Group Detection using finger print", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


from tensorflow.keras.applications.imagenet_utils import preprocess_input

# Standard target size based on your reference snippet
IMG_TARGET_SIZE = (256, 256)


def preprocess_image(file_bytes: bytes) -> np.ndarray:
    try:
        img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    except Exception:
        raise HTTPException(
            status_code=400, detail="Uploaded file is not a valid image."
        )

    # 1. Resize image to match target dimensions
    img = img.resize(IMG_TARGET_SIZE)

    arr = np.array(img, dtype="float32")

    arr = np.expand_dims(arr, axis=0)

    arr = preprocess_input(arr)

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

    return FileResponse(path=file_path, filename=filename, media_type="image/bmp")


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
    preds = model.predict(x)[0]

    pred_idx = np.argmax(preds)
    print(preds, pred_idx)
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
