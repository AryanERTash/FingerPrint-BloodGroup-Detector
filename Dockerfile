FROM python:3.10-slim

# stop tensorflow from spamming the logs with warnings
ENV TF_CPP_MIN_LOG_LEVEL="2"

RUN apt-get update && apt-get install -y --no-install-recommends \
	build-essential \
	gfortran \
	libopenblas-dev \
	liblapack-dev \
	pkg-config \
	meson \
	ninja-build \
	&& rm -rf /var/lib/apt/lists/*

WORKDIR /FGBloodGroup

RUN pip install --no-cache-dir --upgrade pip setuptools wheel

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .


EXPOSE $PORT


CMD gunicorn app:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --timeout 120 --workers 1