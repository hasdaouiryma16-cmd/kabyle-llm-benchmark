from conftest import make_item


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_create_assigns_sequential_ids_per_category(client):
    first = client.post("/api/tests", json=make_item()).json()
    second = client.post("/api/tests", json=make_item()).json()
    other = client.post("/api/tests", json=make_item(category="culture", source_text=None)).json()
    assert (first["id"], second["id"], other["id"]) == (
        "tr-fr-kab-0001",
        "tr-fr-kab-0002",
        "cult-0001",
    )


def test_create_with_existing_id_conflicts(client):
    assert client.post("/api/tests", json=make_item(id="x-1")).status_code == 201
    assert client.post("/api/tests", json=make_item(id="x-1")).status_code == 409


def test_invalid_id_rejected(client):
    assert client.post("/api/tests", json=make_item(id="Pas Valide")).status_code == 422


def test_text_is_nfc_normalized_and_trimmed(client):
    decomposed = "ḥ"  # h + point souscrit combinant
    item = client.post(
        "/api/tests", json=make_item(prompt="  consigne  ", references=[decomposed, ""])
    ).json()
    assert item["references"] == ["ḥ"]  # « ḥ » précomposé, la chaîne vide est retirée
    assert item["prompt"] == "consigne"


def test_ready_requires_reference_for_auto_grading(client):
    response = client.post("/api/tests", json=make_item(references=[]))
    assert response.status_code == 422
    assert "référence" in response.text


def test_draft_can_be_incomplete(client):
    response = client.post("/api/tests", json=make_item(references=[], status="draft"))
    assert response.status_code == 201


def test_comprehension_requires_context(client):
    payload = make_item(category="comprehension", source_text=None)
    assert client.post("/api/tests", json=payload).status_code == 422
    payload["context"] = "texte-factice"
    assert client.post("/api/tests", json=payload).status_code == 201


def test_human_grading_allows_no_reference(client):
    payload = make_item(category="conversation", source_text=None, references=[], grading="human")
    assert client.post("/api/tests", json=payload).status_code == 201


def test_update_and_delete(client):
    item = client.post("/api/tests", json=make_item()).json()
    update = {k: v for k, v in item.items() if k not in ("id", "created_at", "updated_at")}
    update["notes"] = "nouvelle note"
    updated = client.put(f"/api/tests/{item['id']}", json=update).json()
    assert updated["notes"] == "nouvelle note"
    assert updated["created_at"] == item["created_at"]

    assert client.delete(f"/api/tests/{item['id']}").status_code == 204
    assert client.get(f"/api/tests/{item['id']}").status_code == 404


def test_list_filters(client):
    client.post("/api/tests", json=make_item())
    client.post("/api/tests", json=make_item(status="draft", notes="à revoir"))
    client.post("/api/tests", json=make_item(category="culture", source_text=None, split="private"))

    assert len(client.get("/api/tests").json()) == 3
    assert len(client.get("/api/tests", params={"category": "culture"}).json()) == 1
    assert len(client.get("/api/tests", params={"status": "draft"}).json()) == 1
    assert len(client.get("/api/tests", params={"split": "private"}).json()) == 1
    assert len(client.get("/api/tests", params={"q": "revoir"}).json()) == 1
