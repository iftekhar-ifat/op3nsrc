import sys
from pathlib import Path
from typing import Any, Dict

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))


class MLUnavailableError(RuntimeError):
    """Raised when the recommender cannot be loaded for the current environment."""


class ModelService:
    def __init__(self) -> None:
        self.recommender: Any = None
        self.load_error: str | None = None

    def load_model(self) -> None:
        """Train the selected classifier and load the recommendation data."""
        try:
            from ml.recommender.classification import build_dataset
            from ml.recommender.data import load_all
            from ml.recommender.models import make_classifiers
            from ml.recommender.recommend import Recommender

            tables = load_all()
            dataset = build_dataset(tables)
            if dataset.empty:
                raise RuntimeError("the cleaned dataset contains no trainable developers")

            classifier = make_classifiers(include_sbert=False)["TF-IDF + Logistic Regression"]
            classifier.fit(dataset["text"], dataset["repo"])
            self.recommender = Recommender(classifier, tables["repositories"], tables["issues"])
            self.load_error = None
            print("ML recommender loaded successfully.")
        except Exception as exc:
            self.recommender = None
            self.load_error = str(exc)
            print(f"ML recommender is unavailable: {exc}")

    def recommend(self, mode: str, query: str) -> Dict[str, Any]:
        """Run a recommendation request through the loaded ML service."""
        if self.recommender is None:
            raise MLUnavailableError(self.load_error or "ML recommender has not been initialized")

        if mode == "github":
            result = self.recommender.recommend_user(query)
        elif mode == "text":
            result = self.recommender.recommend_text(query)
        else:
            raise ValueError(f"Unsupported recommendation mode: {mode}")

        return {"status": "success", "query": query, "mode": mode, **result}


# Singleton instance shared across requests
ml_service = ModelService()