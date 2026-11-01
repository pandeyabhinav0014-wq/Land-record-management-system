"""
Tests for Scikit-Learn Evaluation Metrics & Multi-Threshold Sensitivity (Section 11)
"""

from evaluation.metrics import compute_evaluation_metrics
from evaluation.threshold_analysis import ThresholdSensitivityAnalyzer

def test_evaluation_metrics_calculation():
    # 4 True Positives, 1 False Positive, 1 False Negative, 4 True Negatives
    y_true = [1, 1, 1, 1, 1, 0, 0, 0, 0, 0]
    y_pred = [1, 1, 1, 1, 0, 1, 0, 0, 0, 0]
    y_scores = [0.95, 0.90, 0.85, 0.80, 0.65, 0.75, 0.40, 0.30, 0.20, 0.10]

    metrics = compute_evaluation_metrics(y_true, y_pred, y_scores)
    
    assert metrics["sample_size"] == 10
    assert metrics["true_positives"] == 4
    assert metrics["false_positives"] == 1
    assert metrics["false_negatives"] == 1
    assert metrics["true_negatives"] == 4
    assert metrics["precision"] == 0.8 # 4 / (4 + 1)
    assert metrics["recall"] == 0.8 # 4 / (4 + 1)
    assert len(metrics["pr_curve"]) > 0

def test_threshold_sensitivity_analyzer():
    analyzer = ThresholdSensitivityAnalyzer(thresholds=[0.50, 0.70, 0.85])
    evaluated_pairs = [
        {"source_record_id_a": "A1", "source_record_id_b": "B1", "final_confidence": 0.92},
        {"source_record_id_a": "A2", "source_record_id_b": "B2", "final_confidence": 0.75},
        {"source_record_id_a": "A3", "source_record_id_b": "B3", "final_confidence": 0.60},
        {"source_record_id_a": "A4", "source_record_id_b": "B4", "final_confidence": 0.40},
    ]
    gt_lookup = {
        ("A1", "B1"): True,
        ("A2", "B2"): True,
        ("A3", "B3"): False,
        ("A4", "B4"): False
    }
    res = analyzer.run_sensitivity_analysis(evaluated_pairs, gt_lookup, detected_conflicts_count=3)
    
    assert len(res["threshold_analysis"]) == 3
    # At threshold 0.85: only A1-B1 is proposed (TP=1, FP=0 -> Precision=1.0)
    high_th = next(r for r in res["threshold_analysis"] if r["threshold"] == 0.85)
    assert high_th["precision"] == 1.0
    assert high_th["auto_accepted_count"] == 1
    assert "reproducibility_metadata" in res

