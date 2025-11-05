import io
import pytest
from app1_3 import app, workouts, user_info, daily_workouts

@pytest.fixture(autouse=True)
def clear_data():
    """Reset app state before and after each test."""
    workouts["Warm-up"].clear()
    workouts["Workout"].clear()
    workouts["Cool-down"].clear()
    user_info.clear()
    daily_workouts.clear()
    yield
    workouts["Warm-up"].clear()
    workouts["Workout"].clear()
    workouts["Cool-down"].clear()
    user_info.clear()
    daily_workouts.clear()

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client


# ---------------------------
# BASIC ROUTES
# ---------------------------

def test_index_page(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"html" in resp.data.lower() or b"<!doctype" in resp.data.lower()


def test_log_page(client):
    resp = client.get("/log")
    assert resp.status_code == 200
    assert b"html" in resp.data.lower()


def test_summary_page_initial(client):
    resp = client.get("/summary")
    assert resp.status_code == 200
    assert b"No sessions" in resp.data or b"Total" in resp.data


def test_progress_page_initial(client):
    resp = client.get("/progress")
    assert resp.status_code == 200
    assert b"html" in resp.data.lower()


# ---------------------------
# USER INFO SAVE
# ---------------------------

def test_save_user_success(client):
    data = {
        "name": "Alice",
        "regn_id": "R001",
        "age": "25",
        "gender": "F",
        "height": "165",
        "weight": "60"
    }
    resp = client.post("/save_user", data=data, follow_redirects=True)
    assert resp.status_code == 200
    assert "BMI" in str(resp.data)
    assert user_info["bmi"] > 0
    assert user_info["bmr"] > 0
    assert user_info["gender"] == "F"


def test_save_user_invalid_data(client):
    data = {"name": "Bob", "height": "abc", "weight": "xyz"}
    resp = client.post("/save_user", data=data, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Invalid input" in resp.data


# ---------------------------
# WORKOUT ADDITION
# ---------------------------

def test_add_workout_success(client):
    user_info.update({"weight": 70})
    data = {"category": "Workout", "exercise": "Push-ups", "duration": "15"}
    resp = client.post("/add_workout", data=data, follow_redirects=True)
    assert resp.status_code == 200
    assert len(workouts["Workout"]) == 1
    entry = workouts["Workout"][0]
    assert entry["exercise"] == "Push-ups"
    assert entry["duration"] == 15
    assert entry["calories"] > 0
    assert b"Added" in resp.data


def test_add_workout_missing_fields(client):
    resp = client.post("/add_workout", data={"category": "Workout", "exercise": "", "duration": ""}, follow_redirects=True)
    assert b"Please enter both exercise and duration" in resp.data
    assert all(len(v) == 0 for v in workouts.values())


def test_add_workout_negative_duration(client):
    data = {"category": "Workout", "exercise": "Run", "duration": "-10"}
    resp = client.post("/add_workout", data=data, follow_redirects=True)
    assert b"Duration must be a positive" in resp.data
    assert len(workouts["Workout"]) == 0


# ---------------------------
# SUMMARY & PROGRESS (AFTER LOGGING)
# ---------------------------

def test_summary_with_data(client):
    user_info.update({"weight": 70})
    client.post("/add_workout", data={"category": "Warm-up", "exercise": "Jog", "duration": "10"}, follow_redirects=True)
    client.post("/add_workout", data={"category": "Workout", "exercise": "Squat", "duration": "20"}, follow_redirects=True)
    resp = client.get("/summary")
    assert resp.status_code == 200
    assert b"Total" in resp.data
    assert b"Squat" in resp.data or b"Jog" in resp.data


def test_progress_with_data(client):
    user_info.update({"weight": 70})
    client.post("/add_workout", data={"category": "Workout", "exercise": "Plank", "duration": "5"}, follow_redirects=True)
    resp = client.get("/progress")
    assert resp.status_code == 200
    assert b"Total" in resp.data


# ---------------------------
# CHART ENDPOINTS
# ---------------------------

def test_chart_bar_and_pie_generation(client):
    user_info.update({"weight": 70})
    client.post("/add_workout", data={"category": "Workout", "exercise": "Push-ups", "duration": "10"}, follow_redirects=True)

    resp_bar = client.get("/chart_bar.png")
    resp_pie = client.get("/chart_pie.png")

    assert resp_bar.status_code == 200
    assert resp_pie.status_code == 200
    assert resp_bar.mimetype == "image/png"
    assert resp_pie.mimetype == "image/png"
    # file content should start with PNG header
    assert resp_bar.data[:4] == b"\x89PNG"


# ---------------------------
# EXPORT PDF
# ---------------------------

def test_export_pdf_without_user_info(client):
    resp = client.get("/export_pdf", follow_redirects=True)
    assert b"Please save user info" in resp.data

def test_export_pdf_with_data(client):
    user_info.update({
        "name": "Alice",
        "regn_id": "R001",
        "age": 25,
        "gender": "F",
        "height": 165,
        "weight": 60,
        "bmi": 22.0,
        "bmr": 1350
    })
    client.post("/add_workout", data={"category": "Workout", "exercise": "Plank", "duration": "5"}, follow_redirects=True)
    resp = client.get("/export_pdf")
    assert resp.status_code == 200
    assert resp.mimetype == "application/pdf"
    assert resp.data.startswith(b"%PDF")
