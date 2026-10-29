"""Standard models.

Classifiers (profile text -> repo), all scikit-learn pipelines:
- Most frequent repo        (DummyClassifier, the baseline)
- TF-IDF + Naive Bayes      (ComplementNB, a classic text classifier)
- TF-IDF + Logistic Regression
  TF-IDF features = words + word pairs, plus character 3-5-grams (catch code
  names like `strftime`, `useState`)
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
from sklearn.pipeline import make_pipeline, make_union

TOKENS = r"(?u)\b[a-zA-Z][a-zA-Z0-9+#.]+\b"     # keeps c++, c#, node.js


def tfidf(**kw):
    return TfidfVectorizer(stop_words="english", sublinear_tf=True, min_df=2, max_df=0.5,
                           token_pattern=TOKENS, **kw)


def text_features():
    """Classifier features: word unigrams + bigrams, and character 3-5-grams."""
    return make_union(
        tfidf(ngram_range=(1, 2)),
        TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True, min_df=2, max_df=0.5),
    )


# Settings chosen by cross-validation (notebooks/classification.ipynb, §3)
NB_ALPHA = 0.1
LR_C = 100

# Small grids searched in the classification notebook
PARAM_GRIDS = {
    "TF-IDF + Naive Bayes": {"complementnb__alpha": [0.03, 0.1, 0.3, 1.0]},
    "TF-IDF + Logistic Regression": {"logisticregression__C": [10, 30, 100]},
}


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
        "TF-IDF + Naive Bayes": make_pipeline(text_features(), ComplementNB(alpha=NB_ALPHA)),
        "TF-IDF + Logistic Regression": make_pipeline(text_features(), LogisticRegression(max_iter=3000, C=LR_C)),
    }
    if include_sbert:
        models["Sentence-BERT + Logistic Regression"] = make_pipeline(
            SbertEncoder(), LogisticRegression(max_iter=2000, C=10))
    return models


def make_low_memory_classifier():
    """A word-TF-IDF classifier sized for small hosted instances.

    It uses the same labels and logistic-regression recommendation flow as the
    full model, while omitting the larger character n-gram feature space.
    """
    vectorizer = TfidfVectorizer(
        stop_words="english",
        sublinear_tf=True,
        min_df=2,
        max_df=0.5,
        max_features=20_000,
        ngram_range=(1, 2),
        token_pattern=TOKENS,
        dtype=np.float32,
    )
    # LogisticRegression's multiclass optimizer can allocate several dense
    # work buffers even for sparse input. ComplementNB stays sparse end to end
    # and is a better fit for Render's 512 MiB free instance.
    return make_pipeline(vectorizer, ComplementNB(alpha=NB_ALPHA))


class TextMatcher:
    """TF-IDF cosine similarity between a profile and documents, plus shared-word explanations."""

    def __init__(self, max_features=None, dtype=np.float64):
        self.max_features = max_features
        self.dtype = dtype

    def fit(self, texts):
        self.vectorizer = tfidf(max_features=self.max_features, dtype=self.dtype).fit(texts)
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
