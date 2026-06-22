import urllib.request, json

# 1. Login to get token
login_data = json.dumps({'username': 'admin', 'password': 'Admin@1234'}).encode()
req_login = urllib.request.Request('https://sop-manager-sr33.vercel.app/api/v1/auth/login', data=login_data, headers={'Content-Type': 'application/json'})
res_login = json.loads(urllib.request.urlopen(req_login).read().decode())
token = res_login['data']['access_token']

req = urllib.request.Request('https://sop-manager-sr33.vercel.app/api/v1/sections')
req.add_header('Authorization', f'Bearer {token}')
try:
    secs = json.loads(urllib.request.urlopen(req).read().decode())
    print("Sections:", secs)
    if secs.get('data'):
        sec_id = secs['data'][0]['id']
        
        # 2. Upload with token
        data = f'--boundary123\r\nContent-Disposition: form-data; name="title"\r\n\r\ntestdoc3\r\n--boundary123\r\nContent-Disposition: form-data; name="section_id"\r\n\r\n{sec_id}\r\n--boundary123\r\nContent-Disposition: form-data; name="file"; filename="test.txt"\r\nContent-Type: text/plain\r\n\r\nHello World 3\r\n--boundary123--\r\n'.encode()
        req_up = urllib.request.Request('https://sop-manager-sr33.vercel.app/api/v1/documents', data=data, method='POST')
        req_up.add_header('Content-Type', 'multipart/form-data; boundary=boundary123')
        req_up.add_header('Authorization', f'Bearer {token}')
        print(urllib.request.urlopen(req_up).read().decode())
except Exception as e:
    print("ERROR:", e)
    if hasattr(e, 'read'):
        print(e.read().decode())
