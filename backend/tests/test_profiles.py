from fastapi.testclient import TestClient
from main import app

# Create a test client instance
client = TestClient(app)

def test_read_root():
    # Make a request just like a real client
    response = client.get("/")
    
    # Assert expected status codes and payloads
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}