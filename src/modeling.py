"""Small, deterministic K-means and logistic-regression implementations."""

from __future__ import annotations

import numpy as np
import pandas as pd


SEED = 732
CLUSTER_COUNT = 4


def _standardize_fit(x: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    mean = x.mean(axis=0)
    scale = x.std(axis=0)
    scale[scale == 0] = 1.0
    return (x - mean) / scale, mean, scale


def _kmeans_once(x: np.ndarray, k: int, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray, float]:
    """K-means++ initialization followed by Lloyd iterations."""
    n = len(x)
    centers = [x[int(rng.integers(n))]]
    min_d2 = np.sum((x - centers[0]) ** 2, axis=1)
    while len(centers) < k:
        total = float(min_d2.sum())
        idx = int(rng.integers(n)) if total <= 0 else int(rng.choice(n, p=min_d2 / total))
        centers.append(x[idx])
        min_d2 = np.minimum(min_d2, np.sum((x - x[idx]) ** 2, axis=1))
    centers_array = np.array(centers, dtype=float)

    for _ in range(300):
        d2 = np.sum((x[:, None, :] - centers_array[None, :, :]) ** 2, axis=2)
        labels = d2.argmin(axis=1)
        updated = centers_array.copy()
        for j in range(k):
            members = x[labels == j]
            if len(members):
                updated[j] = members.mean(axis=0)
            else:
                # Empty clusters are reseeded at the observation least well represented.
                updated[j] = x[int(np.argmax(d2.min(axis=1)))]
        if np.allclose(updated, centers_array, atol=1e-7):
            centers_array = updated
            break
        centers_array = updated

    d2 = np.sum((x[:, None, :] - centers_array[None, :, :]) ** 2, axis=2)
    labels = d2.argmin(axis=1)
    inertia = float(d2[np.arange(n), labels].sum())
    return labels, centers_array, inertia


def _silhouette(x: np.ndarray, labels: np.ndarray) -> float:
    """Mean silhouette coefficient, computed directly for the small match table."""
    names = np.unique(labels)
    if len(names) < 2 or len(names) >= len(labels):
        return float("nan")
    distances = np.sqrt(np.maximum(0, np.sum((x[:, None, :] - x[None, :, :]) ** 2, axis=2)))
    scores = np.zeros(len(x), dtype=float)
    for i, own in enumerate(labels):
        same = np.flatnonzero(labels == own)
        same = same[same != i]
        a = float(distances[i, same].mean()) if len(same) else 0.0
        b = min(
            float(distances[i, labels == other].mean())
            for other in names if other != own
        )
        denom = max(a, b)
        scores[i] = (b - a) / denom if denom else 0.0
    return float(scores.mean())


def cluster_states(
    states: pd.DataFrame,
    feature_names: list[str],
    label_name: str,
    seed: int = SEED,
    k: int = CLUSTER_COUNT,
    starts: int = 10,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    """Cluster standardized state features and return assignments, raw centers, quality."""
    x_raw = states[feature_names].to_numpy(dtype=float)
    if not np.isfinite(x_raw).all() or len(x_raw) <= k:
        raise ValueError("K-means input must be finite and contain more rows than clusters")
    x, mean, scale = _standardize_fit(x_raw)
    best: tuple[np.ndarray, np.ndarray, float] | None = None
    rng = np.random.default_rng(seed)
    for _ in range(starts):
        result = _kmeans_once(x, k, rng)
        if best is None or result[2] < best[2]:
            best = result
    assert best is not None
    labels, centers, inertia = best
    raw_centers = centers * scale + mean

    # Stable display order: ascending powerplay runs, then wickets, then pressure.
    order_cols = [feature_names.index("runs_after_six")]
    if "wickets_lost_after_six" in feature_names:
        order_cols.append(feature_names.index("wickets_lost_after_six"))
    if "required_run_rate" in feature_names:
        order_cols.append(feature_names.index("required_run_rate"))
    ordering = np.lexsort(tuple(raw_centers[:, j] for j in reversed(order_cols)))
    mapping = {int(old): int(new + 1) for new, old in enumerate(ordering)}
    stable_labels = np.array([mapping[int(label)] for label in labels], dtype=int)
    stable_centers = raw_centers[ordering]

    assignment = states[["match_id", "match_date", "chase_success"]].copy()
    assignment[label_name] = stable_labels
    centers_df = pd.DataFrame(stable_centers, columns=feature_names)
    centers_df.insert(0, label_name, np.arange(1, k + 1))
    counts = pd.Series(stable_labels).value_counts().sort_index()
    quality = {
        "clusters": k,
        "features": feature_names,
        "seed": seed,
        "initializations": starts,
        "inertia_standardized": inertia,
        "silhouette_standardized": _silhouette(x, stable_labels),
        "cluster_counts": {str(int(i)): int(v) for i, v in counts.items()},
        "centers_in_original_units": centers_df.to_dict(orient="records"),
        "interpretation_note": "Cluster numbers are stable display indices, not natural cricket categories.",
    }
    return assignment, centers_df, quality


def _sigmoid(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(z, -35, 35)))


def _fit_logistic(x: np.ndarray, y: np.ndarray, alpha: float = 0.02) -> tuple[float, np.ndarray, int]:
    """Fit L2-regularized binary logistic regression by batch gradient descent."""
    design = np.column_stack([np.ones(len(x)), x])
    beta = np.zeros(design.shape[1], dtype=float)
    penalty = np.ones_like(beta)
    penalty[0] = 0.0
    learning_rate = 0.1
    previous = np.inf
    for iteration in range(1, 10001):
        p = _sigmoid(design @ beta)
        gradient = design.T @ (p - y) / len(y) + alpha * penalty * beta
        beta -= learning_rate * gradient
        loss = -np.mean(y * np.log(np.clip(p, 1e-12, 1)) + (1 - y) * np.log(np.clip(1 - p, 1e-12, 1)))
        loss += 0.5 * alpha * float(np.sum(beta[1:] ** 2))
        if abs(previous - loss) < 1e-10:
            break
        previous = loss
    return float(beta[0]), beta[1:], iteration


def _auc(y: np.ndarray, p: np.ndarray) -> float:
    positive = p[y == 1]
    negative = p[y == 0]
    if not len(positive) or not len(negative):
        return float("nan")
    comparisons = positive[:, None] - negative[None, :]
    return float(((comparisons > 0).sum() + 0.5 * (comparisons == 0).sum()) / comparisons.size)


def _metrics(y: np.ndarray, p: np.ndarray, threshold: float = 0.5) -> dict[str, float | int]:
    pred = (p >= threshold).astype(int)
    tp = int(((pred == 1) & (y == 1)).sum())
    tn = int(((pred == 0) & (y == 0)).sum())
    fp = int(((pred == 1) & (y == 0)).sum())
    fn = int(((pred == 0) & (y == 1)).sum())
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {
        "accuracy": float((pred == y).mean()),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(2 * precision * recall / (precision + recall)) if precision + recall else 0.0,
        "roc_auc": _auc(y, p),
        "brier_score": float(np.mean((p - y) ** 2)),
        "true_positive": tp,
        "true_negative": tn,
        "false_positive": fp,
        "false_negative": fn,
    }


def compare_models(states: pd.DataFrame) -> tuple[dict[str, object], pd.DataFrame]:
    """Compare baseline, raw-state, and pressure-aware models on one date holdout."""
    ordered_dates = np.array(sorted(pd.to_datetime(states.match_date).unique()))
    if len(ordered_dates) < 3:
        raise ValueError("A chronological holdout requires at least three distinct match dates")
    cutoff_index = min(max(int(len(ordered_dates) * 0.8), 1), len(ordered_dates) - 1)
    cutoff = pd.Timestamp(ordered_dates[cutoff_index])
    train_mask = states.match_date < cutoff
    test_mask = states.match_date >= cutoff
    y_train = states.loc[train_mask, "chase_success"].to_numpy(dtype=float)
    y_test = states.loc[test_mask, "chase_success"].to_numpy(dtype=int)
    if len(np.unique(y_train)) < 2 or len(np.unique(y_test)) < 2:
        raise ValueError("Both classes must be present in chronological train and test partitions")

    feature_sets = {
        "iteration1_raw_state": ["runs_after_six", "wickets_lost_after_six"],
        "iteration2_target_pressure": ["runs_after_six", "wickets_lost_after_six", "required_run_rate"],
    }
    majority = int(y_train.mean() >= 0.5)
    model_output: dict[str, object] = {
        "target": "chase_success (second-innings batting team is the official winner)",
        "observation_time": "after 36 legal balls in second-innings overs 0-5",
        "feature_sets": feature_sets,
        "split": {
            "strategy": "chronological by distinct match dates; earlier dates train, later dates test",
            "cutoff_date_inclusive_for_test": str(cutoff.date()),
            "train_rows": int(train_mask.sum()),
            "test_rows": int(test_mask.sum()),
            "train_date_min": str(states.loc[train_mask, "match_date"].min().date()),
            "train_date_max": str(states.loc[train_mask, "match_date"].max().date()),
            "test_date_min": str(states.loc[test_mask, "match_date"].min().date()),
            "test_date_max": str(states.loc[test_mask, "match_date"].max().date()),
        },
        "training_only_preprocessing": "Each logistic model's feature means and standard deviations are fit on training rows only.",
        "logistic": {"solver": "batch gradient descent", "l2_alpha": 0.02, "learning_rate": 0.1, "max_iterations": 10000, "threshold": 0.5},
        "majority_baseline_class": majority,
        "models": {},
    }
    predictions = states.loc[test_mask, ["match_id", "match_date", "chase_success"]].copy()
    baseline_prob = np.full(len(y_test), float(y_train.mean()))
    model_output["models"]["majority_baseline"] = _metrics(y_test, np.full(len(y_test), majority, dtype=float))
    model_output["models"]["majority_baseline_probability"] = _metrics(y_test, baseline_prob)
    predictions["baseline_probability"] = baseline_prob

    for name, features in feature_sets.items():
        x_train_raw = states.loc[train_mask, features].to_numpy(dtype=float)
        x_test_raw = states.loc[test_mask, features].to_numpy(dtype=float)
        x_train, mean, scale = _standardize_fit(x_train_raw)
        x_test = (x_test_raw - mean) / scale
        intercept, coefficients, iterations = _fit_logistic(x_train, y_train)
        p = _sigmoid(intercept + x_test @ coefficients)
        metrics = _metrics(y_test, p)
        metrics["iterations"] = iterations
        metrics["coefficients_standardized"] = {
            "intercept": intercept,
            **{feature: float(value) for feature, value in zip(features, coefficients)},
        }
        model_output["models"][name] = metrics
        predictions[f"{name}_probability"] = p
        predictions[f"{name}_prediction"] = (p >= 0.5).astype(int)

    return model_output, predictions.reset_index(drop=True)
