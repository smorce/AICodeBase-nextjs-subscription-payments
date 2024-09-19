from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

def test_create_item():
    response = client.post(
        "/items/",
        json={"name": "Test Item", "description": "This is a test item."}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Item"
    assert data["description"] == "This is a test item."
    assert "id" in data

def test_read_item():
    # 事前にアイテムを作成
    response = client.post(
        "/items/",
        json={"name": "Another Test Item", "description": "Another test."}
    )
    assert response.status_code == 200
    item_id = response.json()["id"]

    # 作成したアイテムを取得
    response = client.get(f"/items/{item_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == item_id
    assert data["name"] == "Another Test Item"
    assert data["description"] == "Another test."