def test_register_and_login(client):
    # Register new user
    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "password123"}
    )
    assert register_response.status_code == 201
    assert register_response.json()["email"] == "test@example.com"
    
    # Login user
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "password123"}
    )
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()
    assert login_response.json()["token_type"] == "bearer"
