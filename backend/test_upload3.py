import urllib.request, json

data = b'--boundary123\r\nContent-Disposition: form-data; name="title"\r\n\r\ntestdoc2\r\n--boundary123\r\nContent-Disposition: form-data; name="section_id"\r\n\r\n00000000-0000-0000-0002-000000000001\r\n--boundary123\r\nContent-Disposition: form-data; name="file"; filename="test.txt"\r\nContent-Type: text/plain\r\n\r\nHello World 2\r\n--boundary123--\r\n'

# 1. Login to get token
login_data = json.dumps({'username': 'admin', 'password': 'Admin@1234'}).encode()
req_login = urllib.request.Request('https://sop-manager-sr33.vercel.app/api/v1/auth/login', data=login_data, headers={'Content-Type': 'application/json'})
res_login = json.loads(urllib.request.urlopen(req_login).read().decode())
token = res_login['data']['access_token']

# 2. Upload with token
req = urllib.request.Request('https://sop-manager-sr33.vercel.app/api/v1/documents', data=data, method='POST')
req.add_header('Content-Type', 'multipart/form-data; boundary=boundary123')
req.add_header('Authorization', f'Bearer {token}')

try:
    print(urllib.request.urlopen(req).read().decode())
except Exception as e:
    print("ERROR:", e)
    if hasattr(e, 'read'):
        print(e.read().decode())
