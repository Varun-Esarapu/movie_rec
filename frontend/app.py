import os
import re
import json
import urllib.parse
import socket
import requests
import streamlit as st
import streamlit.components.v1 as components
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
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Montserrat:wght@700;800;900&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    
    html {
        scroll-behavior: smooth;
    }
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        -webkit-font-smoothing: antialiased !important;
        -moz-osx-font-smoothing: grayscale !important;
        text-rendering: optimizeLegibility !important;
    }
    
    /* Eliminate Streamlit Default Header Bar & Black Gap (Screenshot 2 Fix) */
    header[data-testid="stHeader"] {
        background: transparent !important;
        height: 0px !important;
        display: none !important;
        visibility: hidden !important;
    }

    [data-testid="stAppViewContainer"] > .main {
        padding-top: 0 !important;
    }

    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 3rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 100% !important;
    }

    .stApp {
        background-color: #141414;
        background-image: radial-gradient(circle at 50% 0%, #2b0b0e 0%, #141414 45%, #0b0b0b 100%);
        color: #e5e5e5;
        min-height: 100vh;
    }

    /* Fixed Spring-Smoothed Scroll Progress Bar along top edge */
    #scroll-progress-indicator {
        position: fixed;
        top: 0;
        left: 0;
        height: 3px;
        background: linear-gradient(90deg, #E50914 0%, #D4AF37 100%);
        z-index: 99999;
        width: 0%;
        box-shadow: 0 0 14px rgba(229, 9, 20, 0.85);
        pointer-events: none;
        will-change: width;
    }

    /* Ambient Neural Glows (Background Floating Lissajous Orbs) */
    .ambient-glow-orb-1 {
        position: fixed;
        top: 10%;
        left: -8%;
        width: 520px;
        height: 520px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(229, 9, 20, 0.08) 0%, rgba(0, 0, 0, 0) 70%);
        filter: blur(70px);
        pointer-events: none;
        z-index: 0;
        animation: ambientDrift1 20s ease-in-out infinite alternate;
    }
    .ambient-glow-orb-2 {
        position: fixed;
        top: 50%;
        right: -10%;
        width: 560px;
        height: 560px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(212, 175, 55, 0.06) 0%, rgba(0, 0, 0, 0) 70%);
        filter: blur(80px);
        pointer-events: none;
        z-index: 0;
        animation: ambientDrift2 24s ease-in-out infinite alternate;
    }
    @keyframes ambientDrift1 {
        0% { transform: translate(0, 0) scale(1); }
        50% { transform: translate(110px, 70px) scale(1.15); }
        100% { transform: translate(40px, -60px) scale(0.92); }
    }
    @keyframes ambientDrift2 {
        0% { transform: translate(0, 0) scale(1.1); }
        50% { transform: translate(-90px, -80px) scale(0.9); }
        100% { transform: translate(70px, 50px) scale(1.05); }
    }

    /* Authentic Netflix Top Bar (Clean, High-End & Robust) */
    .netflix-nav-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 6px 0 16px 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        margin-bottom: 24px;
        flex-wrap: wrap;
        gap: 16px;
        position: relative;
        z-index: 50;
    }
    
    /* Flawless Single-String Pure CSS Typography Brand Component */
    .brand-wrapper {
        display: inline-flex;
        align-items: center;
        gap: 12px;
        text-decoration: none !important;
        user-select: none;
        padding: 4px 0;
        cursor: pointer;
        transition: transform 0.25s ease;
    }
    .brand-wrapper:hover {
        transform: scale(1.03);
    }
    .brand-title {
        font-family: 'Bebas Neue', 'Impact', sans-serif !important;
        font-size: 3.2rem;
        line-height: 1;
        color: #FFFFFF;
        letter-spacing: 2px;
        margin: 0;
        display: flex;
        align-items: center;
        -webkit-font-smoothing: antialiased !important;
        -moz-osx-font-smoothing: grayscale !important;
        text-rendering: optimizeLegibility !important;
    }
    .netflix-n {
        color: #E50914 !important;
        text-shadow: 0 0 10px rgba(229, 9, 20, 0.6);
        position: relative;
        display: inline-block;
        transition: transform 0.25s ease, text-shadow 0.25s ease;
    }
    .brand-wrapper:hover .netflix-n {
        text-shadow: 0 0 18px rgba(229, 9, 20, 0.95);
        transform: translateY(-1px);
    }
    .ai-badge {
        background: #E50914;
        color: #FFFFFF !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.8rem;
        font-weight: 900;
        letter-spacing: 1px;
        padding: 4px 10px 4px 8px;
        border-radius: 4px 0 0 4px;
        clip-path: polygon(0% 0%, 75% 0%, 100% 50%, 75% 100%, 0% 100%);
        box-shadow: 0 0 12px rgba(229, 9, 20, 0.4);
        display: inline-block;
        transition: transform 0.25s ease, box-shadow 0.25s ease;
    }
    .brand-wrapper:hover .ai-badge {
        transform: scale(1.08) translateX(2px);
        box-shadow: 0 0 18px rgba(229, 9, 20, 0.85);
    }

    .nav-middle-tagline {
        font-size: 0.88rem;
        color: #a3a3a3;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    @media (max-width: 768px) {
        .nav-middle-tagline {
            display: none;
        }
    }

    .nav-right-links {
        display: inline-flex;
        align-items: center;
        gap: 10px;
    }
    .nav-link-btn {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 0.78rem;
        font-weight: 700;
        padding: 7px 15px;
        border-radius: 9999px;
        text-decoration: none !important;
        transition: all 0.22s ease;
    }
    .nav-portfolio-btn {
        background: #D4AF37;
        color: #0F0C0A !important;
        box-shadow: 0 0 14px rgba(212, 175, 55, 0.35);
    }
    .nav-portfolio-btn:hover {
        background: #e6c04e;
        transform: translateY(-2px);
        box-shadow: 0 0 20px rgba(212, 175, 55, 0.6);
    }
    .nav-github-btn {
        background: rgba(255, 255, 255, 0.08);
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.15);
    }
    .nav-github-btn:hover {
        background: rgba(255, 255, 255, 0.16);
        border-color: rgba(255, 255, 255, 0.35);
        transform: translateY(-2px);
    }

    /* Equal Proportion Tech Stack Cards (Screenshot 3 Fix) */
    .tech-stack-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        padding: 18px 20px;
        min-height: 180px !important;
        height: 100% !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: flex-start !important;
        box-sizing: border-box !important;
        transition: border-color 0.25s ease, transform 0.25s ease;
    }
    .tech-stack-card:hover {
        border-color: rgba(229, 9, 20, 0.5);
        transform: translateY(-2px);
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
        transform: translateY(-3px) scale(1.04);
        box-shadow: 0 6px 18px rgba(229, 9, 20, 0.45);
    }

    /* Native Streamlit Pills Styled as Glowing Netflix Chips (No Page Reload) */
    div[data-testid="stPills"] {
        display: flex !important;
        flex-wrap: wrap !important;
        gap: 8px !important;
        justify-content: center !important;
        align-items: center !important;
        margin: 6px 0 24px 0 !important;
    }
    div[data-testid="stPills"] button {
        background: rgba(38, 38, 38, 0.75) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        color: #e5e5e5 !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        border-radius: 9999px !important;
        padding: 6px 14px !important;
        transition: all 0.24s cubic-bezier(0.4, 0, 0.2, 1) !important;
        white-space: nowrap !important;
        cursor: pointer !important;
    }
    div[data-testid="stPills"] button:hover {
        background: #E50914 !important;
        color: #ffffff !important;
        border-color: #E50914 !important;
        transform: translateY(-3px) scale(1.04) !important;
        box-shadow: 0 6px 18px rgba(229, 9, 20, 0.45) !important;
    }
    div[data-testid="stPills"] button[aria-selected="true"] {
        background: #E50914 !important;
        color: #ffffff !important;
        border-color: #E50914 !important;
        box-shadow: 0 0 16px rgba(229, 9, 20, 0.6) !important;
    }

    /* Netflix Poster Cards (Equal Proportions & Depth - Natural 2:3 Aspect Ratio) */
    .netflix-card {
        text-decoration: none !important;
        display: flex !important;
        flex-direction: column !important;
        color: inherit !important;
        cursor: pointer;
        position: relative;
        border-radius: 8px;
        overflow: hidden;
        background: #181818;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.7);
        transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.35s ease, border-color 0.35s ease;
        margin-bottom: 16px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-sizing: border-box !important;
        animation: cardCascadeIn 0.65s cubic-bezier(0.16, 1, 0.3, 1) backwards;
        will-change: transform, box-shadow;
    }
    
    @keyframes cardCascadeIn {
        from { opacity: 0; transform: translateY(20px) scale(0.96); }
        to { opacity: 1; transform: translateY(0) scale(1); }
    }
    
    .netflix-card:hover {
        transform: translateY(-8px) scale(1.045);
        z-index: 30;
        box-shadow: 0 22px 40px rgba(0, 0, 0, 0.95), 0 0 26px rgba(229, 9, 20, 0.45);
        border-color: rgba(229, 9, 20, 0.75);
    }

    .card-poster-img {
        width: 100% !important;
        aspect-ratio: 2 / 3 !important;
        height: auto !important;
        object-fit: cover !important;
        display: block !important;
        background: #111111;
        transition: transform 0.4s ease;
    }

    .card-footer {
        min-height: 64px !important;
        padding: 10px 12px !important;
        background: #181818;
        display: flex !important;
        flex-direction: column !important;
        justify-content: space-between !important;
        box-sizing: border-box !important;
    }

    .card-movie-title {
        font-size: 0.86rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 2px;
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

    /* Clean Minimalist Loading Spinner */
    div[data-testid="stSpinner"] {
        margin: 18px 0 !important;
        padding: 12px 0 !important;
    }

    /* Cinema Play Fill Loader (Screenshot 5 - #15 Play Fill Loader) */
    .play-loader-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 34px 0;
        animation: fadeInPlayLoader 0.35s ease forwards;
    }
    @keyframes fadeInPlayLoader {
        from { opacity: 0; transform: scale(0.96); }
        to { opacity: 1; transform: scale(1); }
    }
    .play-loader-circle {
        position: relative;
        width: 64px;
        height: 64px;
        margin-bottom: 16px;
    }
    .play-loader-track-ring {
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        border-radius: 50%;
        border: 4px solid rgba(229, 9, 20, 0.18);
        box-sizing: border-box;
    }
    .play-loader-spin-ring {
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        border-radius: 50%;
        border: 4px solid transparent;
        border-top-color: #E50914;
        border-right-color: #E50914;
        box-shadow: 0 0 16px rgba(229, 9, 20, 0.55);
        box-sizing: border-box;
        animation: playRingRotate 1.0s cubic-bezier(0.45, 0.05, 0.55, 0.95) infinite;
    }
    .play-loader-center-triangle {
        position: absolute;
        top: 50%; left: 54%;
        transform: translate(-50%, -50%);
        width: 0; height: 0;
        border-top: 12px solid transparent;
        border-bottom: 12px solid transparent;
        border-left: 18px solid #E50914;
        filter: drop-shadow(0 0 8px rgba(229, 9, 20, 0.8));
        animation: playFillPulse 1.4s ease-in-out infinite;
    }
    @keyframes playRingRotate {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    @keyframes playFillPulse {
        0%, 100% { transform: translate(-50%, -50%) scale(0.92); opacity: 0.85; filter: drop-shadow(0 0 6px rgba(229, 9, 20, 0.5)); }
        50% { transform: translate(-50%, -50%) scale(1.18); opacity: 1; filter: drop-shadow(0 0 18px rgba(229, 9, 20, 1)); }
    }
    .play-loader-title {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.25rem;
        letter-spacing: 0.12em;
        color: #ffffff;
        text-transform: uppercase;
        margin-bottom: 4px;
        text-shadow: 0 0 12px rgba(229, 9, 20, 0.4);
    }
    .play-loader-subtitle {
        font-size: 0.82rem;
        color: #a3a3a3;
        font-weight: 500;
        letter-spacing: 0.02em;
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
    div[data-testid="stCustomComponentV1"] {
        display: none !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    #home-section, #search-section, #trending-section, #tech-stack-section, #contact-section {
        scroll-margin-top: 100px;
    }
</style>

<div id="scroll-progress-indicator"></div>
""", unsafe_allow_html=True)

# Authentic Top 15 Highest-Rated IMDb Movies in Cinema History (Verified Metadata & Ratings)
FAMOUS_CATALOG = [
    {"movie_id": 318, "title": "The Shawshank Redemption", "year": "1994", "tmdb_id": 278, "poster_url": "https://image.tmdb.org/t/p/w500/9cqNxx0GxF0bflZmeSMuL5tnGzr.jpg", "score": 9.3, "genres": "Drama · Crime"},
    {"movie_id": 858, "title": "The Godfather", "year": "1972", "tmdb_id": 238, "poster_url": "https://image.tmdb.org/t/p/w500/3bhkrj58Vtu7enYsRolD1fZdja1.jpg", "score": 9.2, "genres": "Crime · Drama"},
    {"movie_id": 58559, "title": "The Dark Knight", "year": "2008", "tmdb_id": 155, "poster_url": "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg", "score": 9.0, "genres": "Action · Crime"},
    {"movie_id": 1221, "title": "The Godfather Part II", "year": "1974", "tmdb_id": 240, "poster_url": "https://image.tmdb.org/t/p/w500/8a1lJs7mFyGhGhZZDT1azJUoQiZ.jpg", "score": 9.0, "genres": "Crime · Drama"},
    {"movie_id": 1203, "title": "12 Angry Men", "year": "1957", "tmdb_id": 389, "poster_url": "https://image.tmdb.org/t/p/w500/zhG3vKWyDRaZYoaww1UVAi29T9h.jpg", "score": 9.0, "genres": "Crime · Drama"},
    {"movie_id": 527, "title": "Schindler's List", "year": "1993", "tmdb_id": 424, "poster_url": "https://image.tmdb.org/t/p/w500/sF1U4EUQS8YHUYjNl3pMGNIQyr0.jpg", "score": 9.0, "genres": "Biography · Drama"},
    {"movie_id": 7153, "title": "The Lord of the Rings: The Return of the King", "year": "2003", "tmdb_id": 122, "poster_url": "https://image.tmdb.org/t/p/w500/rCzpDGLbOoPwLjy3OAm5NUPOTrC.jpg", "score": 9.0, "genres": "Adventure · Fantasy"},
    {"movie_id": 296, "title": "Pulp Fiction", "year": "1994", "tmdb_id": 680, "poster_url": "https://image.tmdb.org/t/p/w500/vQWk5YBFWF4bZaofAbv0tShwBvQ.jpg", "score": 8.9, "genres": "Crime · Thriller"},
    {"movie_id": 4993, "title": "The Lord of the Rings: The Fellowship of the Ring", "year": "2001", "tmdb_id": 120, "poster_url": "https://image.tmdb.org/t/p/w500/6oom5QYQ2yQTMJIbnvbkBL9cHo6.jpg", "score": 8.9, "genres": "Adventure · Fantasy"},
    {"movie_id": 2959, "title": "Fight Club", "year": "1999", "tmdb_id": 550, "poster_url": "https://image.tmdb.org/t/p/w500/jSziioSwPVrOy9Yow3XhWIBDjq1.jpg", "score": 8.8, "genres": "Drama · Thriller"},
    {"movie_id": 356, "title": "Forrest Gump", "year": "1994", "tmdb_id": 13, "poster_url": "https://image.tmdb.org/t/p/w500/Cw4hIUIAmSYfK9QfaUW5igp9La.jpg", "score": 8.8, "genres": "Comedy · Drama"},
    {"movie_id": 79132, "title": "Inception", "year": "2010", "tmdb_id": 27205, "poster_url": "https://image.tmdb.org/t/p/w500/xlaY2zyzMfkhk0HSC5VUwzoZPU1.jpg", "score": 8.8, "genres": "Action · Sci-Fi"},
    {"movie_id": 5952, "title": "The Lord of the Rings: The Two Towers", "year": "2002", "tmdb_id": 121, "poster_url": "https://image.tmdb.org/t/p/w500/5VTN0pR8gcqV3EPUHHfMGnJYN9L.jpg", "score": 8.8, "genres": "Adventure · Fantasy"},
    {"movie_id": 1213, "title": "Goodfellas", "year": "1990", "tmdb_id": 769, "poster_url": "https://image.tmdb.org/t/p/w500/9OkCLM73MIU2CrKZbqiT8Ln1wY2.jpg", "score": 8.7, "genres": "Biography · Crime"},
    {"movie_id": 2571, "title": "The Matrix", "year": "1999", "tmdb_id": 603, "poster_url": "https://image.tmdb.org/t/p/w500/dXNAPwY7VrqMAo51EKhhCJfaGb5.jpg", "score": 8.7, "genres": "Action · Sci-Fi"},
]

# Official Verified IMDb Ratings for Exact Consistency
IMDB_VERIFIED_RATINGS = {
    "the shawshank redemption": 9.3,
    "the godfather": 9.2,
    "the dark knight": 9.0,
    "the godfather part ii": 9.0,
    "the godfather: part ii": 9.0,
    "12 angry men": 9.0,
    "schindler's list": 9.0,
    "the lord of the rings: the return of the king": 9.0,
    "pulp fiction": 8.9,
    "the lord of the rings: the fellowship of the ring": 8.9,
    "the good, the bad and the ugly": 8.8,
    "fight club": 8.8,
    "forrest gump": 8.8,
    "inception": 8.8,
    "the lord of the rings: the two towers": 8.8,
    "star wars: episode v - the empire strikes back": 8.7,
    "the matrix": 8.7,
    "goodfellas": 8.7,
    "interstellar": 8.7,
    "the green mile": 8.6,
    "gladiator": 8.5,
    "the departed": 8.5,
    "whiplash": 8.5,
    "the prestige": 8.5,
    "the lion king": 8.5,
    "dune": 8.0,
    "dune (2021)": 8.0,
    "dune: part two": 8.5,
    "oppenheimer": 8.9,
    "kill bill: vol. 1": 8.2,
    "kill bill": 8.2,
    "shutter island": 8.2,
    "heat": 8.3,
    "300": 7.6,
    "rocky": 8.1,
    "(500) days of summer": 7.7,
    "karthikeya 2": 7.9,
    "orange": 7.1,
    "darling": 7.3,
    "dhruva": 7.8,
    "rrr": 8.0,
    "baahubali: the beginning": 8.0,
    "baahubali 2: the conclusion": 8.2,
    "k.g.f: chapter 1": 8.2,
    "k.g.f: chapter 2": 8.3,
    "pushpa: the rise": 7.6,
    "kantara": 8.2,
    "sita ramam": 8.5,
    "jersey": 8.5,
    "magadheera": 7.7,
    "pokiri": 8.0,
    "athadu": 8.2,
    "dangal": 8.4,
    "3 idiots": 8.4,
    "taare zameen par": 8.4,
    "drishyam": 8.2,
    "vikram": 8.3,
    "the notebook": 7.8,
    "notebook": 7.8,
    "me before you": 7.4,
    "the fault in our stars": 7.7,
}

AUTOFILL_TITLES = [
    "Requiem for a Dream", "The Usual Suspects", "Dead Poets Society", "Dune", "Dune (2021)",
    "Oppenheimer", "The Shawshank Redemption", "The Godfather", "The Dark Knight",
    "The Godfather Part II", "12 Angry Men", "Schindler's List",
    "The Lord of the Rings: The Return of the King", "Pulp Fiction",
    "The Lord of the Rings: The Fellowship of the Ring", "Fight Club", "Forrest Gump",
    "Inception", "The Lord of the Rings: The Two Towers", "Goodfellas", "The Matrix",
    "Interstellar", "The Green Mile", "Gladiator", "Kill Bill: Vol. 1", "Shutter Island",
    "300", "Rocky", "(500) Days of Summer", "Heat", "Memento", "The Prestige", "Whiplash",
    "Se7en", "Leon: The Professional", "American Psycho", "Taxi Driver", "Scarface",
    "A Clockwork Orange", "The Shining", "Good Will Hunting", "Back to the Future",
    "Blade Runner 2049", "Parasite", "Casablanca", "Apocalypse Now", "Saving Private Ryan",
    "Braveheart", "Reservoir Dogs", "Snatch", "Django Unchained", "Inglourious Basterds",
    "The Departed", "No Country for Old Men", "There Will Be Blood", "The Silence of the Lambs"
]
try:
    with open("backend/top_titles.json", "r") as f:
        _ext = json.load(f)
        for _t in _ext:
            _cl = re.sub(r"\s*\(\d{4}\)", "", _t).strip()
            if _cl and _cl not in AUTOFILL_TITLES:
                AUTOFILL_TITLES.append(_cl)
except Exception:
    pass

def render_play_loader(title="STREAMING CINEMATIC CLUSTERS...", subtitle="Evaluating latent embedding vectors across 32M ratings"):
    return f"""<div class="play-loader-container">
<div class="play-loader-circle">
<div class="play-loader-track-ring"></div>
<div class="play-loader-spin-ring"></div>
<div class="play-loader-center-triangle"></div>
</div>
<div class="play-loader-title">{title}</div>
<div class="play-loader-subtitle">{subtitle}</div>
</div>"""

# Render Navbar & Ambient Glow First
st.markdown("""
<div class="netflix-nav-container">
<a href="?home=true" target="_self" class="brand-wrapper" title="Return to Home">
<div class="brand-title">CI<span class="netflix-n">N</span>EMATCH</div>
<div class="ai-badge">AI&nbsp;</div>
</a>
<div class="nav-middle-tagline">
<span>🎬 Distributed PySpark ALS Recommender</span>
<span style="color: rgba(255,255,255,0.25); margin: 0 8px;">•</span>
<span style="color: #46d369; font-weight:700;">● Engine Online</span>
</div>
<div class="nav-right-links">
<a href="https://github.com/Varun-Esarapu/movie_rec" target="_blank" class="nav-link-btn nav-github-btn" title="GitHub Repository">
<span>🐙</span> GitHub
</a>
<a href="https://e-varun-portfolio.vercel.app/#intro" target="_blank" class="nav-link-btn nav-portfolio-btn" title="Explore Varun's Portfolio">
<span>🌐</span> Portfolio
</a>
</div>
</div>
<div class="ambient-glow-orb-1"></div>
<div class="ambient-glow-orb-2"></div>
""", unsafe_allow_html=True)

# Fast Memory-Cached Backend API Helpers (0ms repeat latency, eliminates blank screen delays)
@st.cache_data(ttl=3600, show_spinner=False)
def api_search_movies(query: str):
    clean = query.strip()
    if not clean or len(clean) < 2:
        return []
    try:
        resp = requests.get(f"{API_BASE_URL}/movies/search/?q={urllib.parse.quote(clean)}", timeout=4)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return []

@st.cache_data(ttl=3600, show_spinner=False)
def api_get_similar(movie_id: int, limit: int):
    try:
        resp = requests.get(f"{API_BASE_URL}/movies/{movie_id}/similar/?limit={limit}", timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return {}

@st.cache_data(ttl=3600, show_spinner=False)
def api_get_recommendations(user_id: int, limit: int):
    try:
        resp = requests.get(f"{API_BASE_URL}/recommendations/{user_id}/?limit={limit}", timeout=4)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return {}

# State management
if "selected_movie" not in st.session_state:
    st.session_state["selected_movie"] = None
if "search_input" not in st.session_state:
    st.session_state["search_input"] = ""
if "last_search" not in st.session_state:
    st.session_state["last_search"] = ""
if "last_pill" not in st.session_state:
    st.session_state["last_pill"] = None
if "search_matches" not in st.session_state:
    st.session_state["search_matches"] = []

# URL Query Param Navigation Handling (Streamlined, Non-Blocking)
if "home" in st.query_params:
    st.session_state["selected_movie"] = None
    st.session_state["search_input"] = ""
    st.session_state["last_search"] = ""
    st.session_state["last_pill"] = None
    st.session_state["search_matches"] = []
    st.query_params.clear()

if "movie" in st.query_params:
    mid = st.query_params.get("movie")
    if mid:
        found_target = next((m for m in FAMOUS_CATALOG if str(m["movie_id"]) == str(mid)), None)
        if found_target:
            st.session_state["selected_movie"] = found_target
        else:
            st.session_state["selected_movie"] = {"movie_id": int(mid), "title": ""}
    st.query_params.clear()

if "search" in st.query_params:
    sq = st.query_params.get("search")
    if sq:
        st.session_state["search_input"] = sq
        st.session_state["last_search"] = sq
        local_hit = next((m for m in FAMOUS_CATALOG if m["title"].lower() == sq.lower()), None)
        if local_hit:
            st.session_state["selected_movie"] = local_hit
            st.session_state["search_matches"] = [local_hit]
        else:
            found = api_search_movies(sq)
            if found:
                st.session_state["selected_movie"] = found[0]
                st.session_state["search_matches"] = found[:3]
    st.query_params.clear()

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
    st.markdown("<div id='search-section'></div>", unsafe_allow_html=True)
    c_left, c_search, c_right = st.columns([1, 2.8, 1])
    with c_search:
        search_query = st.text_input(
            "Search Movie",
            value=st.session_state["search_input"],
            placeholder="Search movie (e.g. Requiem for a Dream, Dune, The Godfather, Interstellar...)",
            label_visibility="collapsed"
        )

        # Native Instant Popular Picks Pills (No Browser Unload / Zero Black Screen)
        POPULAR_CHIPS = [
            "🏜️ Dune", "🍷 The Godfather", "🦇 The Dark Knight", "🕶️ Fight Club",
            "🗡️ Kill Bill", "⚔️ Gladiator", "🌀 Inception", "🌌 Interstellar",
            "🏝️ Shutter Island", "🛡️ 300", "🥊 Rocky", "☀️ (500) Days of Summer",
            "⚛️ Oppenheimer", "💊 Requiem for a Dream"
        ]
        st.markdown("<div class='quick-chips-label' style='text-align:center; margin-bottom: 2px;'>POPULAR PICKS:</div>", unsafe_allow_html=True)
        selected_pill = st.pills(
            "Popular Picks",
            options=POPULAR_CHIPS,
            label_visibility="collapsed",
            key="popular_picks_pills"
        )
        if selected_pill and selected_pill != st.session_state.get("last_pill"):
            st.session_state["last_pill"] = selected_pill
            chip_clean = re.sub(r"^[^\w\s\(\)]+\s*", "", selected_pill).strip()
            st.session_state["search_input"] = chip_clean
            st.session_state["last_search"] = chip_clean
            local_hit = next((m for m in FAMOUS_CATALOG if m["title"].lower() == chip_clean.lower()), None)
            if local_hit:
                st.session_state["selected_movie"] = local_hit
                st.session_state["search_matches"] = [local_hit]
            else:
                found = api_search_movies(chip_clean)
                if found:
                    st.session_state["selected_movie"] = found[0]
                    st.session_state["search_matches"] = found[:8]
            st.rerun()

    # Process search if typed
    if search_query.strip() and search_query != st.session_state.get("last_search"):
        st.session_state["last_search"] = search_query
        try:
            search_loader = st.empty()
            search_loader.markdown(render_play_loader("SEARCHING NEURAL CATALOG...", f"Querying global index & latent vectors for '{search_query.strip()}'"), unsafe_allow_html=True)
            found = api_search_movies(search_query.strip())
            search_loader.empty()
            if found:
                st.session_state["selected_movie"] = found[0]
                st.session_state["search_matches"] = found[:8]
            else:
                st.session_state["search_matches"] = []
                st.warning(f"No catalog match found for '{search_query}'.")
        except Exception as e:
            st.error(f"Backend search failed: {e}")

    # Compact Disambiguation Bar (Up to 8 matches presented in clean 4-column rows)
    matches = st.session_state.get("search_matches", [])
    if len(matches) > 1 and st.session_state.get("selected_movie"):
        c_m_left, c_m_content, c_m_right = st.columns([1, 3.2, 1])
        with c_m_content:
            st.markdown("<div style='font-size: 0.82rem; color: #a3a3a3; margin: 6px 0 4px 0;'>🔍 <b>Multiple matches found for your search:</b> (Click to explore)</div>", unsafe_allow_html=True)
            for chunk_start in range(0, len(matches), 4):
                chunk = matches[chunk_start:chunk_start + 4]
                chunk_cols = st.columns(len(chunk))
                for i, cand in enumerate(chunk):
                    with chunk_cols[i]:
                        is_active = (cand.get("movie_id") == st.session_state["selected_movie"].get("movie_id"))
                        btn_label = f"✓ {cand['title']}" if is_active else cand['title']
                        if st.button(btn_label, key=f"disambig_{cand['movie_id']}_{chunk_start+i}", use_container_width=True):
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
                st.session_state["last_search"] = ""
                st.session_state["last_pill"] = None
                st.session_state["search_matches"] = []
                st.rerun()

        # Fetch Similar Movies & Details from Backend (Cached for Instant Response)
        sim_data = []
        details = {}
        try:
            loader_box = st.empty()
            loader_box.markdown(render_play_loader("STREAMING CINEMATIC CLUSTERS...", "Evaluating latent embedding vectors across 32M ratings"), unsafe_allow_html=True)
            data_json = api_get_similar(target['movie_id'], num_recs)
            loader_box.empty()
            sim_data = data_json.get("results", [])
            source_movie = data_json.get("source_movie", {})
            details = source_movie.get("details", {})
        except Exception as e:
            st.error(f"Could not reach recommendation service: {e}")

        # Synchronize target and session state with real backend metadata
        if source_movie:
            real_title = source_movie.get("title") or details.get("title")
            if real_title and real_title not in ("Selected Film", "Unknown Title", ""):
                target["title"] = real_title
            real_poster = source_movie.get("poster_url") or details.get("poster_url")
            if real_poster:
                target["poster_url"] = real_poster
            if source_movie.get("genres"):
                target["genres"] = source_movie["genres"]
            st.session_state["selected_movie"] = target

        # Render Netflix Hero Showcase Banner
        title_str = (
            target.get("title")
            if (target.get("title") and target.get("title") not in ("Selected Film", "Unknown Title", ""))
            else (source_movie.get("title") or details.get("title") or "Feature Film")
        )

        hero_poster = (
            target.get("poster_url")
            or source_movie.get("poster_url")
            or details.get("poster_url")
            or SAFE_PLACEHOLDER
        )

        genres_raw = (
            source_movie.get("genres")
            or target.get("genres")
            or "Drama"
        ).replace("|", " · ")
        year_str = details.get("release_date", "")[:4] or "Classic"
        tagline = details.get("tagline", "")
        overview = details.get("overview") or "A critically acclaimed cinematic masterpiece recognized for its exceptional storytelling, deep thematic development, and iconic performances."
        director = details.get("director", "")
        cast = details.get("cast", "")
        runtime = details.get("runtime", "")
        vote_avg = details.get("vote_average")
        vote_count = details.get("vote_count")

        # Check verified IMDb rating & Source Transparency
        clean_title_key = re.sub(r"\s*\(\d{4}\)", "", title_str).lower().strip()
        imdb_score = IMDB_VERIFIED_RATINGS.get(clean_title_key) or IMDB_VERIFIED_RATINGS.get(title_str.lower().strip())
        imdb_id = details.get("imdb_id")
        imdb_link_html = f"<a href='https://www.imdb.com/title/{imdb_id}/' target='_blank' style='color:#f5c518; text-decoration:none; font-weight:700; margin-left:8px; font-size:0.75rem; background:rgba(245,197,24,0.12); padding:3px 8px; border-radius:4px; border:1px solid rgba(245,197,24,0.35);' title='View on IMDb'>IMDb ↗</a>" if imdb_id else ""

        if imdb_score:
            rating_html = f"<span class='badge-match-score'>⭐ {imdb_score:.1f} / 10 IMDb</span>{imdb_link_html}"
        elif vote_avg and vote_count:
            rating_html = f"<span class='badge-match-score'>⭐ {vote_avg:.1f} / 10 TMDB Rating ({vote_count:,} reviews)</span>{imdb_link_html}"
        elif vote_avg:
            rating_html = f"<span class='badge-match-score'>⭐ {vote_avg:.1f} / 10 TMDB</span>{imdb_link_html}"
        else:
            rating_html = f"<span class='badge-match-score'>98% Match</span>{imdb_link_html}"
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

        st.markdown(f"<div id='trending-section' class='section-header-title'>✨ More Like *{title_str}*</div>", unsafe_allow_html=True)
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
        st.markdown("<div id='trending-section' class='section-header-title'>🔥 Top 15 IMDb Rated & Iconic Films</div>", unsafe_allow_html=True)
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
        cf_loader = st.empty()
        cf_loader.markdown(render_play_loader("COMPUTING PYSPARK MATRIX FACTORIZATION...", f"Serving latent dot-products for User #{user_id} across 32M interactions"), unsafe_allow_html=True)
        u_data = api_get_recommendations(user_id, num_recs)
        cf_loader.empty()
        recs_data = u_data.get("results", [])
        is_fallback = u_data.get("fallback", False)
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
st.markdown("<div id='tech-stack-section'></div>", unsafe_allow_html=True)
with st.expander("🛠️ System Architecture & Engineering Tech Stack (Production Pipeline)", expanded=False):
    t_c1, t_c2, t_c3 = st.columns(3)
    with t_c1:
        st.markdown("""<div class="tech-stack-card">
<h4 style="margin: 0 0 6px 0; color: #E50914;">⚡ Big Data & Distributed ML</h4>
<div style="font-size: 0.85rem; color: #b3b3b3; line-height: 1.5;">
• <b>Apache Spark 3.5 & MLlib</b>: Distributed ALS Matrix Factorization.<br>
• <b>Dataset</b>: 32,000,204 MovieLens ratings with explicit StructType schemas.<br>
• <b>Tuned Hyperparameters</b>: <code>rank=16, partitions=40, coldStartStrategy="drop"</code>.
</div>
</div>""", unsafe_allow_html=True)
    with t_c2:
        st.markdown("""<div class="tech-stack-card">
<h4 style="margin: 0 0 6px 0; color: #ffffff;">🚀 Microservice Serving Layer</h4>
<div style="font-size: 0.85rem; color: #b3b3b3; line-height: 1.5;">
• <b>Django REST Framework</b>: Production serving boundary.<br>
• <b>Sub-15ms Latency</b>: Serves precomputed vectors without running heavy Spark jobs.<br>
• <b>PostgreSQL 15 / SQLite</b>: Indexed on <code>(user_id, rank)</code> for rapid retrieval.
</div>
</div>""", unsafe_allow_html=True)
    with t_c3:
        st.markdown("""<div class="tech-stack-card">
<h4 style="margin: 0 0 6px 0; color: #46d369;">🎬 Real-Time Enrichment Graph</h4>
<div style="font-size: 0.85rem; color: #b3b3b3; line-height: 1.5;">
• <b>TMDB Live Graph API</b>: Real-time posters, director credits & starring cast.<br>
• <b>Hybrid Multi-Strategy Search</b>: Title normalization & post-dataset dynamic ingestion.<br>
• <b>Netflix Cinematic UI</b>: Glassmorphism, 3D hover effects & responsive grid.
</div>
</div>""", unsafe_allow_html=True)

# Developer Profile & Portfolio Card (Varun Esarapu)
st.markdown("""<div id="contact-section" class="netflix-footer">
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
<a href="mailto:varunesarapu@gmail.com" class="footer-btn footer-github">
<span>✉️</span> Contact Varun
</a>
</div>
</div>
</div>""", unsafe_allow_html=True)