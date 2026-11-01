"""
Evaluation Metrics Framework (Section 11)
Calculates real validation metrics: Precision, Recall, F1, FPR, FNR,
Confusion Matrix, and PR-curve points using Scikit-Learn.
"""

from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix, precision_recall_curve

def compute_evaluation_metrics(
    y_true: List[int],
    y_pred: List[int],
    y_scores: Optional[List[float]] = None
) -> Dict[str, Any]:
    """
    Computes rigorous evaluation metrics from binary ground-truth and predictions.
    y_true: 1 for SAME_PARCEL, 0 for DIFFERENT_PARCEL
    y_pred: 1 for predicted match, 0 for predicted non-match
    y_scores: optional float confidence scores in [0.0, 1.0]
    """
    y_true_arr = np.array(y_true, dtype=int)
    y_pred_arr = np.array(y_pred, dtype=int)

    if len(y_true_arr) == 0:
        return {
            "sample_size": 0,
            "precision": 0.0,
            "recall": 0.0,
            "f1_score": 0.0,
            "false_positive_rate": 0.0,
            "false_negative_rate": 0.0,
            "confusion_matrix": {"tp": 0, "fp": 0, "fn": 0, "tn": 0},
            "pr_curve": []
        }

    # Confusion matrix
    # Format: [[tn, fp], [fn, tp]]
    cm = confusion_matrix(y_true_arr, y_pred_arr, labels=[0, 1])
    tn, fp, fn, tp = int(cm[0, 0]), int(cm[0, 1]), int(cm[1, 0]), int(cm[1, 1])

    prec = float(precision_score(y_true_arr, y_pred_arr, zero_division=0))
    rec = float(recall_score(y_true_arr, y_pred_arr, zero_division=0))
    f1 = float(f1_score(y_true_arr, y_pred_arr, zero_division=0))

    fpr = round(float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0, 4)
    fnr = round(float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0, 4)

    pr_curve_data = []
    if y_scores is not None and len(y_scores) == len(y_true_arr):
        try:
            scores_arr = np.array(y_scores, dtype=float)
            precisions, recalls, thresholds = precision_recall_curve(y_true_arr, scores_arr)
            for p, r, t in zip(precisions, recalls, thresholds):
                pr_curve_data.append({
                    "threshold": round(float(t), 3),
                    "precision": round(float(p), 4),
                    "recall": round(float(r), 4)
                })
        except Exception:
            pr_curve_data = []

    return {
        "sample_size": len(y_true_arr),
        "true_positives": tp,
        "false_positives": fp,
        "true_negatives": tn,
        "false_negatives": fn,
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "false_positive_rate": fpr,
        "false_negative_rate": fnr,
        "confusion_matrix": {
            "tp": tp,
            "fp": fp,
            "tn": tn,
            "fn": fn
        },
        "pr_curve": pr_curve_data
    }
