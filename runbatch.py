#!/usr/bin/env python3

import os
import sys
import glob
import subprocess
import shutil
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

    # Usar solo face_swapper primero, luego agregar enhancer si funciona
    cmd = [
        "python", "run.py",
        "-s", source_img,
        "-t", input_video,
        "-o", output_full_path,
        "--frame-processor", "face_swapper",
        "--execution-provider", execution_provider,
        "--keep-fps",
        "--many-faces",
        "--max-memory", "12",
        "--execution-threads", "4",
        "--temp-frame-format", "png",
        "--temp-frame-quality", "95",
        "--output-video-quality", "85"
    ]

    print(f"🚀 Comando: {' '.join(cmd)}")
    print("-" * 60)

    try:
        # Asegurar que el directorio de salida existe
        os.makedirs("outputVideos", exist_ok=True)

        # Verificar directorio actual y archivos antes
        print(f"📂 Directorio actual: {os.getcwd()}")
        print(f"📁 Carpeta outputVideos existe: {os.path.exists('outputVideos')}")

        result = subprocess.run(cmd, check=True, capture_output=False)

        # Buscar el archivo en múltiples ubicaciones posibles
        possible_paths = [
            output_full_path,
            output_video,  # En caso de que se guarde en el directorio actual
            os.path.join(".", output_video),
            os.path.join("/content", output_video),  # Para Colab
            os.path.join("/content/roop", output_video)
        ]

        found_file = None
        for path in possible_paths:
            if os.path.exists(path):
                found_file = path
                break

        if found_file:
            file_size = os.path.getsize(found_file) / (1024*1024)  # MB
            # Mover archivo a la ubicación correcta si no está ahí
            if found_file != output_full_path:
                import shutil
                shutil.move(found_file, output_full_path)
                print(f"📦 Archivo movido de {found_file} a {output_full_path}")
            print(f"✅ Completado: {output_video} ({file_size:.1f} MB)")
            return True
        else:
            print(f"❌ El archivo de salida no se creó: {output_full_path}")
            print("🔍 Buscando archivos en:")
            for path in possible_paths:
                print(f"   - {path}: {'✅' if os.path.exists(path) else '❌'}")
            # Listar archivos en directorio actual
            print("📋 Archivos en directorio actual:")
            for f in os.listdir("."):
                if output_video.split("_")[0] in f or "DanielaAS" in f:
                    print(f"   🔍 {f}")
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

    # Verificar archivos creados
    print("\n🔍 VERIFICANDO ARCHIVOS CREADOS:")
    output_files = glob.glob("outputVideos/*.mp4")
    if output_files:
        total_size = 0
        for file in sorted(output_files):
            size = os.path.getsize(file) / (1024*1024)  # MB
            total_size += size
            print(f"   📹 {os.path.basename(file)} ({size:.1f} MB)")
        print(f"\n📊 Total: {len(output_files)} archivos ({total_size:.1f} MB)")

        # Comando para descargar en Colab
        print(f"\n💾 Para descargar en Colab:")
        print(f"   from google.colab import files")
        for file in sorted(output_files):
            print(f"   files.download('{file}')")
    else:
        print("   ❌ No se encontraron archivos de video en outputVideos/")
        print("\n🔧 DIAGNÓSTICO:")
        print("   1. Verifica que CUDA esté funcionando")
        print("   2. Verifica que los videos de entrada sean válidos")
        print("   3. Revisa los logs de error arriba")

    if successful > 0:
        print("\n🎉 ¡Procesamiento completado!")

if __name__ == "__main__":
    main()