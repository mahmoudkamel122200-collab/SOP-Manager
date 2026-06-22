import urllib.request, json

# 1. Login to get token
login_data = json.dumps({'username': 'admin', 'password': 'Admin@1234'}).encode()
req_login = urllib.request.Request('https://sop-manager-sr33.vercel.app/api/v1/auth/login', data=login_data, headers={'Content-Type': 'application/json'})
res_login = json.loads(urllib.request.urlopen(req_login).read().decode())
token = res_login['data']['access_token']

# 2. Add missing sections
for section_name in ["Production", "Warehouse"]:
    req = urllib.request.Request('https://sop-manager-sr33.vercel.app/api/v1/sections', data=json.dumps({"name": section_name, "description": "Default section"}).encode(), method='POST')
    req.add_header('Content-Type', 'application/json')
    req.add_header('Authorization', f'Bearer {token}')
    try:
        print(urllib.request.urlopen(req).read().decode())
    except Exception as e:
        print("ERROR:", e)
        if hasattr(e, 'read'):
            print(e.read().decode())
