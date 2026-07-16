from evals.runner import RUBRIC_DIMENSIONS, run_suite


def main() -> int:
    suite = run_suite()

    print("AI SRE Assistant evaluation")
    print("=" * 35)
    for result in suite["results"]:
        checks = " ".join(
            f"{dimension}={'pass' if result['rubric'][dimension] else 'fail'}"
            for dimension in RUBRIC_DIMENSIONS
        )
        print(f"{result['id']}: {result['score']}/{result['max_score']} {checks}")

    print(
        f"\n{suite['cases_passed']}/{suite['cases_total']} cases passed; "
        f"{suite['checks_passed']}/{suite['checks_total']} rubric checks passed."
    )
    return 0 if suite["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
