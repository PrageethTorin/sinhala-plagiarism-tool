"""
Enhanced Fine-Tuning Script for Sinhala Semantic Similarity Models
Supports multiple models and HuggingFace datasets

Models to compare:
1. paraphrase-multilingual-MiniLM-L12-v2 (Current)
2. xlm-roberta-base
3. LaBSE
4. distiluse-base-multilingual-cased-v2

Features:
- HuggingFace dataset integration
- Multiple model training
- Evaluation during training
- Model comparison
"""

import os
import sys
import csv
import json
import torch
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Check dependencies
try:
    from sentence_transformers import SentenceTransformer, InputExample, losses, evaluation
    from sentence_transformers.evaluation import EmbeddingSimilarityEvaluator
    from torch.utils.data import DataLoader
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False
    logger.warning("Install sentence-transformers: pip install sentence-transformers")

try:
    from datasets import load_dataset
    HAS_DATASETS = True
except ImportError:
    HAS_DATASETS = False
    logger.warning("Install datasets: pip install datasets")

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAINING_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")


@dataclass
class ModelConfig:
    """Configuration for a model to train"""
    name: str
    base_model: str
    epochs: int = 3
    batch_size: int = 16
    learning_rate: float = 2e-5
    warmup_steps: int = 100
    use_amp: bool = True  # Automatic Mixed Precision


# Models to compare
MODELS_TO_TRAIN = [
    ModelConfig(
        name="sinhala_minilm_v2",
        base_model="paraphrase-multilingual-MiniLM-L12-v2",
        epochs=3,
        batch_size=16,
        learning_rate=2e-5
    ),
    ModelConfig(
        name="sinhala_xlmr",
        base_model="xlm-roberta-base",
        epochs=3,
        batch_size=8,  # Smaller batch for larger model
        learning_rate=1e-5
    ),
    ModelConfig(
        name="sinhala_labse",
        base_model="sentence-transformers/LaBSE",
        epochs=3,
        batch_size=16,
        learning_rate=2e-5
    ),
    ModelConfig(
        name="sinhala_distiluse",
        base_model="sentence-transformers/distiluse-base-multilingual-cased-v2",
        epochs=3,
        batch_size=16,
        learning_rate=2e-5
    )
]


class TrainingDataLoader:
    """Load training data from various sources"""

    def __init__(self):
        self.train_samples = []
        self.val_samples = []

    def load_from_csv(self, csv_path: str) -> List[InputExample]:
        """Load training examples from CSV file"""
        samples = []

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Handle different column names
                s1 = row.get("sentence_1") or row.get("sentence1") or row.get("text1", "")
                s2 = row.get("sentence_2") or row.get("sentence2") or row.get("text2", "")
                label = float(row.get("label") or row.get("score") or row.get("similarity", 0.5))

                if s1 and s2:
                    samples.append(InputExample(texts=[s1, s2], label=label))

        logger.info(f"Loaded {len(samples)} samples from {csv_path}")
        return samples

    def load_from_huggingface(self, dataset_name: str, max_samples: int = 5000) -> List[InputExample]:
        """Load training examples from HuggingFace dataset"""
        if not HAS_DATASETS:
            logger.error("datasets library not installed")
            return []

        samples = []

        try:
            if dataset_name == "tapaco":
                # Load TaPaCo Sinhala subset
                dataset = load_dataset("community-datasets/tapaco", "si", trust_remote_code=True)

                # Group by paraphrase set
                paraphrase_groups = {}
                for split in dataset.keys():
                    for item in dataset[split]:
                        set_id = item.get("paraphrase_set_id")
                        sentence = item.get("paraphrase", "")
                        if set_id and sentence:
                            if set_id not in paraphrase_groups:
                                paraphrase_groups[set_id] = []
                            paraphrase_groups[set_id].append(sentence)

                # Create pairs
                for sentences in paraphrase_groups.values():
                    if len(sentences) >= 2:
                        for i in range(min(len(sentences) - 1, 2)):
                            samples.append(InputExample(
                                texts=[sentences[i], sentences[i + 1]],
                                label=0.85
                            ))
                            if len(samples) >= max_samples:
                                break
                    if len(samples) >= max_samples:
                        break

            elif dataset_name == "sinhala_short_sentences":
                dataset = load_dataset("NLPC-UOM/Sinhala-short-sentences", trust_remote_code=True)
                for split in dataset.keys():
                    for item in dataset[split]:
                        if "sentence1" in item and "sentence2" in item:
                            samples.append(InputExample(
                                texts=[item["sentence1"], item["sentence2"]],
                                label=float(item.get("similarity", 0.5))
                            ))
                            if len(samples) >= max_samples:
                                break

            logger.info(f"Loaded {len(samples)} samples from HuggingFace: {dataset_name}")

        except Exception as e:
            logger.error(f"Error loading HuggingFace dataset {dataset_name}: {e}")

        return samples

    def prepare_data(self, csv_paths: List[str] = None,
                     hf_datasets: List[str] = None,
                     val_ratio: float = 0.1) -> Tuple[List[InputExample], List[InputExample]]:
        """
        Prepare training and validation data from multiple sources
        """
        all_samples = []

        # Load from CSV files
        if csv_paths:
            for path in csv_paths:
                if os.path.exists(path):
                    all_samples.extend(self.load_from_csv(path))

        # Load from HuggingFace
        if hf_datasets:
            for ds_name in hf_datasets:
                all_samples.extend(self.load_from_huggingface(ds_name))

        # Shuffle and split
        import random
        random.shuffle(all_samples)

        val_size = int(len(all_samples) * val_ratio)
        self.val_samples = all_samples[:val_size]
        self.train_samples = all_samples[val_size:]

        logger.info(f"Training samples: {len(self.train_samples)}")
        logger.info(f"Validation samples: {len(self.val_samples)}")

        return self.train_samples, self.val_samples


