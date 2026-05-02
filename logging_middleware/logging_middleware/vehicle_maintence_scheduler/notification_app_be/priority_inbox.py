import heapq
import os
import json
import requests
from datetime import datetime
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logging_middleware.logger import Log

AUTH_TOKEN = "PASTE_TOKEN_HERE"
BASE_URL = "http://20.207.122.201/evaluation-service"
HEADERS = {"Authorization": f"Bearer {AUTH_TOKEN}"}

TYPE_WEIGHT = {
    "Placement": 3,
    "Result": 2,
    "Event": 1,
}

def fetch_notifications():
    Log("backend", "info", "service", "Fetching notifications from API...")
    response = requests.get(f"{BASE_URL}/notifications", headers=HEADERS)
    response.raise_for_status()
    notifications = response.json()["notifications"]
    Log("backend", "info", "service", f"Fetched {len(notifications)} notifications")
    return notifications

def compute_priority_score(notification):
    ntype = notification.get("Type", "Event")
    weight = TYPE_WEIGHT.get(ntype, 0)
    timestamp_str = notification.get("Timestamp", "1970-01-01T00:00:00")
    try:
        dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        epoch = dt.timestamp()
    except (ValueError, AttributeError):
        epoch = 0.0
    return weight * 1_000_000_000_000 + epoch

def get_top_n(notifications, n):
    heap = []
    for i, notif in enumerate(notifications):
        score = compute_priority_score(notif)
        entry = (score, i, notif)
        if len(heap) < n:
            heapq.heappush(heap, entry)
        elif score > heap[0][0]:
            heapq.heapreplace(heap, entry)
    return [item[2] for item in sorted(heap, key=lambda x: x[0], reverse=True)]

def main():
    Log("backend", "info", "service", "Priority inbox started")
    N = 10
    notifications = fetch_notifications()
    top_n = get_top_n(notifications, N)

    print(f"\n{'='*65}")
    print(f"  PRIORITY INBOX — Top {N} Notifications")
    print(f"{'='*65}")
    for rank, notif in enumerate(top_n, 1):
        print(f"  #{rank:>2}  [{notif.get('Type'):<10}]  {notif.get('Message'):<35}  {notif.get('Timestamp')[:19]}")
    print(f"{'='*65}")

    with open("top_notifications.json", "w") as f:
        json.dump([{
            "rank": i+1,
            "id": n["ID"],
            "type": n["Type"],
            "message": n["Message"],
            "timestamp": n["Timestamp"],
            "score": compute_priority_score(n)
        } for i, n in enumerate(top_n)], f, indent=2)

    Log("backend", "info", "service", f"Top {N} notifications saved")

if __name__ == "__main__":
    main()
