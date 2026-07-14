import json

with open("artifacts/runs/20260714T043718758638Z/decision_audit.json") as f:
    decisions = json.load(f)["data"]

rejections = 0
classified = 0
missing = []

for j in decisions:
    stages = [d["stage"] for d in j.get("decision_history", [])]
    has_rej = "rejection_record" in j and j["rejection_record"] is not None
    if has_rej:
        rejections += 1
    elif "Selection" in stages or "Application" in stages:
        classified += 1
    elif not has_rej:
        classified += 1
        
print("Rejections in audit:", rejections)
print("Classified in audit:", classified)
