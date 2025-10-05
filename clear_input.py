#!/usr/bin/env python3

import os
import glob
from pathlib import Path

def delete_input_videos():
    """Delete all videos from inputVideos folder"""
    input_folder = "inputVideos"

    if not os.path.exists(input_folder):
        print(f"❌ La carpeta '{input_folder}' no existe")
        return

    video_extensions = ["*.mp4", "*.avi", "*.mov", "*.mkv", "*.wmv"]

    videos = []
    for ext in video_extensions:
        videos.extend(glob.glob(os.path.join(input_folder, ext)))
        videos.extend(glob.glob(os.path.join(input_folder, ext.upper())))

    if not videos:
        print(f"✅ La carpeta '{input_folder}' ya está vacía")
        return

    print(f"🗑️  BORRAR VIDEOS DE INPUT")
    print("=" * 50)
    print(f"📁 Carpeta: {input_folder}")
    print(f"🎬 Videos encontrados: {len(videos)}")
    print()

    for i, video in enumerate(videos, 1):
        file_size = os.path.getsize(video) / (1024*1024)  # MB
        print(f"  {i}. {Path(video).name} ({file_size:.1f} MB)")

    print()
    response = input(f"⚠️  ¿Confirmas borrar {len(videos)} videos? (s/N): ")

    if response.lower() not in ['s', 'si', 'y', 'yes']:
        print("❌ Operación cancelada")
        return

    deleted = 0
    failed = 0

    for video in videos:
        try:
            os.remove(video)
            print(f"✅ Borrado: {Path(video).name}")
            deleted += 1
        except Exception as e:
            print(f"❌ Error borrando {Path(video).name}: {e}")
            failed += 1

    print()
    print("=" * 50)
    print(f"✅ Videos borrados: {deleted}")
    if failed > 0:
        print(f"❌ Errores: {failed}")
    print(f"📁 Carpeta '{input_folder}' limpiada")

if __name__ == "__main__":
    delete_input_videos()
