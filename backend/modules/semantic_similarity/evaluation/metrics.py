import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import json
import os
from datetime import datetime


@dataclass
class EvaluationResult:
    """Container for evaluation results"""
    precision: float
    recall: float
    f1_score: float
    accuracy: float
    roc_auc: float
    mse: float
    pearson_r: float
    spearman_r: float
    confusion_matrix: Dict[str, int]
    threshold: float
    sample_count: int

    def to_dict(self) -> Dict:
        return {
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1_score": round(self.f1_score, 4),
            "accuracy": round(self.accuracy, 4),
            "roc_auc": round(self.roc_auc, 4),
            "mse": round(self.mse, 4),
            "pearson_r": round(self.pearson_r, 4),
            "spearman_r": round(self.spearman_r, 4),
            "confusion_matrix": self.confusion_matrix,
            "threshold": self.threshold,
            "sample_count": self.sample_count
        }

    def __str__(self) -> str:
        return f"""
=== Evaluation Results ===
Samples: {self.sample_count}
Threshold: {self.threshold}

Classification Metrics:
  Precision: {self.precision:.4f}
  Recall:    {self.recall:.4f}
  F1 Score:  {self.f1_score:.4f}
  Accuracy:  {self.accuracy:.4f}

Ranking Metrics:
  ROC-AUC:   {self.roc_auc:.4f}

Regression Metrics:
  MSE:       {self.mse:.4f}
  Pearson r: {self.pearson_r:.4f}
  Spearman r:{self.spearman_r:.4f}

Confusion Matrix:
  TP: {self.confusion_matrix['TP']}  FP: {self.confusion_matrix['FP']}
  FN: {self.confusion_matrix['FN']}  TN: {self.confusion_matrix['TN']}
"""


