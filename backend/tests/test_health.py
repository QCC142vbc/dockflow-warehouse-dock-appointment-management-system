def test_root_endpoint(client):
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["application"] == "Dock Appointment Scheduling"
    assert data["version"] == "0.1.0"
    assert data["status"] == "running"


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"