#!/usr/bin/env python3

import os
import subprocess
import json
from pathlib import Path

def check_video_validity(video_path):
    """Check if a video is valid for processing"""
    try:
        # Use ffprobe to get video information
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_format', '-show_streams', video_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)

        # Extract video information
        format_info = data.get('format', {})
        video_streams = [s for s in data.get('streams', []) if s.get('codec_type') == 'video']

        if not video_streams:
            return False, "No video stream found"

        video_stream = video_streams[0]

        duration = float(format_info.get('duration', 0))
        size = int(format_info.get('size', 0))
        width = int(video_stream.get('width', 0))
        height = int(video_stream.get('height', 0))
        frame_count = video_stream.get('nb_frames')

        # Validation criteria
        if size < 100000:  # Less than 100KB
            return False, f"File too small: {size} bytes"

        if duration < 0.5:  # Less than 0.5 seconds
            return False, f"Duration too short: {duration:.2f}s"

        if width < 100 or height < 100:
            return False, f"Resolution too low: {width}x{height}"

        if frame_count and int(frame_count) < 10:
            return False, f"Too few frames: {frame_count}"

        return True, f"Valid: {duration:.1f}s, {width}x{height}, {size//1024}KB"

    except subprocess.CalledProcessError as e:
        return False, f"FFprobe error: {e}"
    except json.JSONDecodeError:
        return False, "Invalid JSON from ffprobe"
    except Exception as e:
        return False, f"Unknown error: {e}"

def main():
    print("🎬 VERIFICADOR DE VIDEOS")
    print("=" * 50)

    input_folder = "inputVideos"
    if not os.path.exists(input_folder):
        print(f"❌ Carpeta {input_folder} no existe")
        return

    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv']
    video_files = []

    for ext in video_extensions:
        video_files.extend(Path(input_folder).glob(f"*{ext}"))
        video_files.extend(Path(input_folder).glob(f"*{ext.upper()}"))

    if not video_files:
        print(f"❌ No se encontraron videos en {input_folder}")
        return

    valid_videos = []
    invalid_videos = []

    for video_file in sorted(video_files):
        file_size = video_file.stat().st_size
        is_valid, reason = check_video_validity(str(video_file))

        print(f"\n📹 {video_file.name}")
        print(f"   📊 Tamaño: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")

        if is_valid:
            print(f"   ✅ {reason}")
            valid_videos.append(video_file)
        else:
            print(f"   ❌ {reason}")
            invalid_videos.append(video_file)

    print("\n" + "=" * 50)
    print("📊 RESUMEN:")
    print(f"✅ Videos válidos: {len(valid_videos)}")
    print(f"❌ Videos inválidos: {len(invalid_videos)}")

    if valid_videos:
        print(f"\n🎯 VIDEOS LISTOS PARA PROCESAR:")
        for video in valid_videos:
            print(f"   ✅ {video.name}")

    if invalid_videos:
        print(f"\n⚠️ VIDEOS QUE NECESITAN REVISIÓN:")
        for video in invalid_videos:
            print(f"   ❌ {video.name}")

        print(f"\n💡 SUGERENCIAS:")
        print(f"   • Verifica que los videos no estén corruptos")
        print(f"   • Asegúrate de que tengan al menos 1 segundo de duración")
        print(f"   • Verifica que el formato sea compatible")
        print(f"   • Re-sube los videos problemáticos")

if __name__ == "__main__":
    main()