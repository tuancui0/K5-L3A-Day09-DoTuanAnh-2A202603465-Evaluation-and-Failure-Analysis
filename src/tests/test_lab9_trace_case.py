"""Regression test for docs/trace_case.md: C-002@11, first wrong step = model_override (FM-03)."""
import pytest

pytestmark = pytest.mark.student


@pytest.fixture(scope="module")
def cases():
    from lab9.trace_case import investigate

    return {shape: investigate(shape, "C-002", 11) for shape in ("seeded_regression", "fixed")}


def ctx(case):
    from pydantic_evals.evaluators import EvaluatorContext

    return EvaluatorContext(name="t", inputs={}, metadata=None, expected_output=case["label"], output=case["trial"],
                            duration=0.0, _span_tree=None, attributes={}, metrics={})


def test_first_wrong_step_is_the_override(cases):
    kinds = [e["kind"] for e in cases["seeded_regression"]["trial"]["events"]]
    assert kinds.index("model_override") == 2          # event 3 in the trace
    assert "model_override" not in [e["kind"] for e in cases["fixed"]["trial"]["events"]]


def test_graders_catch_it_on_the_bug_and_pass_on_fixed(cases):
    from lab9 import graders

    bad, good = ctx(cases["seeded_regression"]), ctx(cases["fixed"])
    assert graders.DbFactKept().evaluate(bad).value is False
    assert graders.RefundAmountCorrect().evaluate(bad).value is False
    assert graders.DbFactKept().evaluate(good).value is True
    assert graders.RefundAmountCorrect().evaluate(good).value is True
    assert graders.ReplyMatchesLedger().evaluate(good).value is True
