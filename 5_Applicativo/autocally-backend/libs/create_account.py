import requests

data = {
    "username": "alex",
    "password": "Admin$00",
    "email": "alex@gmail.com"
}

response = requests.post('http://localhost:5000/api/security/create_user', json=data)
print(response.json())