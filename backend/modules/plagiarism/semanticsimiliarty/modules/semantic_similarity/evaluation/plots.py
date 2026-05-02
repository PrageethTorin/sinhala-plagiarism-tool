"""
Visualization Module for Evaluation Results
Generates plots for research papers and reports

Plots:
- ROC Curve
- Precision-Recall Curve
- Confusion Matrix Heatmap
- Model Comparison Bar Charts
- Score Distribution Histograms
"""

import os
import numpy as np
from typing import List, Dict, Tuple, Optional

# Check if matplotlib is available
try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("Warning: matplotlib not installed. Plotting functions will be disabled.")


class EvaluationPlotter:
    """Generate evaluation visualizations"""

    def __init__(self, output_dir: str = None, style: str = "seaborn-v0_8-whitegrid"):
        """
        Initialize plotter

        Args:
            output_dir: Directory to save plots
            style: Matplotlib style to use
        """
        self.output_dir = output_dir or os.path.dirname(os.path.abspath(__file__))

        if HAS_MATPLOTLIB:
            try:
                plt.style.use(style)
            except OSError:
                plt.style.use('default')

    def plot_roc_curve(self, predictions: np.ndarray, labels: np.ndarray,
                       model_name: str = "Model", threshold: float = 0.5,
                       save: bool = True) -> Optional[str]:
        """
        Plot ROC curve

        Args:
            predictions: Model predictions
            labels: Ground truth labels
            model_name: Name for legend
            threshold: Classification threshold
            save: Whether to save the plot

        Returns:
            Path to saved plot if save=True
        """
        if not HAS_MATPLOTLIB:
            print("matplotlib not available")
            return None

        # Convert labels to binary
        label_binary = (labels >= threshold).astype(int)

        # Calculate TPR and FPR at different thresholds
        thresholds = np.linspace(0, 1, 100)
        tpr_list = []
        fpr_list = []

        n_pos = np.sum(label_binary == 1)
        n_neg = np.sum(label_binary == 0)

        for thresh in thresholds:
            pred_binary = (predictions >= thresh).astype(int)

            tp = np.sum((pred_binary == 1) & (label_binary == 1))
            fp = np.sum((pred_binary == 1) & (label_binary == 0))

            tpr = tp / n_pos if n_pos > 0 else 0
            fpr = fp / n_neg if n_neg > 0 else 0

            tpr_list.append(tpr)
            fpr_list.append(fpr)

        # Calculate AUC
        auc = np.abs(np.trapz(tpr_list, fpr_list))

        # Create plot
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.plot(fpr_list, tpr_list, 'b-', linewidth=2,
                label=f'{model_name} (AUC = {auc:.4f})')
        ax.plot([0, 1], [0, 1], 'k--', linewidth=1, label='Random (AUC = 0.5)')

        ax.set_xlabel('False Positive Rate', fontsize=12)
        ax.set_ylabel('True Positive Rate', fontsize=12)
        ax.set_title('ROC Curve', fontsize=14)
        ax.legend(loc='lower right', fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.set_xlim([0, 1])
        ax.set_ylim([0, 1])

        if save:
            path = os.path.join(self.output_dir, f"roc_curve_{model_name}.png")
            plt.savefig(path, dpi=150, bbox_inches='tight')
            plt.close()
            print(f"Saved: {path}")
            return path

        plt.show()
        return None

    def plot_precision_recall_curve(self, predictions: np.ndarray, labels: np.ndarray,
                                     model_name: str = "Model", threshold: float = 0.5,
                                     save: bool = True) -> Optional[str]:
        """Plot Precision-Recall curve"""
        if not HAS_MATPLOTLIB:
            return None

        label_binary = (labels >= threshold).astype(int)

        thresholds = np.linspace(0.01, 0.99, 100)
        precisions = []
        recalls = []

        for thresh in thresholds:
            pred_binary = (predictions >= thresh).astype(int)

            tp = np.sum((pred_binary == 1) & (label_binary == 1))
            fp = np.sum((pred_binary == 1) & (label_binary == 0))
            fn = np.sum((pred_binary == 0) & (label_binary == 1))

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0

            precisions.append(precision)
            recalls.append(recall)

        fig, ax = plt.subplots(figsize=(8, 6))
        ax.plot(recalls, precisions, 'b-', linewidth=2, label=model_name)

        ax.set_xlabel('Recall', fontsize=12)
        ax.set_ylabel('Precision', fontsize=12)
        ax.set_title('Precision-Recall Curve', fontsize=14)
        ax.legend(loc='lower left', fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.set_xlim([0, 1])
        ax.set_ylim([0, 1])

        if save:
            path = os.path.join(self.output_dir, f"pr_curve_{model_name}.png")
            plt.savefig(path, dpi=150, bbox_inches='tight')
            plt.close()
            print(f"Saved: {path}")
            return path

        plt.show()
        return None

    def plot_confusion_matrix(self, confusion_matrix: Dict[str, int],
                              model_name: str = "Model",
                              save: bool = True) -> Optional[str]:
        """Plot confusion matrix as heatmap"""
        if not HAS_MATPLOTLIB:
            return None

        tp = confusion_matrix["TP"]
        tn = confusion_matrix["TN"]
        fp = confusion_matrix["FP"]
        fn = confusion_matrix["FN"]

        matrix = np.array([[tn, fp], [fn, tp]])

        fig, ax = plt.subplots(figsize=(6, 5))
        im = ax.imshow(matrix, cmap='Blues')

        # Add colorbar
        plt.colorbar(im)

        # Add labels
        ax.set_xticks([0, 1])
        ax.set_yticks([0, 1])
        ax.set_xticklabels(['Predicted Negative', 'Predicted Positive'])
        ax.set_yticklabels(['Actual Negative', 'Actual Positive'])

        # Add values to cells
        for i in range(2):
            for j in range(2):
                text = ax.text(j, i, matrix[i, j],
                              ha="center", va="center", color="black", fontsize=14)

        ax.set_title(f'Confusion Matrix - {model_name}', fontsize=14)
        plt.tight_layout()

        if save:
            path = os.path.join(self.output_dir, f"confusion_matrix_{model_name}.png")
            plt.savefig(path, dpi=150, bbox_inches='tight')
            plt.close()
            print(f"Saved: {path}")
            return path

        plt.show()
        return None

    def plot_model_comparison(self, results: Dict[str, Dict],
                              metrics: List[str] = None,
                              save: bool = True) -> Optional[str]:
        """
        Plot bar chart comparing multiple models

        Args:
            results: Dict mapping model names to their results
            metrics: List of metrics to compare
            save: Whether to save the plot
        """
        if not HAS_MATPLOTLIB:
            return None

        metrics = metrics or ["precision", "recall", "f1_score", "roc_auc"]
        model_names = list(results.keys())

        x = np.arange(len(metrics))
        width = 0.8 / len(model_names)

        fig, ax = plt.subplots(figsize=(12, 6))

        for i, (model_name, model_results) in enumerate(results.items()):
            r = model_results.get("results", model_results)
            values = [r.get(m, 0) for m in metrics]
            offset = (i - len(model_names)/2 + 0.5) * width
            bars = ax.bar(x + offset, values, width, label=model_name)

            # Add value labels on bars
            for bar, val in zip(bars, values):
                height = bar.get_height()
                ax.annotate(f'{val:.3f}',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3),
                           textcoords="offset points",
                           ha='center', va='bottom', fontsize=8)

        ax.set_xlabel('Metric', fontsize=12)
        ax.set_ylabel('Score', fontsize=12)
        ax.set_title('Model Comparison', fontsize=14)
        ax.set_xticks(x)
        ax.set_xticklabels([m.replace('_', ' ').title() for m in metrics])
        ax.legend(loc='upper right', fontsize=10)
        ax.set_ylim([0, 1.1])
        ax.grid(True, alpha=0.3, axis='y')

        if save:
            path = os.path.join(self.output_dir, "model_comparison.png")
            plt.savefig(path, dpi=150, bbox_inches='tight')
            plt.close()
            print(f"Saved: {path}")
            return path

        plt.show()
        return None

    def plot_score_distribution(self, predictions: np.ndarray, labels: np.ndarray,
                                 model_name: str = "Model",
                                 save: bool = True) -> Optional[str]:
        """Plot distribution of predicted scores vs actual labels"""
        if not HAS_MATPLOTLIB:
            return None

        fig, axes = plt.subplots(1, 2, figsize=(12, 5))

        # Plot predictions distribution
        axes[0].hist(predictions, bins=20, color='blue', alpha=0.7, edgecolor='black')
        axes[0].set_xlabel('Predicted Score', fontsize=12)
        axes[0].set_ylabel('Count', fontsize=12)
        axes[0].set_title('Prediction Distribution', fontsize=14)
        axes[0].axvline(x=0.5, color='red', linestyle='--', label='Threshold (0.5)')
        axes[0].legend()

        # Plot predicted vs actual
        axes[1].scatter(labels, predictions, alpha=0.5, s=10)
        axes[1].plot([0, 1], [0, 1], 'r--', linewidth=2, label='Perfect correlation')
        axes[1].set_xlabel('Actual Label', fontsize=12)
        axes[1].set_ylabel('Predicted Score', fontsize=12)
        axes[1].set_title('Predicted vs Actual', fontsize=14)
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)

        plt.suptitle(f'{model_name} - Score Analysis', fontsize=16)
        plt.tight_layout()

        if save:
            path = os.path.join(self.output_dir, f"score_distribution_{model_name}.png")
            plt.savefig(path, dpi=150, bbox_inches='tight')
            plt.close()
            print(f"Saved: {path}")
            return path

        plt.show()
        return None

    def plot_threshold_analysis(self, predictions: np.ndarray, labels: np.ndarray,
                                model_name: str = "Model",
                                save: bool = True) -> Optional[str]:
        """Plot F1, Precision, Recall across different thresholds"""
        if not HAS_MATPLOTLIB:
            return None

        thresholds = np.linspace(0.1, 0.9, 81)
        f1_scores = []
        precisions = []
        recalls = []

        label_binary = (labels >= 0.5).astype(int)

        for thresh in thresholds:
            pred_binary = (predictions >= thresh).astype(int)

            tp = np.sum((pred_binary == 1) & (label_binary == 1))
            fp = np.sum((pred_binary == 1) & (label_binary == 0))
            fn = np.sum((pred_binary == 0) & (label_binary == 1))

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

            precisions.append(precision)
            recalls.append(recall)
            f1_scores.append(f1)

        # Find optimal threshold
        best_idx = np.argmax(f1_scores)
        best_threshold = thresholds[best_idx]

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(thresholds, f1_scores, 'b-', linewidth=2, label='F1 Score')
        ax.plot(thresholds, precisions, 'g--', linewidth=2, label='Precision')
        ax.plot(thresholds, recalls, 'r--', linewidth=2, label='Recall')
        ax.axvline(x=best_threshold, color='purple', linestyle=':',
                   linewidth=2, label=f'Optimal Threshold ({best_threshold:.2f})')

        ax.set_xlabel('Threshold', fontsize=12)
        ax.set_ylabel('Score', fontsize=12)
        ax.set_title(f'Threshold Analysis - {model_name}', fontsize=14)
        ax.legend(loc='lower center', fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.set_xlim([0.1, 0.9])
        ax.set_ylim([0, 1])

        if save:
            path = os.path.join(self.output_dir, f"threshold_analysis_{model_name}.png")
            plt.savefig(path, dpi=150, bbox_inches='tight')
            plt.close()
            print(f"Saved: {path}")
            return path

        plt.show()
        return None


def generate_all_plots(predictions: np.ndarray, labels: np.ndarray,
                       model_name: str, confusion_matrix: Dict,
                       output_dir: str = None):
    """Generate all evaluation plots for a model"""
    plotter = EvaluationPlotter(output_dir)

    print(f"\nGenerating plots for {model_name}...")

    plotter.plot_roc_curve(predictions, labels, model_name)
    plotter.plot_precision_recall_curve(predictions, labels, model_name)
    plotter.plot_confusion_matrix(confusion_matrix, model_name)
    plotter.plot_score_distribution(predictions, labels, model_name)
    plotter.plot_threshold_analysis(predictions, labels, model_name)

    print("All plots generated successfully!")


if __name__ == "__main__":
    # Example usage with dummy data
    np.random.seed(42)
    n = 100

    labels = np.random.uniform(0, 1, n)
    predictions = labels + np.random.normal(0, 0.2, n)
    predictions = np.clip(predictions, 0, 1)

    confusion = {"TP": 30, "TN": 40, "FP": 15, "FN": 15}

    generate_all_plots(predictions, labels, "test_model", confusion)
