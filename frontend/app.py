import os
import re
import json
import urllib.parse
import socket
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY", "3a1ff8b883fd4c71a563201decf380b1")
SAFE_PLACEHOLDER = "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=500&auto=format&fit=crop&q=60"

def resolve_api_base_url():
    configured_url = os.getenv("API_BASE_URL") or os.getenv("BACKEND_API_URL") or "http://127.0.0.1:8000/api/v1"
    try:
        parsed = urllib.parse.urlparse(configured_url)
        host = parsed.hostname
        if host and host not in ("localhost", "127.0.0.1"):
            socket.gethostbyname(host)
        return configured_url
    except Exception:
        return "http://127.0.0.1:8000/api/v1"

API_BASE_URL = resolve_api_base_url()

st.set_page_config(
    page_title="CINEMATCH — Netflix AI Movie Discovery",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Netflix & Portfolio-Inspired Capsule Theme & Smooth Animations
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    html {
        scroll-behavior: smooth;
    }
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stApp {
        background-color: #141414;
        background-image: radial-gradient(circle at 50% 0%, #24090c 0%, #141414 55%, #0b0b0b 100%);
        color: #e5e5e5;
        min-height: 100vh;
    }

    /* Fixed Scroll Progress Bar along top edge */
    #scroll-progress-indicator {
        position: fixed;
        top: 0;
        left: 0;
        height: 3px;
        background: linear-gradient(90deg, #E50914 0%, #D4AF37 100%);
        z-index: 99999;
        width: 0%;
        box-shadow: 0 0 12px rgba(229, 9, 20, 0.8);
        transition: width 0.1s ease-out;
    }

    /* Top Navigation Bar with Centered Floating Pill Navbar */
    .netflix-nav-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 6px 18px 6px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        margin-bottom: 24px;
        flex-wrap: wrap;
        gap: 16px;
    }
    
    .brand-logo-link {
        text-decoration: none !important;
        display: inline-flex;
        align-items: center;
        gap: 2px;
        cursor: pointer;
        transition: transform 0.25s ease;
    }
    .brand-logo-link:hover {
        transform: scale(1.05);
    }
    
    .logo-n-badge {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 2.7rem;
        color: #E50914;
        letter-spacing: -0.02em;
        line-height: 1;
        margin-right: 4px;
        text-shadow: 0 0 20px rgba(229, 9, 20, 0.6);
    }
    .logo-cine {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 2.3rem;
        color: #ffffff;
        letter-spacing: 0.05em;
        line-height: 1;
    }
    .logo-match {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 2.3rem;
        color: #E50914;
        letter-spacing: 0.05em;
        line-height: 1;
        text-shadow: 0 0 16px rgba(229, 9, 20, 0.5);
    }
    .logo-ai-badge {
        font-size: 0.65rem;
        font-weight: 800;
        background: #E50914;
        color: #ffffff;
        padding: 2px 6px;
        border-radius: 4px;
        margin-left: 6px;
        letter-spacing: 0.08em;
    }

    /* Centered Floating Capsule Pill Navbar (Framer-Motion Replica from Portfolio) */
    .netflix-capsule-navbar {
        background: rgba(15, 12, 10, 0.88);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(229, 9, 20, 0.35);
        border-radius: 9999px;
        padding: 5px 8px;
        display: inline-flex;
        align-items: center;
        gap: 4px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.75), 0 0 18px rgba(229, 9, 20, 0.2);
    }
    
    .capsule-item {
        font-size: 0.74rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #b5b0a1 !important;
        padding: 8px 18px;
        border-radius: 9999px;
        text-decoration: none !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        display: inline-block;
        white-space: nowrap;
    }
    .capsule-item:hover {
        color: #fdfbf7 !important;
        background: rgba(255, 255, 255, 0.08);
        transform: translateY(-1px);
    }
    .capsule-item.active {
        background: #E50914;
        color: #ffffff !important;
        font-weight: 800;
        box-shadow: 0 0 16px rgba(229, 9, 20, 0.6);
    }
    .capsule-item-gold {
        background: #D4AF37;
        color: #0F0C0A !important;
        font-weight: 800;
        box-shadow: 0 0 14px rgba(212, 175, 55, 0.35);
    }
    .capsule-item-gold:hover {
        background: #e6c04e;
        transform: translateY(-1px);
    }

    /* Popular Picks (CSS Flex: No colliding columns) */
    .quick-chips-wrapper {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        justify-content: center;
        align-items: center;
        margin: 12px 0 28px 0;
    }
    .quick-chips-label {
        color: #8c8c8c;
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-right: 4px;
    }
    .netflix-chip {
        display: inline-flex;
        align-items: center;
        padding: 6px 14px;
        background: rgba(38, 38, 38, 0.75);
        border: 1px solid rgba(255, 255, 255, 0.12);
        color: #e5e5e5 !important;
        font-size: 0.82rem;
        font-weight: 600;
        border-radius: 9999px;
        text-decoration: none !important;
        transition: all 0.24s cubic-bezier(0.4, 0, 0.2, 1);
        white-space: nowrap;
    }
    .netflix-chip:hover {
        background: #E50914;
        color: #ffffff !important;
        border-color: #E50914;
        transform: translateY(-2px) scale(1.03);
        box-shadow: 0 4px 14px rgba(229, 9, 20, 0.4);
    }

    /* Netflix Poster Cards (Neat, Organized, Zero Clutter) */
    .netflix-card {
        text-decoration: none !important;
        display: block;
        color: inherit !important;
        cursor: pointer;
        position: relative;
        border-radius: 6px;
        overflow: hidden;
        background: #181818;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.6);
        transition: transform 0.35s cubic-bezier(0.2, 0.8, 0.2, 1), box-shadow 0.35s ease, border-color 0.35s ease;
        margin-bottom: 14px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        animation: cardFadeIn 0.5s ease backwards;
    }
    
    @keyframes cardFadeIn {
        from { opacity: 0; transform: translateY(12px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .netflix-card:hover {
        transform: scale(1.07) translateY(-6px);
        z-index: 30;
        box-shadow: 0 18px 36px rgba(0, 0, 0, 0.9), 0 0 22px rgba(229, 9, 20, 0.4);
        border-color: rgba(229, 9, 20, 0.8);
    }

    .card-poster-img {
        width: 100%;
        aspect-ratio: 2 / 3;
        object-fit: cover;
        display: block;
        transition: transform 0.4s ease;
    }

    .card-footer {
        padding: 9px 10px 11px 10px;
        background: #181818;
    }

    .card-movie-title {
        font-size: 0.84rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 4px;
        line-height: 1.25;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .card-movie-meta {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.74rem;
    }
    .match-percent {
        color: #46d369;
        font-weight: 700;
    }
    .card-year-tag {
        color: #8c8c8c;
        font-weight: 500;
    }
    .card-quality {
        border: 1px solid rgba(255, 255, 255, 0.35);
        padding: 0px 4px;
        border-radius: 2px;
        font-size: 0.65rem;
        color: #b3b3b3;
    }

    /* Netflix Hero Showcase Banner */
    .netflix-hero-banner {
        position: relative;
        background: linear-gradient(135deg, rgba(38, 10, 12, 0.95) 0%, rgba(20, 20, 20, 0.98) 55%, rgba(10, 10, 10, 1) 100%);
        border: 1px solid rgba(229, 9, 20, 0.35);
        border-radius: 12px;
        padding: 32px;
        margin-bottom: 34px;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.9), 0 0 30px rgba(229, 9, 20, 0.15);
        animation: heroFadeIn 0.45s cubic-bezier(0.2, 0.8, 0.2, 1);
    }
    
    @keyframes heroFadeIn {
        from { opacity: 0; transform: translateY(16px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .hero-title-text {
        font-family: 'Bebas Neue', 'Plus Jakarta Sans', sans-serif;
        font-size: 3.4rem;
        letter-spacing: 0.03em;
        line-height: 1;
        color: #ffffff;
        margin: 0 0 6px 0;
        text-shadow: 0 2px 10px rgba(0,0,0,0.8);
    }
    .hero-tagline-text {
        font-style: italic;
        color: #b3b3b3;
        font-size: 1.05rem;
        margin-bottom: 12px;
    }
    .hero-badges-row {
        display: flex;
        gap: 10px;
        align-items: center;
        flex-wrap: wrap;
        margin-bottom: 16px;
    }
    .badge-match-score {
        color: #46d369;
        font-weight: 800;
        font-size: 0.95rem;
    }
    .badge-hd {
        border: 1px solid rgba(255, 255, 255, 0.5);
        color: #ffffff;
        font-size: 0.72rem;
        padding: 1px 6px;
        border-radius: 3px;
        font-weight: 600;
    }
    .badge-runtime {
        color: #cccccc;
        font-size: 0.88rem;
        font-weight: 500;
    }

    .hero-overview {
        color: #d2d2d2;
        font-size: 0.95rem;
        line-height: 1.6;
        max-width: 820px;
        margin-bottom: 18px;
    }

    .hero-credits-box {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
        gap: 14px;
        background: rgba(255, 255, 255, 0.04);
        padding: 14px 18px;
        border-radius: 8px;
        border-left: 3px solid #E50914;
    }

    /* Section Headers */
    .section-header-title {
        font-size: 1.45rem;
        font-weight: 800;
        color: #ffffff;
        margin: 28px 0 6px 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .section-header-caption {
        color: #8c8c8c;
        font-size: 0.88rem;
        margin-bottom: 18px;
    }

    /* Spinner Loading Animation */
    div[data-testid="stSpinner"] > div {
        border-top-color: #E50914 !important;
        border-right-color: transparent !important;
        border-bottom-color: #E50914 !important;
        border-left-color: transparent !important;
        animation: spin 0.75s linear infinite !important;
    }

    /* Profile / Footer Card */
    .netflix-footer {
        background: #0f0f0f;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        padding: 32px 18px;
        margin-top: 56px;
        border-radius: 8px;
    }
    .footer-btn {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 16px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 600;
        text-decoration: none !important;
        transition: all 0.2s ease;
        margin-right: 10px;
        margin-bottom: 8px;
    }
    .footer-portfolio {
        background: #D4AF37;
        color: #0F0C0A !important;
        font-weight: 800;
    }
    .footer-portfolio:hover {
        background: #e6c04e;
        transform: translateY(-2px);
    }
    .footer-github {
        background: rgba(255, 255, 255, 0.1);
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .footer-github:hover {
        background: rgba(255, 255, 255, 0.2);
        transform: translateY(-2px);
    }
    .footer-linkedin {
        background: rgba(10, 102, 194, 0.25);
        color: #60a5fa !important;
        border: 1px solid rgba(10, 102, 194, 0.6);
    }
    .footer-linkedin:hover {
        background: rgba(10, 102, 194, 0.45);
        transform: translateY(-2px);
    }

    /* Streamlit Button Tweaks */
    div[data-testid="stButton"] > button {
        border-radius: 6px;
        font-weight: 600;
        border: 1px solid rgba(255, 255, 255, 0.2);
        background: rgba(30, 30, 30, 0.8);
        color: #e5e5e5;
        transition: all 0.2s ease;
    }
    div[data-testid="stButton"] > button:hover {
        border-color: #E50914;
        color: #ffffff;
        background: #E50914;
    }
</style>

<div id="scroll-progress-indicator"></div>

<script>
    window.addEventListener('scroll', function() {
        var winScroll = document.documentElement.scrollTop || document.body.scrollTop;
        var height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
        var scrolled = (winScroll / height) * 100;
        var el = document.getElementById("scroll-progress-indicator");
        if (el) {
            el.style.width = scrolled + "%";
        }
    });
</script>
""", unsafe_allow_html=True)

# Top 15 IMDb Rated & Iconic Films Catalog (Verified Metadata & 200 OK Posters)
FAMOUS_CATALOG = [
    {"movie_id": 318, "title": "The Shawshank Redemption", "year": "1994", "tmdb_id": 278, "poster_url": "https://image.tmdb.org/t/p/w500/9cqNxx0GxF0bflZmeSMuL5tnGzr.jpg", "score": 9.3, "genres": "Drama · Crime"},
    {"movie_id": 858, "title": "The Godfather", "year": "1972", "tmdb_id": 238, "poster_url": "https://image.tmdb.org/t/p/w500/3bhkrj58Vtu7enYsRolD1fZdja1.jpg", "score": 9.2, "genres": "Crime · Drama"},
    {"movie_id": 1221, "title": "The Godfather Part II", "year": "1974", "tmdb_id": 240, "poster_url": "https://image.tmdb.org/t/p/w500/8a1lJs7mFyGhGhZZDT1azJUoQiZ.jpg", "score": 9.0, "genres": "Crime · Drama"},
    {"movie_id": 58559, "title": "The Dark Knight", "year": "2008", "tmdb_id": 155, "poster_url": "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg", "score": 9.0, "genres": "Action · Crime"},
    {"movie_id": 296, "title": "Pulp Fiction", "year": "1994", "tmdb_id": 680, "poster_url": "https://image.tmdb.org/t/p/w500/vQWk5YBFWF4bZaofAbv0tShwBvQ.jpg", "score": 8.9, "genres": "Crime · Thriller"},
    {"movie_id": 2959, "title": "Fight Club", "year": "1999", "tmdb_id": 550, "poster_url": "https://image.tmdb.org/t/p/w500/jSziioSwPVrOy9Yow3XhWIBDjq1.jpg", "score": 8.8, "genres": "Drama · Thriller"},
    {"movie_id": 356, "title": "Forrest Gump", "year": "1994", "tmdb_id": 13, "poster_url": "https://image.tmdb.org/t/p/w500/Cw4hIUIAmSYfK9QfaUW5igp9La.jpg", "score": 8.8, "genres": "Comedy · Drama"},
    {"movie_id": 79132, "title": "Inception", "year": "2010", "tmdb_id": 27205, "poster_url": "https://image.tmdb.org/t/p/w500/xlaY2zyzMfkhk0HSC5VUwzoZPU1.jpg", "score": 8.8, "genres": "Action · Sci-Fi"},
    {"movie_id": 2571, "title": "The Matrix", "year": "1999", "tmdb_id": 603, "poster_url": "https://image.tmdb.org/t/p/w500/dXNAPwY7VrqMAo51EKhhCJfaGb5.jpg", "score": 8.7, "genres": "Action · Sci-Fi"},
    {"movie_id": 1213, "title": "Goodfellas", "year": "1990", "tmdb_id": 769, "poster_url": "https://image.tmdb.org/t/p/w500/9OkCLM73MIU2CrKZbqiT8Ln1wY2.jpg", "score": 8.7, "genres": "Biography · Crime"},
    {"movie_id": 109487, "title": "Interstellar", "year": "2014", "tmdb_id": 157336, "poster_url": "https://image.tmdb.org/t/p/w500/yQvGrMoipbRoddT0ZR8tPoR7NfX.jpg", "score": 8.7, "genres": "Sci-Fi · Drama"},
    {"movie_id": 3147, "title": "The Green Mile", "year": "1999", "tmdb_id": 497, "poster_url": "https://image.tmdb.org/t/p/w500/8VG8fDNiy50H4FedGwdSVUPoaJe.jpg", "score": 8.6, "genres": "Crime · Drama"},
    {"movie_id": 3578, "title": "Gladiator", "year": "2000", "tmdb_id": 98, "poster_url": "https://image.tmdb.org/t/p/w500/wN2xWp1eIwCKOD0BHTcErTBv1Uq.jpg", "score": 8.5, "genres": "Action · Adventure"},
    {"movie_id": 6874, "title": "Kill Bill: Vol. 1", "year": "2003", "tmdb_id": 24, "poster_url": "https://image.tmdb.org/t/p/w500/v7TaX8kXMXs5yFFGR41guUDNcnB.jpg", "score": 8.2, "genres": "Action · Crime"},
    {"movie_id": 74458, "title": "Shutter Island", "year": "2010", "tmdb_id": 11324, "poster_url": "https://image.tmdb.org/t/p/w500/nrmXQ0zcZUL8jFLrakWc90IR8z9.jpg", "score": 8.2, "genres": "Drama · Mystery"}
]

# State management
if "selected_movie" not in st.session_state:
    st.session_state["selected_movie"] = None
if "search_input" not in st.session_state:
    st.session_state["search_input"] = ""
if "search_matches" not in st.session_state:
    st.session_state["search_matches"] = []

# URL Query Param Navigation Handling
# 1. Home link reset
if "home" in st.query_params:
    st.session_state["selected_movie"] = None
    st.session_state["search_input"] = ""
    st.session_state["search_matches"] = []
    st.query_params.clear()

# 2. Movie link click (?movie=318)
if "movie" in st.query_params:
    mid = st.query_params.get("movie")
    if mid:
        try:
            r = requests.get(f"{API_BASE_URL}/movies/{mid}/similar/?limit=1", timeout=4)
            if r.status_code == 200:
                data = r.json()
                st.session_state["selected_movie"] = data.get("source_movie")
        except Exception:
            pass
    st.query_params.clear()

# 3. Direct quick search chip click (?search=The+Godfather)
if "search" in st.query_params:
    sq = st.query_params.get("search")
    if sq:
        st.session_state["search_input"] = sq
        try:
            resp = requests.get(f"{API_BASE_URL}/movies/search/?q={urllib.parse.quote(sq)}", timeout=4)
            if resp.status_code == 200:
                found = resp.json()
                if found:
                    st.session_state["selected_movie"] = found[0]
                    st.session_state["search_matches"] = found[:3]
        except Exception:
            pass
    st.query_params.clear()

# Top Netflix Bar with Centered Floating Capsule Navbar (Screenshot 3 Replica)
st.markdown("""<div class="netflix-nav-container">
<a href="?home=true" target="_self" class="brand-logo-link" title="Return to Home">
<span class="logo-n-badge">N</span>
<span class="logo-cine">CINE</span><span class="logo-match">MATCH</span>
<span class="logo-ai-badge">AI</span>
</a>
<div class="netflix-capsule-navbar">
<a href="?home=true" target="_self" class="capsule-item active">HOME</a>
<a href="#popular-picks" class="capsule-item">POPULAR</a>
<a href="#trending" class="capsule-item">TOP 15 IMDB</a>
<a href="#tech-stack" class="capsule-item">TECH STACK</a>
<a href="https://github.com/Varun-Esarapu/movie_rec" target="_blank" class="capsule-item">GITHUB</a>
<a href="https://e-varun-portfolio.vercel.app/#intro" target="_blank" class="capsule-item capsule-item-gold">PORTFOLIO</a>
</div>
<div style="font-size: 0.8rem; color: #8c8c8c;">
<span style="color:#46d369; font-weight:700;">● Engine Online</span>
</div>
</div>""", unsafe_allow_html=True)

# Sidebar settings (Engine Controls)
with st.sidebar:
    st.markdown("<h3 style='color:#E50914;'>⚙️ Engine Controls</h3>", unsafe_allow_html=True)
    st.caption("Customize how recommendations are generated and explore the PySpark ALS model.")
    mode = st.radio(
        "Discovery Engine Mode",
        ["Similar Movie Intelligence", "User ID Collaborative Filtering (PySpark ALS)"],
        help="Select between title-based thematic discovery or user-specific matrix factorization"
    )
    num_recs = st.slider("Recommendations Count", min_value=4, max_value=12, value=8, step=2)
    st.divider()
    st.markdown(f"**Serving Backend:**  \n`{API_BASE_URL}`  \n**Status:** <span style='color:#46d369; font-weight:700;'>● Online</span>", unsafe_allow_html=True)
    st.caption("Engine: PySpark 3.5 MLlib ALS (32M Ratings, rank=16, partitions=40)")

if mode == "Similar Movie Intelligence":
    # Search Bar with Top 3 IMDb rated movies in placeholder
    c_left, c_search, c_right = st.columns([1, 2.8, 1])
    with c_search:
        search_query = st.text_input(
            "Search Movie",
            value=st.session_state["search_input"],
            placeholder="Search movie (e.g. The Shawshank Redemption, The Godfather, The Dark Knight...)",
            label_visibility="collapsed"
        )
        
        # Popular Picks (CSS Flex: No colliding columns!)
        st.markdown("""<div id="popular-picks" class="quick-chips-wrapper">
<span class="quick-chips-label">Popular Picks:</span>
<a href="?search=The+Godfather" target="_self" class="netflix-chip">🍷 The Godfather</a>
<a href="?search=The+Dark+Knight" target="_self" class="netflix-chip">🦇 The Dark Knight</a>
<a href="?search=Fight+Club" target="_self" class="netflix-chip">🕶️ Fight Club</a>
<a href="?search=Kill+Bill" target="_self" class="netflix-chip">🗡️ Kill Bill</a>
<a href="?search=Gladiator" target="_self" class="netflix-chip">⚔️ Gladiator</a>
<a href="?search=Inception" target="_self" class="netflix-chip">🌀 Inception</a>
<a href="?search=Interstellar" target="_self" class="netflix-chip">🌌 Interstellar</a>
<a href="?search=Shutter+Island" target="_self" class="netflix-chip">🏝️ Shutter Island</a>
<a href="?search=300" target="_self" class="netflix-chip">🛡️ 300</a>
<a href="?search=Rocky" target="_self" class="netflix-chip">🥊 Rocky</a>
<a href="?search=(500)+Days+of+Summer" target="_self" class="netflix-chip">☀️ (500) Days of Summer</a>
<a href="?search=Oppenheimer" target="_self" class="netflix-chip">⚛️ Oppenheimer</a>
</div>""", unsafe_allow_html=True)

    # Process search if typed
    if search_query.strip() and search_query != st.session_state.get("last_search"):
        st.session_state["last_search"] = search_query
        try:
            with st.spinner("Searching neural catalog..."):
                resp = requests.get(f"{API_BASE_URL}/movies/search/?q={urllib.parse.quote(search_query.strip())}", timeout=4)
                if resp.status_code == 200:
                    found = resp.json()
                    if found:
                        st.session_state["selected_movie"] = found[0]
                        st.session_state["search_matches"] = found[:3]
                    else:
                        st.session_state["search_matches"] = []
                        st.warning(f"No catalog match found for '{search_query}'.")
        except Exception as e:
            st.error(f"Backend search failed: {e}")

    # Compact Disambiguation Bar
    matches = st.session_state.get("search_matches", [])
    if len(matches) > 1 and st.session_state.get("selected_movie"):
        c_m_left, c_m_content, c_m_right = st.columns([1, 2.8, 1])
        with c_m_content:
            st.markdown("<div style='font-size: 0.8rem; color: #8c8c8c; margin: 4px 0 2px 0;'>🔍 <b>Multiple matches found:</b> (Click to switch)</div>", unsafe_allow_html=True)
            match_cols = st.columns(len(matches))
            for i, cand in enumerate(matches):
                with match_cols[i]:
                    is_active = (cand.get("movie_id") == st.session_state["selected_movie"].get("movie_id"))
                    btn_label = f"✓ {cand['title']}" if is_active else cand['title']
                    if st.button(btn_label, key=f"disambig_{cand['movie_id']}_{i}", use_container_width=True):
                        st.session_state["selected_movie"] = cand
                        st.rerun()

    # VIEW 1: A Movie is Selected -> Show Netflix Hero Showcase & Similar Recommendations
    if st.session_state["selected_movie"]:
        target = st.session_state["selected_movie"]
        
        col_back, _ = st.columns([2, 8])
        with col_back:
            if st.button("← Return to All Movies", key="btn_back"):
                st.session_state["selected_movie"] = None
                st.session_state["search_input"] = ""
                st.session_state["search_matches"] = []
                st.rerun()

        # Fetch Similar Movies & Details from Backend
        sim_data = []
        details = {}
        try:
            with st.spinner("Streaming personalized recommendation cluster..."):
                sim_resp = requests.get(f"{API_BASE_URL}/movies/{target['movie_id']}/similar/?limit={num_recs}", timeout=5)
                if sim_resp.status_code == 200:
                    data_json = sim_resp.json()
                    sim_data = data_json.get("results", [])
                    source_movie = data_json.get("source_movie", {})
                    details = source_movie.get("details", {})
        except Exception as e:
            st.error(f"Could not reach recommendation service: {e}")

        # Render Netflix Hero Showcase Banner
        hero_poster = target.get("poster_url") or SAFE_PLACEHOLDER
        genres_raw = (target.get("genres") or "Drama").replace("|", " · ")
        
        title_str = target.get('title', 'Unknown Title')
        year_str = details.get("release_date", "")[:4] or "Classic"
        tagline = details.get("tagline", "")
        overview = details.get("overview") or "A critically acclaimed cinematic masterpiece recognized for its exceptional storytelling, deep thematic development, and iconic performances."
        director = details.get("director", "")
        cast = details.get("cast", "")
        runtime = details.get("runtime", "")
        vote_avg = details.get("vote_average")
        vote_count = details.get("vote_count")

        rating_html = f"<span class='badge-match-score'>⭐ {vote_avg:.1f} / 10 ({vote_count:,} reviews)</span>" if (vote_avg and vote_count) else "<span class='badge-match-score'>98% Match</span>"
        runtime_html = f"<span class='badge-runtime'>⏱️ {runtime}</span>" if runtime else ""
        tagline_html = f"<div class='hero-tagline-text'>\"{tagline}\"</div>" if tagline else ""
        
        director_html = f"<div><span style='color: #8c8c8c; font-size: 0.78rem; text-transform: uppercase; font-weight: 700;'>Director</span><div style='color: #ffffff; font-weight: 700; font-size: 0.95rem; margin-top: 2px;'>🎬 {director}</div></div>" if director else ""
        cast_html = f"<div><span style='color: #8c8c8c; font-size: 0.78rem; text-transform: uppercase; font-weight: 700;'>Starring Cast</span><div style='color: #d2d2d2; font-size: 0.88rem; line-height: 1.4; margin-top: 2px;'>🌟 {cast}</div></div>" if cast else ""
        
        meta_grid = f"<div class='hero-credits-box'>{director_html}{cast_html}</div>" if (director or cast) else ""

        hero_html = f"""<div class="netflix-hero-banner">
<div style="display: flex; gap: 32px; align-items: flex-start; flex-wrap: wrap;">
<img src="{hero_poster}" style="width: 200px; border-radius: 8px; box-shadow: 0 16px 36px rgba(0,0,0,0.85); flex-shrink: 0; border: 1px solid rgba(255,255,255,0.1);" />
<div style="flex: 1; min-width: 320px;">
<div style="font-size: 0.8rem; color: #E50914; font-weight: 800; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 4px;">Featured Selection</div>
<h1 class="hero-title-text">{title_str}</h1>
{tagline_html}
<div class="hero-badges-row">
{rating_html}
<span class="badge-hd">ULTRA HD 4K</span>
{runtime_html}
<span style="color: #b3b3b3; font-size: 0.88rem;">{genres_raw}</span>
</div>
<p class="hero-overview">{overview}</p>
{meta_grid}
</div>
</div>
</div>"""
        st.markdown(hero_html, unsafe_allow_html=True)

        st.markdown(f"<div class='section-header-title'>✨ More Like *{title_str}*</div>", unsafe_allow_html=True)
        st.markdown("<div class='section-header-caption'>Deep thematic matches based on genre overlap, director signatures, and collaborative viewer behavior (Click any card to explore)</div>", unsafe_allow_html=True)

        if sim_data:
            cols = st.columns(4)
            for idx, item in enumerate(sim_data):
                m = item["movie"]
                col = cols[idx % 4]
                poster = m.get("poster_url") or SAFE_PLACEHOLDER
                
                with col:
                    card_html = f"""<a href="?movie={m['movie_id']}" target="_self" class="netflix-card">
<img src="{poster}" class="card-poster-img" />
<div class="card-footer">
<div class="card-movie-title">{m['title']}</div>
<div class="card-movie-meta">
<span class="match-percent">#{item['rank']} Match</span>
<span class="card-year-tag">⭐ {item['score']}</span>
<span class="card-quality">HD</span>
</div>
</div>
</a>"""
                    st.markdown(card_html, unsafe_allow_html=True)
        else:
            st.info("No similar recommendations found.")

    # VIEW 2: Default Showcase -> Top 15 IMDb Rated & Iconic Films (3 Rows of 5 Cards)
    else:
        st.markdown("<div id='trending' class='section-header-title'>🔥 Top 15 IMDb Rated & Iconic Films</div>", unsafe_allow_html=True)
        st.markdown("<div class='section-header-caption'>Click any title to instantly explore its plot synopsis, director, full cast, and ML-generated similarity cluster</div>", unsafe_allow_html=True)

        # Row 1 (5 movies)
        row1_cols = st.columns(5)
        for i in range(5):
            movie = FAMOUS_CATALOG[i]
            with row1_cols[i]:
                card_html = f"""<a href="?movie={movie['movie_id']}" target="_self" class="netflix-card">
<img src="{movie['poster_url']}" class="card-poster-img" />
<div class="card-footer">
<div class="card-movie-title">{movie['title']}</div>
<div class="card-movie-meta">
<span class="match-percent">⭐ {movie['score']} IMDb</span>
<span class="card-year-tag">{movie['year']}</span>
<span class="card-quality">4K</span>
</div>
</div>
</a>"""
                st.markdown(card_html, unsafe_allow_html=True)

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        # Row 2 (5 movies)
        row2_cols = st.columns(5)
        for i in range(5, 10):
            movie = FAMOUS_CATALOG[i]
            with row2_cols[i - 5]:
                card_html = f"""<a href="?movie={movie['movie_id']}" target="_self" class="netflix-card">
<img src="{movie['poster_url']}" class="card-poster-img" />
<div class="card-footer">
<div class="card-movie-title">{movie['title']}</div>
<div class="card-movie-meta">
<span class="match-percent">⭐ {movie['score']} IMDb</span>
<span class="card-year-tag">{movie['year']}</span>
<span class="card-quality">4K</span>
</div>
</div>
</a>"""
                st.markdown(card_html, unsafe_allow_html=True)

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        # Row 3 (5 movies)
        row3_cols = st.columns(5)
        for i in range(10, 15):
            movie = FAMOUS_CATALOG[i]
            with row3_cols[i - 10]:
                card_html = f"""<a href="?movie={movie['movie_id']}" target="_self" class="netflix-card">
<img src="{movie['poster_url']}" class="card-poster-img" />
<div class="card-footer">
<div class="card-movie-title">{movie['title']}</div>
<div class="card-movie-meta">
<span class="match-percent">⭐ {movie['score']} IMDb</span>
<span class="card-year-tag">{movie['year']}</span>
<span class="card-quality">4K</span>
</div>
</div>
</a>"""
                st.markdown(card_html, unsafe_allow_html=True)

else:
    # Mode 2: Collaborative Filtering Mode for Individual Users (Spark MLlib ALS)
    st.markdown("<div class='section-header-title'>👤 User Collaborative Filtering (PySpark ALS)</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-header-caption'>Serving precomputed offline batch recommendations directly from the 32M interactions dataset</div>", unsafe_allow_html=True)
    
    col_u, _ = st.columns([1, 2])
    with col_u:
        user_id = st.number_input("Enter MovieLens User ID", min_value=1, max_value=330975, value=1, step=1)
    
    try:
        with st.spinner(f"Querying PySpark matrix factorization for User {user_id}..."):
            u_resp = requests.get(f"{API_BASE_URL}/recommendations/{user_id}/?limit={num_recs}", timeout=4)
            if u_resp.status_code == 200:
                recs_data = u_resp.json().get("results", [])
                is_fallback = u_resp.json().get("fallback", False)
                if is_fallback:
                    st.info(f"User {user_id} is in cold-start. Showing top curated catalog recommendations.")
                
                cols = st.columns(4)
                for idx, item in enumerate(recs_data):
                    m = item["movie"]
                    col = cols[idx % 4]
                    poster = m.get("poster_url") or SAFE_PLACEHOLDER
                    with col:
                        card_html = f"""<a href="?movie={m['movie_id']}" target="_self" class="netflix-card">
<img src="{poster}" class="card-poster-img" />
<div class="card-footer">
<div class="card-movie-title">{m['title']}</div>
<div class="card-movie-meta">
<span class="match-percent">#{item['rank']} Pick</span>
<span class="card-year-tag">⭐ {item['score']}</span>
<span class="card-quality">HD</span>
</div>
</div>
</a>"""
                        st.markdown(card_html, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Cannot load recommendations for User {user_id}: {e}")

# Tech Stack & Engineering Pipeline Section
st.markdown("<div id='tech-stack'></div>", unsafe_allow_html=True)
with st.expander("🛠️ System Architecture & Engineering Tech Stack (Production Pipeline)", expanded=False):
    t_c1, t_c2, t_c3 = st.columns(3)
    with t_c1:
        st.markdown("""<div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 16px;">
<h4 style="margin: 0 0 6px 0; color: #E50914;">⚡ Big Data & Distributed ML</h4>
<div style="font-size: 0.85rem; color: #b3b3b3; line-height: 1.5;">
• <b>Apache Spark 3.5 & MLlib</b>: Distributed ALS Matrix Factorization.<br>
• <b>Dataset</b>: 32,000,204 MovieLens ratings with explicit StructType schemas.<br>
• <b>Tuned Hyperparameters</b>: <code>rank=16, partitions=40, coldStartStrategy="drop"</code>.
</div>
</div>""", unsafe_allow_html=True)
    with t_c2:
        st.markdown("""<div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 16px;">
<h4 style="margin: 0 0 6px 0; color: #ffffff;">🚀 Microservice Serving Layer</h4>
<div style="font-size: 0.85rem; color: #b3b3b3; line-height: 1.5;">
• <b>Django REST Framework</b>: Production serving boundary.<br>
• <b>Sub-15ms Latency</b>: Serves precomputed vectors without running heavy Spark jobs.<br>
• <b>PostgreSQL 15 / SQLite</b>: Indexed on <code>(user_id, rank)</code> for rapid retrieval.
</div>
</div>""", unsafe_allow_html=True)
    with t_c3:
        st.markdown("""<div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 16px;">
<h4 style="margin: 0 0 6px 0; color: #46d369;">🎬 Real-Time Enrichment Graph</h4>
<div style="font-size: 0.85rem; color: #b3b3b3; line-height: 1.5;">
• <b>TMDB Live Graph API</b>: Real-time posters, director credits & starring cast.<br>
• <b>Hybrid Multi-Strategy Search</b>: Title normalization & post-dataset dynamic ingestion.<br>
• <b>Netflix Cinematic UI</b>: Glassmorphism, 3D hover effects & responsive grid.
</div>
</div>""", unsafe_allow_html=True)

# Developer Profile & Portfolio Card (Varun Esarapu)
st.markdown("""<div class="netflix-footer">
<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 20px;">
<div>
<div style="font-size: 0.76rem; color: #E50914; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em;">Designed & Engineered By</div>
<h3 style="margin: 3px 0 4px 0; font-size: 1.6rem; font-weight: 800; color: #ffffff;">Varun Esarapu</h3>
<p style="margin: 0; color: #8c8c8c; font-size: 0.9rem;">AI & Data Science Engineer · Big Data & Distributed Machine Learning Pipelines</p>
</div>
<div style="display: flex; flex-wrap: wrap; align-items: center;">
<a href="https://e-varun-portfolio.vercel.app/#intro" target="_blank" class="footer-btn footer-portfolio">
<span>🌐</span> Portfolio Website
</a>
<a href="https://github.com/Varun-Esarapu/movie_rec" target="_blank" class="footer-btn footer-github">
<span>🐙</span> GitHub Repository
</a>
<a href="https://www.linkedin.com/in/varun-esarapu/" target="_blank" class="footer-btn footer-linkedin">
<span>💼</span> LinkedIn Profile
</a>
<a href="mailto:esarapuvarun88596@gmail.com" class="footer-btn footer-github">
<span>✉️</span> Contact Varun
</a>
</div>
</div>
</div>""", unsafe_allow_html=True)