class EvaluationMetrics:
    """
    Complete evaluation metrics for semantic similarity models
    """

    def __init__(self, threshold: float = 0.5):
        """
        Initialize evaluator

        Args:
            threshold: Classification threshold for plagiarism detection
        """
        self.threshold = threshold

    def precision(self, predictions: np.ndarray, labels: np.ndarray) -> float:
        """
        Calculate precision: TP / (TP + FP)
        Precision measures how many of the predicted positives are actual positives
        """
        pred_binary = (predictions >= self.threshold).astype(int)
        label_binary = (labels >= self.threshold).astype(int)

        true_positives = np.sum((pred_binary == 1) & (label_binary == 1))
        false_positives = np.sum((pred_binary == 1) & (label_binary == 0))

        if true_positives + false_positives == 0:
            return 0.0

        return true_positives / (true_positives + false_positives)

    def recall(self, predictions: np.ndarray, labels: np.ndarray) -> float:
        """
        Calculate recall: TP / (TP + FN)
        Recall measures how many of the actual positives are correctly identified
        """
        pred_binary = (predictions >= self.threshold).astype(int)
        label_binary = (labels >= self.threshold).astype(int)

        true_positives = np.sum((pred_binary == 1) & (label_binary == 1))
        false_negatives = np.sum((pred_binary == 0) & (label_binary == 1))

        if true_positives + false_negatives == 0:
            return 0.0

        return true_positives / (true_positives + false_negatives)

    def f1_score(self, predictions: np.ndarray, labels: np.ndarray) -> float:
        """
        Calculate F1 score: 2 * (precision * recall) / (precision + recall)
        Harmonic mean of precision and recall
        """
        p = self.precision(predictions, labels)
        r = self.recall(predictions, labels)

        if p + r == 0:
            return 0.0

        return 2 * (p * r) / (p + r)

    def accuracy(self, predictions: np.ndarray, labels: np.ndarray) -> float:
        """
        Calculate accuracy: (TP + TN) / Total
        """
        pred_binary = (predictions >= self.threshold).astype(int)
        label_binary = (labels >= self.threshold).astype(int)

        correct = np.sum(pred_binary == label_binary)
        return correct / len(predictions)

    def confusion_matrix(self, predictions: np.ndarray, labels: np.ndarray) -> Dict[str, int]:
        """
        Calculate confusion matrix components

        Returns:
            Dict with TP, TN, FP, FN counts
        """
        pred_binary = (predictions >= self.threshold).astype(int)
        label_binary = (labels >= self.threshold).astype(int)

        tp = int(np.sum((pred_binary == 1) & (label_binary == 1)))
        tn = int(np.sum((pred_binary == 0) & (label_binary == 0)))
        fp = int(np.sum((pred_binary == 1) & (label_binary == 0)))
        fn = int(np.sum((pred_binary == 0) & (label_binary == 1)))

        return {"TP": tp, "TN": tn, "FP": fp, "FN": fn}

    def roc_auc(self, predictions: np.ndarray, labels: np.ndarray) -> float:
        """
        Calculate ROC-AUC (Area Under the ROC Curve)
        Uses trapezoidal rule for numerical integration
        """
        # Convert labels to binary
        label_binary = (labels >= self.threshold).astype(int)

        # Sort by predictions (descending)
        sorted_indices = np.argsort(predictions)[::-1]
        sorted_labels = label_binary[sorted_indices]

        # Calculate TPR and FPR at each threshold
        n_pos = np.sum(label_binary == 1)
        n_neg = np.sum(label_binary == 0)

        if n_pos == 0 or n_neg == 0:
            return 0.5  # Undefined, return random baseline

        tpr_list = []
        fpr_list = []

        tp = 0
        fp = 0

        for i in range(len(sorted_labels)):
            if sorted_labels[i] == 1:
                tp += 1
            else:
                fp += 1

            tpr_list.append(tp / n_pos)
            fpr_list.append(fp / n_neg)

        # Calculate AUC using trapezoidal rule
        auc = 0.0
        for i in range(1, len(fpr_list)):
            auc += (fpr_list[i] - fpr_list[i-1]) * (tpr_list[i] + tpr_list[i-1]) / 2

        return auc

    def precision_recall_curve(self, predictions: np.ndarray, labels: np.ndarray,
                                num_thresholds: int = 100) -> Tuple[List[float], List[float], List[float]]:
        """
        Calculate precision-recall curve at multiple thresholds

        Returns:
            Tuple of (precisions, recalls, thresholds)
        """
        thresholds = np.linspace(0, 1, num_thresholds)
        precisions = []
        recalls = []

        original_threshold = self.threshold

        for thresh in thresholds:
            self.threshold = thresh
            precisions.append(self.precision(predictions, labels))
            recalls.append(self.recall(predictions, labels))

        self.threshold = original_threshold

        return list(precisions), list(recalls), list(thresholds)

    def mse(self, predictions: np.ndarray, labels: np.ndarray) -> float:
        """
        Calculate Mean Squared Error
        Measures average squared difference between predictions and labels
        """
        return float(np.mean((predictions - labels) ** 2))

    def rmse(self, predictions: np.ndarray, labels: np.ndarray) -> float:
        """
        Calculate Root Mean Squared Error
        """
        return float(np.sqrt(self.mse(predictions, labels)))

    def mae(self, predictions: np.ndarray, labels: np.ndarray) -> float:
        """
        Calculate Mean Absolute Error
        """
        return float(np.mean(np.abs(predictions - labels)))

    def pearson_correlation(self, predictions: np.ndarray, labels: np.ndarray) -> float:
        """
        Calculate Pearson correlation coefficient
        Measures linear correlation between predictions and labels
        """
        if len(predictions) < 2:
            return 0.0

        # Calculate means
        pred_mean = np.mean(predictions)
        label_mean = np.mean(labels)

        # Calculate correlation
        numerator = np.sum((predictions - pred_mean) * (labels - label_mean))
        denominator = np.sqrt(
            np.sum((predictions - pred_mean) ** 2) *
            np.sum((labels - label_mean) ** 2)
        )

        if denominator == 0:
            return 0.0

        return numerator / denominator

    def spearman_correlation(self, predictions: np.ndarray, labels: np.ndarray) -> float:
        """
        Calculate Spearman rank correlation coefficient
        Measures monotonic relationship between predictions and labels
        """
        if len(predictions) < 2:
            return 0.0

        # Rank the values
        pred_ranks = self._rank_data(predictions)
        label_ranks = self._rank_data(labels)

        # Calculate Pearson correlation on ranks
        return self.pearson_correlation(pred_ranks, label_ranks)

    def _rank_data(self, data: np.ndarray) -> np.ndarray:
        """Rank data (handling ties with average)"""
        sorted_indices = np.argsort(data)
        ranks = np.empty_like(sorted_indices, dtype=float)

        # Assign ranks
        for i, idx in enumerate(sorted_indices):
            ranks[idx] = i + 1

        return ranks

    def evaluate_all(self, predictions: np.ndarray, labels: np.ndarray) -> EvaluationResult:
        """
        Run all evaluation metrics and return comprehensive results

        Args:
            predictions: Model predictions (0-1 range)
            labels: Ground truth labels (0-1 range)

        Returns:
            EvaluationResult with all metrics
        """
        predictions = np.array(predictions, dtype=float)
        labels = np.array(labels, dtype=float)

        # Validate inputs
        assert len(predictions) == len(labels), "Predictions and labels must have same length"
        assert len(predictions) > 0, "Empty predictions"

        return EvaluationResult(
            precision=self.precision(predictions, labels),
            recall=self.recall(predictions, labels),
            f1_score=self.f1_score(predictions, labels),
            accuracy=self.accuracy(predictions, labels),
            roc_auc=self.roc_auc(predictions, labels),
            mse=self.mse(predictions, labels),
            pearson_r=self.pearson_correlation(predictions, labels),
            spearman_r=self.spearman_correlation(predictions, labels),
            confusion_matrix=self.confusion_matrix(predictions, labels),
            threshold=self.threshold,
            sample_count=len(predictions)
        )


