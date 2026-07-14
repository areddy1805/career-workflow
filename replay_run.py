import sys
import json
import logging
from pathlib import Path

from src.orchestration.context import PipelineContext
from src.orchestration.metrics import PipelineRunMetrics
from src.orchestration.pipeline import CareerWorkflowPipeline
from control_center.data import read_run_state

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    if len(sys.argv) < 2:
        print("Usage: python replay_run.py RUN_ID")
        sys.exit(1)
        
    run_id = sys.argv[1]
    run_dir = Path(f"artifacts/runs/{run_id}")
    
    if not run_dir.exists():
        print(f"Error: Run {run_id} not found at {run_dir}")
        sys.exit(1)
        
    raw_file = run_dir / "acquired_jobs_raw.json"
    if not raw_file.exists():
        print(f"Error: {raw_file} not found. Cannot replay.")
        sys.exit(1)
        
    # Read the raw acquired jobs
    with open(raw_file, "r", encoding="utf-8") as f:
        raw_jobs = json.load(f)
        
    print(f"Replaying {len(raw_jobs)} jobs from {run_id}")
    
    # Read run state to get the max_applications setting
    state = read_run_state(run_dir)
    max_apps = state.get("max_applications", 50)
    
    # Generate a NEW run ID for the replay
    import datetime
    new_run_id = f"REPLAY_{run_id}_{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S')}Z"
    
    pipeline = CareerWorkflowPipeline(
        acquisition_mode="replay",
        dry_run=True,
        max_applications=max_apps,
        force_live=False,
        canary=False
    )
    
    # Override context run_id
    pipeline.context.run_id = new_run_id
    pipeline.context.acquired_jobs = raw_jobs
    
    # Run downstream pipeline steps manually
    print("Running classification...")
    pipeline.classify()
    
    print("Running selection...")
    pipeline.select()
    
    print("Running application (dry-run)...")
    pipeline.apply()
    
    print("Running reconciliation...")
    pipeline.reconcile()
    
    print("Running strategy...")
    pipeline.strategy()
    
    print("Finalizing run...")
    pipeline.finalize_run()
    
    print(f"\nReplay complete. New run saved as {new_run_id}")

if __name__ == "__main__":
    main()
