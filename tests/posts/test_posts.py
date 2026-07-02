def test_create_and_list_posts(client):
    # Register and login first to get the token
    client.post(
        "/api/v1/auth/register",
        json={"email": "creator@example.com", "password": "password123"}
    )
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "creator@example.com", "password": "password123"}
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create post
    post_res = client.post(
        "/api/v1/posts/",
        json={"title": "Hello GCP", "content": "Integration testing works!"},
        headers=headers
    )
    assert post_res.status_code == 201
    assert post_res.json()["title"] == "Hello GCP"
    
    # List posts
    list_res = client.get("/api/v1/posts/")
    assert list_res.status_code == 200
    data = list_res.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Hello GCP"
