import os
import re
import json
import time
import logging
import urllib.parse
import subprocess
import requests
import math
from django.db.models import Q
from api.models import Movie
from api.serializers import MovieSerializer

logger = logging.getLogger(__name__)

TMDB_GENRES = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy", 80: "Crime",
    99: "Documentary", 18: "Drama", 10751: "Family", 14: "Fantasy", 36: "History",
    27: "Horror", 10402: "Music", 9648: "Mystery", 10749: "Romance", 878: "Sci-Fi",
    10770: "TV Movie", 53: "Thriller", 10752: "War", 37: "Western"
}

_SIMILAR_CACHE = {}
_DETAILS_CACHE = {}
_SEARCH_CACHE = {}
_TMDB_CACHE = {}

def normalize_movie_title(raw_title):
    """Normalizes titles by stripping release years, flipping 'Title, The' -> 'The Title', and removing brackets."""
    if not raw_title:
        return ""
    t = re.sub(r"\(\d{4}\)", "", raw_title).strip()
    t = re.sub(r"[\(\)\[\]]", " ", t).strip()
    t = re.sub(r"\s+", " ", t)
    m = re.match(r"^(.*?),\s*(the|a|an)$", t, re.I)
    if m:
        t = f"{m.group(2)} {m.group(1)}"
    return t.lower().strip()

def fetch_tmdb_data(endpoint):
    """Robust TMDB API fetcher with requests + curl.exe fallback with IPv4 & retry, cached in memory."""
    if endpoint in _TMDB_CACHE:
        return _TMDB_CACHE[endpoint]

    key = os.getenv("TMDB_API_KEY", "3a1ff8b883fd4c71a563201decf380b1")
    url = f"https://api.themoviedb.org/3/{endpoint}"
    sep = "&" if "?" in endpoint else "?"
    full_url = f"{url}{sep}api_key={key}&language=en-US"

    # Method 1: Requests
    try:
        resp = requests.get(full_url, timeout=2.0)
        if resp.status_code == 200:
            data = resp.json()
            _TMDB_CACHE[endpoint] = data
            return data
    except Exception:
        pass

    # Method 2: System curl fallback with IPv4 & retry (bypasses Windows SSL handshake reset)
    for attempt in range(3):
        try:
            res = subprocess.run(
                ["curl.exe", "-s", "-4", "--retry", "2", full_url],
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                timeout=5
            )
            if res.returncode == 0 and res.stdout:
                data = json.loads(res.stdout)
                if isinstance(data, dict):
                    _TMDB_CACHE[endpoint] = data
                    return data
        except Exception:
            pass
        time.sleep(0.12)

    return None

def fetch_movie_credits_and_details(tmdb_id):
    """Fetches overview, director, top cast, runtime, and ratings for the selected title."""
    if not tmdb_id:
        return {}

    if tmdb_id in _DETAILS_CACHE:
        return _DETAILS_CACHE[tmdb_id]

    details = fetch_tmdb_data(f"movie/{tmdb_id}?append_to_response=credits") or {}
    credits_data = details.get("credits", {})

    director = ""
    for member in credits_data.get("crew", []):
        if member.get("job") == "Director":
            director = member.get("name", "")
            break

    cast_names = [actor.get("name", "") for actor in credits_data.get("cast", [])[:5] if actor.get("name")]
    cast_str = ", ".join(cast_names)

    runtime_min = details.get("runtime") or 0
    if runtime_min > 0:
        hrs = runtime_min // 60
        mins = runtime_min % 60
        runtime_str = f"{hrs}h {mins}m" if hrs else f"{mins}m"
    else:
        runtime_str = ""

    poster_path = details.get("poster_path")
    poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else ""
    backdrop_path = details.get("backdrop_path")
    backdrop_url = f"https://image.tmdb.org/t/p/original{backdrop_path}" if backdrop_path else ""

    result = {
        "title": details.get("title") or details.get("original_title") or "",
        "poster_url": poster_url,
        "backdrop_url": backdrop_url,
        "overview": details.get("overview") or "",
        "tagline": details.get("tagline") or "",
        "director": director,
        "cast": cast_str,
        "runtime": runtime_str,
        "vote_average": details.get("vote_average"),
        "vote_count": details.get("vote_count"),
        "release_date": details.get("release_date", ""),
        "imdb_id": details.get("imdb_id") or ""
    }

    _DETAILS_CACHE[tmdb_id] = result
    return result

