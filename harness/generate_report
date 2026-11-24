#!/usr/bin/env python3
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from harness.report import generate_markdown_report, generate_svg_rd_curve
from harness.vmaf_bd_rate import run_full_dataset_evaluation


def main():
    parser = argparse.ArgumentParser(description="Generate Research Reports & RD Curves")
    parser.add_argument("--eval-json", default="docs/research/bd_rate_results.json", help="Path to evaluation JSON")
    parser.add_argument("--output-md", default="docs/research/research_report.md", help="Output Markdown report path")
    parser.add_argument("--output-curves-dir", default="docs/research/curves", help="Directory for SVG curves")
    args = parser.parse_args()

    if os.path.exists(args.eval_json):
        with open(args.eval_json, "r", encoding="utf-8") as f:
            eval_data = json.load(f)
    else:
        print("Evaluation JSON not found. Running fresh evaluation...")
        eval_data = run_full_dataset_evaluation()
        os.makedirs(os.path.dirname(args.eval_json), exist_ok=True)
        with open(args.eval_json, "w", encoding="utf-8") as f:
            json.dump(eval_data, f, indent=2)

    # Generate Markdown report
    os.makedirs(os.path.dirname(args.output_md), exist_ok=True)
    report_md = generate_markdown_report(eval_data)
    with open(args.output_md, "w", encoding="utf-8") as f:
        f.write(report_md)
    print(f"Generated Markdown report at {args.output_md}")

    # Generate SVG RD Curves per rung
    os.makedirs(args.output_curves_dir, exist_ok=True)
    first_evals = {e["rung"]: e for e in eval_data["evaluations"]}
    for rung_name, eval_item in first_evals.items():
        svg_filename = f"rd_curve_{rung_name}.svg"
        svg_path = os.path.join(args.output_curves_dir, svg_filename)
        generate_svg_rd_curve(
            rung_name=rung_name,
            resolution=f"{eval_item['width']}x{eval_item['height']}",
            h264_pts=eval_item["h264_points"],
            hevc_pts=eval_item["hevc_points"],
            av1_pts=eval_item["av1_points"],
            output_svg_path=svg_path,
        )
        print(f"Generated RD curve: {svg_path}")


if __name__ == "__main__":
    main()
