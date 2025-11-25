def extract_certification(release_dates):
    """Return US certification if present."""
    for entry in release_dates.get("results", []):
        if entry.get("iso_3166_1") == "US":
            for rel in entry.get("release_dates", []):
                cert = rel.get("certification")
                if cert:
                    return cert
    return None


def top_director(credits):
    """Return director name from credits."""
    for crew in credits.get("crew", []):
        if crew.get("job") == "Director":
            return crew.get("name", "")
    return ""


def build_soup(det):
    """
    Build a weighted text soup for TF-IDF.
    High-signal fields repeated so recommendations feel on-theme.
    """
    credits = det.get("credits", {})
    cast = [c["name"].replace(" ", "").lower()
            for c in credits.get("cast", [])[:5]]

    director_raw = top_director(credits)
    director = director_raw.replace(" ", "").lower() if director_raw else ""

    keywords = [k["name"].replace(" ", "").lower()
                for k in det.get("keywords", {}).get("keywords", [])]

    genres = [g["name"].replace(" ", "").lower()
              for g in det.get("genres", [])]

    overview = (det.get("overview") or "").lower()

    weighted_tokens = (
        genres * 4 +        # genres matter a lot
        keywords * 6 +      # keywords matter even more
        cast * 2 +          # cast some influence
        [director] * 2 +    # director some influence
        overview.split()    # plot words once
    )

    return " ".join([w for w in weighted_tokens if w])
