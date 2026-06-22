import urllib.request, json

data = b'--boundary123\r\nContent-Disposition: form-data; name="title"\r\n\r\ntestdoc\r\n--boundary123\r\nContent-Disposition: form-data; name="section_id"\r\n\r\n00000000-0000-0000-0002-000000000001\r\n--boundary123\r\nContent-Disposition: form-data; name="file"; filename="test.txt"\r\nContent-Type: text/plain\r\n\r\nHello World\r\n--boundary123--\r\n'

req = urllib.request.Request('https://sop-manager-sr33.vercel.app/api/v1/documents', data=data, method='POST')
req.add_header('Content-Type', 'multipart/form-data; boundary=boundary123')
req.add_header('Authorization', 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwMDAwMDAwMC0wMDAwLTAwMDAtMDAwMS0wMDAwMDAwMDAwMDEiLCJpYXQiOjE3ODIwNjg2NTgsImV4cCI6MTc4MjA3MDQ1OCwianRpIjoiYTJkZWQ0ZGItNjk1My00NTUwLTk4MmYtMjM5Mzg0MTQ5MWY4IiwidHlwZSI6ImFjY2VzcyIsInJvbGUiOiJBRE1JTiJ9.EeLh3M5YhUaOg0a4vC7Qfb8CoCxqWT_LhSeI9VHzUag')

try:
    print(urllib.request.urlopen(req).read().decode())
except Exception as e:
    print("ERROR:", e)
    if hasattr(e, 'read'):
        print(e.read().decode())
