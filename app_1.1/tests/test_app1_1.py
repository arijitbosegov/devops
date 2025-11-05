import pytest
from app1_1 import app, workouts
from datetime import datetime

@pytest.fixture(autouse=True)
def reset_workouts():
    """Clear workouts dict before each test to isolate state."""
    for key in workouts.keys():
        workouts[key].clear()
    yield
    for key in workouts.keys():
        workouts[key].clear()

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

# --- Core Page Tests ---

def test_index_route(client):
    resp = client.get('/')
    assert resp.status_code == 200
    # page should have HTML markup (minimal template works too)
    assert b'<html' in resp.data or b'<!doctype' in resp.data

def test_summary_page(client):
    resp = client.get('/summary')
    assert resp.status_code == 200
    assert b'Good start' in resp.data or b'Nice effort' in resp.data or b'Excellent dedication' in resp.data

# --- Add Workout Tests ---

def test_add_workout_success(client):
    resp = client.post('/add_workout', data={
        'category': 'Workout',
        'workout': 'Pushups',
        'duration': '20'
    }, follow_redirects=True)

    assert resp.status_code == 200
    assert len(workouts['Workout']) == 1
    entry = workouts['Workout'][0]
    assert entry['exercise'] == 'Pushups'
    assert entry['duration'] == 20
    assert b'Pushups added' in resp.data

def test_add_workout_missing_fields(client):
    resp = client.post('/add_workout', data={
        'category': 'Warm-up',
        'workout': '',
        'duration': ''
    }, follow_redirects=True)
    assert b'Please enter both exercise and duration.' in resp.data
    assert all(len(v) == 0 for v in workouts.values())

def test_add_workout_invalid_duration(client):
    resp = client.post('/add_workout', data={
        'category': 'Workout',
        'workout': 'Run',
        'duration': 'abc'
    }, follow_redirects=True)
    assert b'Duration must be a positive number.' in resp.data
    assert len(workouts['Workout']) == 0

def test_add_workout_negative_duration(client):
    resp = client.post('/add_workout', data={
        'category': 'Cool-down',
        'workout': 'Stretch',
        'duration': '-10'
    }, follow_redirects=True)
    assert b'Duration must be a positive number.' in resp.data
    assert len(workouts['Cool-down']) == 0

# --- Delete Workout Tests ---

def test_delete_workout(client):
    # manually add a workout to delete
    workouts['Workout'].append({
        'id': 1,
        'exercise': 'Jogging',
        'duration': 15,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    assert len(workouts['Workout']) == 1

    resp = client.post('/delete_workout/Workout/1', follow_redirects=True)
    assert resp.status_code == 200
    assert len(workouts['Workout']) == 0
    assert b'Workout deleted successfully!' in resp.data

# --- API Tests ---

def test_get_workouts_api(client):
    workouts['Warm-up'].append({
        'id': 1, 'exercise': 'Jumping Jacks',
        'duration': 5, 'timestamp': '2025-11-05 10:00:00'
    })
    resp = client.get('/api/workouts')
    data = resp.get_json()
    assert resp.status_code == 200
    assert 'Warm-up' in data
    assert data['Warm-up'][0]['exercise'] == 'Jumping Jacks'

def test_get_stats_api(client):
    workouts['Workout'].append({'id': 1, 'exercise': 'Run', 'duration': 30, 'timestamp': 't'})
    workouts['Cool-down'].append({'id': 2, 'exercise': 'Stretch', 'duration': 10, 'timestamp': 't'})
    resp = client.get('/api/stats')
    data = resp.get_json()
    assert resp.status_code == 200
    assert data['total_time'] == 40
    assert data['total_workouts'] == 2
    assert 'by_category' in data
    assert data['by_category']['Workout']['total_minutes'] == 30
    assert data['by_category']['Cool-down']['count'] == 1
