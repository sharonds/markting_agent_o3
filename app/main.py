import argparse
from app.io import read_yaml, parse_frontmatter_markdown
from app.state import ProjectState
from app.logs import start_run
from app.orchestrator.core import run_pipeline

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--goal", required=True, help="Overall objective for the run")
    p.add_argument("--compass", default="data/compass.md")
    p.add_argument("--intake", default="data/intake.yaml")
    args = p.parse_args()

    compass_meta, compass_body = parse_frontmatter_markdown(args.compass)
    intake = read_yaml(args.intake)
    run_id, run_dir, logger = start_run()
    logger.event("run_started", run_id=run_id, goal=args.goal)

    state = ProjectState(compass_meta=compass_meta, compass_body=compass_body, intake=intake)
    run_pipeline(state, run_dir, logger)

if __name__ == "__main__":
    main()
