import requests
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logging_middleware.logger import Log

BASE_URL = "http://20.207.122.201/evaluation-service"
AUTH_TOKEN = "PASTE_TOKEN_HERE"
HEADERS = {"Authorization": f"Bearer {AUTH_TOKEN}"}


def fetch_depots():
    Log("backend", "info", "service", "Fetching depots from API...")
    response = requests.get(f"{BASE_URL}/depots", headers=HEADERS)
    response.raise_for_status()
    depots = response.json()["depots"]
    Log("backend", "info", "service", f"Fetched {len(depots)} depots")
    return depots


def fetch_vehicles():
    Log("backend", "info", "service", "Fetching vehicles from API...")
    response = requests.get(f"{BASE_URL}/vehicles", headers=HEADERS)
    response.raise_for_status()
    vehicles = response.json()["vehicles"]
    Log("backend", "info", "service", f"Fetched {len(vehicles)} vehicles")
    return vehicles


def knapsack_01(vehicles, capacity):
    n = len(vehicles)
    dp = [0] * (capacity + 1)
    for i in range(n):
        duration = vehicles[i]["Duration"]
        impact = vehicles[i]["Impact"]
        for w in range(capacity, duration - 1, -1):
            if dp[w - duration] + impact > dp[w]:
                dp[w] = dp[w - duration] + impact
    max_impact = dp[capacity]
    selected = []
    w = capacity
    for i in range(n - 1, -1, -1):
        duration = vehicles[i]["Duration"]
        impact = vehicles[i]["Impact"]
        if w >= duration and dp[w] == dp[w - duration] + impact:
            selected.append(vehicles[i]["TaskID"])
            w -= duration
            if w == 0:
                break
    return max_impact, selected


def main():
    Log("backend", "info", "service", "Vehicle scheduler started")
    depots = fetch_depots()
    vehicles = fetch_vehicles()
    all_results = {}

    for depot in depots:
        depot_id = depot["ID"]
        budget = depot["MechanicHours"]
        Log("backend", "info", "service", f"Solving knapsack for Depot {depot_id} | Budget: {budget}h")
        max_impact, selected_tasks = knapsack_01(vehicles, budget)
        all_results[depot_id] = {
            "depot_id": depot_id,
            "mechanic_hours_budget": budget,
            "max_operational_impact": max_impact,
            "num_tasks_selected": len(selected_tasks),
            "selected_task_ids": selected_tasks,
        }
        Log("backend", "info", "service", f"Depot {depot_id} → Max Impact: {max_impact} | Tasks: {len(selected_tasks)}")
        print(f"\n{'='*60}")
        print(f"Depot {depot_id}  (Budget: {budget} mechanic-hours)")
        print(f"  Max Operational Impact : {max_impact}")
        print(f"  Tasks Selected         : {len(selected_tasks)}")
        for tid in selected_tasks:
            task = next(v for v in vehicles if v["TaskID"] == tid)
            print(f"    • {tid}  |  Duration: {task['Duration']}h  |  Impact: {task['Impact']}")

    with open("results.json", "w") as f:
        json.dump(all_results, f, indent=2)
    Log("backend", "info", "service", "Results saved to results.json")
    print("\n✓ Results written to results.json")


if __name__ == "__main__":
    main()
