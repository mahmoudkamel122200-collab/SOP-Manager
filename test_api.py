import requests

base_url = "http://localhost:8000/api/v1"
resp = requests.post(f"{base_url}/auth/login", json={"username": "admin", "password": "Admin@1234"})
if resp.status_code != 200:
    print("Login failed:", resp.status_code, resp.text)
    exit(1)

token = resp.json()["data"]["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Test the new combined endpoint
data = {
    "item_code": "TT-777777",
    "material_name": "Combined Test Material",
    "quantity": 42.0,
    "unit": "KG",
    "warehouse_name": "NewWarehouse",
    "rack": "N01",
    "shelf": "N02",
    "position": "N03"
}
resp = requests.post(f"{base_url}/warehouse/items/with-location", json=data, headers=headers)
print("Combined Create Status:", resp.status_code)
print("Combined Create Body:", resp.text)
