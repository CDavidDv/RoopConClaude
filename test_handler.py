#!/usr/bin/env python3
"""
Test script para validar handler.py localmente
Simula lo que haría Runpod
"""

import sys
import os
import json
from pathlib import Path

# Verificar que estamos en el directorio correcto
if not os.path.exists('handler.py'):
    print("❌ Error: No estoy en el directorio raíz de roop")
    print(f"   Directorio actual: {os.getcwd()}")
    sys.exit(1)

print("✅ Estoy en el directorio correcto")
print()

# Test 1: Importar módulos
print("📋 Test 1: Importando módulos...")
try:
    from handler import handler, download_file
    print("✅ handler.py importado correctamente")
except ImportError as e:
    print(f"❌ Error importando handler.py: {e}")
    sys.exit(1)

try:
    from roop import core, globals
    print("✅ roop.core y roop.globals importados correctamente")
except ImportError as e:
    print(f"❌ Error importando roop: {e}")
    sys.exit(1)

try:
    import runpod
    print("✅ runpod importado correctamente")
except ImportError as e:
    print(f"❌ Error: runpod no instalado")
    print("   Instala con: pip install runpod")
    sys.exit(1)

print()

# Test 2: Verificar archivos requeridos
print("📋 Test 2: Verificando archivos requeridos...")
required_files = ['source', 'inputVideos', 'requirements.txt']
for file in required_files:
    if os.path.exists(file):
        print(f"✅ {file} existe")
    else:
        print(f"⚠️  {file} NO existe")

print()

# Test 3: Verificar si hay imágenes de prueba
print("📋 Test 3: Buscando imágenes de prueba...")
test_images = list(Path('source').glob('*')) if os.path.exists('source') else []
if test_images:
    print(f"✅ Encontradas {len(test_images)} imágenes en source/")
    for img in test_images[:3]:
        print(f"   - {img.name}")
else:
    print(f"⚠️  No hay imágenes en source/")
    print(f"   Coloca una imagen JPG en source/ para testing")

print()

# Test 4: Verificar si hay videos de prueba
print("📋 Test 4: Buscando videos de prueba...")
test_videos = list(Path('inputVideos').glob('*.mp4')) if os.path.exists('inputVideos') else []
if test_videos:
    print(f"✅ Encontrados {len(test_videos)} videos en inputVideos/")
    for vid in test_videos[:3]:
        print(f"   - {vid.name}")
else:
    print(f"⚠️  No hay videos MP4 en inputVideos/")
    print(f"   Coloca un video MP4 en inputVideos/ para testing")

print()

# Test 5: Simular un request a handler
print("📋 Test 5: Simulando request a handler...")
print()

# Crear un request de ejemplo
if test_images and test_videos:
    test_job = {
        "input": {
            "source_image_path": str(test_images[0]),
            "target_video_path": str(test_videos[0]),
            "output_filename": "test_output.mp4",
            "frame_processors": ["face_swapper"],
            "keep_fps": True,
            "execution_provider": "cuda",
            "max_memory": 8,
            "execution_threads": 4
        }
    }

    print(f"📤 Request JSON:")
    print(json.dumps(test_job, indent=2))
    print()

    print(f"🎬 Procesando...")
    print(f"   Imagen: {test_images[0].name}")
    print(f"   Video: {test_videos[0].name}")
    print()

    try:
        # Ejecutar handler
        result = handler(test_job)

        print(f"📥 Response:")
        print(json.dumps(result, indent=2))
        print()

        if result.get("status") == "success":
            print("✅ ¡Handler funcionó correctamente!")
            print(f"   Output: {result.get('output_path')}")
            print(f"   Tamaño: {result.get('file_size')} bytes")
        else:
            print(f"❌ Handler retornó error: {result.get('message')}")

    except Exception as e:
        print(f"❌ Error ejecutando handler: {e}")
        import traceback
        traceback.print_exc()

else:
    print("⚠️  No puedo hacer test sin imagen y video")
    print()
    print("Para testing, necesitas:")
    print("1. Una imagen JPG en source/")
    print("2. Un video MP4 en inputVideos/")
    print()
    print("Ejemplo:")
    print("  - source/cara.jpg")
    print("  - inputVideos/video.mp4")

print()
print("=" * 60)
print("📊 RESUMEN DE DIAGNOSTICO")
print("=" * 60)

checks = {
    "Módulos importados": True,
    "Archivos de configuración": os.path.exists('requirements.txt'),
    "Carpeta source": os.path.exists('source'),
    "Carpeta inputVideos": os.path.exists('inputVideos'),
    "Imágenes de prueba": len(test_images) > 0,
    "Videos de prueba": len(test_videos) > 0,
}

for check, status in checks.items():
    emoji = "✅" if status else "❌"
    print(f"{emoji} {check}")

all_good = all(checks.values())

print()
if all_good:
    print("🎉 Todo listo para Runpod!")
else:
    print("⚠️  Hay algunos problemas que corregir antes de Runpod")

print()
print("Próximos pasos:")
print("1. Si todo pasó ✅, estás listo para deploying en Runpod")
print("2. Usa: docker build -t tu-usuario/roop:latest .")
print("3. Push a Docker Hub: docker push tu-usuario/roop:latest")
print("4. Deploy en Runpod con esa imagen")
