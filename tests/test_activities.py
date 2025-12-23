from copy import deepcopy
import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the in-memory activities after each test to avoid state leakage."""
    original = deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


def test_list_activities():
    client = TestClient(app)
    r = client.get("/activities")
    assert r.status_code == 200
    assert isinstance(r.json(), dict)


def test_signup_and_unregister():
    client = TestClient(app)
    data = client.get("/activities").json()
    activity_name = next(iter(data))
    email = "test@example.com"

    # Ensure clean precondition
    if email in data[activity_name]["participants"]:
        client.post(f"/activities/{activity_name}/unregister", params={"email": email})

    # Signup
    r = client.post(f"/activities/{activity_name}/signup", params={"email": email})
    assert r.status_code == 200
    assert "Signed up" in r.json().get("message", "")

    # Verify added
    after = client.get("/activities").json()
    assert email in after[activity_name]["participants"]

    # Unregister
    r2 = client.post(f"/activities/{activity_name}/unregister", params={"email": email})
    assert r2.status_code == 200
    assert "Unregistered" in r2.json().get("message", "")

    # Verify removed
    after2 = client.get("/activities").json()
    assert email not in after2[activity_name]["participants"]


def test_duplicate_signup():
    client = TestClient(app)
    data = client.get("/activities").json()
    activity_name = next(iter(data))
    email = "dup@example.com"

    # Clean up if necessary
    if email in data[activity_name]["participants"]:
        client.post(f"/activities/{activity_name}/unregister", params={"email": email})

    r = client.post(f"/activities/{activity_name}/signup", params={"email": email})
    assert r.status_code == 200

    # Duplicate should fail
    r2 = client.post(f"/activities/{activity_name}/signup", params={"email": email})
    assert r2.status_code == 400


def test_unregister_nonexistent_activity():
    client = TestClient(app)
    r = client.post("/activities/ThisActivityDoesNotExist/unregister", params={"email": "x@y.com"})
    assert r.status_code == 404


def test_signup_nonexistent_activity():
    client = TestClient(app)
    r = client.post("/activities/ThisActivityDoesNotExist/signup", params={"email": "x@y.com"})
    assert r.status_code == 404
