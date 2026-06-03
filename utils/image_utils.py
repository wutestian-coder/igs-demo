import io

import cv2
import numpy as np
from PIL import Image


def png_bytes_to_array(png_bytes: bytes) -> np.ndarray:
    img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def calc_frame_diff(frame1: np.ndarray, frame2: np.ndarray) -> float:
    return float(cv2.absdiff(frame1, frame2).mean())


def is_motion_stopped(frame1: np.ndarray, frame2: np.ndarray, threshold: float) -> bool:
    return calc_frame_diff(frame1, frame2) < threshold
