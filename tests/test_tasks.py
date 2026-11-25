def test_login_and_me(client):
    client.post("/auth/register", json={
        "email": "user@example.com", 
        "name": "Jan", 
        "password": "Haslo123!"
    })
    
    response = client.post("/auth/login", data={
        "username": "user@example.com", 
        "password": "Haslo123!"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    
    token = data["access_token"]
    
    me_response = client.get(
        "/users/me", 
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "user@example.com"

def test_protected_without_token(client):
    response = client.get("/users/me")
    assert response.status_code == 401

def test_tasks_are_scoped_to_current_user(client):
    client.post("/auth/register", json={"email": "u1@example.com", "name": "User1", "password": "Haslo123!"})
    client.post("/auth/register", json={"email": "u2@example.com", "name": "User2", "password": "Haslo123!"})
    
    r1 = client.post("/auth/login", data={"username": "u1@example.com", "password": "Haslo123!"})
    token1 = r1.json()["access_token"]
    
    r2 = client.post("/auth/login", data={"username": "u2@example.com", "password": "Haslo123!"})
    token2 = r2.json()["access_token"]
    
    client.post(
        "/tasks", 
        json={"title": "Zadanie Usera 1", "completed": False, "priority": 1},
        headers={"Authorization": f"Bearer {token1}"}
    )
    
    tasks_response = client.get(
        "/tasks",
        headers={"Authorization": f"Bearer {token2}"}
    )
    assert tasks_response.status_code == 200
    assert len(tasks_response.json()) == 0
