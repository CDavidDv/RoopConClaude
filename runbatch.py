#!/usr/bin/env python3

import os
import sys
import glob
import subprocess
import psutil
import shutil
import time
from pathlib import Path

# Detectar si estamos en Google Colab
def is_colab():
    """Verificar si se está ejecutando en Google Colab"""
    try:
        import google.colab
        return True
    except ImportError:
        return False

# Función para sincronizar con Google Drive
def setup_drive_sync():
    """Configurar sincronización con Google Drive en Colab"""
    if not is_colab():
        return None

    try:
        from google.colab import drive
        drive.mount('/content/drive')
        return '/content/drive/My Drive/RoopOutput'
    except Exception as e:
        print(f"⚠️ No se pudo montar Google Drive: {e}")
        return None

# Función para descargar en Colab
def download_file_colab(file_path):
    """Descargar archivo en Google Colab"""
    try:
        # Intenta con google.colab.files (método interactivo)
        try:
            from google.colab import files
            import IPython
            print(f"📥 Descargando: {Path(file_path).name}...")
            # Ejecutar en contexto IPython para que funcione desde script
            IPython.display.display(IPython.display.FileLink(file_path))
            files.download(file_path)
            print(f"✅ Descargado: {Path(file_path).name}")
            return True
        except (AttributeError, NameError, RuntimeError):
            # Si falla, intenta copiar a /content/output para descargar manualmente
            output_dir = "/content/output"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            output_path = os.path.join(output_dir, Path(file_path).name)
            shutil.copy2(file_path, output_path)
            print(f"📁 Guardado en: {output_path}")
            print(f"📥 Disponible para descargar desde /content/output/")
            return True
    except Exception as e:
        print(f"⚠️ Error en descarga: {e}")
        return False

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

def get_memory_usage():
    """Get current memory usage in GB"""
    try:
        process = psutil.Process()
        return process.memory_info().rss / (1024**3)
    except:
        return 0

def get_system_memory_usage():
    """Get total system memory usage in GB"""
    try:
        return psutil.virtual_memory().used / (1024**3)
    except:
        return 0

def clean_temp_frames():
    """Remove temporary frame folders"""
    try:
        import glob as glob_module
        temp_folders = glob_module.glob("roop/temp*")
        for folder in temp_folders:
            if os.path.isdir(folder):
                shutil.rmtree(folder)
                print(f"🧹 Limpiado: {folder}")
    except:
        pass

