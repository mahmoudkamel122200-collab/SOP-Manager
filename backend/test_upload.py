import requests
import json

def test_upload():
    # Login as admin to get token
    res = requests.post("http://localhost:8000/api/v1/auth/login", json={"username":"admin", "password":"Admin@1234"})
    token = res.json()["data"]["access_token"]
    
    # Get a section id
    sec_res = requests.get("http://localhost:8000/api/v1/sections", headers={"Authorization": f"Bearer {token}"})
    section_id = sec_res.json()["data"][0]["id"]
    
    # Upload document
    files = {'file': ('test.pdf', b'PDF content here', 'application/pdf')}
    data = {
        'title': 'Test Document',
        'description': '',
        'section_id': section_id
    }
    
    upload_res = requests.post(
        "http://localhost:8000/api/v1/documents", 
        headers={"Authorization": f"Bearer {token}"},
        data=data,
        files=files
    )
    
    print("Status:", upload_res.status_code)
    print("Response:", upload_res.text)

test_upload()
