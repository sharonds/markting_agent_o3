
#!/usr/bin/env python3
import os, sys, subprocess, time, json, csv, glob, argparse, shutil, statistics as stats

def latest_run_dir():
    runs = sorted(glob.glob("out/*"))
    return runs[-1] if runs else None

def parse_args():
    ap = argparse.ArgumentParser(description="Run offline A/B experiments for the marketing agent.")
    ap.add_argument("--experiment-id", required=True)
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--goal", required=True)
    ap.add_argument("--iterations", type=int, default=5)
    ap.add_argument("--baseline-search", default="none")
    ap.add_argument("--treatment-search", default="perplexity")
    ap.add_argument("--baseline-keywords", default="llm")
    ap.add_argument("--treatment-keywords", default="dataforseo")
    ap.add_argument("--auto-approve", action="store_true")
    return ap.parse_args()

def run_one(variant, run_number, goal, env_overrides):
    env = os.environ.copy()
    env.update(env_overrides)
    env["EXPERIMENT_ID"] = env.get("EXPERIMENT_ID","experiment")
    env["VARIANT"] = variant
    env["RUN_NUMBER"] = str(run_number)
    if env.get("AUTO_APPROVE","") == "":
        env["AUTO_APPROVE"] = "1"
    cmd = [sys.executable, "app/main.py", "--goal", goal]
    subprocess.run(cmd, check=True, env=env)
    rd = latest_run_dir()
    art = os.path.join(rd, "artifacts")
    metrics = json.load(open(os.path.join(art, "metrics.json"), "r", encoding="utf-8"))
    return rd, metrics

def main():
    args = parse_args()
    rows = []
    for i in range(1, args.iterations+1):
        # Baseline
        base_env = {
            "EXPERIMENT_ID": args.experiment_id,
            "SCENARIO": args.scenario,
            "PROVIDER_SEARCH": args.baseline_search,
            "PROVIDER_KEYWORDS": args.baseline_keywords,
            "AUTO_APPROVE": "1" if args.auto_approve else os.environ.get("AUTO_APPROVE","1")
        }
        rd_b, m_b = run_one("baseline", i, args.goal, base_env)

        # Treatment
        treat_env = {
            "EXPERIMENT_ID": args.experiment_id,
            "SCENARIO": args.scenario,
            "PROVIDER_SEARCH": args.treatment_search,
            "PROVIDER_KEYWORDS": args.treatment_keywords,
            "AUTO_APPROVE": "1" if args.auto_approve else os.environ.get("AUTO_APPROVE","1")
        }
        rd_t, m_t = run_one("treatment", i, args.goal, treat_env)

        rows.append({
            "iter": i,
            "baseline_run": rd_b,
            "treatment_run": rd_t,
            "baseline_qa": m_b.get("qa",{}).get("score"),
            "treatment_qa": m_t.get("qa",{}).get("score"),
            "baseline_prov": m_b.get("evidence",{}).get("avg_provenance"),
            "treatment_prov": m_t.get("evidence",{}).get("avg_provenance"),
            "baseline_llm_cost": m_b.get("cost",{}).get("llm_total_eur"),
            "treatment_llm_cost": m_t.get("cost",{}).get("llm_total_eur"),
            "baseline_tool_cost": m_b.get("cost",{}).get("tool_total_eur"),
            "treatment_tool_cost": m_t.get("cost",{}).get("tool_total_eur"),
        })

    # Write CSV summary
    os.makedirs("out/experiments", exist_ok=True)
    csv_path = f"out/experiments/{args.experiment_id}_{args.scenario}.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    # Write Markdown report
    md_path = f"out/experiments/{args.experiment_id}_{args.scenario}.md"
    def col(name): return [r[name] for r in rows if r[name] is not None]
    def mean(v): return round(sum(v)/len(v), 3) if v else None
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# Experiment Report: {args.experiment_id} — {args.scenario}\n\n")
        f.write(f"- iterations: {args.iterations}\n")
        qa_b, qa_t = col("baseline_qa"), col("treatment_qa")
        prov_b, prov_t = col("baseline_prov"), col("treatment_prov")
        cllm_b, cllm_t = col("baseline_llm_cost"), col("treatment_llm_cost")
        ctool_b, ctool_t = col("baseline_tool_cost"), col("treatment_tool_cost")
        f.write(f"- mean QA: baseline {mean(qa_b)} vs treatment {mean(qa_t)}\n")
        f.write(f"- mean provenance: baseline {mean(prov_b)} vs treatment {mean(prov_t)}\n")
        f.write(f"- mean LLM EUR: baseline {mean(cllm_b)} vs treatment {mean(cllm_t)}\n")
        f.write(f"- mean TOOL EUR: baseline {mean(ctool_b)} vs treatment {mean(ctool_t)}\n")
        f.write("\n## Runs\n")
        for r in rows:
            f.write(f"- iter {r['iter']}: {r['baseline_run']} vs {r['treatment_run']}\n")

    print("CSV:", csv_path)
    print("MD:", md_path)

if __name__ == "__main__":
    main()
