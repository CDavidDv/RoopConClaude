#!/usr/bin/env python3

import os
import subprocess
import sys

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ {description} completado")
    else:
        print(f"❌ Error en {description}:")
        print(result.stderr)
        return False
    return True

def setup_colab_environment():
    """Setup optimized environment for Google Colab"""
    print("🚀 CONFIGURANDO ROOP PARA GOOGLE COLAB")
    print("=" * 50)

    # Lista de comandos de instalación
    commands = [
        ("pip install onnxruntime-gpu==1.15.1", "Instalando ONNX Runtime GPU"),
        ("pip install opencv-python==4.8.0.74", "Instalando OpenCV"),
        ("pip install onnx==1.14.0", "Instalando ONNX"),
        ("pip install insightface==0.7.3", "Instalando InsightFace"),
        ("pip install customtkinter==5.2.0", "Instalando CustomTkinter"),
        ("pip install gfpgan==1.3.8", "Instalando GFPGAN"),
        ("pip install psutil==5.9.5", "Instalando PSUtil"),
        ("pip install opennsfw2==0.10.2", "Instalando OpenNSFW2"),
        ("pip install protobuf==4.23.4", "Instalando Protobuf"),
        ("pip install tqdm==4.65.0", "Instalando TQDM"),
    ]

    # Ejecutar instalaciones
    for cmd, desc in commands:
        if not run_command(cmd, desc):
            return False

    # Crear estructura de carpetas
    folders = ["source", "inputVideos", "outputVideos"]
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"📁 Creada carpeta: {folder}")

    # Verificar instalación de CUDA
    print("\n🔍 Verificando soporte CUDA...")
    try:
        import onnxruntime as ort
        providers = ort.get_available_providers()
        if 'CUDAExecutionProvider' in providers:
            print("✅ CUDA disponible para ONNX Runtime")
        else:
            print("⚠️ CUDA no disponible, se usará CPU")
    except ImportError:
        print("❌ Error importando ONNX Runtime")
        return False

    print("\n🎉 ¡Configuración completada!")
    print("\n📝 INSTRUCCIONES DE USO:")
    print("1. Sube tu imagen de referencia a la carpeta 'source/'")
    print("2. Sube tus videos a procesar a la carpeta 'inputVideos/'")
    print("3. Ejecuta: python runbatch.py")
    print("4. Los resultados aparecerán en 'outputVideos/'")

    return True

if __name__ == "__main__":
    success = setup_colab_environment()
    if not success:
        sys.exit(1)