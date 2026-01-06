# ROOP on Google Colab Setup Guide

## 🎯 Quick Start

### Option 1: Using the Colab Notebook (Recommended)
1. Open [ROOP_COLAB.ipynb](ROOP_COLAB.ipynb) directly in Google Colab
2. Follow the cells in order:
   - **Step 1**: Run setup to install dependencies
   - **Step 2**: Check GPU availability
   - **Step 3**: Upload your source image and target video
   - **Step 4**: Process video with GPU acceleration
   - **Step 5**: Download results

### Option 2: Manual Setup
If you prefer to use your own Colab notebook:

```python
# 1. Clone repository
!git clone https://github.com/s0md3v/roop.git --depth 1
%cd roop

# 2. Install CUDA libraries (required for GPU)
!apt-get update
!apt-get install -y libcuda11-0 libcublas11 libcufft10 libcudnn8 libnccl2 cuda-runtime-11-2 ffmpeg

# 3. Install Python dependencies
!pip install -q -r requirements.txt

# 4. Run face swap
!python run.py -s source.jpg -t target.mp4 -o output.mp4 \
  --frame-processor face_swapper face_enhancer \
  --execution-provider cuda --keep-fps --many-faces \
  --max-memory 10 --output-video-encoder h264_nvenc
```

## 🔧 GPU Optimization

The setup includes automatic GPU optimization:
- **TensorRT Provider** is prioritized over CUDA for better InsightFace compatibility
- **CUDA Compute Capability 7.5** (Tesla T4 / V100) fully supported
- **H.264 NVENC** hardware encoding for faster video creation

### Verify GPU Setup
```python
import onnxruntime as ort
print(ort.get_available_providers())
# Should show: ['TensorrtExecutionProvider', 'CUDAExecutionProvider', 'CPUExecutionProvider']
```

## 📊 Performance Expectations

### Tesla T4 (Colab Free Tier)
- **Face Detection**: ~200ms per frame (GPU-accelerated)
- **Face Swapping**: ~1-1.5s per frame
- **Face Enhancement**: ~0.5-1s per frame
- **Total**: ~2-3 minutes per minute of video

### V100 (Colab Pro)
- **Total**: ~1-2 minutes per minute of video

## ⚙️ Recommended Settings

```bash
python run.py -s source.jpg -t target.mp4 -o output.mp4 \
  --frame-processor face_swapper face_enhancer \
  --execution-provider cuda \
  --keep-fps \
  --many-faces \
  --max-memory 10 \
  --execution-threads 8 \
  --output-video-encoder h264_nvenc \
  --output-video-quality 18 \
  --temp-frame-format png \
  --temp-frame-quality 100
```

### Parameter Explanation

| Parameter | Value | Why |
|-----------|-------|-----|
| `frame-processor` | face_swapper face_enhancer | Swap faces + enhance quality |
| `execution-provider` | cuda | Use GPU acceleration |
| `keep-fps` | - | Preserve original video framerate |
| `many-faces` | - | Process all faces in video |
| `max-memory` | 10 | 10GB GPU memory limit (T4 safe) |
| `execution-threads` | 8 | Optimal for T4 GPU |
| `output-video-encoder` | h264_nvenc | Hardware-accelerated H.264 encoding |
| `output-video-quality` | 18 | High quality (0=best, 51=worst) |
| `temp-frame-format` | png | Lossless frame extraction |
| `temp-frame-quality` | 100 | Maximum frame quality |

## 🐛 Troubleshooting

### Problem: "Failed to load library libonnxruntime_providers_cuda.so"
**Solution**: The CUDA libraries weren't installed properly.
```bash
apt-get install -y libcuda11-0 libcublas11 libcufft10 libcudnn8
pip uninstall -y onnxruntime-gpu
pip install onnxruntime-gpu==1.15.1
```

### Problem: "Applied providers: ['CPUExecutionProvider']"
**Solution**: InsightFace is falling back to CPU. Check if:
1. CUDA libraries are installed (see above)
2. Restart the kernel after installation
3. Check TensorRT support: `python -c "import onnxruntime; print(onnxruntime.get_available_providers())"`

### Problem: "CUDA out of memory"
**Solutions** (in order):
1. Reduce `--max-memory` to 8 instead of 10
2. Remove `face_enhancer` processor
3. Process shorter videos
4. Use Colab Pro for V100 GPU

### Problem: "ffmpeg not found"
**Solution**:
```bash
apt-get install -y ffmpeg
```

## 📁 File Structure

```
roop/
├── ROOP_COLAB.ipynb          # Google Colab notebook
├── setup_colab.sh            # Setup script for manual installation
├── COLAB_SETUP.md            # This file
├── run.py                     # Main entry point
├── requirements.txt           # Python dependencies
└── roop/
    ├── core.py               # Core processing logic
    ├── face_analyser.py      # Face detection (with TensorRT support)
    └── ...
```

## 💡 Tips

1. **Batch Processing**: Process multiple videos in one session to save setup time
2. **Use Longer Videos**: The setup/teardown takes time; 1-2 minute videos are more efficient
3. **Monitor GPU**: Use `!nvidia-smi` to monitor GPU usage during processing
4. **Save Checkpoints**: Download intermediate results frequently
5. **Use PNG Frames**: Provides better quality than JPG during processing

## 🚀 Batch Processing Example

```python
from pathlib import Path
import subprocess

source = 'source/DanielaAS.jpg'
videos = list(Path('input_videos').glob('*.mp4'))

for i, video in enumerate(videos, 1):
    output = f'output_videos/{video.stem}_result.mp4'
    print(f"[{i}/{len(videos)}] Processing {video.name}...")

    subprocess.run([
        'python', 'run.py',
        '-s', source,
        '-t', str(video),
        '-o', output,
        '--frame-processor', 'face_swapper', 'face_enhancer',
        '--execution-provider', 'cuda',
        '--keep-fps', '--many-faces',
        '--max-memory', '10',
        '--execution-threads', '8',
        '--output-video-encoder', 'h264_nvenc',
        '--output-video-quality', '18',
        '--temp-frame-format', 'png'
    ])
```

## 📝 License

ROOP is a community project. This setup guide is provided for educational purposes.

## 🆘 Need Help?

- Check the [original ROOP repository](https://github.com/s0md3v/roop)
- Review GPU diagnostics with the diagnostic script
- Check Colab's system logs for CUDA-related errors
