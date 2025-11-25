import os
import requests
import streamlit as st
from dotenv import load_dotenv

BASE_URL = "https://api.themoviedb.org/3"

# Load environment variables from .env (in project root)
# This lets each user keep their own TMDB_API_KEY local & private.
load_dotenv()


@st.cache_data(ttl=3600)
def tmdb_get(path, params=None):
    """
    Cached TMDB GET using API key from environment.
    Expects TMDB_API_KEY to be set in a .env file or environment variable.
    """
    params = dict(params) if params else {}

    # 🔥 THIS is the correct line: string key name, not a variable
    api_key = os.getenv("TMDB_API_KEY")
    if not api_key:
        raise ValueError(
            "TMDB_API_KEY is not set.\n"
            "Create a .env file in the project root with:\n"
            "TMDB_API_KEY=your_real_tmdb_key_here"
        )

    params["api_key"] = api_key

    url = f"{BASE_URL}{path}"
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    return r.json()


def search_movie(query, page=1):
    return tmdb_get("/search/movie", {"query": query, "page": page})


def search_person(query, page=1):
    return tmdb_get("/search/person", {"query": query, "page": page})


def movie_details(movie_id):
    return tmdb_get(
        f"/movie/{movie_id}",
        {"append_to_response": "credits,keywords,release_dates"},
    )


def trending_movies():
    return tmdb_get("/trending/movie/week")


def discover_movies(filters, page=1):
    f = dict(filters)
    f["page"] = page
    return tmdb_get("/discover/movie", f)


def similar_movies(movie_id, page=1):
    """TMDB similar endpoint (used to tighten rec pools)."""
    return tmdb_get(f"/movie/{movie_id}/similar", {"page": page})
