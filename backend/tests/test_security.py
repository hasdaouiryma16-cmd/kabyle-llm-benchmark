from tests.conftest import make_item


def test_write_from_lab_ui_origin_is_accepted(client):
    response = client.post(
        "/api/tests", json=make_item(), headers={"origin": "http://localhost:5173"}
    )
    assert response.status_code == 201


def test_write_without_origin_is_accepted(client):
    # Scripts et outils locaux (curl, tests) n'envoient pas d'en-tête Origin
    assert client.post("/api/tests", json=make_item()).status_code == 201


def test_write_from_another_site_is_refused(client):
    response = client.post(
        "/api/tests", json=make_item(), headers={"origin": "https://site-malveillant.example"}
    )
    assert response.status_code == 403
    assert client.get("/api/tests").json() == []


def test_cross_site_form_without_origin_is_refused(client):
    response = client.post("/api/testset/load-from-repo", headers={"sec-fetch-site": "cross-site"})
    assert response.status_code == 403


def test_reads_from_another_origin_are_not_blocked_by_this_check(client):
    # La lecture reste protégée par CORS (le navigateur ne livre pas la réponse)
    response = client.get("/api/health", headers={"origin": "https://site-malveillant.example"})
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_unexpected_host_is_refused(client):
    # « DNS rebinding » : un domaine externe qui pointe vers 127.0.0.1
    response = client.get("/api/health", headers={"host": "attaquant.example:8800"})
    assert response.status_code == 400


def test_docker_service_host_is_accepted(client):
    # Le relais de Vite (changeOrigin) envoie « Host: api:8000 »
    assert client.get("/api/health", headers={"host": "api:8000"}).status_code == 200
