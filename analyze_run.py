import json
import os
from collections import defaultdict

run_dir = "artifacts/runs/20260715T152059147611Z"
with open(f"{run_dir}/classification.json") as f:
    class_data = json.load(f)["data"]
with open(f"{run_dir}/rejected_jobs.json") as f:
    rejected_data = json.load(f)["data"]
with open(f"{run_dir}/selected_jobs.json") as f:
    selected_data = json.load(f)["data"]
with open(f"{run_dir}/acquisition.json") as f:
    acq_data = json.load(f)["data"]
with open(f"{run_dir}/selection.json") as f:
    sel_data = json.load(f)["data"]

print("Acquisition:", acq_data)
print("Classification Summary:", class_data["summary"])
print("Selection Summary:", sel_data)
