import re

with open("src/client/job_classifier.py", "r") as f:
    content = f.read()

# Add self.decisions = []
content = re.sub(r'(def __init__\(self, metrics: PipelineRunMetrics \| None = None\):\n\s*self\.metrics = metrics)', r'\1\n        self.decisions = []', content)

# Add record_decision method
method_code = """
    def record_decision(self, job, stage, code, reason, ai_explanation="", score=None, threshold=None):
        from datetime import datetime, timezone
        self.decisions.append({
            "job_id": str(job.get("job_id", "")),
            "title": str(job.get("title", "")),
            "company": str(job.get("company", "")),
            "search_query": str(job.get("search_query", "")),
            "stage": stage,
            "code": code,
            "reason": reason,
            "ai_explanation": ai_explanation,
            "score": score,
            "threshold": threshold,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
"""
content = re.sub(r'(class JobFilterPipeline2:.*?def __init__.*?self\.decisions = \[\])', r'\1\n' + method_code, content, flags=re.DOTALL)

with open("src/client/job_classifier.py", "w") as f:
    f.write(content)