class SinhalaModelTrainer:
    """Train and evaluate Sinhala semantic similarity models"""

    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir or MODELS_DIR
        os.makedirs(self.output_dir, exist_ok=True)

        self.training_history = []

    def train_model(self, config: ModelConfig,
                    train_samples: List[InputExample],
                    val_samples: List[InputExample]) -> str:
        """
        Train a single model with given configuration
        """
        if not HAS_SENTENCE_TRANSFORMERS:
            logger.error("sentence-transformers not installed")
            return None

        logger.info(f"\n{'='*60}")
        logger.info(f"Training: {config.name}")
        logger.info(f"Base model: {config.base_model}")
        logger.info(f"{'='*60}")

        # Load base model
        try:
            model = SentenceTransformer(config.base_model)
        except Exception as e:
            logger.error(f"Error loading model {config.base_model}: {e}")
            return None

        # Create data loader
        train_dataloader = DataLoader(
            train_samples,
            shuffle=True,
            batch_size=config.batch_size
        )

        # Loss function
        train_loss = losses.CosineSimilarityLoss(model)

        # Evaluator
        evaluator = None
        if val_samples:
            sentences1 = [s.texts[0] for s in val_samples]
            sentences2 = [s.texts[1] for s in val_samples]
            scores = [s.label for s in val_samples]

            evaluator = EmbeddingSimilarityEvaluator(
                sentences1, sentences2, scores,
                name=f"{config.name}_val"
            )

        # Output path
        model_output_path = os.path.join(self.output_dir, config.name)

        # Training
        start_time = datetime.now()

        try:
            model.fit(
                train_objectives=[(train_dataloader, train_loss)],
                evaluator=evaluator,
                epochs=config.epochs,
                warmup_steps=config.warmup_steps,
                output_path=model_output_path,
                evaluation_steps=500,
                save_best_model=True,
                use_amp=config.use_amp
            )

            training_time = (datetime.now() - start_time).total_seconds()

            # Evaluate final model
            final_score = 0.0
            if evaluator:
                final_score = evaluator(model)

            # Log results
            result = {
                "model_name": config.name,
                "base_model": config.base_model,
                "epochs": config.epochs,
                "batch_size": config.batch_size,
                "train_samples": len(train_samples),
                "val_samples": len(val_samples),
                "final_eval_score": final_score,
                "training_time_seconds": training_time,
                "output_path": model_output_path
            }

            self.training_history.append(result)

            logger.info(f"\nTraining complete!")
            logger.info(f"Final evaluation score: {final_score:.4f}")
            logger.info(f"Training time: {training_time:.1f}s")
            logger.info(f"Model saved to: {model_output_path}")

            return model_output_path

        except Exception as e:
            logger.error(f"Error training {config.name}: {e}")
            return None

    def train_all_models(self, train_samples: List[InputExample],
                          val_samples: List[InputExample],
                          models: List[ModelConfig] = None) -> List[Dict]:
        """
        Train all configured models
        """
        models = models or MODELS_TO_TRAIN

        logger.info("\n" + "=" * 60)
        logger.info("TRAINING ALL MODELS")
        logger.info(f"Models to train: {len(models)}")
        logger.info("=" * 60)

        for i, config in enumerate(models, 1):
            logger.info(f"\n[{i}/{len(models)}] Training {config.name}...")
            self.train_model(config, train_samples, val_samples)

        return self.training_history

    def save_training_report(self) -> str:
        """Save training results to JSON"""
        report_path = os.path.join(
            self.output_dir,
            f"training_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "models_trained": len(self.training_history),
                "results": self.training_history
            }, f, indent=2)

        logger.info(f"Training report saved to: {report_path}")
        return report_path

    def compare_models(self) -> str:
        """Generate model comparison table"""
        if not self.training_history:
            return "No training results available"

        # Sort by evaluation score
        sorted_results = sorted(
            self.training_history,
            key=lambda x: x.get("final_eval_score", 0),
            reverse=True
        )

        table = "\n=== MODEL COMPARISON ===\n\n"
        table += f"{'Model':<25} {'Base Model':<40} {'Eval Score':<12} {'Time(s)':<10}\n"
        table += "-" * 90 + "\n"

        for result in sorted_results:
            table += f"{result['model_name']:<25} "
            table += f"{result['base_model']:<40} "
            table += f"{result.get('final_eval_score', 0):.4f}       "
            table += f"{result.get('training_time_seconds', 0):.1f}\n"

        return table


