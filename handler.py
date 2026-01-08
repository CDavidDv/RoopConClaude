#!/usr/bin/env python3
"""
Runpod Serverless handler for RoopConClaude
Handles face swapping requests from Runpod API
"""

import os
import sys
import json
import tempfile
import requests
from pathlib import Path
import runpod

# Add roop to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from roop import core, globals


def download_file(url: str, output_path: str) -> bool:
    """Download a file from URL to output path"""
    try:
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return True
    except Exception as e:
        print(f"Error downloading {url}: {str(e)}")
        return False


def handler(job):
    """
    Handler function for Runpod Serverless

    Expected input:
    {
        "source_image_url": "https://...",  # or "source_image_path"
        "target_video_url": "https://...",  # or "target_video_path"
        "output_filename": "output.mp4",
        "frame_processors": ["face_swapper", "face_enhancer"],
        "keep_fps": true,
        "many_faces": false,
        "output_video_quality": 95,
        "execution_provider": "cuda"
    }
    """

    try:
        job_input = job["input"]

        # Create temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Download or copy source image
            if "source_image_url" in job_input:
                source_image = os.path.join(temp_dir, "source.jpg")
                if not download_file(job_input["source_image_url"], source_image):
                    return {"status": "error", "message": "Failed to download source image"}
            elif "source_image_path" in job_input:
                source_image = job_input["source_image_path"]
            else:
                return {"status": "error", "message": "source_image_url or source_image_path required"}

            if not os.path.exists(source_image):
                return {"status": "error", "message": "Source image not found"}

            # Download or copy target video
            if "target_video_url" in job_input:
                target_video = os.path.join(temp_dir, "target.mp4")
                if not download_file(job_input["target_video_url"], target_video):
                    return {"status": "error", "message": "Failed to download target video"}
            elif "target_video_path" in job_input:
                target_video = job_input["target_video_path"]
            else:
                return {"status": "error", "message": "target_video_url or target_video_path required"}

            if not os.path.exists(target_video):
                return {"status": "error", "message": "Target video not found"}

            # Prepare output path
            output_filename = job_input.get("output_filename", "output.mp4")
            output_path = os.path.join(temp_dir, output_filename)

            # Get output directory from job (if provided, use it; otherwise use temp)
            if "output_directory" in job_input:
                output_dir = job_input["output_directory"]
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, output_filename)

            # Configure globals for headless execution
            globals.source_path = source_image
            globals.target_path = target_video
            globals.output_path = output_path

            # Frame processors
            frame_processors = job_input.get("frame_processors", ["face_swapper", "face_enhancer"])
            if isinstance(frame_processors, str):
                frame_processors = frame_processors.split()
            globals.frame_processors = frame_processors

            # Additional options
            globals.keep_fps = job_input.get("keep_fps", True)
            globals.keep_frames = job_input.get("keep_frames", False)
            globals.skip_audio = job_input.get("skip_audio", False)
            globals.many_faces = job_input.get("many_faces", False)

            # Quality settings
            globals.output_video_quality = job_input.get("output_video_quality", 95)
            globals.temp_frame_quality = job_input.get("temp_frame_quality", 100)
            globals.temp_frame_format = job_input.get("temp_frame_format", "jpg")

            # Video encoder
            globals.output_video_encoder = job_input.get("output_video_encoder", "libx264")

            # Execution settings
            globals.execution_provider = job_input.get("execution_provider", ["cuda"])
            if isinstance(globals.execution_provider, str):
                globals.execution_provider = [globals.execution_provider]

            globals.execution_threads = job_input.get("execution_threads", 1)
            globals.max_memory = job_input.get("max_memory", 0)

            # Reference face settings
            globals.reference_face_position = job_input.get("reference_face_position", 0)
            globals.reference_frame_number = job_input.get("reference_frame_number", 0)
            globals.similar_face_distance = job_input.get("similar_face_distance", 0.85)

            # Face analyser settings
            globals.detectors = job_input.get("detectors", ["retinaface"])

            # Run the face swapping
            print(f"Starting face swap: {source_image} -> {target_video}")
            print(f"Output: {output_path}")
            print(f"Frame processors: {frame_processors}")

            try:
                core.run()

                # Verify output was created
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    return {
                        "status": "success",
                        "output_path": output_path,
                        "file_size": file_size,
                        "message": f"Face swap completed successfully. Output size: {file_size / (1024*1024):.2f} MB"
                    }
                else:
                    return {"status": "error", "message": "Output file was not created"}

            except Exception as e:
                print(f"Error during face swap: {str(e)}")
                return {"status": "error", "message": f"Face swap failed: {str(e)}"}

    except Exception as e:
        print(f"Handler error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": f"Handler error: {str(e)}"}


if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
