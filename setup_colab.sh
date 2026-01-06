#!/bin/bash
# Setup script for Google Colab environment
# This installs all necessary CUDA dependencies and Python packages for ROOP

set -e

echo "======================================"
echo "🚀 ROOP Colab Setup"
echo "======================================"

# Update system packages
echo "📦 Updating system packages..."
apt-get update

# Install CUDA runtime libraries
echo "📦 Installing CUDA runtime libraries..."
apt-get install -y \
    libcuda11-0 \
    libcublas11 \
    libcufft10 \
    libcudnn8 \
    libnccl2 \
    cuda-runtime-11-2

# Install ffmpeg if not present
echo "📦 Installing ffmpeg..."
apt-get install -y ffmpeg

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip setuptools wheel

# Install ROOP requirements
echo "📦 Installing ROOP requirements..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "⚠️  requirements.txt not found"
fi

echo ""
echo "======================================"
echo "✅ Setup completed successfully!"
echo "======================================"
echo ""
echo "To run ROOP in headless mode:"
echo "python run.py -s source_image.jpg -t target_video.mp4 -o output.mp4"
echo ""
echo "To check available GPU providers:"
echo "python -c \"import onnxruntime; print(onnxruntime.get_available_providers())\""