def search_movies_hybrid(query, limit=15):
    """
    Intelligent hybrid search combining:
    1. TMDB Global Search (for latest movies like Oppenheimer, correct popularity, and high-res posters)
    2. Local MovieLens database matching (handling '(500) Days of Summer' and 'Heat, The')
    3. Multi-tier relevance ranking favoring exact title match & high popularity over obscure titles.
    4. Typo & spelling tolerance (e.g. 'dhurva' -> 'Dhruva').
    """
    clean_q = query.strip()
    if not clean_q or len(clean_q) < 2:
        return []

    cache_key = f"{clean_q.lower()}_{limit}"
    if cache_key in _SEARCH_CACHE:
        return _SEARCH_CACHE[cache_key]

    q_norm = normalize_movie_title(clean_q)
    q_stripped = re.sub(r"^(the|a|an)\s+", "", q_norm).strip()
    candidates = {}

    # 1. TMDB Global Search (Pulls blockbusters like Oppenheimer 2023, correct spelling)
    q_encoded = urllib.parse.quote_plus(clean_q)
    tmdb_search = fetch_tmdb_data(f"search/movie?query={q_encoded}")

    # Typo / Transposition Tolerance (e.g. "dhurva" -> "dhruva")
    if not tmdb_search or not tmdb_search.get("results"):
        chars = list(clean_q)
        for i in range(len(chars) - 1):
            transposed = chars.copy()
            transposed[i], transposed[i+1] = transposed[i+1], transposed[i]
            cand_q = "".join(transposed)
            t_res = fetch_tmdb_data(f"search/movie?query={urllib.parse.quote_plus(cand_q)}")
            if t_res and t_res.get("results"):
                tmdb_search = t_res
                break

    if tmdb_search:
        for item in tmdb_search.get("results", [])[:30]:
            t_id = item.get("id")
            title = item.get("title", "")
            year = (item.get("release_date") or "")[:4]
            full_title = f"{title} ({year})" if year else title
            poster_path = item.get("poster_path")
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
            pop = float(item.get("popularity", 0.0))
            vote_avg = float(item.get("vote_average", 0.0) or 0.0)
            vote_cnt = int(item.get("vote_count", 0) or 0)

            # Check if this TMDB movie already exists in DB
            existing = Movie.objects.filter(Q(tmdb_id=t_id) | Q(title__iexact=full_title) | Q(title__iexact=title)).first()
            if existing:
                if poster_url and existing.poster_url != poster_url:
                    existing.poster_url = poster_url
                    existing.save(update_fields=["poster_url"])
                candidates[f"local_{existing.movie_id}"] = {
                    "movie_id": existing.movie_id,
                    "title": existing.title,
                    "genres": existing.genres,
                    "tmdb_id": existing.tmdb_id,
                    "poster_url": existing.poster_url,
                    "popularity": pop,
                    "vote_average": vote_avg,
                    "vote_count": vote_cnt
                }
            else:
                # Dynamically register movie in catalog
                new_id = 900000 + (t_id % 90000)
                while Movie.objects.filter(movie_id=new_id).exists():
                    new_id += 1

                genre_ids = item.get("genre_ids", [])
                genres_str = "|".join([TMDB_GENRES[gid] for gid in genre_ids if gid in TMDB_GENRES]) or "Drama"

                new_movie = Movie.objects.create(
                    movie_id=new_id,
                    title=full_title,
                    genres=genres_str,
                    tmdb_id=t_id,
                    poster_url=poster_url
                )
                candidates[f"local_{new_movie.movie_id}"] = {
                    "movie_id": new_movie.movie_id,
                    "title": new_movie.title,
                    "genres": new_movie.genres,
                    "tmdb_id": new_movie.tmdb_id,
                    "poster_url": new_movie.poster_url,
                    "popularity": pop,
                    "vote_average": vote_avg,
                    "vote_count": vote_cnt
                }

    # 2. Local Database Multi-Strategy Search
    # A. Exact or prefix matches
    prefix_q = Q(title__icontains=clean_q)
    if q_stripped and q_stripped != clean_q:
        prefix_q |= Q(title__icontains=q_stripped)
        prefix_q |= Q(title__icontains=f"{q_stripped}, The")

    # B. Word-token intersection (handles '(500) Days of Summer' and punctuation)
    words = [w for w in re.sub(r"[^\w\s]", " ", clean_q).split() if len(w) > 1 and w.lower() not in ("the", "a", "an", "of", "and", "in")]
    if words:
        word_q = Q()
        for w in words:
            word_q &= Q(title__icontains=w)
        prefix_q |= word_q

    local_matches = list(Movie.objects.filter(prefix_q)[:40])
    for m in local_matches:
        cid = f"local_{m.movie_id}"
        if cid not in candidates:
            candidates[cid] = {
                "movie_id": m.movie_id,
                "title": m.title,
                "genres": m.genres,
                "tmdb_id": m.tmdb_id,
                "poster_url": m.poster_url,
                "popularity": 10.0,
                "vote_average": 6.0,
                "vote_count": 100
            }

    # 3. High-Precision Acclaim & Relevance Scoring
    scored = []
    for item in candidates.values():
        t_norm = normalize_movie_title(item["title"])
        t_stripped = re.sub(r"^(the|a|an)\s+", "", t_norm).strip()

        score = 0.0
        # Exact title match (with or without 'The', 'A', 'An')
        if q_norm == t_norm:
            score += 320.0
        elif q_stripped and (q_stripped == t_stripped or t_norm == q_stripped or t_stripped == q_norm):
            score += 300.0
            if ("the " in q_norm) == ("the " in t_norm):
                score += 10.0
        elif t_norm.startswith(q_norm) or (q_stripped and t_stripped.startswith(q_stripped)):
            score += 160.0
        elif q_stripped and re.search(r"\b" + re.escape(q_stripped) + r"\b", t_stripped):
            score += 120.0
        elif q_stripped and q_stripped in t_stripped:
            score += 60.0
        else:
            score += 20.0

        # Prioritize movies with high-res posters
        if item.get("poster_url"):
            score += 40.0

        # Critical Acclaim & Critical Mass Weighting (Prefers highest-rated and critically acclaimed versions)
        vote_avg = float(item.get("vote_average", 0.0) or 0.0)
        vote_cnt = float(item.get("vote_count", 0) or 0)
        pop = float(item.get("popularity", 0.0) or 0.0)

        if vote_avg >= 6.5:
            score += (vote_avg - 6.0) * 22.0

        if vote_cnt > 0:
            score += min(math.log10(max(vote_cnt, 1.0)) * 16.0, 75.0)

        # Global popularity weighting
        score += min(pop * 1.5, 95.0)

        # Release year tie-breaker: modern acclaimed versions over vintage obscure ones for identical title matches
        year_match = re.search(r"\((\d{4})\)", item.get("title", ""))
        if year_match:
            yr = int(year_match.group(1))
            if yr >= 2000:
                score += min((yr - 2000) * 1.5, 35.0)

        scored.append((score, item))

    # Sort descending by calculated relevance score
    scored.sort(key=lambda x: x[0], reverse=True)
    res = [s[1] for s in scored[:limit]]
    _SEARCH_CACHE[cache_key] = res
    return res

