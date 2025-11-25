import numpy as np
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

# --- VADER guard for deployment ---
try:
    nltk.data.find("sentiment/vader_lexicon.zip")
except LookupError:
    nltk.download("vader_lexicon")

_sia = SentimentIntensityAnalyzer()


def build_feature_frame(movies):
    df = pd.DataFrame(movies).copy()

    df["overview"] = df["overview"].fillna("")
    df["soup"] = df["soup"].fillna("")
    df["vote_average"] = df["vote_average"].fillna(0.0)
    df["vote_count"] = df["vote_count"].fillna(0).astype(int)
    df["release_date"] = df["release_date"].fillna("")
    df["runtime"] = df["runtime"].fillna(np.nan)
    df["cert"] = df["cert"].fillna("")
    df["language"] = df["language"].fillna("")

    for col in ["genres_list", "keywords_list", "cast_list"]:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: x if isinstance(x, list) else [])

    return df


def fit_tfidf(df):
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1)
    mat = vec.fit_transform(df["soup"])
    return vec, mat


def _sentiment(text):
    return _sia.polarity_scores(text or "")["compound"]


def recommend_hybrid(df, tfidf_matrix, seed_id, top_n=10, w_content=0.75, w_sent=0.25):
    if "sentiment" not in df.columns:
        df["sentiment"] = df["overview"].apply(_sentiment)

    idx_map = pd.Series(df.index, index=df["id"]).drop_duplicates()
    if seed_id not in idx_map:
        return pd.DataFrame()

    seed_idx = idx_map[seed_id]

    sims = cosine_similarity(tfidf_matrix[seed_idx], tfidf_matrix).flatten()
    sims = (sims - sims.min()) / (sims.max() - sims.min() + 1e-9)

    seed_sent = df.loc[seed_idx, "sentiment"]
    sent_close = 1 - np.abs(df["sentiment"] - seed_sent) / 2.0

    hybrid = w_content * sims + w_sent * sent_close.values

    out = df.copy()
    out["hybrid_score"] = hybrid
    out = out[out["id"] != seed_id]
    out = out.sort_values("hybrid_score", ascending=False)

    return out.head(top_n)


def explain_similarity(seed_row, row):
    reasons = []

    seed_genres = set(seed_row.get("genres_list", []))
    row_genres = set(row.get("genres_list", []))
    shared_genres = seed_genres.intersection(row_genres)
    if shared_genres:
        reasons.append("Shared genres: " + ", ".join(list(shared_genres)[:2]))

    seed_kw = set(seed_row.get("keywords_list", []))
    row_kw = set(row.get("keywords_list", []))
    shared_kw = seed_kw.intersection(row_kw)
    if shared_kw:
        reasons.append("Shared keywords: " + ", ".join(list(shared_kw)[:2]))

    seed_cast = set(seed_row.get("cast_list", []))
    row_cast = set(row.get("cast_list", []))
    shared_cast = seed_cast.intersection(row_cast)
    if shared_cast:
        reasons.append("Shared cast: " + ", ".join(list(shared_cast)[:1]))

    if seed_row.get("director") and row.get("director") and seed_row["director"] == row["director"]:
        reasons.append("Same director")

    if not reasons:
        return "Similar plot/style based on hybrid match."
    return " · ".join(reasons[:3])
