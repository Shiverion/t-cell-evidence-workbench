"""Command-line interface for data generation, auditing, and full runs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from tcell_exhaustion.config import AnalysisConfig, load_config
from tcell_exhaustion.data import audit_input, load_h5ad
from tcell_exhaustion.demo import demo_config, write_demo_h5ad
from tcell_exhaustion.pipeline import run_pipeline


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tcell-triage",
        description="Donor-aware CD8+ T-cell exhaustion triage",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    make_demo = subparsers.add_parser("make-demo", help="write the deterministic teaching dataset")
    make_demo.add_argument("--output", type=Path, default=Path("data/demo_tcells.h5ad"))
    make_demo.add_argument("--seed", type=int, default=42)
    make_demo.add_argument("--donors-per-condition", type=int, default=6)
    make_demo.add_argument("--cells-per-subtype-per-donor", type=int, default=12)

    inspect = subparsers.add_parser("inspect", help="audit an input without running the analysis")
    inspect.add_argument("--config", type=Path, required=True)

    run = subparsers.add_parser("run", help="run an analysis from a YAML contract")
    run.add_argument("--config", type=Path, required=True)
    run.add_argument("--evidence", type=Path)

    demo = subparsers.add_parser("demo", help="generate data and run the complete teaching demo")
    demo.add_argument("--data", type=Path, default=Path("data/demo_tcells.h5ad"))
    demo.add_argument("--output-dir", type=Path, default=Path("output/demo"))
    demo.add_argument("--evidence", type=Path)
    demo.add_argument("--seed", type=int, default=42)
    demo.add_argument("--donors-per-condition", type=int, default=6)
    demo.add_argument("--cells-per-subtype-per-donor", type=int, default=12)
    return parser


def _run_from_config(config: AnalysisConfig, evidence: Path | None) -> int:
    result = run_pipeline(config, evidence_path=evidence)
    print(json.dumps(result.to_dict(), indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    """Execute the CLI and return a process status code."""

    args = _parser().parse_args(argv)
    if args.command == "make-demo":
        path = write_demo_h5ad(
            args.output,
            seed=args.seed,
            donors_per_condition=args.donors_per_condition,
            cells_per_subtype_per_donor=args.cells_per_subtype_per_donor,
        )
        print(path.resolve())
        return 0
    if args.command == "inspect":
        config = load_config(args.config)
        audit = audit_input(load_h5ad(config.input_path), config)
        print(json.dumps(audit.to_dict(), indent=2, sort_keys=True))
        return 1 if audit.blocked else 0
    if args.command == "run":
        return _run_from_config(load_config(args.config), args.evidence)
    if args.command == "demo":
        write_demo_h5ad(
            args.data,
            seed=args.seed,
            donors_per_condition=args.donors_per_condition,
            cells_per_subtype_per_donor=args.cells_per_subtype_per_donor,
        )
        config = demo_config(args.data.resolve(), args.output_dir.resolve(), seed=args.seed)
        return _run_from_config(config, args.evidence)
    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

