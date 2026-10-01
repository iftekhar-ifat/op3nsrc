"""Op3nSrc recommender.

data            load the cleaned tables, build repo/issue texts
classification  dataset (developer text -> repo), train/test split, metrics
models          standard classifiers + TF-IDF text matcher
github_profile  GitHub user data -> profile text
recommend       Recommender: user -> top 5 repos (classifier) -> top 3 issues each
"""