def train_with_huggingface_data():
    """
    Main function to train models using HuggingFace datasets
    """
    logger.info("=" * 60)
    logger.info("SINHALA SEMANTIC SIMILARITY - MODEL TRAINING")
    logger.info("Using HuggingFace Datasets")
    logger.info("=" * 60)

    # Prepare data
    data_loader = TrainingDataLoader()

    # Try to load from HuggingFace first
    train_samples, val_samples = data_loader.prepare_data(
        hf_datasets=["tapaco"],  # Start with TaPaCo
        csv_paths=[
            os.path.join(TRAINING_DIR, "sinhala_similarity_train_large.csv"),
            os.path.join(TRAINING_DIR, "huggingface_training_data_*.csv")
        ],
        val_ratio=0.1
    )

    if not train_samples:
        logger.error("No training data available!")
        return

    # Train models (start with just MiniLM for speed)
    trainer = SinhalaModelTrainer()

    # Train single model first
    single_model_config = ModelConfig(
        name="sinhala_minilm_hf",
        base_model="paraphrase-multilingual-MiniLM-L12-v2",
        epochs=3,
        batch_size=16
    )

    trainer.train_model(single_model_config, train_samples, val_samples)

    # Save report
    trainer.save_training_report()

    # Print comparison
    print(trainer.compare_models())

    logger.info("\nTraining complete!")


def train_all_models_comparison():
    """
    Train all models for comparison (takes longer)
    """
    logger.info("=" * 60)
    logger.info("TRAINING ALL MODELS FOR COMPARISON")
    logger.info("=" * 60)

    # Prepare data
    data_loader = TrainingDataLoader()
    train_samples, val_samples = data_loader.prepare_data(
        hf_datasets=["tapaco"],
        csv_paths=[
            os.path.join(TRAINING_DIR, "sinhala_similarity_train_large.csv")
        ],
        val_ratio=0.1
    )

    if not train_samples:
        logger.error("No training data!")
        return

    # Train all models
    trainer = SinhalaModelTrainer()
    trainer.train_all_models(train_samples, val_samples)

    # Save results
    trainer.save_training_report()
    print(trainer.compare_models())


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Train Sinhala semantic similarity models")
    parser.add_argument("--all", action="store_true", help="Train all models for comparison")
    parser.add_argument("--model", type=str, help="Train specific model")

    args = parser.parse_args()

    if args.all:
        train_all_models_comparison()
    else:
        train_with_huggingface_data()
