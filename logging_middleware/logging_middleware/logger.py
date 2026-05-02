import requests

ACCESS_TOKEN = "PASTE_TOKEN_HERE"

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

def Log(stack: str, level: str, package: str, message: str):
    payload = {
        "stack": stack,
        "level": level,
        "package": package,
        "message": message
    }
    try:
        res = requests.post(
            "http://20.207.122.201/evaluation-service/logs",
            json=payload,
            headers=HEADERS
        )
        return res.json()
    except Exception as e:
        print(f"Log failed: {e}")