class MultiThresholdEvaluator:
    """Evaluate model at multiple thresholds to find optimal"""

    def __init__(self, thresholds: List[float] = None):
        self.thresholds = thresholds or [0.3, 0.4, 0.5, 0.6, 0.7]

    def find_optimal_threshold(self, predictions: np.ndarray,
                                labels: np.ndarray,
                                metric: str = "f1") -> Tuple[float, float]:
        """
        Find optimal threshold based on specified metric

        Args:
            predictions: Model predictions
            labels: Ground truth
            metric: Metric to optimize ("f1", "precision", "recall", "accuracy")

        Returns:
            Tuple of (optimal_threshold, best_score)
        """
        best_threshold = 0.5
        best_score = 0.0

        for thresh in np.linspace(0.1, 0.9, 81):
            evaluator = EvaluationMetrics(threshold=thresh)
            result = evaluator.evaluate_all(predictions, labels)

            if metric == "f1":
                score = result.f1_score
            elif metric == "precision":
                score = result.precision
            elif metric == "recall":
                score = result.recall
            elif metric == "accuracy":
                score = result.accuracy
            else:
                score = result.f1_score

            if score > best_score:
                best_score = score
                best_threshold = thresh

        return best_threshold, best_score

    def evaluate_at_thresholds(self, predictions: np.ndarray,
                                labels: np.ndarray) -> List[Dict]:
        """Evaluate at multiple thresholds"""
        results = []

        for thresh in self.thresholds:
            evaluator = EvaluationMetrics(threshold=thresh)
            result = evaluator.evaluate_all(predictions, labels)
            result_dict = result.to_dict()
            results.append(result_dict)

        return results


def save_evaluation_results(results: EvaluationResult, model_name: str,
                            output_dir: str = None):
    """Save evaluation results to JSON file"""
    output_dir = output_dir or os.path.dirname(os.path.abspath(__file__))

    filename = f"eval_{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump({
            "model_name": model_name,
            "timestamp": datetime.now().isoformat(),
            "results": results.to_dict()
        }, f, indent=2)

    print(f"Results saved to: {filepath}")
    return filepath


# Example usage
if __name__ == "__main__":
    # Example: Test with dummy data
    np.random.seed(42)

    # Simulate predictions and labels
    n_samples = 100
    labels = np.random.uniform(0, 1, n_samples)
    predictions = labels + np.random.normal(0, 0.2, n_samples)  # Add noise
    predictions = np.clip(predictions, 0, 1)

    # Evaluate
    evaluator = EvaluationMetrics(threshold=0.5)
    results = evaluator.evaluate_all(predictions, labels)

    print(results)

    # Find optimal threshold
    multi_eval = MultiThresholdEvaluator()
    optimal_thresh, best_f1 = multi_eval.find_optimal_threshold(predictions, labels)
    print(f"\nOptimal Threshold: {optimal_thresh:.2f} (F1: {best_f1:.4f})")
