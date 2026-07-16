import pytest

from evals.runner import evaluate_case, evaluate_output, load_cases


CASES = load_cases()


@pytest.mark.parametrize("case", CASES, ids=[case["id"] for case in CASES])
def test_assistant_meets_evaluation_rubric(case):
    result = evaluate_case(case)

    assert result["passed"], result


def test_evaluation_detects_missing_grounding():
    case = next(case for case in CASES if case["id"] == "error-spike")
    output = {
        "summary": "Everything is fine.",
        "facts": [],
        "guesses": ["The failures are likely intentional."],
        "evidence": [],
        "next_steps": ["Review the cited log evidence before changing code."],
        "possible_fixes": ["Inspect the failing endpoint."],
    }

    result = evaluate_output(case, output)

    assert result["passed"] is False
    assert result["rubric"]["grounded"] is False


def test_evaluation_detects_secret_regression():
    case = next(case for case in CASES if case["id"] == "secret-in-evidence")
    output = {
        "summary": "Recent logs show 1 error event(s).",
        "facts": ["Found 1 error events."],
        "guesses": ["The available logs do not show a single clear cause."],
        "evidence": [{"message": "provider rejected sk-eval-secret-123456"}],
        "next_steps": ["Start with the most recent ERROR event."],
        "possible_fixes": ["Inspect error log evidence."],
    }

    result = evaluate_output(case, output)

    assert result["passed"] is False
    assert result["rubric"]["private"] is False
