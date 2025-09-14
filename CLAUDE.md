# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Roop is a deep learning-based face replacement tool for videos and images. It uses AI models to swap faces in media content using just a single source image. The project is now discontinued but still functional.

## Development Commands

### Installation
```bash
# Install dependencies (choose based on use case)
pip install -r requirements.txt          # Full GUI version
pip install -r requirements-headless.txt # Headless version only
```

### Running the Application
```bash
# GUI mode
python run.py

# Headless mode (command line)
python run.py -s source_image.jpg -t target_video.mp4 -o output.mp4

# With specific frame processors
python run.py -s source.jpg -t target.mp4 -o output.mp4 --frame-processor face_swapper face_enhancer
```

### Code Quality Tools
```bash
# Linting with flake8
flake8

# Type checking with mypy
mypy roop/
```

## Architecture Overview

### Core Structure
- **`run.py`**: Entry point that calls `roop.core.run()`
- **`roop/core.py`**: Main application logic, argument parsing, and orchestration
- **`roop/globals.py`**: Global configuration variables and state
- **`roop/ui.py`**: GUI interface using customtkinter
- **`roop/utilities.py`**: Shared utility functions for file handling, video processing

### Key Modules
- **`face_analyser.py`**: Face detection and analysis using InsightFace
- **`face_reference.py`**: Reference face selection and management
- **`capturer.py`**: Frame capture functionality
- **`predictor.py`**: Image/video processing prediction logic
- **`metadata.py`**: Application metadata and versioning

### Frame Processors
Located in `roop/processors/frame/`:
- **`face_swapper.py`**: Core face swapping functionality
- **`face_enhancer.py`**: Face enhancement using GFPGAN
- **`core.py`**: Frame processor management and loading

### Configuration Management
- Global state managed through `roop.globals` module
- Command-line arguments parsed in `core.py` and stored as global variables
- Two execution modes: GUI (`ui.py`) and headless (command-line only)

## Development Guidelines

### Code Style
- **Functional programming only** - no OOP/classes allowed (per CONTRIBUTING.md)
- Follow existing naming conventions and module structure
- Use type hints (configured in `mypy.ini` with strict settings)
- No code comments - use descriptive naming instead

### Dependencies
- **Core ML**: ONNX Runtime, TensorFlow, InsightFace, OpenCV
- **GUI**: customtkinter, tkinterdnd2
- **Enhancement**: GFPGAN for face quality improvement
- **Platform-specific ONNX**: Different providers for CPU/GPU/Apple Silicon

### Testing
- Verify functionality with both GUI and headless modes
- Test with different execution providers (CPU, CUDA, etc.)
- Ensure proper memory management (TensorFlow GPU memory is limited to 1024MB)

### Key Technical Details
- Single-threaded execution optimizes CUDA performance
- Frame processors are dynamically loaded modules
- Temporary frame extraction supports JPG/PNG formats
- Multiple video encoders supported (H.264, H.265, VP9, NVENC)
- Face distance threshold configurable for recognition accuracy