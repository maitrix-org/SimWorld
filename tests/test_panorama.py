"""Check panorama geometry and actual MP4 encoding without an Unreal server."""

from unittest.mock import Mock

import cv2
import numpy as np
import pytest

from simworld.utils.panorama import CubemapProjector, save_panorama_video


def solid_faces(size=32, color=None):
    """Create distinct face colors or a single constant-color sphere."""
    colors = {
        'front': (0, 0, 255), 'right': (0, 255, 0), 'back': (255, 0, 0),
        'left': (0, 255, 255), 'up': (255, 0, 255), 'down': (255, 255, 0),
    }
    return {name: np.full((size, size, 3), rgb if color is None else color, dtype=np.uint8)
            for name, rgb in colors.items()}


def direction_faces(size=64):
    """Render an analytic direction-colored sphere with yaw/pitch matrices."""
    rotations = {'front': (0, 0), 'right': (0, 90), 'back': (0, 180),
                 'left': (0, -90), 'up': (90, 0), 'down': (-90, 0)}
    coordinates = (np.arange(size) + 0.5) / size * 2 - 1
    right, down = np.meshgrid(coordinates, coordinates)
    local = np.stack((np.ones_like(right), right, -down), axis=-1)
    local /= np.linalg.norm(local, axis=-1, keepdims=True)
    faces = {}
    for name, (pitch, yaw) in rotations.items():
        pitch, yaw = np.radians([pitch, yaw])
        cp, sp, cy, sy = np.cos(pitch), np.sin(pitch), np.cos(yaw), np.sin(yaw)
        rotation = np.array([[cp * cy, -sy, -sp * cy],
                             [cp * sy, cy, -sp * sy], [sp, 0, cp]])
        world = local @ rotation.T
        faces[name] = np.rint((world + 1) * 127.5).astype(np.uint8)
    return faces


def test_cardinal_directions_and_poles():
    """The panorama contains all six faces in the documented orientation."""
    faces = solid_faces()
    image = CubemapProjector(32, (256, 128)).project(faces)
    assert image.shape == (128, 256, 3)
    assert image.dtype == np.uint8
    for name, (row, col) in {
        'front': (64, 128), 'right': (64, 192), 'back': (64, 0),
        'left': (64, 64), 'up': (0, 128), 'down': (127, 128),
    }.items():
        np.testing.assert_array_equal(image[row, col], faces[name][0, 0])
    np.testing.assert_array_equal(image[64, -1], faces['back'][0, 0])


def test_projection_matches_independent_analytic_sphere():
    """Per-pixel world directions catch mirrored faces and incorrect pole rolls."""
    image = CubemapProjector(64, (256, 128)).project(direction_faces())
    longitude = (np.arange(256) + 0.5) * (2 * np.pi / 256) - np.pi
    latitude = np.pi / 2 - (np.arange(128) + 0.5) * (np.pi / 128)
    expected = np.empty((128, 256, 3))
    expected[:, :, 0] = np.outer(np.cos(latitude), np.cos(longitude))
    expected[:, :, 1] = np.outer(np.cos(latitude), np.sin(longitude))
    expected[:, :, 2] = np.sin(latitude)[:, None]
    error = np.abs(image.astype(float) - (expected + 1) * 127.5)
    assert error.max() < 3
    assert error.mean() < 0.5


@pytest.mark.parametrize('resolution', [(128, 128), (0, 0), (128.0, 64), (128, -64), (128,), (65536, 32768)])
def test_rejects_invalid_resolution(resolution):
    """Reject dimensions that cannot represent a complete ERP image."""
    with pytest.raises(ValueError):
        CubemapProjector(32, resolution)


@pytest.mark.parametrize('size', [0, -1, 2.5, True, 32767])
def test_rejects_invalid_face_size(size):
    """Require positive square dimensions supported by OpenCV."""
    with pytest.raises(ValueError):
        CubemapProjector(size, (128, 64))


@pytest.mark.parametrize('problem', ['missing', 'extra', 'size', 'dtype', 'channels', 'none'])
def test_rejects_incompatible_faces(problem):
    """Malformed frames must not silently produce incomplete panoramas."""
    faces = solid_faces()
    if problem == 'missing':
        del faces['up']
    elif problem == 'extra':
        faces['extra'] = faces['front']
    elif problem == 'size':
        faces['up'] = np.zeros((31, 32, 3), dtype=np.uint8)
    elif problem == 'dtype':
        faces['up'] = faces['up'].astype(np.float32)
    elif problem == 'channels':
        faces['up'] = faces['up'][:, :, 0]
    else:
        faces['up'] = None
    with pytest.raises(ValueError):
        CubemapProjector(32, (128, 64)).project(faces)


