"""Verify runtime actor sensors on a dedicated Base20260201 empty-map server.

Run from the repository root with ``python -m examples.verify_runtime_sensors
--port 19090 --output sensor-evidence``. Saves raw captures and exits nonzero if
boxes, humanoids, or vehicles are missing from depth or object_mask after spawning
or moving. The script creates a camera and three actors, then removes them.
"""

import argparse
import hashlib
import json
import re
import time
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from PIL import Image

from simworld.communicator.communicator import Communicator
from simworld.communicator.unrealcv import UnrealCV
from simworld.utils.vector import Vector


def capture(request, camera, output):
    """Save the server's original PNG/NPY bytes without client visualization."""
    output.mkdir(parents=True, exist_ok=True)
    images = {}
    for mode, extension in [('lit', 'png'), ('depth', 'npy'), ('object_mask', 'png')]:
        payload = request(f'vget /camera/{camera}/{mode} {extension}')
        if not isinstance(payload, bytes):
            raise RuntimeError(f'{mode} capture failed: {payload!r}')
        (output / f'{mode}.{extension}').write_bytes(payload)
        if extension == 'npy':
            images[mode] = np.load(BytesIO(payload), allow_pickle=False)
        else:
            images[mode] = np.asarray(Image.open(BytesIO(payload)).convert('RGB'))
    return images


def measure(images, background, colors):
    """Measure each actor's mask area and foreground depth at those same pixels."""
    results = {}
    for name, color in colors.items():
        region = np.all(images['object_mask'] == color, axis=-1)
        ys, xs = np.nonzero(region)
        count = int(region.sum())
        closer = images['depth'][region] < background['depth'][region] - 1.0
        results[name] = {
            'rgb': color, 'mask_pixels': count,
            'centroid_x': float(xs.mean()) if count else None,
            'centroid_y': float(ys.mean()) if count else None,
            'foreground_depth_fraction': float(closer.mean()) if count else 0.0,
            'median_depth_cm': float(np.median(images['depth'][region])) if count else None,
            'median_background_depth_cm': float(np.median(background['depth'][region])) if count else None,
            'passed': count > 50 and float(closer.mean()) > 0.9,
        }
    return results


def main():
    """Exercise public spawn methods, capture evidence, and check moving actors."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, required=True, help='Port of a dedicated empty-map server')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    ucv = UnrealCV(port=args.port, resolution=(640, 480))
    communicator = Communicator(ucv)
    original_request = ucv.client.request
    transcript = []

    def request(command, *positional, **kwargs):
        """Record the real protocol exchange, hashing binary responses."""
        if not positional:
            kwargs.setdefault('timeout', 30)
        response = original_request(command, *positional, **kwargs)
        record = {'command': command}
        if isinstance(response, bytes):
            record.update(bytes=len(response), sha256=hashlib.sha256(response).hexdigest())
        else:
            record['response'] = response
        transcript.append(record)
        return response

    ucv.client.request = request
    box = 'SensorCheckBox'
    human = SimpleNamespace(id='sensor_check', position=Vector(0, 0), direction=Vector(-1, 0))
    vehicle = SimpleNamespace(id='sensor_check', position=Vector(0, 450), direction=Vector(1, 0),
                              vehicle_reference='/Game/TrafficSystem/Vehicle/Vehicle1.Vehicle1_C')
    names = [box, communicator.get_humanoid_name(human.id), communicator.get_vehicle_name(vehicle.id)]
    created = []
    camera_actor = None
    summary = {}
    try:
        existing = ucv.get_objects()
        if any(name in existing for name in names):
            raise RuntimeError('SensorCheck actors already exist; use a fresh dedicated empty-map server')
        (args.output / 'status.txt').write_text(str(request('vget /unrealcv/status')), encoding='utf-8')
        cameras_before = ucv.get_cameras().split()
        camera_actor = request('vset /cameras/spawn')
        if len(ucv.get_cameras().split()) != len(cameras_before) + 1:
            raise RuntimeError('Expected one new capture camera')
        # The endpoint lists sensor names, but capture commands take their indices.
        camera = len(cameras_before)
        ucv.set_camera_location(camera, (-1200, 0, 500))
        ucv.set_camera_rotation(camera, (-16, 0, 0))
        ucv.set_camera_resolution(camera, (640, 480))
        ucv.set_camera_fov(camera, 90)
        time.sleep(1)
        background = capture(request, camera, args.output / 'background')

        created.append(box)
        communicator.spawn_object(box, '/Game/CityDatabase/blueprints/BP_Box.BP_Box_C',
                                  (0, -350, 150), (0, 0, 0))
        ucv.set_scale((3, 3, 3), box)
        created.append(names[1])
        communicator.spawn_agent(human, None, position=(0, 0, 600))
        created.append(names[2])
        communicator.spawn_vehicles([vehicle])
        time.sleep(4)
        colors = {}
        for name in names:
            response = str(request(f'vget /object/{name}/color'))
            values = re.search(r'R=(\d+),G=(\d+),B=(\d+)', response)
            if values is None:
                raise RuntimeError(f'Cannot read {name} label: {response}')
            colors[name] = [int(value) for value in values.groups()]
        spawned = capture(request, camera, args.output / 'spawned')
        summary['spawned'] = measure(spawned, background, colors)
        summary['spawned_depth_identical_to_background'] = bool(np.array_equal(spawned['depth'], background['depth']))
        summary['spawned_mask_identical_to_background'] = bool(np.array_equal(spawned['object_mask'], background['object_mask']))

        for name, location in zip(names, [(0, -500, 150), (0, -150, 150), (0, 650, 150)]):
            ucv.set_location(location, name)
        time.sleep(2)
        moved = capture(request, camera, args.output / 'moved')
        summary['moved'] = measure(moved, background, colors)
        for name in names:
            before_x = summary['spawned'][name]['centroid_x']
            after_x = summary['moved'][name]['centroid_x']
            shift = abs(after_x - before_x) if before_x is not None and after_x is not None else 0.0
            summary['moved'][name]['centroid_shift_pixels'] = shift
            summary['moved'][name]['passed'] &= shift > 5
        summary['passed'] = all(result['passed'] for stage in ('spawned', 'moved') for result in summary[stage].values())
        (args.output / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
        print(json.dumps(summary, indent=2))
        if not summary['passed']:
            raise RuntimeError('Runtime sensor verification failed; see summary.json and raw captures')
    finally:
        try:
            existing = ucv.get_objects()
            for name in created + ([camera_actor] if camera_actor else []):
                if name in existing:
                    ucv.destroy(name)
        finally:
            (args.output / 'transcript.json').write_text(json.dumps(transcript, indent=2), encoding='utf-8')
            ucv.disconnect()


if __name__ == '__main__':
    main()
