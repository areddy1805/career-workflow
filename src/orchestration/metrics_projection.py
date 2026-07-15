import json
from pathlib import Path
from typing import Dict, Any

class MetricsProjection:
    def __init__(self):
        self.counts = {
            "acquired": 0,
            "selected": 0,
            "attempted": 0,
            "submitted": 0,
            "already_applied": 0,
            "skipped_local": 0,
            "native_applied": 0,
            "ats_queue": 0,
            "generic_queue": 0,
            "manual_queue": 0,
            "unsupported": 0,
            "policy_rejected": 0,
            "dry_run_skipped": 0,
            "run_limit_reached": 0,
            "failed": 0,
            "manual_review": 0,
        }

    def process_event(self, event: Dict[str, Any]):
        event_type = event.get("event")
        stage = event.get("stage")
        payload = event.get("payload", {})
        code = payload.get("code", "")
        outcome = payload.get("outcome", "")
        strategy = payload.get("strategy", "")
        reason = payload.get("reason", "")
        
        if event_type == "JobAcquired":
            self.counts["acquired"] += 1
            
        elif event_type == "JobSelected":
            self.counts["selected"] += 1
            
        elif event_type == "JobSkipped":
            if code == "DRY_RUN":
                self.counts["dry_run_skipped"] += 1
            else:
                self.counts["skipped_local"] += 1
                
        elif event_type == "JobFailed":
            self.counts["failed"] += 1
            self.counts["attempted"] += 1
            
        elif event_type == "JobRejected":
            if stage == "Application":
                if code == "ALREADY_APPLIED":
                    self.counts["already_applied"] += 1
                elif code == "POLICY_REJECTED":
                    self.counts["policy_rejected"] += 1
                elif code == "APPLICATION_QUOTA":
                    self.counts["run_limit_reached"] += 1
            elif stage == "Selection Limit" and code == "ATTEMPT_BUDGET":
                # In legacy, run_limit_reached is only incremented in Application limits.
                pass
                
        elif event_type == "JobRouted":
            if strategy == "EXTERNAL_ATS":
                self.counts["ats_queue"] += 1
            elif strategy == "GENERIC_CAREER_SITE":
                self.counts["generic_queue"] += 1
            elif strategy == "MANUAL_REVIEW":
                self.counts["manual_queue"] += 1
            elif strategy == "UNSUPPORTED":
                self.counts["unsupported"] += 1
                
        elif event_type == "JobApplied":
            self.counts["submitted"] += 1
            self.counts["attempted"] += 1
            self.counts["native_applied"] += 1

    def build_report(self) -> Dict[str, int]:
        return self.counts.copy()