def get_similar_movies_for_target(target_movie, limit=8):
    """
    Produces unique, highly-accurate recommendations for the selected target movie.
    Uses TMDB collaborative and similar clusters with fallback to genre/keyword overlap.
    """
    cache_key = f"{target_movie.movie_id}_{limit}"
    if cache_key in _SIMILAR_CACHE:
        return _SIMILAR_CACHE[cache_key]

    results = []
    seen_tmdb_ids = {target_movie.tmdb_id} if target_movie.tmdb_id else set()
    seen_movie_ids = {target_movie.movie_id}

    # 1. Primary: TMDB Recommendations & Similar Clusters
    if target_movie.tmdb_id:
        t_details = fetch_tmdb_data(f"movie/{target_movie.tmdb_id}") or {}
        orig_lang = t_details.get("original_language", "en")

        data = fetch_tmdb_data(f"movie/{target_movie.tmdb_id}/recommendations")
        raw_items = data.get("results", []) if data else []

        if len(raw_items) < limit:
            sim_data = fetch_tmdb_data(f"movie/{target_movie.tmdb_id}/similar")
            if sim_data:
                raw_items.extend(sim_data.get("results", []))

        # Language-Aware Regional Clustering (e.g. Telugu 'te', Hindi 'hi', Tamil 'ta', Korean 'ko')
        # Recommend authentic cinema from the same language/culture rather than defaulting to unrelated Hollywood titles
        if orig_lang and orig_lang != "en":
            genre_list = [g.get("id") for g in t_details.get("genres", []) if g.get("id")]
            genre_param = f"&with_genres={','.join(map(str, genre_list[:2]))}" if genre_list else ""
            regional_data = fetch_tmdb_data(f"discover/movie?with_original_language={orig_lang}{genre_param}&sort_by=vote_count.desc")
            if regional_data and regional_data.get("results"):
                reg_films = [f for f in regional_data["results"] if f.get("id") != target_movie.tmdb_id]
                raw_items = reg_films[:limit] + raw_items

        for item in raw_items:
            t_id = item.get("id")
            if not t_id or t_id in seen_tmdb_ids:
                continue
            seen_tmdb_ids.add(t_id)

            title = item.get("title", "")
            poster_path = item.get("poster_path")
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
            vote_avg = item.get("vote_average", 8.0)
            genre_ids = item.get("genre_ids", [])
            genres_str = "|".join([TMDB_GENRES[gid] for gid in genre_ids if gid in TMDB_GENRES])

            db_movie = Movie.objects.filter(Q(tmdb_id=t_id) | Q(title__iexact=title)).first()
            if db_movie:
                if poster_url and db_movie.poster_url != poster_url:
                    db_movie.poster_url = poster_url
                    db_movie.save(update_fields=["poster_url"])
                movie_dict = MovieSerializer(db_movie).data
                seen_movie_ids.add(db_movie.movie_id)
            else:
                movie_dict = {
                    "movie_id": t_id,
                    "title": title,
                    "genres": genres_str or "Drama",
                    "tmdb_id": t_id,
                    "poster_url": poster_url
                }

            results.append({
                "rank": len(results) + 1,
                "score": round(vote_avg, 1),
                "movie": movie_dict
            })

            if len(results) >= limit:
                break

    # 2. Local Catalog Genre & Semantic Fallback
    if len(results) < limit:
        target_genres = [g.strip() for g in (target_movie.genres or "").split("|") if g.strip()]
        needed = limit - len(results)

        candidates = Movie.objects.filter(
            poster_url__isnull=False
        ).exclude(movie_id__in=seen_movie_ids)

        if target_genres:
            genre_query = Q()
            for g in target_genres[:2]:
                genre_query |= Q(genres__icontains=g)
            filtered = list(candidates.filter(genre_query)[:60])
        else:
            filtered = list(candidates[:60])

        scored_candidates = []
        target_words = set(target_movie.title.lower().split()) - {"the", "a", "an", "of", "and", "in", "to"}
        for cand in filtered:
            cand_genres = set(cand.genres.split("|")) if cand.genres else set()
            genre_overlap = len(set(target_genres) & cand_genres)
            cand_words = set(cand.title.lower().split())
            word_overlap = len(target_words & cand_words)
            score = (genre_overlap * 2.5) + (word_overlap * 1.5)
            scored_candidates.append((score, cand))

        scored_candidates.sort(key=lambda x: x[0], reverse=True)

        for _, cand in scored_candidates[:needed]:
            results.append({
                "rank": len(results) + 1,
                "score": round(8.5 - (len(results) * 0.1), 1),
                "movie": MovieSerializer(cand).data
            })
            seen_movie_ids.add(cand.movie_id)

    _SIMILAR_CACHE[cache_key] = results
    return results
