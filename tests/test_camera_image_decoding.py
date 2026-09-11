"""Regression tests for camera image channels, colors, and BMP row layout."""

import struct
from io import BytesIO
from threading import Lock
from unittest.mock import Mock

import numpy as np
import pytest
from PIL import Image

from simworld.communicator.unrealcv import UnrealCV


@pytest.fixture
def rgb_pixels():
    """Use distinct colors and an odd width to expose swaps and row padding."""
    return np.array([
        [[255, 0, 0], [0, 255, 0], [0, 0, 255]],
        [[12, 34, 56], [78, 90, 123], [145, 167, 189]],
    ], dtype=np.uint8)


@pytest.fixture
def camera():
    """Create the real decoder without connecting to an Unreal server."""
    camera = UnrealCV.__new__(UnrealCV)
    camera.lock = Lock()
    camera.client = Mock()
    return camera


def encode_png(pixels, mode):
    """Encode PNGs with and without an alpha channel or a palette."""
    image = Image.fromarray(pixels).convert(mode)
    stream = BytesIO()
    image.save(stream, format='PNG')
    return stream.getvalue(), np.array(image.convert('RGB'))[:, :, ::-1]


def encode_bmp(pixels, bits_per_pixel, top_down):
    """Build uncompressed BMP fixtures with explicit orientation and padding."""
    height, width, _ = pixels.shape
    bgr = pixels[:, :, ::-1]
    if bits_per_pixel == 32:
        alpha = np.full((height, width, 1), 173, dtype=np.uint8)
        bgr = np.concatenate((bgr, alpha), axis=2)
    if not top_down:
        bgr = bgr[::-1]
    row_padding = b'\0' * ((-width * (bits_per_pixel // 8)) % 4)
    data = b''.join(row.tobytes() + row_padding for row in bgr)
    file_header = struct.pack('<2sIHHI', b'BM', 54 + len(data), 0, 0, 54)
    info_header = struct.pack(
        '<IiiHHIIiiII', 40, width, -height if top_down else height,
        1, bits_per_pixel, 0, len(data), 0, 0, 0, 0,
    )
    return file_header + info_header + data


@pytest.mark.parametrize('mode', ['RGB', 'RGBA', 'P', 'L'])
def test_png_always_returns_three_bgr_channels(camera, rgb_pixels, mode):
    """Dropping alpha must not discard blue or fail on palette/grayscale PNGs."""
    payload, expected = encode_png(rgb_pixels, mode)
    actual = camera._decode_png(payload)
    assert actual.shape == (2, 3, 3)
    assert actual.dtype == np.uint8
    np.testing.assert_array_equal(actual, expected)


@pytest.mark.parametrize('bits_per_pixel', [24, 32])
@pytest.mark.parametrize('top_down', [False, True])
def test_bmp_returns_bgr_with_correct_row_order(camera, rgb_pixels, bits_per_pixel, top_down):
    """BMP capture must preserve colors and orientation for either row layout."""
    payload = encode_bmp(rgb_pixels, bits_per_pixel, top_down)
    actual = camera._decode_bmp(payload)
    assert actual.shape == (2, 3, 3)
    assert actual.dtype == np.uint8
    np.testing.assert_array_equal(actual, rgb_pixels[:, :, ::-1])


@pytest.mark.parametrize('viewmode', ['lit', 'object_mask'])
@pytest.mark.parametrize('mode,encoding', [('direct', 'png'), ('fast', 'bmp')])
def test_camera_modes_preserve_the_same_bgr_colors(camera, rgb_pixels, viewmode, mode, encoding):
    """The public image API must not change colors when switching transport."""
    if encoding == 'png':
        payload, expected = encode_png(rgb_pixels, 'RGB')
    else:
        payload = encode_bmp(rgb_pixels, 24, False)
        expected = rgb_pixels[:, :, ::-1]
    camera.client.request.return_value = payload

    actual = camera.get_image(7, viewmode, mode=mode)

    camera.client.request.assert_called_once_with(f'vget /camera/7/{viewmode} {encoding}')
    np.testing.assert_array_equal(actual, expected)
