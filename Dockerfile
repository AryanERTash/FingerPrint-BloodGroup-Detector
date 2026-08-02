# Use official Python 3.10 slim image on Linux
FROM python:3.10-slim

# Install system dependencies (gfortran, C compilers, and BLAS libraries for SciPy/NumPy)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    pkg-config \
    meson \
    ninja-build \
    && rm -rf /var/lib/apt/lists/*

# Set working directory inside the container
WORKDIR /app

# Upgrade pip and build tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements file first (leveraging Docker layer caching)
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code (including root app.py)
COPY . .

# Expose default port
EXPOSE 5000

# Start Gunicorn server pointing to root app.py (app:app)
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000", "--timeout", "120", "--workers", "2"]