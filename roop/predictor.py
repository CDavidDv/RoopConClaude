import threading
import numpy
from PIL import Image

from roop.typing import Frame

PREDICTOR = None
THREAD_LOCK = threading.Lock()
MAX_PROBABILITY = 0.85


def get_predictor():
    return None


def clear_predictor() -> None:
    global PREDICTOR
    PREDICTOR = None


def predict_frame(target_frame: Frame) -> bool:
    return False


def predict_image(target_path: str) -> bool:
    return False


def predict_video(target_path: str) -> bool:
    return False
