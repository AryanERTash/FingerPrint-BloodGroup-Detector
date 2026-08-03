FROM python:3.10-slim

# Suppress TensorFlow stupidity
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

EXPOSE 5000

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000", "--timeout", "120", "--workers", "2"]