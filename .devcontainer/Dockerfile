FROM mcr.microsoft.com/devcontainers/python:3-3.13-bookworm

# Install system libraries required by OpenCV and other dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libxrandr2 \
    libx11-6 \
    && rm -rf /var/lib/apt/lists/*
