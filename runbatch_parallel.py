#!/usr/bin/env python3
"""
Versión paralela de ROOP Batch Processor
Procesa múltiples videos de forma simultánea para máximo rendimiento
Optimizado para T4 GPU con 15GB VRAM + 12GB RAM
"""

import os
import sys
import glob
import subprocess
import psutil
import shutil
import time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Tuple, Optional

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

def get_system_memory_usage():
    """Get total system memory usage in GB"""
    try:
        return psutil.virtual_memory().used / (1024**3)
    except:
        return 0

def get_gpu_memory_usage():
    """Get GPU memory usage using nvidia-smi"""
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=memory.used', '--format=csv,nounits,noheader'],
                              capture_output=True, text=True, timeout=5)
        return float(result.stdout.strip()) / 1024  # Convertir MB a GB
    except:
        return 0

def extract_video_number(video_path):
    """Extract number from video filename"""
    filename = Path(video_path).stem
    import re
    numbers = re.findall(r'\d+', filename)
    return numbers[-1] if numbers else filename

def create_output_name(source_image, video_path):
    """Create output filename: imagename_videonumber.mp4"""
    source_name = Path(source_image).stem
    video_number = extract_video_number(video_path)
    return f"{source_name}_{video_number}.mp4"

def clean_temp_frames():
    """Remove temporary frame folders"""
    try:
        import glob as glob_module
        temp_folders = glob_module.glob("roop/temp*")
        for folder in temp_folders:
            if os.path.isdir(folder):
                shutil.rmtree(folder)
    except:
        pass

def run_face_processing_worker(args: Tuple[str, str, str, str]) -> Tuple[bool, str, str]:
    """
    Worker function para procesamiento paralelo
    Returns: (success, output_name, error_message)
    """
    source_img, input_video, output_video, execution_provider = args
    output_full_path = os.path.join("outputVideos", output_video)

    # Verificar si ya existe
    if os.path.exists(output_full_path):
        return (None, output_video, "skip")

    try:
        # Configuración optimizada para T4 (15GB VRAM, 12GB RAM)
        cmd = [
            "python", "run.py",
            "-s", source_img,
            "-t", input_video,
            "-o", output_full_path,
            "--frame-processor", "face_swapper", "face_enhancer",
            "--execution-provider", execution_provider,
            "--keep-fps",
            "--many-faces",
            "--max-memory", "11",        # ← AUMENTADO de 8 a 11
            "--execution-threads", "6",   # ← AUMENTADO para T4
            "--output-video-encoder", "h264_nvenc" if execution_provider == "cuda" else "libx264",
            "--output-video-quality", "18",
            "--temp-frame-format", "png",
            "--temp-frame-quality", "100"
        ]

        result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=3600)
        clean_temp_frames()

        if os.path.exists(output_full_path):
            return (True, output_video, "success")
        else:
            return (False, output_video, "output_not_created")

    except subprocess.TimeoutExpired:
        clean_temp_frames()
        return (False, output_video, "timeout")
    except subprocess.CalledProcessError as e:
        clean_temp_frames()
        return (False, output_video, f"error: {str(e)[:50]}")
    except Exception as e:
        clean_temp_frames()
        return (False, output_video, f"exception: {str(e)[:50]}")

