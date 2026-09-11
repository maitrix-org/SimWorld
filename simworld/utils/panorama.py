"""Project six perspective camera views into 2:1 equirectangular videos."""

import math
import os
from numbers import Integral

import cv2
import numpy as np

# Unreal coordinates: +X forward, +Y right, +Z up. Each face is square,
# has a 90-degree horizontal field of view, and uses (pitch, yaw, roll).
CUBEMAP_ROTATIONS = {
    'front': (0, 0, 0),
    'right': (0, 90, 0),
    'back': (0, 180, 0),
    'left': (0, -90, 0),
    'up': (90, 0, 0),
    'down': (-90, 0, 0),
}

# Forward, image-right and image-up vectors for the rotations above.
_FACE_AXES = {
    'front': ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
    'right': ((0, 1, 0), (-1, 0, 0), (0, 0, 1)),
    'back': ((-1, 0, 0), (0, -1, 0), (0, 0, 1)),
    'left': ((0, -1, 0), (1, 0, 0), (0, 0, 1)),
    'up': ((0, 0, 1), (0, 1, 0), (-1, 0, 0)),
    'down': ((0, 0, -1), (0, 1, 0), (1, 0, 0)),
}


class CubemapProjector:
    """Reuse projection maps to convert BGR cubemaps to ERP frames.

    Longitude zero (+X/front) is at the image center; +Y/right is at three
    quarters of its width. The back face wraps across both image edges.
    +Z/up is at the top. All six inputs must share one optical center and
    simulation instant. This class performs projection, not camera capture.
    """

    def __init__(self, face_size, resolution=(1440, 720)):
        """Precompute maps for square faces and a (width, height) ERP output."""
        if isinstance(face_size, bool) or not isinstance(face_size, Integral) or face_size < 1:
            raise ValueError('face_size must be a positive integer')
        if len(resolution) != 2 or any(
            isinstance(size, bool) or not isinstance(size, Integral) or size < 1
            for size in resolution
        ):
            raise ValueError('resolution must contain two positive integers')
        width, height = resolution
        if width != 2 * height:
            raise ValueError('ERP resolution must have a 2:1 width-to-height ratio')
        if max(face_size, width, height) >= 32767:
            raise ValueError('Image dimensions must be below 32767 for OpenCV remap')
        self.face_size = int(face_size)
        self.resolution = (int(width), int(height))

        longitude = ((np.arange(width, dtype=np.float32) + 0.5) / width - 0.5) * (2 * np.pi)
        latitude = (0.5 - (np.arange(height, dtype=np.float32) + 0.5) / height) * np.pi
        lon, lat = np.meshgrid(longitude, latitude)
        rays = np.stack((np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)), axis=-1)
        forwards = np.array([axes[0] for axes in _FACE_AXES.values()], dtype=np.float32)
        face_indices = np.argmax(rays @ forwards.T, axis=-1)
        self._maps = []
        for index, (name, (forward, right, up)) in enumerate(_FACE_AXES.items()):
            mask = face_indices == index
            # Only selected rays face this camera; avoid division by zero
            # for the unused pixels in the full-sized OpenCV remap arrays.
            distance = np.where(mask, rays @ np.array(forward, dtype=np.float32), 1.0)
            u = (rays @ np.array(right, dtype=np.float32)) / distance
            v = -(rays @ np.array(up, dtype=np.float32)) / distance
            map_x = ((u + 1) * face_size / 2 - 0.5).astype(np.float32)
            map_y = ((v + 1) * face_size / 2 - 0.5).astype(np.float32)
            self._maps.append((name, mask, map_x, map_y))

    def project(self, faces):
        """Return an ERP BGR uint8 frame from six named BGR uint8 arrays.

        Args:
            faces: Mapping with front, right, back, left, up and down keys.
                Each value has shape (face_size, face_size, 3), with BGR
                channels as returned by SimWorld's camera observations.

        Raises:
            ValueError: A face is missing or has an incompatible shape/dtype.
        """
        if set(faces) != set(_FACE_AXES):
            raise ValueError('faces must contain exactly front, right, back, left, up and down')
        expected_shape = (self.face_size, self.face_size, 3)
        for name, face in faces.items():
            if not isinstance(face, np.ndarray) or face.shape != expected_shape or face.dtype != np.uint8:
                raise ValueError(f'{name} must be a uint8 BGR array with shape {expected_shape}')
        width, height = self.resolution
        frame = np.empty((height, width, 3), dtype=np.uint8)
        for name, mask, map_x, map_y in self._maps:
            sampled = cv2.remap(
                faces[name], map_x, map_y, cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_REPLICATE,
            )
            frame[mask] = sampled[mask]
        return frame


def save_panorama_video(cubemap_frames, video_path, resolution=(1440, 720), fps=25.0):
    """Stream cubemap recordings into an MP4 with 2:1 ERP pixel projection.

    Args:
        cubemap_frames: Iterable of six-face mappings accepted by
            CubemapProjector.project. A generator can capture frames on demand.

        video_path: Output MP4 path; its parent directory must exist.

        resolution: Output (width, height), with width == 2 * height and an
            even height so the video codec does not crop odd dimensions.

        fps: Positive, finite playback frame rate, independent of capture speed.

    Returns:
        Output path as a string. No spherical-player metadata is inserted.

    Raises:
        ValueError: Frames are empty or invalid, or encoding parameters are invalid.
        RuntimeError: OpenCV cannot open the output video writer.
    """
    if not math.isfinite(fps) or fps <= 0:
        raise ValueError('fps must be positive and finite')
    frames = iter(cubemap_frames)
    try:
        first = next(frames)
    except StopIteration as error:
        raise ValueError('At least one cubemap frame is required') from error
    front = first.get('front')
    if not isinstance(front, np.ndarray) or front.ndim != 3:
        raise ValueError('front must be a square uint8 BGR array')
    projector = CubemapProjector(front.shape[0], resolution)
    if projector.resolution[1] % 2:
        raise ValueError('Video height must be even to avoid codec cropping')
    image = projector.project(first)
    video_path = os.fspath(video_path)
    writer = cv2.VideoWriter(video_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, projector.resolution)
    try:
        if not writer.isOpened():
            raise RuntimeError(f'Could not open video writer: {video_path}')
        writer.write(image)
        for faces in frames:
            writer.write(projector.project(faces))
    finally:
        writer.release()
    return video_path
