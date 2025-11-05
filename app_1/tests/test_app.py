# tests/test_app.py
import pytest
from app_1 import app, workouts
from datetime import datetime

@pytest.fixture(autouse=True)
def clear_workouts():
    """
    Runs before each test to ensure global `workouts` list is clean.
    """
    # Clear and reset to known state
    workouts.clear()
    yield
    workouts.clear()

@pytest.fixture
def client():
    app.config['TESTING'] = True
    # Turn off debug log noise if desired:
    app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False
    with app.test_client() as client:
        yield client

def test_index_renders(client):
    resp = client.get('/')
    assert resp.status_code == 200
    # basic check that response contains a HTML opening tag (template required in real run)
    assert b'<!DOCTYPE html' in resp.data or b'<html' in resp.data

def test_add_workout_success(client):
    resp = client.post('/add_workout', data={'workout': 'Run', 'duration': '30'}, follow_redirects=True)
    assert resp.status_code == 200
    # Check that workouts list updated
    assert len(workouts) == 1
    w = workouts[0]
    assert w['workout'] == 'Run'
    assert w['duration'] == 30
    assert 'timestamp' in w

def test_add_workout_missing_fields(client):
    resp = client.post('/add_workout', data={'workout': '', 'duration': ''}, follow_redirects=True)
    assert resp.status_code == 200
    # No new workouts
    assert len(workouts) == 0
    # Should have flashed an error — flash renders into the HTML, so check message string appears
    assert b'Please enter both workout and duration.' in resp.data

def test_add_workout_invalid_duration(client):
    resp = client.post('/add_workout', data={'workout': 'Swim', 'duration': 'abc'}, follow_redirects=True)
    assert resp.status_code == 200
    assert len(workouts) == 0
    assert b'Duration must be a positive number.' in resp.data

def test_add_workout_negative_duration(client):
    resp = client.post('/add_workout', data={'workout': 'Bike', 'duration': '-5'}, follow_redirects=True)
    assert resp.status_code == 200
    assert len(workouts) == 0
    # your code currently raises and flashes 'Duration must be a positive number.' on ValueError,
    # so we look for that message or the generic message path.
    assert b'Duration must be a positive number.' in resp.data or b'Duration must be positive' in resp.data

def test_delete_workout(client):
    # prepare one workout
    workouts.append({
        'id': 1,
        'workout': 'Pushups',
        'duration': 10,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    assert len(workouts) == 1
    resp = client.post('/delete_workout/1', follow_redirects=True)
    assert resp.status_code == 200
    assert len(workouts) == 0
    assert b'Workout deleted successfully!' in resp.data

def test_api_get_workouts(client):
    workouts.append({'id': 1, 'workout': 'Yoga', 'duration': 20, 'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
    resp = client.get('/api/workouts')
    assert resp.status_code == 200
    json_data = resp.get_json()
    assert isinstance(json_data, list)
    assert len(json_data) == 1
    assert json_data[0]['workout'] == 'Yoga'
