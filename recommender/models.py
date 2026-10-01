"""Standard models.

Classifiers (profile text -> repo), all scikit-learn pipelines:
- Most frequent repo        (DummyClassifier, the baseline)
- TF-IDF + Naive Bayes      (ComplementNB, a classic text classifier)
- TF-IDF + Logistic Regression
- Sentence-BERT + Logistic Regression (pretrained all-MiniLM-L6-v2 embeddings)

TextMatcher: TF-IDF cosine similarity, used to rank issues inside a
recommended repo and to explain matches with shared words.
"""

import os
import warnings

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import ComplementNB
from sklearn.pipeline import make_pipeline

TOKENS = r"(?u)\b[a-zA-Z][a-zA-Z0-9+#.]+\b"     # keeps c++, c#, node.js


def tfidf(**kw):
    return TfidfVectorizer(stop_words="english", sublinear_tf=True, min_df=2, max_df=0.5,
                           token_pattern=TOKENS, **kw)


def _quiet_huggingface():
    """Hide download progress bars and info warnings when loading Sentence-BERT."""
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    os.environ.setdefault("HF_HUB_VERBOSITY", "error")
    os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
    warnings.filterwarnings("ignore", message="IProgress not found")


class SbertEncoder(BaseEstimator, TransformerMixin):
    """Sentence-BERT as a scikit-learn step: texts -> 384-d normalised embeddings."""

    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model_name = model_name

    def fit(self, X, y=None):
        return self                           # pretrained: nothing to learn

    def transform(self, X):
        if not hasattr(self, "_model"):
            _quiet_huggingface()
            from sentence_transformers import SentenceTransformer   # slow import, only when used
            self._model = SentenceTransformer(self.model_name)
        return self._model.encode(list(X), batch_size=64, normalize_embeddings=True,
                                  show_progress_bar=False)


def make_classifiers(include_sbert=True):
    models = {
        "Most frequent repo (baseline)": make_pipeline(tfidf(), DummyClassifier(strategy="most_frequent")),
        "TF-IDF + Naive Bayes": make_pipeline(tfidf(), ComplementNB()),
        "TF-IDF + Logistic Regression": make_pipeline(tfidf(), LogisticRegression(max_iter=2000, C=10)),
    }
    if include_sbert:
        models["Sentence-BERT + Logistic Regression"] = make_pipeline(
            SbertEncoder(), LogisticRegression(max_iter=2000, C=10))
    return models


class TextMatcher:
    """TF-IDF cosine similarity between a profile and documents, plus shared-word explanations."""

    def fit(self, texts):
        self.vectorizer = tfidf().fit(texts)
        self.terms = self.vectorizer.get_feature_names_out()
        return self

    def embed(self, texts):
        return self.vectorizer.transform(list(texts))     # rows are L2-normalised

    @staticmethod
    def similarity(query_vec, doc_matrix):
        return (doc_matrix @ query_vec.T).toarray().ravel()

    def shared_terms(self, a, b, n=5):
        contrib = a.multiply(b).toarray().ravel()
        top = [i for i in np.argsort(-contrib)[:n + 5] if contrib[i] > 0 and len(self.terms[i]) > 2]
        return [self.terms[i] for i in top[:n]]
