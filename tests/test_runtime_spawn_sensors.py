"""Regression coverage for runtime actor sensor registration and spawn failures."""

import json
from threading import Lock
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from simworld.communicator.communicator import Communicator
from simworld.communicator.unrealcv import UnrealCV
from simworld.utils.vector import Vector


@pytest.fixture
def client():
    """Exercise the production protocol methods without requiring Unreal Engine."""
    client = UnrealCV.__new__(UnrealCV)
    client.lock = Lock()
    client.client = Mock()
    client.client.request.return_value = 'ok'
    return client


def commands(client):
    """Return commands observed at the network boundary."""
    return [call.args[0] for call in client.client.request.call_args_list]


@pytest.mark.parametrize('kind', ['object', 'agent', 'scooter', 'vehicles', 'pedestrians', 'traffic_signals', 'waypoint_mark'])
def test_runtime_spawners_register_after_placement_and_mobility(client, kind):
    """All rendered runtime actors need annotation at their final initial pose."""
    communicator = Communicator(client)
    actor = SimpleNamespace(id=7, position=Vector(150, 250), direction=Vector(0, 1),
                            vehicle_reference='/Game/Vehicle.Vehicle_C', type='both')
    model = '/Game/Actor.Actor_C'
    if kind == 'object':
        communicator.spawn_object('Box', model, (150, 250, 100), (0, 90, 0))
    elif kind == 'agent':
        communicator.spawn_agent(actor, None, position=(150, 250, 100), model_path=model)
    elif kind == 'scooter':
        communicator.spawn_scooter(actor, model)
    elif kind in ('vehicles', 'pedestrians', 'traffic_signals'):
        getattr(communicator, f'spawn_{kind}')([actor])
    else:
        communicator.spawn_waypoint_mark([actor], model)

    sent = commands(client)
    name = sent[0].split()[-1]
    labels = [command for command in sent if command.startswith(f'vset /object/{name}/color ')]
    assert len(labels) == 1, f'{kind} did not register the actor for depth/object_mask'
    rgb = tuple(map(int, labels[0].split()[-3:]))
    assert all(0 <= value <= 255 for value in rgb)
    assert rgb != (0, 0, 0)
    for setting in ('location', 'rotation', 'scale', 'collision', 'object_mobility'):
        placement = next(command for command in sent if command.startswith(f'vset /object/{name}/{setting} '))
        assert sent.index(placement) < sent.index(labels[0])


def test_default_labels_are_stable_and_actor_specific(client):
    """A repeated actor name retains its label without Python's randomized hash."""
    client.set_color('Box')
    client.set_color('Pedestrian')
    client.set_color('Box')
    colors = [command.split()[-3:] for command in commands(client)]
    assert colors[0] == colors[2]
    assert colors[0] != colors[1]


def test_explicit_label_is_preserved(client):
    """Existing semantic palettes must still send the exact requested RGB value."""
    client.set_color('Road', (12, 34, 56))
    assert commands(client) == ['vset /object/Road/color 12 34 56']


@pytest.mark.parametrize('response', ['error Can not find object', None])
def test_registration_failure_is_reported(client, response):
    """A missing annotation must not silently look like a successful spawn."""
    client.client.request.return_value = response
    with pytest.raises(RuntimeError, match='Road'):
        client.set_color('Road', (12, 34, 56))


@pytest.mark.parametrize('response', ['error Can not load asset', 'Error: unavailable', None, ''])
def test_failed_spawn_stops_before_object_configuration(client, response):
    """Never send physics or mobility commands for an actor that did not spawn."""
    client.client.request.return_value = response
    with pytest.raises(RuntimeError, match='MissingBox'):
        Communicator(client).spawn_object('MissingBox', '/Game/Missing.Missing_C', (0, 0, 0), (0, 0, 0))
    assert commands(client) == ['vset /objects/spawn_bp_asset /Game/Missing.Missing_C MissingBox']


@pytest.mark.parametrize('response', ['ok', 'Box'])
def test_spawn_accepts_success_and_actor_name_responses(client, response):
    """The official packaged backend responds with the spawned actor name."""
    client.client.request.return_value = response
    client.spawn_bp_asset('/Game/Box.Box_C', 'Box')


@pytest.mark.parametrize('run_time', [True, False])
def test_world_generation_preserves_palette_after_placement(client, tmp_path, run_time):
    """Static city assets retain their configured semantic colors and final pose."""
    world = tmp_path / 'world.json'
    assets = tmp_path / 'assets.json'
    world.write_text(json.dumps({'nodes': [{
        'id': 'Building', 'instance_name': 'BuildingModel',
        'properties': {'location': {'x': 10, 'y': 20, 'z': 0},
                       'orientation': {'pitch': 0, 'yaw': 90, 'roll': 0},
                       'scale': {'x': 2, 'y': 3, 'z': 4}},
    }]}), encoding='utf-8')
    assets.write_text(json.dumps({
        'BuildingModel': {'asset_path': '/Game/Building.Building_C', 'color': 'building'},
        'colors': {'building': '(R=12,G=34,B=56)'},
    }), encoding='utf-8')
    assert Communicator(client).generate_world(world, assets, run_time=run_time) == {'Building'}
    sent = commands(client)
    label = 'vset /object/Building/color 12 34 56'
    if run_time:
        assert sent[-1] == label
    else:
        assert label not in sent