def test_mp4_round_trip_preserves_dimensions_fps_frames_and_colors(tmp_path):
    """Encode a real MP4 and inspect every decoded frame with OpenCV."""
    colors = [(0, 0, 255), (0, 255, 0), (255, 0, 0)]
    path = tmp_path / 'panorama.mp4'
    result = save_panorama_video((solid_faces(color=color) for color in colors), path, (128, 64), fps=12)
    assert result == str(path)
    capture = cv2.VideoCapture(str(path))
    try:
        assert capture.isOpened()
        assert capture.get(cv2.CAP_PROP_FRAME_WIDTH) == 128
        assert capture.get(cv2.CAP_PROP_FRAME_HEIGHT) == 64
        assert capture.get(cv2.CAP_PROP_FPS) == pytest.approx(12)
        assert capture.get(cv2.CAP_PROP_FRAME_COUNT) == 3
        for color in colors:
            ok, frame = capture.read()
            assert ok
            assert frame.shape == (64, 128, 3)
            np.testing.assert_allclose(frame.mean(axis=(0, 1)), color, atol=6)
        assert not capture.read()[0]
    finally:
        capture.release()


def test_direction_sphere_video_round_trip(tmp_path):
    """Save a visible ERP fixture and verify its geometry survives encoding."""
    faces = direction_faces(128)
    expected = CubemapProjector(128, (512, 256)).project(faces)
    assert cv2.imwrite(str(tmp_path / 'synthetic-erp-reference.png'), expected)
    path = tmp_path / 'synthetic-erp.mp4'
    save_panorama_video((faces for _ in range(24)), path, (512, 256), fps=12)
    capture = cv2.VideoCapture(str(path))
    try:
        assert capture.isOpened()
        for _ in range(24):
            ok, frame = capture.read()
            assert ok
            assert frame.shape == expected.shape
            assert np.abs(frame.astype(float) - expected).mean() < 3
        assert not capture.read()[0]
    finally:
        capture.release()


def test_export_consumes_frames_incrementally_and_releases_writer(tmp_path, monkeypatch):
    """Write each frame before asking a potentially unbounded source for more."""
    writer = Mock()
    monkeypatch.setattr(cv2, 'VideoWriter', Mock(return_value=writer))

    def frames():
        for index in range(3):
            assert writer.write.call_count == index
            yield solid_faces()

    save_panorama_video(frames(), tmp_path / 'panorama.mp4', (128, 64))
    assert writer.write.call_count == 3
    writer.release.assert_called_once()


def test_invalid_later_frame_releases_writer(tmp_path, monkeypatch):
    """Flush already written frames when a capture or projection fails."""
    writer = Mock()
    monkeypatch.setattr(cv2, 'VideoWriter', Mock(return_value=writer))
    with pytest.raises(ValueError):
        save_panorama_video([solid_faces(), {}], tmp_path / 'panorama.mp4', (128, 64))
    writer.write.assert_called_once()
    writer.release.assert_called_once()


def test_source_failure_releases_writer(tmp_path, monkeypatch):
    """Do not leak the encoder when the source raises during capture."""
    writer = Mock()
    monkeypatch.setattr(cv2, 'VideoWriter', Mock(return_value=writer))

    def frames():
        yield solid_faces()
        raise RuntimeError('capture failed')

    with pytest.raises(RuntimeError, match='capture failed'):
        save_panorama_video(frames(), tmp_path / 'panorama.mp4', (128, 64))
    writer.release.assert_called_once()


def test_writer_open_failure_is_reported(tmp_path, monkeypatch):
    """A missing codec or unwritable path must not be reported as success."""
    writer = Mock()
    writer.isOpened.return_value = False
    monkeypatch.setattr(cv2, 'VideoWriter', Mock(return_value=writer))
    with pytest.raises(RuntimeError, match='Could not open video writer'):
        save_panorama_video([solid_faces()], tmp_path / 'panorama.mp4', (128, 64))
    writer.write.assert_not_called()
    writer.release.assert_called_once()


@pytest.mark.parametrize('fps', [0, -1, float('nan'), float('inf')])
def test_rejects_invalid_fps(tmp_path, fps):
    """Frame rates must be finite and positive."""
    with pytest.raises(ValueError, match='fps'):
        save_panorama_video([solid_faces()], tmp_path / 'panorama.mp4', fps=fps)


def test_empty_source_does_not_create_output(tmp_path):
    """Report an empty recording before creating an unusable file."""
    path = tmp_path / 'panorama.mp4'
    with pytest.raises(ValueError, match='At least one'):
        save_panorama_video(iter(()), path)
    assert not path.exists()


def test_odd_video_height_is_rejected_before_encoding(tmp_path):
    """Reject video dimensions that would silently crop the ERP aspect ratio."""
    path = tmp_path / 'panorama.mp4'
    with pytest.raises(ValueError, match='height must be even'):
        save_panorama_video([solid_faces()], path, (126, 63))
    assert not path.exists()
