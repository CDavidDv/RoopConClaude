#!/bin/bash
# Optimized setup script for Google Colab
# This installs all dependencies in the correct order

echo "🚀 ROOP SETUP - OPTIMIZADO PARA GOOGLE COLAB"
echo "=============================================="

# Install dependencies avoiding conflicts
echo "📦 Instalando dependencias optimizadas..."

# Core dependencies with compatible versions
pip install -q numpy==1.23.5
pip install -q tensorflow==2.12.0
pip install -q onnxruntime-gpu==1.15.1
pip install -q opencv-python==4.8.0.74
pip install -q onnx==1.14.0
pip install -q insightface==0.7.3
pip install -q customtkinter==5.2.0
pip install -q gfpgan==1.3.8
pip install -q psutil==5.9.5
pip install -q opennsfw2==0.10.2
pip install -q protobuf==4.23.4
pip install -q tqdm==4.65.0

echo "✅ Dependencias instaladas"

# Verify CUDA
echo ""
echo "🔍 Verificando CUDA..."
python -c "import onnxruntime as ort; providers = ort.get_available_providers(); print('✅ CUDA disponible' if 'CUDAExecutionProvider' in providers else '⚠️  Solo CPU disponible'); print(f'Proveedores: {providers}')"

echo ""
echo "✅ Setup completado!"
echo ""
echo "📝 Próximos pasos:"
echo "1. Sube tu imagen de referencia a: source/"
echo "2. Sube tus videos a: inputVideos/"
echo "3. Ejecuta: python runbatch.py"
echo ""