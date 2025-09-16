#!/usr/bin/env python3

import os
import subprocess
import sys

def test_single_video():
    """Test processing a single video with detailed diagnostics"""

    print("🔧 DIAGNÓSTICO DETALLADO - VIDEO ÚNICO")
    print("=" * 50)

    # Verificar archivos de entrada
    source = "source/DanielaAS.jpg"
    target = "inputVideos/24.mp4"

    if not os.path.exists(source):
        print(f"❌ No existe: {source}")
        return
    if not os.path.exists(target):
        print(f"❌ No existe: {target}")
        return

    print(f"✅ Imagen fuente: {source} ({os.path.getsize(source)} bytes)")
    print(f"✅ Video objetivo: {target} ({os.path.getsize(target)/1024/1024:.1f} MB)")

    # Test 1: Solo face_swapper, formato simple
    print("\n🧪 TEST 1: Face swapper básico")
    cmd1 = [
        "python", "run.py",
        "-s", source,
        "-t", target,
        "-o", "test1_basic.mp4",
        "--frame-processor", "face_swapper",
        "--execution-provider", "cpu",  # Forzar CPU para estabilidad
        "--keep-fps"
    ]

    print(f"🚀 Comando: {' '.join(cmd1)}")
    try:
        result = subprocess.run(cmd1, check=True, capture_output=True, text=True)
        if os.path.exists("test1_basic.mp4"):
            size = os.path.getsize("test1_basic.mp4") / 1024 / 1024
            print(f"✅ TEST 1 EXITOSO: test1_basic.mp4 ({size:.1f} MB)")
        else:
            print("❌ TEST 1 FALLIDO: No se creó archivo")
            print("STDOUT:", result.stdout[-500:] if result.stdout else "vacío")
            print("STDERR:", result.stderr[-500:] if result.stderr else "vacío")
    except subprocess.CalledProcessError as e:
        print(f"❌ TEST 1 ERROR: {e}")
        print("STDOUT:", e.stdout[-500:] if e.stdout else "vacío")
        print("STDERR:", e.stderr[-500:] if e.stderr else "vacío")

    # Test 2: Con keep-frames para ver frames temporales
    print("\n🧪 TEST 2: Con frames temporales guardados")
    cmd2 = [
        "python", "run.py",
        "-s", source,
        "-t", target,
        "-o", "test2_frames.mp4",
        "--frame-processor", "face_swapper",
        "--execution-provider", "cpu",
        "--keep-fps",
        "--keep-frames",
        "--temp-frame-format", "jpg"
    ]

    print(f"🚀 Comando: {' '.join(cmd2)}")
    try:
        result = subprocess.run(cmd2, check=True, capture_output=True, text=True)
        if os.path.exists("test2_frames.mp4"):
            size = os.path.getsize("test2_frames.mp4") / 1024 / 1024
            print(f"✅ TEST 2 EXITOSO: test2_frames.mp4 ({size:.1f} MB)")
        else:
            print("❌ TEST 2 FALLIDO: No se creó archivo")

        # Verificar si hay frames temporales
        temp_files = [f for f in os.listdir(".") if "temp" in f.lower()]
        if temp_files:
            print(f"🔍 Archivos temporales encontrados: {len(temp_files)}")
            print(f"   Ejemplos: {temp_files[:5]}")
        else:
            print("🔍 No se encontraron archivos temporales")

    except subprocess.CalledProcessError as e:
        print(f"❌ TEST 2 ERROR: {e}")

    # Test 3: Verificar que funciona con un video de prueba muy corto
    print("\n🧪 TEST 3: Crear video corto de prueba")
    try:
        # Extraer solo 3 segundos del video original para prueba rápida
        cmd_extract = [
            "ffmpeg", "-i", target, "-t", "3", "-c", "copy", "test_short.mp4", "-y"
        ]
        subprocess.run(cmd_extract, check=True, capture_output=True)

        if os.path.exists("test_short.mp4"):
            print(f"✅ Video corto creado: test_short.mp4")

            cmd3 = [
                "python", "run.py",
                "-s", source,
                "-t", "test_short.mp4",
                "-o", "test3_short.mp4",
                "--frame-processor", "face_swapper",
                "--execution-provider", "cpu"
            ]

            result = subprocess.run(cmd3, check=True, capture_output=True, text=True)
            if os.path.exists("test3_short.mp4"):
                size = os.path.getsize("test3_short.mp4") / 1024 / 1024
                print(f"✅ TEST 3 EXITOSO: test3_short.mp4 ({size:.1f} MB)")
            else:
                print("❌ TEST 3 FALLIDO: No se creó archivo")

    except Exception as e:
        print(f"❌ TEST 3 ERROR: {e}")

    # Resumen
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE TESTS:")
    test_files = ["test1_basic.mp4", "test2_frames.mp4", "test3_short.mp4"]
    for f in test_files:
        if os.path.exists(f):
            size = os.path.getsize(f) / 1024 / 1024
            print(f"✅ {f} ({size:.1f} MB)")
        else:
            print(f"❌ {f} (no creado)")

if __name__ == "__main__":
    test_single_video()