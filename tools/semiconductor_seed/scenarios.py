from __future__ import annotations

from .domain import ExperimentSpec


def experiment_specs() -> tuple[ExperimentSpec, ...]:
    return (
        ExperimentSpec("baseline-v1", "Baseline", "1.0.0", "baseline", {}),
        ExperimentSpec("baseline-v2", "Baseline", "2.0.0", "baseline", {}),
        ExperimentSpec("logistic-c-0.1-v1", "Model Comparison", "1.0.0", "logistic", {"c": 0.1}),
        ExperimentSpec("logistic-c-1-v1", "Model Comparison", "1.0.0", "logistic", {"c": 1.0}),
        ExperimentSpec("logistic-c-0.1-v2", "Model Comparison", "2.0.0", "logistic", {"c": 0.1}),
        ExperimentSpec("logistic-c-1-v2", "Model Comparison", "2.0.0", "logistic", {"c": 1.0}),
        ExperimentSpec("tree-depth-3-v1", "Model Comparison", "1.0.0", "tree", {"max_depth": 3}),
        ExperimentSpec("tree-depth-6-v1", "Model Comparison", "1.0.0", "tree", {"max_depth": 6}),
        ExperimentSpec("tree-depth-3-v2", "Parameter Tuning", "2.0.0", "tree", {"max_depth": 3}),
        ExperimentSpec("tree-depth-6-v2", "Parameter Tuning", "2.0.0", "tree", {"max_depth": 6}),
        ExperimentSpec(
            "tree-unlimited-v2",
            "Parameter Tuning",
            "2.0.0",
            "tree",
            {"max_depth": None},
        ),
        ExperimentSpec(
            "forest-50-depth-5-v1",
            "Model Comparison",
            "1.0.0",
            "forest",
            {"n_estimators": 50, "max_depth": 5},
        ),
        ExperimentSpec(
            "forest-100-v1",
            "Model Comparison",
            "1.0.0",
            "forest",
            {"n_estimators": 100, "max_depth": None},
            register_model=True,
        ),
        ExperimentSpec(
            "forest-50-depth-5-v2",
            "Parameter Tuning",
            "2.0.0",
            "forest",
            {"n_estimators": 50, "max_depth": 5},
        ),
        ExperimentSpec(
            "forest-100-depth-8-v2",
            "Parameter Tuning",
            "2.0.0",
            "forest",
            {"n_estimators": 100, "max_depth": 8},
        ),
        ExperimentSpec(
            "forest-150-depth-12-v2",
            "Parameter Tuning",
            "2.0.0",
            "forest",
            {"n_estimators": 150, "max_depth": 12},
            register_model=True,
        ),
        ExperimentSpec(
            "forest-200-v2",
            "Parameter Tuning",
            "2.0.0",
            "forest",
            {"n_estimators": 200, "max_depth": None},
            register_model=True,
        ),
        ExperimentSpec(
            "forest-300-depth-16-v2",
            "Parameter Tuning",
            "2.0.0",
            "forest",
            {"n_estimators": 300, "max_depth": 16},
        ),
        ExperimentSpec(
            "failure-missing-feature",
            "Model Comparison",
            "2.0.0",
            "failure",
            {},
            final_status="failed",
        ),
        ExperimentSpec(
            "aborted-large-search",
            "Parameter Tuning",
            "2.0.0",
            "aborted",
            {},
            final_status="aborted",
        ),
    )
