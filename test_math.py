import json

with open("artifacts/runs/20260714T043718758638Z/result.json") as f:
    result = json.load(f)["data"]
    
with open("artifacts/runs/20260714T043718758638Z/pipeline_funnel.json") as f:
    funnel = json.load(f)["data"]["funnel"]

print("result.json:", result["acquired"], result["classified"])
print("funnel.json:", funnel["acquired"], funnel["classified"])
total_rej = sum(funnel["rejections"].values())
print(f"Acquired: {funnel['acquired']}, Rejections: {total_rej}, Diff: {funnel['acquired'] - total_rej}, Classified: {funnel['classified']}")

with open("artifacts/runs/20260714T043718758638Z/decision_audit.json") as f:
    decisions = json.load(f)["data"]
print("Decision audit count:", len(decisions))
