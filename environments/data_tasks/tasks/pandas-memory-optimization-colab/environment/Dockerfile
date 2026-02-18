FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    tmux \
    asciinema \
    && rm -rf /var/lib/apt/lists/*

# Copy notebook to workspace
COPY process_data.ipynb /workspace/process_data.ipynb
WORKDIR /workspace

# Install Python dependencies
RUN pip install --no-cache-dir \
    pandas==2.0.3 \
    numpy==1.24.3 \
    psutil==5.9.5 \
    pytest \
    jupyter \
    nbconvert \
    nbformat \
    ipykernel

# Set environment variables
ENV PYTHONUNBUFFERED=1
