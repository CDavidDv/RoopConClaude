#!/usr/bin/env python3

import os
import sys
import glob
import subprocess
from pathlib import Path

def get_source_image():
    """Get the first image from source folder"""
    source_folder = "source"
    image_extensions = ["*.jpg", "*.jpeg", "*.png", "*.bmp"]

    for ext in image_extensions:
        images = glob.glob(os.path.join(source_folder, ext))
        images.extend(glob.glob(os.path.join(source_folder, ext.upper())))
        if images:
            return images[0]

    print("❌ No se encontró imagen de referencia en la carpeta 'source'")
    print("   Formatos soportados: jpg, jpeg, png, bmp")
    return None

def get_input_videos():
    """Get all videos from inputVideos folder"""
    input_folder = "inputVideos"
    video_extensions = ["*.mp4", "*.avi", "*.mov", "*.mkv", "*.wmv"]

    videos = []
    for ext in video_extensions:
        videos.extend(glob.glob(os.path.join(input_folder, ext)))
        videos.extend(glob.glob(os.path.join(input_folder, ext.upper())))

    return sorted(videos)

def extract_video_number(video_path):
    """Extract number from video filename"""
    filename = Path(video_path).stem
    # Try to extract number from filename
    import re
    numbers = re.findall(r'\d+', filename)
    return numbers[-1] if numbers else filename

def create_output_name(source_image, video_path):
    """Create output filename: imagename_videonumber.mp4"""
    source_name = Path(source_image).stem
    video_number = extract_video_number(video_path)
    return f"{source_name}_{video_number}.mp4"

def run_face_processing(source_img, input_video, output_video):
    """Run the complete face processing pipeline"""

    print(f"🎬 Procesando: {Path(input_video).name}")
    print(f"📸 Imagen fuente: {Path(source_img).name}")
    print(f"💾 Salida: {output_video}")

    output_full_path = os.path.join("outputVideos", output_video)

    # Verificar proveedores de ejecución disponibles
    try:
        import onnxruntime as ort
        available_providers = ort.get_available_providers()
        print(f"🔍 Proveedores disponibles: {available_providers}")

        if 'CUDAExecutionProvider' in available_providers:
            execution_provider = "cuda"
            print("🚀 Usando CUDA")
        else:
            execution_provider = "cpu"
            print("⚠️ CUDA no disponible, usando CPU")
    except ImportError:
        execution_provider = "cpu"
        print("⚠️ ONNX Runtime no encontrado, usando CPU")

    # Optimized pipeline for maximum quality on T4 GPU
    cmd = [
        "python", "run.py",
        "-s", source_img,
        "-t", input_video,
        "-o", output_full_path,
        "--frame-processor", "face_enhancer", "face_swapper", "face_enhancer",
        "--execution-provider", execution_provider,
        "--keep-fps",
        "--many-faces",
        "--max-memory", "10",
        "--execution-threads", "14" if execution_provider == "cuda" else "1",
        "--output-video-encoder", "h264_nvenc" if execution_provider == "cuda" else "libx264",
        "--output-video-quality", "18",
        "--temp-frame-format", "png",
        "--temp-frame-quality", "100"
    ]

    print(f"🚀 Comando: {' '.join(cmd)}")
    print("-" * 60)

    try:
        result = subprocess.run(cmd, check=True, capture_output=False)

        # Verificar que el archivo de salida se creó
        if os.path.exists(output_full_path):
            file_size = os.path.getsize(output_full_path) / (1024*1024)  # MB
            print(f"✅ Completado: {output_video} ({file_size:.1f} MB)")
            return True
        else:
            print(f"❌ El archivo de salida no se creó: {output_full_path}")
            return False

    except subprocess.CalledProcessError as e:
        print(f"❌ Error procesando {input_video}: {e}")
        return False
    except KeyboardInterrupt:
        print(f"\n⚠️ Procesamiento interrumpido por el usuario")
        return False

def main():
    print("🎭 ROOP BATCH PROCESSOR")
    print("=" * 50)

    # Verificar estructura de carpetas
    folders = ["source", "inputVideos", "outputVideos"]
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"📁 Creada carpeta: {folder}")

    # Obtener imagen de referencia
    source_image = get_source_image()
    if not source_image:
        return

    # Obtener videos de entrada
    input_videos = get_input_videos()
    if not input_videos:
        print("❌ No se encontraron videos en la carpeta 'inputVideos'")
        print("   Formatos soportados: mp4, avi, mov, mkv, wmv")
        return

    print(f"📸 Imagen fuente: {Path(source_image).name}")
    print(f"🎬 Videos encontrados: {len(input_videos)}")
    print()

    # Mostrar lista de videos a procesar
    for i, video in enumerate(input_videos, 1):
        output_name = create_output_name(source_image, video)
        print(f"  {i}. {Path(video).name} → {output_name}")


    # Procesar cada video
    successful = 0
    failed = 0

    for i, video in enumerate(input_videos, 1):
        print(f"\n🎯 Procesando video {i}/{len(input_videos)}")
        output_name = create_output_name(source_image, video)

        # Verificar si ya existe el archivo de salida
        output_path = os.path.join("outputVideos", output_name)
        if os.path.exists(output_path):
            response = input(f"⚠️ {output_name} ya existe. ¿Sobrescribir? (s/N): ")
            if response.lower() not in ['s', 'si', 'y', 'yes']:
                print(f"⏭️ Saltando {output_name}")
                continue

        if run_face_processing(source_image, video, output_name):
            successful += 1
        else:
            failed += 1

        print("-" * 60)

    # Resumen final
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE PROCESAMIENTO")
    print(f"✅ Exitosos: {successful}")
    print(f"❌ Fallidos: {failed}")
    print(f"📁 Resultados en: ./outputVideos/")

    if successful > 0:
        print("\n🎉 ¡Procesamiento completado!")

if __name__ == "__main__":
    main()