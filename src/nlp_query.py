import re
from datetime import datetime

GENRE_WORDS = {
    "action": 28,
    "adventure": 12,
    "animation": 16,
    "comedy": 35,
    "crime": 80,
    "documentary": 99,
    "drama": 18,
    "family": 10751,
    "fantasy": 14,
    "history": 36,
    "horror": 27,
    "music": 10402,
    "mystery": 9648,
    "romance": 10749,
    "science fiction": 878,
    "thriller": 53,
    "war": 10752,
    "western": 37,
    "tv movie": 10770,
}

GENRE_SYNONYMS = {
    "sci fi": "science fiction",
    "scifi": "science fiction",
    "science-fiction": "science fiction",
    "romcom": ["romance", "comedy"],
    "rom-com": ["romance", "comedy"],
    "slasher": "horror",
    "monster": "horror",
    "superhero": "action",
    "comic book": "action",
    "spy": "action",
    "detective": "mystery",
    "whodunit": "mystery",
    "noir": "crime",
    "biopic": "history",
    "period piece": "history",
    "stoner": "comedy",
    "raunchy": "comedy",
    "buddy": "comedy",
    "coming of age": "drama",
    "tearjerker": "drama",
    "anime": "animation",
    "kids": "family",
    "family friendly": "family",
    "feel good": "comedy",
}

LANG_SYNONYMS = {
    "english": "en",
    "spanish": "es",
    "french": "fr",
    "german": "de",
    "italian": "it",
    "japanese": "ja",
    "korean": "ko",
    "hindi": "hi",
    "chinese": "zh",
    "mandarin": "zh",
    "cantonese": "zh",
    "portuguese": "pt",
    "russian": "ru",
    "arabic": "ar",
}

CERT_SYNONYMS = {
    "g": "G",
    "pg": "PG",
    "pg-13": "PG-13",
    "pg13": "PG-13",
    "rated pg-13": "PG-13",
    "r": "R",
    "rated r": "R",
    "nc-17": "NC-17",
    "nc17": "NC-17",
    "family friendly": "PG",
    "kids": "PG",
}

NOW_YEAR = datetime.now().year


def _find_genres(text: str):
    found = set()

    for g in GENRE_WORDS:
        if re.search(rf"\b{re.escape(g)}\b", text):
            found.add(g)

    for syn, target in GENRE_SYNONYMS.items():
        if re.search(rf"\b{re.escape(syn)}\b", text):
            if isinstance(target, list):
                for t in target:
                    found.add(t)
            else:
                found.add(target)

    return list(found)


def _year_filters(text: str, filters: dict):
    m = re.search(r"between\s+(\d{4})\s+and\s+(\d{4})", text)
    if m:
        y1, y2 = int(m.group(1)), int(m.group(2))
        filters["primary_release_date.gte"] = f"{min(y1,y2)}-01-01"
        filters["primary_release_date.lte"] = f"{max(y1,y2)}-12-31"
        return

    m = re.search(r"(after|since)\s+(\d{4})", text)
    if m:
        y = int(m.group(2))
        filters["primary_release_date.gte"] = f"{y}-01-01"

    m = re.search(r"(before|until)\s+(\d{4})", text)
    if m:
        y = int(m.group(2))
        filters["primary_release_date.lte"] = f"{y}-12-31"

    m = re.search(r"\b(\d{2})0s\b", text)
    if m:
        decade = int(m.group(1)) * 10
        y1 = 1900 + decade if decade >= 50 else 2000 + decade
        filters["primary_release_date.gte"] = f"{y1}-01-01"
        filters["primary_release_date.lte"] = f"{y1+9}-12-31"

    m = re.search(r"\b(19\d{2}|20\d{2})s\b", text)
    if m:
        y1 = int(m.group(1))
        filters["primary_release_date.gte"] = f"{y1}-01-01"
        filters["primary_release_date.lte"] = f"{y1+9}-12-31"

    m = re.search(r"last\s+(\d+)\s+years", text)
    if m:
        n = int(m.group(1))
        filters["primary_release_date.gte"] = f"{NOW_YEAR - n}-01-01"

    if "recent" in text or "new" in text or "latest" in text:
        filters.setdefault("primary_release_date.gte", f"{NOW_YEAR-5}-01-01")