def main():
    print("🎭 ROOP BATCH PROCESSOR - VERSIÓN PARALELA")
    print("=" * 60)
    print("⚡ MODO AGRESIVO: Máximo uso de memoria (12GB RAM + 15GB VRAM)")
    print()

    # Verificar estructura de carpetas
    folders = ["source", "inputVideos", "outputVideos"]
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)

    # Obtener imagen de referencia
    source_image = get_source_image()
    if not source_image:
        return

    # Obtener videos de entrada
    input_videos = get_input_videos()
    if not input_videos:
        print("❌ No se encontraron videos en la carpeta 'inputVideos'")
        return

    print(f"📸 Imagen fuente: {Path(source_image).name}")
    print(f"🎬 Videos encontrados: {len(input_videos)}")
    print()

    # Detectar proveedor de ejecución
    try:
        import onnxruntime as ort
        available_providers = ort.get_available_providers()
        execution_provider = "cuda" if 'CUDAExecutionProvider' in available_providers else "cpu"
    except:
        execution_provider = "cpu"

    # Permitir rango de videos
    start_idx = 0
    end_idx = len(input_videos)
    parallel_jobs = 1

    if len(sys.argv) > 1:
        if sys.argv[1] == "--parallel":
            # Modo paralelo: python runbatch_parallel.py --parallel [num_workers]
            parallel_jobs = int(sys.argv[2]) if len(sys.argv) > 2 else 2
            print(f"⚡ Modo paralelo: {parallel_jobs} videos simultáneos")
        elif '-' in sys.argv[1]:
            start, end = sys.argv[1].split('-')
            start_idx = int(start) - 1
            end_idx = int(end)
            print(f"📋 Procesando rango: {start}-{end}")
        else:
            start_idx = int(sys.argv[1]) - 1
            end_idx = start_idx + 1

    input_videos = input_videos[start_idx:end_idx]
    print(f"🎯 Videos a procesar: {len(input_videos)}")
    print(f"⚡ Trabajadores paralelos: {parallel_jobs}")
    print()

    # Mostrar info de sistema
    total_ram = psutil.virtual_memory().total / (1024**3)
    print(f"📊 Sistema: {total_ram:.1f}GB RAM disponibles")
    print(f"📊 GPU: T4 con ~15GB VRAM")
    print("-" * 60)
    print()

    # Preparar tareas
    tasks = []
    for video in input_videos:
        output_name = create_output_name(source_image, video)
        output_path = os.path.join("outputVideos", output_name)

        # Si existe, saltarlo
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path) / (1024*1024)
            print(f"⏭️ Ya existe: {output_name} ({file_size:.1f} MB)")
            continue

        tasks.append((source_image, video, output_name, execution_provider))

    print(f"📝 Tareas a ejecutar: {len(tasks)}")
    print()

    # Ejecutar en paralelo
    successful = 0
    failed = 0
    skipped = 0

    start_time = time.time()

    with ProcessPoolExecutor(max_workers=parallel_jobs) as executor:
        futures = {executor.submit(run_face_processing_worker, task): task for task in tasks}

        completed = 0
        for future in as_completed(futures):
            completed += 1
            success, output_name, status = future.result()

            elapsed = time.time() - start_time
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)

            if status == "skip":
                skipped += 1
                print(f"[{completed}/{len(tasks)}] ⏭️  {output_name}")
            elif success:
                successful += 1
                file_size = os.path.getsize(os.path.join("outputVideos", output_name)) / (1024*1024)
                print(f"[{completed}/{len(tasks)}] ✅ {output_name} ({file_size:.1f}MB) - {hours}h {minutes}m")
            else:
                failed += 1
                print(f"[{completed}/{len(tasks)}] ❌ {output_name} - {status}")

            # Mostrar estado de memoria cada 5 videos
            if completed % 5 == 0:
                ram_used = get_system_memory_usage()
                gpu_used = get_gpu_memory_usage()
                print(f"   💾 RAM: {ram_used:.1f}GB | GPU: {gpu_used:.1f}GB")

    elapsed = time.time() - start_time
    hours = int(elapsed // 3600)
    minutes = int((elapsed % 3600) // 60)
    seconds = int(elapsed % 60)

    # Resumen
    print()
    print("=" * 60)
    print("📊 RESUMEN DE PROCESAMIENTO")
    print(f"✅ Exitosos: {successful}")
    print(f"⏭️ Saltados: {skipped}")
    print(f"❌ Fallidos: {failed}")
    print(f"⏱️ Tiempo total: {hours}h {minutes}m {seconds}s")

    if successful > 0:
        avg_time = (elapsed / successful) / 60
        print(f"📈 Tiempo promedio por video: {avg_time:.1f} minutos")

    # Estadísticas de tamaño
    total_output_size = 0
    output_count = 0
    if os.path.exists("outputVideos"):
        for file in os.listdir("outputVideos"):
            file_path = os.path.join("outputVideos", file)
            if os.path.isfile(file_path):
                total_output_size += os.path.getsize(file_path)
                output_count += 1

    total_output_gb = total_output_size / (1024**3)
    print(f"📁 Archivos generados: {output_count}")
    print(f"💿 Tamaño total: {total_output_gb:.1f}GB")
    print(f"📁 Resultados en: ./outputVideos/")

    if successful > 0:
        print("\n🎉 ¡Procesamiento completado!")

if __name__ == "__main__":
    main()
