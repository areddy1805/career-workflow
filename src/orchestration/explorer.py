import hashlib
import json
import os
import time
import uuid
from typing import Any, Dict, List

def get_git_commit() -> str:
    try:
        import subprocess
        return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
    except Exception:
        return "unknown"

def hash_dict(d: dict) -> str:
    return hashlib.sha256(json.dumps(d, sort_keys=True).encode("utf-8")).hexdigest()[:8]

class PipelineExplorer:
    def __init__(self, run_id: str):
        self.run_id = run_id
        self.stages = []
        self.current_stage = None
        self.job_traces = {}
        
        # Run fingerprinting
        self.fingerprint = {
            "git_commit": get_git_commit(),
            "pipeline_version": "3.0.0",
        }
    
    def set_config_fingerprint(self, config_dict: dict, strategy_dict: dict):
        self.fingerprint["config_hash"] = hash_dict(config_dict)
        self.fingerprint["strategy_hash"] = hash_dict(strategy_dict)

    def init_job(self, job: Any):
        """Assigns an immutable pipeline job ID and initializes trace."""
        is_dict = isinstance(job, dict)
        
        if is_dict:
            if "pipeline_job_id" not in job:
                job["pipeline_job_id"] = str(uuid.uuid4())
            jid = job["pipeline_job_id"]
            title = job.get("title", "")
            company = job.get("company", "")
            provider_id = job.get("job_id", "")
        else:
            if not hasattr(job, "pipeline_job_id"):
                job.pipeline_job_id = str(uuid.uuid4())
            jid = job.pipeline_job_id
            title = getattr(job, "title", "")
            company = getattr(job, "company", "")
            provider_id = getattr(job, "job_id", "")
            
        if jid not in self.job_traces:
            self.job_traces[jid] = {
                "pipeline_job_id": jid,
                "title": title,
                "company": company,
                "provider_id": provider_id,
                "timeline": []
            }

    def _record_trace(self, job: Any, stage: str, event: str, details: dict = None):
        is_dict = isinstance(job, dict)
        jid = job.get("pipeline_job_id") if is_dict else getattr(job, "pipeline_job_id", None)
        
        if not jid:
            return
        
        self.job_traces[jid]["timeline"].append({
            "stage": stage,
            "event": event,
            "details": details or {},
            "timestamp": time.time()
        })
        self.job_traces[jid]["final_state"] = event

    def start_stage(self, stage_name: str, input_jobs: List[Any]):
        if self.current_stage:
            raise RuntimeError(f"Cannot start {stage_name}, {self.current_stage['name']} is still running")
            
        # Ensure all incoming jobs have IDs
        for j in input_jobs:
            self.init_job(j)
            
        top_entering = []
        for j in input_jobs[:5]:
            is_dict = isinstance(j, dict)
            jid = j.get("pipeline_job_id") if is_dict else getattr(j, "pipeline_job_id", None)
            title = j.get("title") if is_dict else getattr(j, "title", None)
            company = j.get("company") if is_dict else getattr(j, "company", None)
            top_entering.append({"id": jid, "title": title, "company": company})
            
        self.current_stage = {
            "name": stage_name,
            "input_count": len(input_jobs),
            "start_time": time.perf_counter(),
            "removed_jobs": [],
            "cache_hits": 0,
            "cache_misses": 0,
            "top_entering": top_entering
        }

    def record_cache_hit(self):
        if self.current_stage:
            self.current_stage["cache_hits"] += 1

    def record_cache_miss(self):
        if self.current_stage:
            self.current_stage["cache_misses"] += 1

    def record_rejection(self, job: dict, reason: str, code: str = "UNKNOWN", explanation: dict = None):
        if not self.current_stage:
            return
        self.current_stage["removed_jobs"].append({
            "job": job,
            "reason": reason,
            "code": code
        })
        
        if explanation is None:
            explanation = {"reason": reason, "code": code}
        
        if isinstance(job, dict):
            job["explanation"] = explanation
        else:
            job.explanation = explanation
            
        self._record_trace(job, self.current_stage["name"], "REJECTED", explanation)

    def record_selection(self, job: dict, explanation: dict = None):
        if self.current_stage:
            self._record_trace(job, self.current_stage["name"], "SELECTED", explanation)
            if explanation:
                if isinstance(job, dict):
                    job["explanation"] = explanation
                else:
                    job.explanation = explanation

    def record_application(self, job: dict, outcome: str, explanation: dict = None):
        if self.current_stage:
            self._record_trace(job, self.current_stage["name"], outcome, explanation)
            if explanation:
                job["explanation"] = explanation

    def finish_stage(self, output_jobs: List[dict]):
        if not self.current_stage:
            raise RuntimeError("No active stage to finish")
            
        end_time = time.perf_counter()
        duration_ms = (end_time - self.current_stage["start_time"]) * 1000
        
        input_count = self.current_stage["input_count"]
        output_count = len(output_jobs)
        removed_count = len(self.current_stage["removed_jobs"])
        
        # INVARIANT CHECK
        if input_count != output_count + removed_count:
            raise RuntimeError(
                f"Stage Invariant Failed in {self.current_stage['name']}: "
                f"Input ({input_count}) != Output ({output_count}) + Removed ({removed_count})"
            )
            
        removal_percentage = round((removed_count / input_count * 100), 2) if input_count > 0 else 0.0
        
        top_reasons = {}
        examples = {}
        for r in self.current_stage["removed_jobs"]:
            code = r["code"]
            top_reasons[code] = top_reasons.get(code, 0) + 1
            if code not in examples:
                examples[code] = []
            if len(examples[code]) < 3:
                job = r["job"]
                examples[code].append({
                    "pipeline_job_id": getattr(job, "pipeline_job_id", job.get("pipeline_job_id") if hasattr(job, "get") else None),
                    "title": getattr(job, "title", job.get("title") if hasattr(job, "get") else None),
                    "company": getattr(job, "company", job.get("company") if hasattr(job, "get") else None),
                    "reason": r["reason"]
                })
                
        sorted_reasons = dict(sorted(top_reasons.items(), key=lambda item: item[1], reverse=True))

        self.stages.append({
            "stage": self.current_stage["name"],
            "input_count": input_count,
            "output_count": output_count,
            "removed_count": removed_count,
            "removal_percentage": removal_percentage,
            "duration_ms": round(duration_ms, 2),
            "cache_hits": self.current_stage["cache_hits"],
            "cache_misses": self.current_stage["cache_misses"],
            "top_reasons": sorted_reasons,
            "examples": examples,
            "top_entering": self.current_stage["top_entering"],
            "top_leaving": [{"id": getattr(j, "pipeline_job_id", j.get("pipeline_job_id") if hasattr(j, "get") else None), "title": getattr(j, "title", j.get("title") if hasattr(j, "get") else None), "company": getattr(j, "company", j.get("company") if hasattr(j, "get") else None)} for j in output_jobs[:5]]
        })
        
        self.current_stage = None

    def export_explorer(self) -> Dict[str, Any]:
        return {
            "version": "2.0",
            "run_id": self.run_id,
            "fingerprint": self.fingerprint,
            "stages": self.stages
        }
        
    def export_traces(self) -> List[Dict[str, Any]]:
        return list(self.job_traces.values())
