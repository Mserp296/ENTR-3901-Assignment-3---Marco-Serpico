import streamlit as st
import streamlit.components.v1 as components

from tmdb_client import (
    search_movie, search_person, movie_details,
    discover_movies, trending_movies, similar_movies
)
from features import build_soup, extract_certification, top_director
from recommender import (
    build_feature_frame, fit_tfidf,
    recommend_hybrid, explain_similarity
)
from nlp_query import parse_nl_query, GENRE_WORDS

st.set_page_config(page_title="CineCompass", layout="wide")

st.markdown(
    """
    <style>
    .stApp {
        background: radial-gradient(1200px circle at 10% -10%, #101827 0%, #070B12 55%, #05070b 100%);
        color: #EEF2FF;
    }

    .badge {
        display: inline-block;
        padding: 0.18rem 0.55rem;
        border-radius: 999px;
        font-size: 0.80rem;
        font-weight: 600;
        margin-right: 0.35rem;
        margin-bottom: 0.35rem;
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.10);
    }

    .card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 14px 14px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.35);
        margin-bottom: 12px;
    }

    .poster-frame {
        width: 100%;
        aspect-ratio: 2 / 3;
        border-radius: 12px;
        background: rgba(255,255,255,0.06);
        border: 1px dashed rgba(255,255,255,0.14);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.95rem;
        color: #aab3c5;
        text-align: center;
        padding: 8px;
        box-sizing: border-box;
    }

    .title-clamp {
        font-weight: 700;
        min-height: 2.8em;
        line-height: 1.4em;
        margin-top: 6px;
    }

    .hero {
        background: linear-gradient(135deg, rgba(142,166,255,0.10), rgba(255,107,160,0.08));
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 22px;
        padding: 22px 22px;
        box-shadow: 0 12px 40px rgba(0,0,0,0.45);
        margin-bottom: 18px;
    }

    .hero-top {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 14px;
        flex-wrap: wrap;
    }

    .logo-pill {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        padding: 8px 12px;
        border-radius: 999px;
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.12);
        font-weight: 800;
        letter-spacing: 0.5px;
    }

    .hero-title {
        font-size: 2.6rem;
        font-weight: 900;
        line-height: 1.05;
        letter-spacing: 0.6px;
        background: linear-gradient(90deg, #c7d2ff, #8ea6ff, #ff7ab6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .hero-sub {
        color: #aab3c5;
        font-size: 1.05rem;
        margin-top: 4px;
    }

    .hero-chips {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-top: 12px;
    }

    .chip {
        display: inline-block;
        padding: 0.30rem 0.70rem;
        border-radius: 999px;
        font-size: 0.85rem;
        font-weight: 700;
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.10);
        color: #d8def0;
    }

    section[data-testid="stSidebar"] {
        background: rgba(7,11,18,0.9);
        border-right: 1px solid rgba(255,255,255,0.06);
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="hero">
      <div class="hero-top">
        <div class="logo-pill">🎬 CineCompass</div>
        <div style="opacity:0.9; font-size:0.9rem; color:#aab3c5;">
          Powered by TMDB Hybrid AI
        </div>
      </div>

      <div style="margin-top:10px;">
        <div class="hero-title">Find your next favorite movie.</div>
        <div class="hero-sub">
          Recommendations that match vibe, genre, cast, and story — not just popularity.
        </div>
      </div>

      <div class="hero-chips">
        <span class="chip">Content Similarity</span>
        <span class="chip">Sentiment Matching</span>
        <span class="chip">Natural-Language Search</span>
        <span class="chip">Watchlist Recs</span>
        <span class="chip">Trending Now</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True
)

# ---------- session state ----------
if "watchlist" not in st.session_state:
    st.session_state.watchlist = []
if "movie_cache" not in st.session_state:
    st.session_state.movie_cache = {}

if "search_results" not in st.session_state:
    st.session_state.search_results = []
if "seed_id" not in st.session_state:
    st.session_state.seed_id = None
if "seed_det" not in st.session_state:
    st.session_state.seed_det = None
if "scroll_to_recs" not in st.session_state:
    st.session_state.scroll_to_recs = False


def cached_details(mid):
    if mid not in st.session_state.movie_cache:
        st.session_state.movie_cache[mid] = movie_details(mid)
    return st.session_state.movie_cache[mid]


def person_id_from_name(name):
    if not name.strip():
        return None
    res = search_person(name)
    people = res.get("results", [])
    if not people:
        return None
    return people[0]["id"]


def hydrate_movie(det):
    credits = det.get("credits", {})
    cast_list = [c["name"] for c in credits.get("cast", [])[:5]]
    director = top_director(credits)
    keywords_list = [k["name"] for k in det.get("keywords", {}).get("keywords", [])]
    genres_list = [g["name"] for g in det.get("genres", [])]

    return {
        "id": det["id"],
        "title": det["title"],
        "overview": det.get("overview","") or "",
        "soup": build_soup(det),
        "vote_average": det.get("vote_average",0),
        "vote_count": det.get("vote_count",0),
        "release_date": det.get("release_date","") or "",
        "runtime": det.get("runtime"),
        "cert": extract_certification(det.get("release_dates",{})),
        "language": det.get("original_language",""),
        "genres_list": genres_list,
        "keywords_list": keywords_list,
        "cast_list": cast_list,
        "director": director,
        "poster_path": det.get("poster_path")
    }


def poster_url(poster_path, size="w500"):
    if not poster_path:
        return None
    return f"https://image.tmdb.org/t/p/{size}{poster_path}"


def render_movie_card(row, seed_row=None, allow_add=True, key_prefix="rec"):
    title = row["title"]
    year = (row["release_date"] or "")[:4]
    rating = row.get("vote_average", 0)
    votes = int(row.get("vote_count", 0))
    runtime = row.get("runtime")
    cert = row.get("cert")
    lang = row.get("language")
    poster = poster_url(row.get("poster_path"))

    badges = []
    if rating: badges.append(f"⭐ {rating:.1f}")
    if votes: badges.append(f"🗳️ {votes:,} votes")
    if runtime: badges.append(f"⏱️ {runtime} min")
    if cert: badges.append(f"🎟️ {cert}")
    if lang: badges.append(f"🌐 {lang.upper()}")

    badges_html = "".join([f"<span class='badge'>{b}</span>" for b in badges])

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    cols = st.columns([1.2, 4.6, 1.2])

    if poster:
        cols[0].image(poster, use_container_width=True)
    else:
        cols[0].markdown("<div class='poster-frame'>🎞️<br>No poster available</div>", unsafe_allow_html=True)

    with cols[1]:
        st.markdown(f"### {title} ({year})")
        st.markdown(badges_html, unsafe_allow_html=True)
        if seed_row is not None:
            st.caption(explain_similarity(seed_row, row))

    if allow_add:
        added = int(row["id"]) in st.session_state.watchlist
        btn_label = "✅ Added" if added else "➕ Watchlist"
        if cols[2].button(btn_label, key=f"{key_prefix}_{row['id']}"):
            if not added:
                st.session_state.watchlist.append(int(row["id"]))

    st.markdown("</div>", unsafe_allow_html=True)


# ---------- sidebar filters ----------
st.sidebar.header("Filters")

with st.sidebar.expander("📆 Release window", expanded=True):
    year_min, year_max = st.slider("Year range", 1950, 2025, (1950, 2025))

with st.sidebar.expander("⭐ Quality", expanded=True):
    min_rating = st.slider("Min rating", 0.0, 10.0, 6.0, 0.1)
    min_votes = st.number_input("Min vote count", 0, 50000, 0)

with st.sidebar.expander("🎬 Content", expanded=True):
    runtime_range = st.slider("Runtime (min)", 60, 240, (70, 200))
    cert = st.selectbox("Certification (US)", ["Any","G","PG","PG-13","R","NC-17"])
    cert_val = None if cert == "Any" else cert
    language = st.text_input("Original language (ISO 639-1)", "")

with st.sidebar.expander("🎭 Genres", expanded=True):
    genre_logic = st.radio("Logic", ["AND", "OR"], horizontal=True)
    genre_names = sorted(GENRE_WORDS.keys())
    selected_genres = st.multiselect("Pick genres", genre_names)
    genres_param = None
    if selected_genres:
        gids = [str(GENRE_WORDS[g]) for g in selected_genres]
        op = "," if genre_logic == "AND" else "|"
        genres_param = op.join(gids)

with st.sidebar.expander("🧑‍🎤 People (optional)", expanded=False):
    actor_name = st.text_input("Preferred actor")
    director_name = st.text_input("Preferred director")
    actor_id = person_id_from_name(actor_name)
    director_id = person_id_from_name(director_name)

tab1, tab2, tab3 = st.tabs(["Search + Recommend", "Natural-Language Query", "Trending"])

# ======================================================
# TAB 1: SEARCH + RECOMMEND
# ======================================================
with tab1:
    st.markdown(
        """
        <div class="card" style="padding:18px 18px; margin-bottom:18px;">
          <div style="display:flex; align-items:center; gap:12px;">
            <div style="font-size:1.6rem;">🔎</div>
            <div>
              <div style="font-size:1.35rem; font-weight:800;">Find your seed movie</div>
              <div style="color:#aab3c5; font-size:0.95rem;">
                Search → pick a poster → get hybrid recommendations
              </div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    with st.form("search_form", clear_on_submit=False):
        q = st.text_input(
            "Search",
            placeholder="Try: Superbad, Harold & Kumar, The Shining…",
            label_visibility="collapsed"
        )
        submitted = st.form_submit_button("Search")

    if submitted and q.strip():
        res = search_movie(q.strip())
        st.session_state.search_results = res.get("results", [])[:12]
        st.session_state.seed_id = None
        st.session_state.seed_det = None

    results = st.session_state.search_results

    if results:
        st.markdown("#### Results (pick one as your seed)")
        cols = st.columns(4)

        for i, m in enumerate(results):
            det = cached_details(m["id"])
            rec = hydrate_movie(det)
            p = poster_url(rec.get("poster_path"), size="w342")

            with cols[i % 4]:
                st.markdown("<div class='card' style='padding:10px;'>", unsafe_allow_html=True)

                if p:
                    st.image(p, use_container_width=True)
                else:
                    st.markdown("<div class='poster-frame'>🎞️<br>No poster available</div>", unsafe_allow_html=True)

                st.markdown(f"<div class='title-clamp'>{rec['title']}</div>", unsafe_allow_html=True)
                st.caption((rec["release_date"] or "")[:4])

                if st.button("Use as seed", key=f"seedpick_{rec['id']}"):
                    st.session_state.seed_id = rec["id"]
                    st.session_state.seed_det = det
                    st.session_state.scroll_to_recs = True
                    st.rerun()

                st.markdown("</div>", unsafe_allow_html=True)

    seed_id = st.session_state.seed_id
    seed_det = st.session_state.seed_det

    if seed_id and seed_det:
        st.markdown("#### Because you picked:")
        render_movie_card(hydrate_movie(seed_det), allow_add=False, key_prefix="seed")
        st.write("")

        seed_cert = extract_certification(seed_det.get("release_dates", {}))
        seed_genre_ids = [str(g["id"]) for g in seed_det.get("genres", [])]
        seed_genre_names = {g["name"] for g in seed_det.get("genres", [])}
        seed_keyword_ids = [str(k["id"]) for k in seed_det.get("keywords", {}).get("keywords", [])[:5]]

        discover_params = {
            "primary_release_date.gte": f"{year_min}-01-01",
            "primary_release_date.lte": f"{year_max}-12-31",
            "vote_average.gte": min_rating,
            "vote_count.gte": min_votes,
            "with_runtime.gte": runtime_range[0],
            "with_runtime.lte": runtime_range[1],
            "sort_by": "popularity.desc"
        }
        if language:
            discover_params["with_original_language"] = language

        pool_genres_param = genres_param
        if not pool_genres_param and seed_genre_ids:
            pool_genres_param = "|".join(seed_genre_ids)
        if pool_genres_param:
            discover_params["with_genres"] = pool_genres_param

        if (not selected_genres) and (not actor_id) and (not director_id) and seed_keyword_ids:
            discover_params["with_keywords"] = "|".join(seed_keyword_ids)

        if cert_val:
            discover_params["certification_country"] = "US"
            discover_params["certification"] = cert_val

        if actor_id:
            discover_params["with_cast"] = actor_id
        if director_id:
            discover_params["with_crew"] = director_id

        with st.spinner("Building recommendation pool…"):
            pool = []
            for page in [1, 2, 3]:
                pool += discover_movies(discover_params, page=page).get("results", [])
            for page in [1, 2]:
                pool += similar_movies(seed_id, page=page).get("results", [])

            seen = set()
            uniq_pool = []
            for m in pool:
                mid = m.get("id")
                if mid and mid not in seen:
                    seen.add(mid)
                    uniq_pool.append(m)

            movies = [hydrate_movie(cached_details(m["id"])) for m in uniq_pool[:160]]

            if not any(x["id"] == seed_id for x in movies):
                movies.append(hydrate_movie(seed_det))

            if (cert_val is None) and (seed_cert in ["R", "NC-17"]):
                kid_certs = {"G", "PG", "PG-13"}
                movies = [mv for mv in movies if (mv.get("cert") not in kid_certs)]

            if (not selected_genres) and seed_genre_names:
                filtered = [
                    mv for mv in movies
                    if seed_genre_names.intersection(set(mv.get("genres_list", [])))
                ]
                if filtered:
                    movies = filtered

            df = build_feature_frame(movies)
            _, mat = fit_tfidf(df)
            recs = recommend_hybrid(df, mat, seed_id, top_n=10)

        if recs.empty:
            st.warning("No recommendations found — widen filters.")
            st.stop()

        st.markdown("<div id='recs'></div>", unsafe_allow_html=True)
        if st.session_state.scroll_to_recs:
            components.html(
                """
                <script>
                const doc = window.parent.document;
                const recs = doc.querySelector('#recs');
                if (recs) { recs.scrollIntoView({behavior: 'smooth', block: 'start'}); }
                </script>
                """,
                height=0,
            )
            st.session_state.scroll_to_recs = False

        st.markdown(f"#### Your Recommendations  ·  Pool size: {len(df)}")
        seed_row = df[df["id"] == seed_id].iloc[0]

        for _, row in recs.iterrows():
            render_movie_card(row, seed_row=seed_row, key_prefix="rec")

        st.caption("Hybrid score = TF-IDF similarity + sentiment closeness.")

# ======================================================
# TAB 2: NL QUERY
# ======================================================
with tab2:
    st.write("Example: *raunchy comedy after 2000 under 115 min rating >= 7*")
    nlq = st.text_input("Describe what you want:", placeholder="horror 80s rating over 7 under 110 min")

    if nlq:
        nl_filters = parse_nl_query(nlq)
        nl_filters.setdefault("vote_average.gte", min_rating)
        nl_filters.setdefault("vote_count.gte", min_votes)

        matches = discover_movies(nl_filters, page=1).get("results", [])

        if not matches:
            st.warning("No matches — try different wording.")
        else:
            st.markdown("#### Matches")
            for m in matches[:12]:
                det = cached_details(m["id"])
                render_movie_card(hydrate_movie(det), allow_add=True, key_prefix="nl")

# ======================================================
# TAB 3: TRENDING
# ======================================================
with tab3:
    t = trending_movies().get("results", [])
    st.markdown("#### Trending this week")
    for m in t[:12]:
        det = cached_details(m["id"])
        render_movie_card(hydrate_movie(det), allow_add=True, key_prefix="trend")
