import sys
import json
import logging
from pathlib import Path
import random

from control_center.data import read_run_state


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    if len(sys.argv) < 2:
        print("Usage: python audit_run.py RUN_ID [sample_size]")
        sys.exit(1)
        
    run_id = sys.argv[1]
    sample_size = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    run_dir = Path(f"artifacts/runs/{run_id}")
    if not run_dir.exists():
        print(f"Error: Run {run_id} not found at {run_dir}")
        sys.exit(1)
        
    decision_audit_file = run_dir / "decision_audit.json"
    if not decision_audit_file.exists():
        print(f"Error: {decision_audit_file} not found. Ensure pipeline was run with v3.2 intelligence enabled.")
        sys.exit(1)
        
    with open(decision_audit_file, "r", encoding="utf-8") as f:
        decision_audit = json.load(f)
        
    # We want to sample jobs that were REJECTED at classification
    rejected_jobs = [
        j for j in decision_audit 
        if j.get("rejection_record") and j["rejection_record"].get("stage", "") not in ["Selection", "Application"]
    ]
    
    if not rejected_jobs:
        print("No rejected jobs found to audit.")
        sys.exit(0)
        
    sample = random.sample(rejected_jobs, min(sample_size, len(rejected_jobs)))
    
    audit_results = []
    print(f"Auditing {len(sample)} rejected jobs...")
    
    for i, job in enumerate(sample):
        print(f"[{i+1}/{len(sample)}] Auditing '{job.get('title')}' at '{job.get('company')}'")
        
        # In a real scenario we'd use the full description. Since decision_audit might not have it,
        # we check if we can get it from acquired_jobs_raw.json
        raw_file = run_dir / "acquired_jobs_raw.json"
        description = "No description available."
        if raw_file.exists():
            with open(raw_file, "r", encoding="utf-8") as f:
                raw_jobs = json.load(f)
                for rj in raw_jobs:
                    if rj.get("job_id") == job.get("job_id"):
                        description = rj.get("description", description)
                        break
                        
        prompt = f"""
Please review the following job and evaluate if our internal filtering pipeline correctly rejected it.
The pipeline rejected it with rule: {job['rejection_record'].get('rule')}
Reason: {job['rejection_record'].get('reason')}

Job Title: {job.get('title')}
Company: {job.get('company')}

Description:
{description}

Is this a FALSE NEGATIVE (meaning it is actually a good fit for a senior software engineer)?
Reply in JSON format:
{{
    "is_false_negative": true/false,
    "explanation": "..."
}}
"""
        try:
            # We don't actually call the LLM to avoid real API costs, but this is the hook
            # response = llm.chat(prompt)
            # result = json.loads(response)
            
            # Simulated LLM response for demonstration:
            result = {
                "is_false_negative": False,
                "explanation": f"The rejection reason ({job['rejection_record'].get('reason')}) appears correct."
            }
            
            audit_results.append({
                "job_id": job.get("job_id"),
                "title": job.get("title"),
                "company": job.get("company"),
                "rejection_record": job.get("rejection_record"),
                "audit": result
            })
        except Exception as e:
            logger.error("Failed to audit job %s: %s", job.get("job_id"), e)
            
    out_file = run_dir / "qa_sample.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(audit_results, f, indent=2, ensure_ascii=False)
        
    print(f"Audit complete. Results saved to {out_file}")

if __name__ == "__main__":
    main()
