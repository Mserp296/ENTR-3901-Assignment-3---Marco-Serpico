# README.md

# Movie Recommender System

# 🎬 CineCompass – TMDB Movie Recommender

CineCompass is a hybrid movie recommendation app built with **Python + Streamlit** and powered by the **TMDB API**.  

It lets you:
- Search for a movie and get **“similar vibe” recommendations**
- Filter by year, rating, votes, runtime, certification, language, genres, actor, and director
- Use **natural-language queries** like  
  > "raunchy comedy after 2000 under 115 min rating >= 7"  
- Browse **trending movies** and build a **watchlist**

---

## 🔑 TMDB API Key Setup

This project **requires your own TMDB API key**.

1. Create a free account at [The Movie Database (TMDB)](https://www.themoviedb.org/).
2. Go to **Settings → API** and request an API key (v3 auth).
3. In the project folder, you’ll see a file called:

   ```text
   .env.example

Make a copy of it and rename the copy to:

.env


Open .env and replace the placeholder value with your real key:

TMDB_API_KEY=YOUR_REAL_TMDB_API_KEY_HERE 
this cant be in quotations, just the API key

Never commit your real .env to a public repo.
Only .env.example should be shared.


## Project Structure

movie-recommender/
  app.py               # Main Streamlit app
  tmdb_client.py       # TMDB API client (uses TMDB_API_KEY from .env)
  features.py          # Feature engineering (text "soup")
  recommender.py       # TF-IDF + sentiment hybrid recommender
  nlp_query.py         # Natural-language query → TMDB filter parser
  requirements.txt     # Python dependencies
  .env.example         # Template for TMDB_API_KEY
  (optional) .gitignore

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd movie-recommender
   ```

2. **Create a virtual environment:**

      1. **clone or download the project**

      git clone https://github.com/your-username/movie-recommender.git
      cd movie-recommender

      2. **Create and activate a virtual environment**

      Windows (PowerShell):

      py -m venv .venv
      Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
      .\.venv\Scripts\Activate.ps1


      Windows (CMD):

      py -m venv .venv
      .venv\Scripts\activate.bat


      macOS / Linux:

      python3 -m venv .venv
      source .venv/bin/activate

      3. **Install dependencies**
      pip install -r requirements.txt

      4. **Create your .env file**

      Copy .env.example → .env and put your TMDB API key in it:

      TMDB_API_KEY=YOUR_REAL_TMDB_API_KEY_HERE

## Running the Application

To run the Streamlit application, execute the following command:

```bash
streamlit run src/app.py
```

This will start the application, and you can access it in your web browser at `http://localhost:8501`.

## How the Recommender Works
Content Features

For each movie, the app builds a weighted text “soup” in features.py, combining:

Genres (weighted)

Keywords (weighted more)

Top cast

Director

Overview text

This soup is vectorized using TF-IDF with unigrams + bigrams, then cosine similarity is computed between the seed movie and other movies in a filtered pool.

Sentiment Matching

Plot summaries (overviews) are scored using VADER sentiment (from nltk.sentiment).

Movies are also ranked by how close their sentiment is to the seed movie.

Hybrid Score

In recommender.py, the hybrid score is roughly:

hybrid_score = 0.75 * content_similarity + 0.25 * sentiment_closeness


Movies are sorted by this score, and the seed movie itself is excluded from the results.

Pool Building

The app:

Builds a pool of candidate movies using the TMDB /discover/movie endpoint, applying:

Year range

Rating / vote count thresholds

Runtime range

Certification (US)

Language

Genres (AND / OR)

Actor / director preferences

Automatically tightens the pool using:

The seed movie’s genres (if user didn’t pick genres)

The seed’s top keywords (where helpful)

TMDB’s /movie/{id}/similar endpoint

For R/NC-17 seeds with no cert filter, it automatically filters out G, PG, and PG-13 so you don’t get kids’ movies from raunchy R-rated seeds.

##Natural-Language Query

The “Natural-Language Query” mode lets you type things like:

raunchy comedy after 2000 under 115 min rating >= 7

horror 80s highly rated under 110 minutes

korean thriller after 2015

family friendly animated movie under 100 minutes

nlp_query.py parses your text into TMDB discover parameters:

Genres (with synonyms: romcom, raunchy, stoner, etc.)

Year ranges / decades (80s, 1990s, after 2010, between 2000 and 2010)

Rating thresholds (rating >= 7, highly rated, top rated)

Runtime (under 120 minutes, over 2 hours, short, long)

Certification (rated r, family friendly)

Language (korean, spanish, english, etc.)

Sorting (trending, top rated, newest)

The parsed filters are passed to TMDB /discover/movie.

##