def wait_for_memory(target_gb=2, timeout=120):
    """Wait until system memory drops below target"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        mem = get_system_memory_usage()
        if mem < target_gb:
            return True
        print(f"⏳ Esperando liberación de memoria... ({mem:.1f}GB)")
        time.sleep(5)
    return False

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

def run_face_processing(source_img, input_video, output_video, drive_path=None):
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

    # Optimized pipeline for T4 GPU (15GB VRAM, 12GB RAM)
    cmd = [
        "python", "run.py",
        "-s", source_img,
        "-t", input_video,
        "-o", output_full_path,
        "--frame-processor", "face_swapper", "face_enhancer",
        "--execution-provider", execution_provider,
        "--keep-fps",
        "--many-faces",
        "--max-memory", "11",
        "--execution-threads", "6" if execution_provider == "cuda" else "1",
        "--output-video-encoder", "h264_nvenc" if execution_provider == "cuda" else "libx264",
        "--output-video-quality", "18",
        "--temp-frame-format", "png",
        "--temp-frame-quality", "100"
    ]

    print(f"🚀 Comando: {' '.join(cmd)}")
    print("-" * 60)

    try:
        mem_before = get_system_memory_usage()
        print(f"📊 Memoria antes: {mem_before:.1f}GB")

        result = subprocess.run(cmd, check=True, capture_output=False)

        # Limpieza después del procesamiento
        clean_temp_frames()
        mem_after = get_system_memory_usage()
        print(f"📊 Memoria después: {mem_after:.1f}GB (diferencia: {mem_after - mem_before:+.1f}GB)")

        # Verificar que el archivo de salida se creó
        if os.path.exists(output_full_path):
            file_size = os.path.getsize(output_full_path) / (1024*1024)  # MB
            print(f"✅ Completado: {output_video} ({file_size:.1f} MB)")

            # Sincronizar en Colab
            if is_colab():
                if drive_path:
                    # Guardar en Google Drive
                    try:
                        if not os.path.exists(drive_path):
                            os.makedirs(drive_path)
                        drive_file = os.path.join(drive_path, output_video)
                        shutil.copy2(output_full_path, drive_file)
                        print(f"☁️ Guardado en Drive: {output_video}")
                    except Exception as e:
                        print(f"⚠️ Error guardando en Drive: {e}")
                        download_file_colab(output_full_path)
                else:
                    # Descargar o copiar a /content/output
                    download_file_colab(output_full_path)

            return True
        else:
            print(f"❌ El archivo de salida no se creó: {output_full_path}")
            return False

    except subprocess.CalledProcessError as e:
        print(f"❌ Error procesando {input_video}: {e}")
        clean_temp_frames()
        return False
    except KeyboardInterrupt:
        print(f"\n⚠️ Procesamiento interrumpido por el usuario")
        clean_temp_frames()
        return False

def main():
    print("🎭 ROOP BATCH PROCESSOR")
    print("=" * 50)

    # Detectar si estamos en Colab
    in_colab = is_colab()
    drive_path = None

    if in_colab:
        print("🔷 Detectado: Google Colab")
        print("📥 Opciones de descarga disponibles:")
        print("   1. Descargar directamente")
        print("   2. Sincronizar con Google Drive")
        print("   3. Copiar a /content/output")
        print()

        # Intentar montar Drive si está disponible
        try:
            from google.colab import drive
            drive.mount('/content/drive', force_remount=False)
            drive_path = '/content/drive/My Drive/RoopOutput'
            print("✅ Google Drive montado")
            print(f"📁 Los archivos se guardarán en: {drive_path}")
        except:
            print("⚠️ Google Drive no disponible")
            drive_path = None
        print()

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

    # Permitir procesar solo un rango (útil para lotes)
    start_idx = 0
    end_idx = len(input_videos)

    if len(sys.argv) > 1:
        try:
            if '-' in sys.argv[1]:
                start, end = sys.argv[1].split('-')
                start_idx = int(start) - 1
                end_idx = int(end)
                print(f"📋 Procesando rango: {start}-{end}")
            else:
                start_idx = int(sys.argv[1]) - 1
                end_idx = start_idx + 1
                print(f"📋 Procesando solo video #{sys.argv[1]}")
        except:
            print("⚠️ Formato de rango inválido.")
            print("   Uso: python runbatch.py [inicio-fin]")
            print("   Ejemplos:")
            print("     python runbatch.py 1-40    # Procesa videos 1 a 40")
            print("     python runbatch.py 5       # Procesa solo video 5")
            if in_colab:
                print("   En Colab: Los archivos se descargan automáticamente")

    input_videos = input_videos[start_idx:end_idx]
    print(f"🎯 Videos a procesar: {len(input_videos)}")
    print()

    # Mostrar lista de videos a procesar
    for i, video in enumerate(input_videos, 1):
        output_name = create_output_name(source_image, video)
        print(f"  {i}. {Path(video).name} → {output_name}")

    # Procesar cada video
    successful = 0
    failed = 0
    skipped = 0
    memory_warnings = 0

    print(f"\n📈 Memoria del sistema disponible: {psutil.virtual_memory().total / (1024**3):.1f}GB")
    print()

    for i, video in enumerate(input_videos, 1):
        print(f"\n🎯 Procesando video {i}/{len(input_videos)}")
        output_name = create_output_name(source_image, video)

        # Verificar si ya existe el archivo de salida (auto-skip)
        output_path = os.path.join("outputVideos", output_name)
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path) / (1024*1024)
            print(f"⏭️ Ya existe: {output_name} ({file_size:.1f} MB) - Saltando")
            skipped += 1
            print("-" * 60)
            continue

        # Monitorear memoria antes de procesar
        current_mem = get_system_memory_usage()
        total_mem = psutil.virtual_memory().total / (1024**3)
        mem_percent = (current_mem / total_mem) * 100
        print(f"💾 Memoria actual: {current_mem:.1f}GB / {total_mem:.1f}GB ({mem_percent:.1f}%)")

        if mem_percent > 85:
            print(f"⚠️ Memoria alta ({mem_percent:.1f}%). Esperando antes de continuar...")
            memory_warnings += 1
            if not wait_for_memory(target_gb=total_mem * 0.5):
                print("⏱️ Timeout esperando memoria. Continuando de todas formas...")

        if run_face_processing(source_image, video, output_name, drive_path):
            successful += 1
        else:
            failed += 1

        print("-" * 60)

    # Resumen final
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE PROCESAMIENTO")
    print(f"✅ Exitosos: {successful}")
    print(f"⏭️ Saltados: {skipped}")
    print(f"❌ Fallidos: {failed}")
    print(f"⚠️ Advertencias de memoria: {memory_warnings}")

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

    if in_colab:
        if drive_path:
            print(f"☁️ Archivos guardados en: {drive_path}")
            print(f"📝 Accesibles desde Google Drive")
        else:
            print(f"📁 Archivos disponibles en: /content/output/")
            print(f"📥 Descarga manual disponible")
    else:
        print(f"📁 Resultados en: ./outputVideos/")

    if successful > 0:
        print("\n🎉 ¡Procesamiento completado!")

if __name__ == "__main__":
    main()