def _rating_filters(text: str, filters: dict):
    m = re.search(r"(rating|score)\s*(>=|=>|>|at least|over)\s*(\d+(\.\d+)?)", text)
    if m:
        filters["vote_average.gte"] = float(m.group(3))
        return

    m = re.search(r"(rating|score)\s*(<=|=<|<|under|below)\s*(\d+(\.\d+)?)", text)
    if m:
        filters["vote_average.lte"] = float(m.group(3))
        return

    m = re.search(r"at least\s*(\d+(\.\d+)?)\s*(stars|rating|score)?", text)
    if m:
        filters["vote_average.gte"] = float(m.group(1))

    if "highly rated" in text or "best rated" in text or "top rated" in text:
        filters.setdefault("vote_average.gte", 7.5)


def _vote_filters(text: str, filters: dict):
    m = re.search(r"(at least|over|>=)\s*(\d{3,})\s*(votes|vote count)", text)
    if m:
        filters["vote_count.gte"] = int(m.group(2))
        return

    if "popular" in text:
        filters.setdefault("vote_count.gte", 1000)
        filters.setdefault("sort_by", "popularity.desc")


def _runtime_filters(text: str, filters: dict):
    m = re.search(r"(under|below|<=|less than)\s*(\d{2,3})\s*(min|mins|minutes)", text)
    if m:
        filters["with_runtime.lte"] = int(m.group(2))

    m = re.search(r"(over|above|>=|more than)\s*(\d{2,3})\s*(min|mins|minutes)", text)
    if m:
        filters["with_runtime.gte"] = int(m.group(2))

    m = re.search(r"under\s*(\d+(\.\d+)?)\s*hours", text)
    if m:
        filters["with_runtime.lte"] = int(float(m.group(1)) * 60)

    m = re.search(r"over\s*(\d+(\.\d+)?)\s*hours", text)
    if m:
        filters["with_runtime.gte"] = int(float(m.group(1)) * 60)

    if "short" in text:
        filters.setdefault("with_runtime.lte", 100)
    if "long" in text or "epic" in text:
        filters.setdefault("with_runtime.gte", 140)


def _cert_filters(text: str, filters: dict):
    for syn, cert in CERT_SYNONYMS.items():
        if syn in text:
            filters["certification_country"] = "US"
            filters["certification"] = cert
            return


def _language_filters(text: str, filters: dict):
    m = re.search(r"\blanguage\s*[:=]?\s*([a-z]{2})\b", text)
    if m:
        filters["with_original_language"] = m.group(1).lower()
        return

    for name, code in LANG_SYNONYMS.items():
        if re.search(rf"\b{re.escape(name)}\b", text):
            filters["with_original_language"] = code
            return


def parse_nl_query(query: str) -> dict:
    text = (query or "").lower().strip()
    filters = {}

    genres = _find_genres(text)
    if genres:
        gids = [str(GENRE_WORDS[g]) for g in genres if g in GENRE_WORDS]
        if gids:
            if " and " in text:
                filters["with_genres"] = ",".join(gids)
            else:
                filters["with_genres"] = "|".join(gids)

    _year_filters(text, filters)
    _rating_filters(text, filters)
    _vote_filters(text, filters)
    _runtime_filters(text, filters)
    _cert_filters(text, filters)
    _language_filters(text, filters)

    if "trending" in text:
        filters["sort_by"] = "popularity.desc"
    if "newest" in text:
        filters["sort_by"] = "primary_release_date.desc"
    if "oldest" in text:
        filters["sort_by"] = "primary_release_date.asc"
    if "top rated" in text or "best" in text:
        filters["sort_by"] = "vote_average.desc"

    return filters
