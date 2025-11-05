import pytest
from app1_2 import app, workouts, workout_chart, diet_plans
from datetime import datetime

@pytest.fixture(autouse=True)
def clear_workouts():
    """Clear the workouts dict before and after each test."""
    for key in workouts.keys():
        workouts[key].clear()
    yield
    for key in workouts.keys():
        workouts[key].clear()

@pytest.fixture
def client():
    """Create a Flask test client."""
    app.config["TESTING"] = True
    app.config["PRESERVE_CONTEXT_ON_EXCEPTION"] = False
    with app.test_client() as client:
        yield client

# ---------------------------
# BASIC ROUTES
# ---------------------------

def test_index_route(client):
    resp = client.get('/')
    assert resp.status_code == 200
    assert b'<html' in resp.data or b'<!doctype' in resp.data

def test_summary_route(client):
    resp = client.get('/summary')
    assert resp.status_code == 200
    # The motivational text should match one of the expected phrases
    assert any(phrase.encode() in resp.data for phrase in [
        "Good start", "Nice effort", "Excellent dedication"
    ])

def test_workout_chart_page(client):
    resp = client.get('/workout-chart')
    assert resp.status_code == 200
    # Ensure that at least one workout name is present in HTML
    assert any(item.encode() in resp.data for item in workout_chart["Workout"])

def test_diet_chart_page(client):
    resp = client.get('/diet-chart')
    assert resp.status_code == 200
    # Check that at least one diet plan is visible
    assert any(item.encode() in resp.data for item in diet_plans["Weight Loss"])

# ---------------------------
# ADD WORKOUT TESTS
# ---------------------------

def test_add_workout_success(client):
    resp = client.post('/add_workout', data={
        'category': 'Workout',
        'workout': 'Push-ups',
        'duration': '15'
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert len(workouts['Workout']) == 1
    w = workouts['Workout'][0]
    assert w['exercise'] == 'Push-ups'
    assert w['duration'] == 15
    assert b'Push-ups added to Workout category successfully' in resp.data

def test_add_workout_missing_fields(client):
    resp = client.post('/add_workout', data={'workout': '', 'duration': ''}, follow_redirects=True)
    assert b'Please enter both exercise and duration' in resp.data
    assert all(len(v) == 0 for v in workouts.values())

def test_add_workout_invalid_duration(client):
    resp = client.post('/add_workout', data={'workout': 'Run', 'duration': 'abc'}, follow_redirects=True)
    assert b'Duration must be a positive number' in resp.data
    assert all(len(v) == 0 for v in workouts.values())

def test_add_workout_negative_duration(client):
    resp = client.post('/add_workout', data={'workout': 'Run', 'duration': '-5'}, follow_redirects=True)
    assert b'Duration must be a positive number' in resp.data
    assert all(len(v) == 0 for v in workouts.values())

# ---------------------------
# DELETE WORKOUT TEST
# ---------------------------

def test_delete_workout(client):
    workouts['Workout'].append({
        'id': 1,
        'exercise': 'Jogging',
        'duration': 10,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    resp = client.post('/delete_workout/Workout/1', follow_redirects=True)
    assert resp.status_code == 200
    assert len(workouts['Workout']) == 0
    assert b'Workout deleted successfully!' in resp.data

# ---------------------------
# API TESTS
# ---------------------------

def test_get_workouts_api(client):
    workouts['Warm-up'].append({
        'id': 1,
        'exercise': 'Jumping Jacks',
        'duration': 5,
        'timestamp': '2025-11-05 10:00:00'
    })
    resp = client.get('/api/workouts')
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'Warm-up' in data
    assert data['Warm-up'][0]['exercise'] == 'Jumping Jacks'

def test_get_stats_api(client):
    workouts['Workout'].append({'id': 1, 'exercise': 'Run', 'duration': 30, 'timestamp': 't'})
    workouts['Cool-down'].append({'id': 2, 'exercise': 'Stretch', 'duration': 10, 'timestamp': 't'})
    resp = client.get('/api/stats')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['total_time'] == 40
    assert data['total_workouts'] == 2
    assert data['by_category']['Workout']['total_minutes'] == 30
    assert data['by_category']['Cool-down']['count'] == 1
