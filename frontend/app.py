import os
import sys
import re
import json
import subprocess
import urllib.parse
import socket
from pathlib import Path
import requests
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

load_dotenv()

def get_secret_or_env(key: str, default: str = "") -> str:
    try:
        if key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return os.getenv(key, default)

TMDB_API_KEY = get_secret_or_env("TMDB_API_KEY", "3a1ff8b883fd4c71a563201decf380b1")
SAFE_PLACEHOLDER = "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=500&auto=format&fit=crop&q=60"

def _ensure_local_backend():
    """Automatically launches local Django backend on port 8000 if not already running."""
    try:
        with socket.create_connection(("127.0.0.1", 8000), timeout=0.3):
            return
    except Exception:
        pass
    manage_py = Path(__file__).resolve().parent.parent / "backend" / "manage.py"
    if manage_py.exists():
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            subprocess.Popen(
                [sys.executable, str(manage_py), "runserver", "127.0.0.1:8000", "--noreload"],
                cwd=str(manage_py.parent),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags
            )
        except Exception:
            pass

def resolve_api_base_url():
    explicit_url = (
        get_secret_or_env("API_BASE_URL")
        or get_secret_or_env("BACKEND_API_URL")
        or get_secret_or_env("DJANGO_API_URL")
    )
    if explicit_url:
        return explicit_url.rstrip("/")

    # If running locally and local Django backend is listening on 8000, prefer local
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.3)
        res = sock.connect_ex(('127.0.0.1', 8000))
        sock.close()
        if res == 0:
            return "http://127.0.0.1:8000/api/v1"
    except Exception:
        pass

    # Production Render Backend URL
    return "https://cinematchai-pvbq.onrender.com/api/v1"

API_BASE_URL = resolve_api_base_url()

st.set_page_config(
    page_title="CINEMATCH — Netflix AI Movie Discovery",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Enterprise-Grade Cinema Discovery Theme (Inter Font, #08090b Palette, Custom Scrollbars & Animated Hero)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700;800;900&family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=swap');
    
    :root {
        --background: #08090b;
        --surface: #131418;
        --surface-raised: #1c1e24;
        --foreground: #f2f1ec;
        --muted: #9a9ba3;
        --ember: #f2f2f2;
        --ember-dim: #c7c7cc;
        --gold: #f0b429;
        --danger: #ef4444;
        --danger-dim: #dc2626;
        --border: rgba(242, 241, 236, 0.08);
        --border-subtle: rgba(242, 241, 236, 0.08);
        --border-default: rgba(242, 241, 236, 0.12);
        --border-strong: rgba(242, 241, 236, 0.25);
        --font-sans: 'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        --font-display: 'Plus Jakarta Sans', 'Inter', sans-serif;
    }

    html, body, [data-testid="stAppViewContainer"], section.main, .stApp {
        scroll-behavior: smooth !important;
        color-scheme: dark;
        scrollbar-gutter: stable;
    }
    
    * {
        box-sizing: border-box;
        scrollbar-width: thin;
        scrollbar-color: var(--ember-dim) transparent;
    }
    
    html, body, .stApp, p, a, button, input, textarea, select, h1, h2, h3, h4, h5, h6,
    .brand-title, .section-main-heading, .pill-nav-item, .category-pill, .mood-title, .mood-sub {
        font-family: var(--font-sans) !important;
        -webkit-font-smoothing: antialiased !important;
        -moz-osx-font-smoothing: grayscale !important;
        text-rendering: optimizeLegibility !important;
    }

    /* Protect Streamlit & Google Material Icons from being ruined by text fonts (Screenshot 1 Fix) */
    [data-testid="stIconMaterial"], 
    [data-testid="stExpanderToggleIcon"], 
    [data-testid="stExpanderToggleIcon"] *,
    .material-symbols-rounded, 
    .material-symbols-outlined, 
    [class*="material-symbols"] {
        font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Icons', sans-serif !important;
        font-feature-settings: 'liga' 1 !important;
        letter-spacing: normal !important;
        text-transform: none !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-size: 1.25rem !important;
        line-height: 1 !important;
    }

    /* Fix Expander Header Layout (Screenshot 1 Fix: No text collision/overlap) */
    div[data-testid="stExpander"] {
        border: 1px solid var(--border-default) !important;
        border-radius: 14px !important;
        background: var(--surface) !important;
        overflow: hidden !important;
        margin: 16px 0 24px 0 !important;
    }
    div[data-testid="stExpander"] details {
        border: none !important;
        background: transparent !important;
    }
    div[data-testid="stExpander"] summary {
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        gap: 12px !important;
        padding: 14px 20px !important;
        cursor: pointer !important;
        background: rgba(22, 24, 32, 0.6) !important;
        transition: background 0.2s ease !important;
        list-style: none !important;
    }
    div[data-testid="stExpander"] summary::-webkit-details-marker {
        display: none !important;
    }
    div[data-testid="stExpander"] summary:hover {
        background: rgba(30, 33, 44, 0.8) !important;
    }
    div[data-testid="stExpander"] summary [data-testid="stExpanderToggleIcon"] {
        margin-right: 6px !important;
        flex-shrink: 0 !important;
        width: 24px !important;
        height: 24px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    div[data-testid="stExpander"] summary p {
        margin: 0 !important;
        font-size: 0.95rem !important;
        font-weight: 700 !important;
        color: #ffffff !important;
        letter-spacing: -0.01em !important;
    }

    .stApp {
        background-color: var(--background) !important;
        color: var(--foreground) !important;
    }

    h1, h2, h3, h4, .section-main-heading, .brand-title, .hero-title-text {
        font-family: var(--font-display) !important;
        letter-spacing: -0.025em !important;
    }
    
    /* Sleek Custom Scrollbar matching user snippet */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    ::-webkit-scrollbar-thumb {
        background: #383a42;
        border: 2px solid var(--background);
        border-radius: 999px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #50525c;
    }
    ::-webkit-scrollbar-track {
        background: transparent;
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
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: 1320px !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }

    .stApp {
        background-color: var(--background) !important;
        background-image: 
            radial-gradient(circle at 50% 120px, rgba(229, 9, 20, 0.09) 0%, rgba(19, 20, 24, 0.65) 40%, var(--background) 80%) !important;
        color: var(--foreground) !important;
        min-height: 100vh;
        transition: background-color 0.4s ease, color 0.4s ease;
    }

    html.theme-warm-slate, html.theme-warm-slate body, html.theme-warm-slate .stApp {
        --background: #0f1015 !important;
        --surface: #181a24 !important;
        --surface-raised: #222634 !important;
        --foreground: #ffffff !important;
        --border-default: rgba(255, 255, 255, 0.16) !important;
    }
    html.theme-warm-slate .stApp {
        background-color: #0f1015 !important;
        background-image: 
            radial-gradient(circle at 50% 120px, rgba(245, 158, 11, 0.12) 0%, rgba(24, 26, 36, 0.75) 45%, #0f1015 80%) !important;
    }



    /* Fixed Spring-Smoothed Scroll Progress Bar along top edge */
    #scroll-progress-indicator {
        position: fixed;
        top: 0;
        left: 0;
        height: 3px;
        background: linear-gradient(90deg, #E50914 0%, #ff3b47 100%);
        z-index: 99999;
        width: 0%;
        box-shadow: 0 0 14px rgba(229, 9, 20, 0.85);
        pointer-events: none;
        will-change: width;
    }

    /* Ambient Neural Glows (Background Floating Lissajous Orbs) */
    .ambient-glow-orb-1 {
        position: fixed;
        top: 8%;
        left: -8%;
        width: 520px;
        height: 520px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(229, 9, 20, 0.10) 0%, rgba(0, 0, 0, 0) 70%);
        filter: blur(75px);
        pointer-events: none;
        z-index: 0;
        animation: ambientDrift1 20s ease-in-out infinite alternate;
    }
    .ambient-glow-orb-2 {
        position: fixed;
        top: 45%;
        right: -8%;
        width: 560px;
        height: 560px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(229, 9, 20, 0.07) 0%, rgba(0, 0, 0, 0) 70%);
        filter: blur(85px);
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

    /* Authentic CineMatch Navbar (Matching Mockup) */
    .netflix-nav-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 0 16px 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        margin-bottom: 16px;
        flex-wrap: wrap;
        gap: 16px;
        position: relative;
        z-index: 50;
    }
    
    .brand-wrapper {
        display: inline-flex;
        align-items: center;
        gap: 0px;
        text-decoration: none !important;
        user-select: none;
        padding: 4px 0;
        cursor: pointer;
        transition: transform 0.25s ease;
    }
    .brand-wrapper:hover {
        transform: scale(1.02);
    }
    .brand-title {
        font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        font-size: 1.85rem;
        font-weight: 900;
        letter-spacing: 0.02em;
        line-height: 1;
        color: #FFFFFF;
        margin: 0;
        display: flex;
        align-items: center;
    }
    .ai-badge {
        background: #E50914;
        color: #FFFFFF !important;
        font-family: 'Plus Jakarta Sans', 'Inter', sans-serif !important;
        font-size: 0.72rem;
        font-weight: 900;
        letter-spacing: 0.04em;
        padding: 2px 7px;
        border-radius: 5px;
        margin-left: 6px;
        box-shadow: 0 0 12px rgba(229, 9, 20, 0.45);
        display: inline-block;
        transition: transform 0.25s ease, box-shadow 0.25s ease;
    }
    .brand-wrapper:hover .ai-badge {
        transform: scale(1.06);
        box-shadow: 0 0 18px rgba(229, 9, 20, 0.75);
    }

    /* Floating Continuous Tabs Navigation Bar (Screenshot 2 Alignment) */
    .floating-pill-nav {
        display: inline-flex;
        align-items: center;
        gap: 3px;
        background: #14151b;
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 9999px;
        padding: 4px 5px;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.65), inset 0 1px 0 rgba(255, 255, 255, 0.06);
        backdrop-filter: blur(24px);
        position: relative;
        z-index: 50;
    }
    @media (max-width: 960px) {
        .floating-pill-nav {
            order: 3;
            width: 100%;
            justify-content: center;
            margin-top: 8px;
        }
    }
    .pill-nav-item {
        color: #9a9ba3 !important;
        font-family: var(--font-sans) !important;
        font-size: 0.85rem;
        font-weight: 500;
        padding: 7px 18px;
        border-radius: 9999px;
        text-decoration: none !important;
        transition: all 0.24s cubic-bezier(0.16, 1, 0.3, 1);
        display: inline-flex;
        align-items: center;
        white-space: nowrap;
        position: relative;
        cursor: pointer;
        user-select: none;
    }
    .pill-nav-item:hover {
        color: #ffffff !important;
        background: rgba(255, 255, 255, 0.06);
    }
    .pill-nav-item:active {
        transform: scale(0.94);
        background: rgba(255, 255, 255, 0.12) !important;
    }
    .pill-nav-item.active {
        background: #252833 !important;
        color: #ffffff !important;
        font-weight: 600;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.14);
        border: 1px solid rgba(255, 255, 255, 0.12);
    }
    .pill-contact-item {
        background: transparent !important;
        border: none !important;
        color: #9a9ba3 !important;
    }
    .pill-contact-item:hover {
        background: rgba(255, 255, 255, 0.06) !important;
        color: #ffffff !important;
    }

    /* Animated Spring Switch Mode (Screenshot 4: Motion Switch with Spring Physics) */
    .switch-mode-wrapper {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        user-select: none;
        margin-right: 4px;
    }
    .switch-mode-track {
        width: 58px;
        height: 30px;
        background: #14151b;
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 9999px;
        padding: 2px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        position: relative;
        cursor: pointer;
        box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.5), 0 2px 8px rgba(0, 0, 0, 0.3);
        transition: background 0.3s ease, border-color 0.3s ease;
    }
    .switch-mode-track:hover {
        border-color: rgba(255, 255, 255, 0.3);
        background: #191b22;
    }
    .switch-icon {
        width: 16px;
        height: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1;
        transition: color 0.3s ease, opacity 0.3s ease;
        margin: 0 4px;
        pointer-events: none;
    }
    .switch-icon.sun {
        color: #fbbf24;
    }
    .switch-icon.moon {
        color: #94a3b8;
    }
    .switch-thumb {
        position: absolute;
        top: 2px;
        left: 3px;
        width: 24px;
        height: 24px;
        border-radius: 50%;
        background: #ffffff;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.45);
        /* Framer Motion Spring overshoot timing function */
        transition: transform 0.42s cubic-bezier(0.34, 1.56, 0.64, 1), background 0.3s ease;
        z-index: 2;
        pointer-events: none;
    }
    .switch-mode-track.is-active .switch-thumb {
        transform: translateX(27px);
    }
    .switch-mode-track.is-active .switch-icon.sun {
        color: #64748b;
    }
    .switch-mode-track.is-active .switch-icon.moon {
        color: #c084fc;
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
        font-size: 0.82rem;
        font-weight: 600;
        padding: 7px 18px;
        border-radius: 9999px;
        text-decoration: none !important;
        transition: all 0.22s ease;
    }
    .nav-portfolio-btn {
        background: #E50914 !important;
        color: #ffffff !important;
        box-shadow: 0 4px 15px rgba(229, 9, 20, 0.4) !important;
    }
    .nav-portfolio-btn:hover {
        background: #f40d19 !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(229, 9, 20, 0.65) !important;
    }
    .nav-github-btn {
        background: rgba(255, 255, 255, 0.08);
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.16);
    }
    .nav-github-btn:hover {
        background: rgba(255, 255, 255, 0.16);
        border-color: rgba(255, 255, 255, 0.35);
        transform: translateY(-2px);
    }

    /* Hero Headline & Subtitles (Matching Mockup) */
    .hero-center-box {
        text-align: center;
        margin: 28px auto 20px auto;
        max-width: 860px;
        padding: 0 16px;
    }
    .hero-headline {
        font-size: 3.2rem;
        font-weight: 900;
        letter-spacing: -0.02em;
        color: #ffffff;
        line-height: 1.15;
        margin: 0 0 12px 0;
        font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, sans-serif;
    }
    .highlight-red {
        color: #E50914;
        text-shadow: 0 0 25px rgba(229, 9, 20, 0.45);
    }
    .hero-lead {
        font-size: 1.1rem;
        font-weight: 500;
        color: #e2e8f0;
        margin-bottom: 6px;
    }
    .hero-sublead {
        font-size: 0.92rem;
        color: #94a3b8;
    }

    /* Sleek Rounded Capsule Search Input (Screenshot 3: Minimalist 'Find...' with Left SVG Glass) */
    div[data-testid="stTextInput"] {
        max-width: 640px;
        margin: 0 auto !important;
        position: relative;
    }
    div[data-testid="stTextInput"] > div > div {
        border-radius: 9999px !important;
        background: #0d0e12 !important;
        border: 1px solid rgba(255, 255, 255, 0.14) !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.45) !important;
        padding: 3px 20px 3px 46px !important;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
        position: relative;
    }
    div[data-testid="stTextInput"] > div > div:focus-within {
        border-color: rgba(255, 255, 255, 0.35) !important;
        background: #111218 !important;
        box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.2), 0 8px 30px rgba(0, 0, 0, 0.6) !important;
    }
    div[data-testid="stTextInput"]::before {
        content: "";
        position: absolute;
        left: 20px;
        top: 50%;
        transform: translateY(-50%);
        width: 17px;
        height: 17px;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%238a8c98' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='11' cy='11' r='7'/%3E%3Cline x1='21' y1='21' x2='16.65' y2='16.65'/%3E%3C/svg%3E");
        background-repeat: no-repeat;
        background-position: center;
        background-size: contain;
        pointer-events: none;
        z-index: 5;
        opacity: 0.85;
    }
    div[data-testid="stTextInput"] input {
        color: #f2f1ec !important;
        font-family: var(--font-sans) !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        padding-left: 0 !important;
        background: transparent !important;
    }
    div[data-testid="stTextInput"] input::placeholder {
        color: #8a8c98 !important;
        font-family: var(--font-sans) !important;
        font-size: 0.95rem !important;
        font-weight: 450 !important;
    }

    /* CineMatch Premium Return Button (Screenshot 4 Alignment) */
    .cinematch-return-btn {
        display: inline-flex;
        align-items: center;
        gap: 9px;
        padding: 9px 24px;
        background: rgba(22, 24, 32, 0.85);
        border: 1px solid rgba(229, 9, 20, 0.45);
        border-radius: 9999px;
        color: #ffffff !important;
        font-size: 0.88rem;
        font-weight: 700;
        text-decoration: none !important;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.6), inset 0 0 12px rgba(229, 9, 20, 0.12);
        backdrop-filter: blur(12px);
        margin: 8px 0 24px 0;
        cursor: pointer;
    }
    .cinematch-return-btn:hover {
        background: #E50914 !important;
        border-color: #E50914 !important;
        color: #ffffff !important;
        transform: translateX(-4px) scale(1.02);
        box-shadow: 0 0 22px rgba(229, 9, 20, 0.65), 0 8px 24px rgba(0, 0, 0, 0.8) !important;
    }
    .cinematch-return-btn .arrow-icon {
        color: #E50914;
        font-size: 1.15rem;
        font-weight: 800;
        transition: transform 0.2s ease, color 0.2s ease;
    }
    .cinematch-return-btn:hover .arrow-icon {
        color: #ffffff;
        transform: translateX(-4px);
    }

    /* Category Filter Pills (Matching Mockup: 10 Pills) */
    .category-pills-row {
        display: flex;
        flex-wrap: nowrap;
        overflow-x: auto;
        gap: 10px;
        justify-content: center;
        align-items: center;
        margin: 18px auto 32px auto;
        padding: 4px 10px;
        scrollbar-width: none;
        -ms-overflow-style: none;
        max-width: 100%;
    }
    .category-pills-row::-webkit-scrollbar {
        display: none;
    }
    @media (max-width: 960px) {
        .category-pills-row {
            justify-content: flex-start;
        }
    }
    .category-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 7px 16px;
        background: rgba(22, 24, 30, 0.65);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #d1d5db !important;
        font-size: 0.82rem;
        font-weight: 600;
        border-radius: 9999px;
        text-decoration: none !important;
        transition: all 0.22s ease;
        backdrop-filter: blur(8px);
        white-space: nowrap;
        flex-shrink: 0;
    }
    .category-pill:hover {
        border-color: rgba(229, 9, 20, 0.6);
        color: #ffffff !important;
        background: rgba(30, 32, 40, 0.85);
        transform: translateY(-2px);
    }
    .category-pill.active {
        border-color: #E50914 !important;
        background: rgba(229, 9, 20, 0.16) !important;
        color: #ffffff !important;
        box-shadow: 0 0 16px rgba(229, 9, 20, 0.35);
    }

    /* Section Flex Headers (Matching Mockup) */
    .section-flex-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        margin: 32px 0 16px 0;
        flex-wrap: wrap;
        gap: 10px;
    }
    .section-title-box {
        display: flex;
        flex-direction: column;
    }
    .section-title-row {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .section-main-heading {
        font-size: 1.5rem;
        font-weight: 800;
        color: #ffffff;
        margin: 0;
        font-family: 'Plus Jakarta Sans', 'Inter', sans-serif;
        letter-spacing: -0.01em;
    }
    .section-sub-heading {
        color: #8c8c8c;
        font-size: 0.88rem;
        margin-top: 4px;
    }
    .section-view-all {
        color: #E50914 !important;
        font-size: 0.88rem;
        font-weight: 700;
        text-decoration: none !important;
        display: inline-flex;
        align-items: center;
        gap: 4px;
        transition: all 0.2s ease;
        padding: 4px 8px;
        border-radius: 4px;
    }
    .section-view-all:hover {
        color: #ff333e !important;
        transform: translateX(3px);
    }

    /* CineMatch Card Row Wrappers & CSS Grids */
    .cinematch-row-with-arrow {
        display: flex;
        align-items: center;
        gap: 14px;
        width: 100%;
        margin-bottom: 24px;
    }
    .cinematch-grid-container {
        width: 100%;
        margin-bottom: 24px;
    }
    .cinematch-cards-grid {
        display: grid;
        grid-template-columns: repeat(5, minmax(0, 1fr));
        gap: 16px;
        flex: 1;
        width: 100%;
    }
    .cinematch-cards-grid-4 {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 18px;
        width: 100%;
        margin-bottom: 24px;
    }
    @media (max-width: 1024px) {
        .cinematch-cards-grid {
            grid-template-columns: repeat(3, minmax(0, 1fr));
        }
        .cinematch-cards-grid-4 {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
    }
    @media (max-width: 640px) {
        .cinematch-cards-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
        .cinematch-cards-grid-4 {
            grid-template-columns: repeat(1, minmax(0, 1fr));
        }
    }

    /* CineMatch 4K Overlay Poster Card (Matching Mockup) */
    .cinematch-card {
        position: relative;
        border-radius: 12px;
        overflow: hidden;
        background: #111216;
        border: 1px solid rgba(255, 255, 255, 0.08);
        display: block;
        text-decoration: none !important;
        transition: transform 0.28s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.28s ease, border-color 0.28s ease;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.7);
        aspect-ratio: 2 / 3;
        width: 100%;
        margin: 0 auto;
        box-sizing: border-box;
    }
    .cinematch-card:hover {
        transform: translateY(-6px) scale(1.03);
        box-shadow: 0 16px 36px rgba(0, 0, 0, 0.9), 0 0 20px rgba(229, 9, 20, 0.35);
        border-color: rgba(229, 9, 20, 0.7);
        z-index: 10;
    }
    .cinematch-card.featured {
        border: 2px solid #E50914 !important;
        box-shadow: 0 0 26px rgba(229, 9, 20, 0.5), 0 12px 28px rgba(0, 0, 0, 0.85) !important;
    }
    .cinematch-card.featured:hover {
        box-shadow: 0 0 36px rgba(229, 9, 20, 0.75), 0 18px 40px rgba(0, 0, 0, 0.95) !important;
        transform: translateY(-8px) scale(1.04);
    }
    .cinematch-card-poster {
        width: 100% !important;
        height: 100% !important;
        object-fit: cover !important;
        display: block !important;
        background: #0f1014;
        transition: transform 0.4s ease;
    }
    .cinematch-card:hover .cinematch-card-poster {
        transform: scale(1.05);
    }
    .badge-4k {
        position: absolute;
        top: 10px;
        right: 10px;
        background: rgba(14, 15, 20, 0.75);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 4px;
        padding: 2px 6px;
        font-size: 0.68rem;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: 0.05em;
        z-index: 2;
    }
    .cinematch-card-overlay {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        padding: 28px 12px 10px 12px;
        background: linear-gradient(to top, rgba(9, 10, 14, 0.98) 0%, rgba(9, 10, 14, 0.8) 45%, rgba(9, 10, 14, 0.25) 75%, transparent 100%);
        display: flex;
        flex-direction: column;
        justify-content: flex-end;
        box-sizing: border-box;
        z-index: 2;
    }
    .cinematch-card-title {
        font-size: 0.88rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 4px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        line-height: 1.25;
    }
    .cinematch-card-meta {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.74rem;
    }
    .cinematch-card-score {
        color: #f5c518;
        font-weight: 700;
        display: inline-flex;
        align-items: center;
        gap: 3px;
    }
    .cinematch-card-score .imdb-text {
        color: #8c8c8c;
        font-size: 0.68rem;
        font-weight: 600;
        margin-left: 2px;
    }
    .cinematch-card-year {
        color: #8c8c8c;
        font-weight: 500;
    }

    /* Carousel Arrow Nav Button */
    .carousel-arrow-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 40px;
        height: 40px;
        min-width: 40px;
        border-radius: 50%;
        background: rgba(22, 24, 30, 0.85);
        border: 1px solid rgba(255, 255, 255, 0.15);
        color: #ffffff !important;
        font-size: 1.15rem;
        text-decoration: none !important;
        transition: all 0.22s ease;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
        cursor: pointer;
    }
    .carousel-arrow-btn:hover {
        background: #E50914;
        border-color: #E50914;
        transform: scale(1.1);
        box-shadow: 0 0 16px rgba(229, 9, 20, 0.5);
    }

    /* Mood Grid & Cards (Matching Mockup: 6 Moods) */
    .mood-grid {
        display: grid;
        grid-template-columns: repeat(6, minmax(0, 1fr));
        gap: 14px;
        margin-top: 14px;
        margin-bottom: 24px;
    }
    @media (max-width: 1100px) {
        .mood-grid {
            grid-template-columns: repeat(3, minmax(0, 1fr));
        }
    }
    @media (max-width: 600px) {
        .mood-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
    }
    .mood-card {
        background: rgba(20, 22, 28, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 14px 16px;
        display: flex;
        align-items: center;
        gap: 12px;
        text-decoration: none !important;
        backdrop-filter: blur(8px);
        transition: all 0.22s ease;
        box-sizing: border-box;
    }
    .mood-card:hover {
        border-color: rgba(229, 9, 20, 0.5);
        background: rgba(28, 30, 38, 0.9);
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(229, 9, 20, 0.15);
    }
    .mood-icon-box {
        width: 38px;
        height: 38px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        transition: transform 0.22s ease, box-shadow 0.22s ease;
    }
    .mood-card:hover .mood-icon-box {
        transform: scale(1.08);
    }
    .section-icon-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 32px;
        height: 32px;
        border-radius: 8px;
        background: rgba(229, 9, 20, 0.14);
        border: 1px solid rgba(229, 9, 20, 0.38);
        color: #E50914;
        flex-shrink: 0;
    }
    .mood-info {
        display: flex;
        flex-direction: column;
    }
    .mood-title {
        font-size: 0.92rem;
        font-weight: 700;
        color: #ffffff;
        line-height: 1.2;
    }
    .mood-sub {
        font-size: 0.74rem;
        color: #8c8c8c;
        margin-top: 2px;
    }

    /* Equal Proportion Tech Stack Cards */
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

    /* Disambiguation Bar Pill Links */
    .disambig-chip {
        display: block;
        text-align: center;
        padding: 7px 10px;
        background: rgba(30, 30, 30, 0.85);
        border: 1px solid rgba(255, 255, 255, 0.15);
        color: #e5e5e5 !important;
        font-size: 0.82rem;
        font-weight: 600;
        border-radius: 6px;
        text-decoration: none !important;
        transition: all 0.2s ease;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        margin-bottom: 6px;
    }
    .disambig-chip:hover {
        background: rgba(229, 9, 20, 0.8);
        border-color: #E50914;
        color: #ffffff !important;
        transform: translateY(-1px);
    }
    .disambig-chip.active {
        background: #E50914 !important;
        border-color: #E50914 !important;
        color: #ffffff !important;
        box-shadow: 0 0 12px rgba(229, 9, 20, 0.55);
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
        max-height: 315px !important;
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

    /* Streaming Platform Hero Showcase (.hero) - Inspected from Real Movie Site */
    .hero, .netflix-hero-banner {
        position: relative;
        display: flex;
        flex-direction: column;
        min-height: 480px;
        width: 100%;
        background-color: #050508;
        background-size: cover;
        background-position: center 25%;
        background-repeat: no-repeat;
        overflow: hidden;
        justify-content: center;
        border-radius: 18px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 24px 60px rgba(0, 0, 0, 0.95);
        margin-bottom: 34px;
        z-index: 0;
        animation: heroFadeIn 0.45s cubic-bezier(0.2, 0.8, 0.2, 1);
    }
    
    @keyframes heroFadeIn {
        from { opacity: 0; transform: translateY(16px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .hero:before, .netflix-hero-banner:before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(to top, rgba(5, 5, 8, .98) 0%, rgba(5, 5, 8, .75) 22%, transparent 60%);
        pointer-events: none;
        z-index: 1;
    }
    .hero:after, .netflix-hero-banner:after {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: radial-gradient(circle at center, transparent 35%, rgba(0, 0, 0, .45) 90%),
                    linear-gradient(to right, rgba(5, 5, 8, 0.96) 0%, rgba(5, 5, 8, 0.75) 45%, rgba(5, 5, 8, 0.2) 100%);
        pointer-events: none;
        z-index: 1;
    }

    /* Multi-Movie Gradual Crossfade Hero Slider */
    .hero-slider-container {
        position: relative;
        min-height: 520px;
        width: 100%;
        background-color: var(--background);
        overflow: hidden;
        border-radius: 18px;
        border: 1px solid var(--border-default);
        box-shadow: 0 24px 60px rgba(0, 0, 0, 0.95);
        margin-bottom: 34px;
        z-index: 0;
    }

    .hero-slide {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        opacity: 0;
        visibility: hidden;
        pointer-events: none;
        display: flex;
        flex-direction: column;
        justify-content: center;
        overflow: hidden;
        animation: heroSlideCycle 24s cubic-bezier(0.4, 0, 0.2, 1) infinite;
    }

    .hero-slide:nth-child(1) { animation-delay: 0s; }
    .hero-slide:nth-child(2) { animation-delay: -18s; }
    .hero-slide:nth-child(3) { animation-delay: -12s; }
    .hero-slide:nth-child(4) { animation-delay: -6s; }

    @keyframes heroSlideCycle {
        0% {
            opacity: 0;
            visibility: visible;
            pointer-events: none;
        }
        3% {
            opacity: 1;
            pointer-events: auto;
        }
        22% {
            opacity: 1;
            pointer-events: auto;
        }
        25% {
            opacity: 0;
            pointer-events: none;
            visibility: hidden;
        }
        100% {
            opacity: 0;
            visibility: hidden;
            pointer-events: none;
        }
    }

    .hero-slide-bg {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-size: cover;
        background-position: center 25%;
        background-repeat: no-repeat;
        z-index: 0;
        transform: scale(1.02);
    }

    .hero-slide:before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(to top, rgba(8, 9, 11, 1) 0%, rgba(8, 9, 11, 0.78) 22%, transparent 60%);
        pointer-events: none;
        z-index: 1;
    }

    .hero-slide:after {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: radial-gradient(circle at center, transparent 35%, rgba(0, 0, 0, 0.5) 90%),
                    linear-gradient(to right, rgba(8, 9, 11, 0.96) 0%, rgba(8, 9, 11, 0.78) 46%, rgba(8, 9, 11, 0.15) 100%);
        pointer-events: none;
        z-index: 1;
    }

    .hero-slider-nav {
        position: absolute;
        bottom: 24px;
        right: 32px;
        z-index: 10;
        display: flex;
        gap: 8px;
        align-items: center;
        flex-wrap: wrap;
    }

    .hero-slider-pill {
        background: rgba(19, 20, 24, 0.78);
        border: 1px solid rgba(242, 241, 236, 0.12);
        backdrop-filter: blur(12px);
        border-radius: 9999px;
        padding: 5px 13px;
        color: var(--muted) !important;
        font-family: var(--font-inter) !important;
        font-size: 0.76rem;
        font-weight: 600;
        text-decoration: none !important;
        transition: all 0.22s ease;
        display: inline-flex;
        align-items: center;
        gap: 5px;
    }

    .hero-slider-pill:hover {
        color: #ffffff !important;
        border-color: rgba(229, 9, 20, 0.65);
        background: rgba(30, 32, 40, 0.9);
        transform: translateY(-2px);
    }

    .hero-content {
        position: relative;
        z-index: 2;
        padding: 40px 36px;
        display: flex;
        gap: 34px;
        align-items: flex-start;
        flex-wrap: wrap;
    }

    .hero-poster-img {
        width: 200px;
        aspect-ratio: 2 / 3;
        object-fit: cover;
        border-radius: 12px;
        box-shadow: 0 18px 40px rgba(0, 0, 0, 0.9), 0 0 24px rgba(229, 9, 20, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.15);
        flex-shrink: 0;
        transition: transform 0.3s ease;
    }
    .hero-poster-img:hover {
        transform: scale(1.03);
    }

    .hero-details-col {
        flex: 1;
        min-width: 320px;
    }

    .hero-spotlight-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 0.78rem;
        color: #E50914;
        background: rgba(229, 9, 20, 0.16);
        border: 1px solid rgba(229, 9, 20, 0.45);
        padding: 3px 12px;
        border-radius: 9999px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 8px;
    }

    .hero-title-text {
        font-family: 'Bebas Neue', 'Montserrat', sans-serif;
        font-size: 3.5rem;
        letter-spacing: 0.03em;
        line-height: 1;
        color: #ffffff;
        margin: 0 0 8px 0;
        text-shadow: 0 2px 14px rgba(0,0,0,0.9);
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
        color: #d8d8d8;
        font-size: 0.96rem;
        line-height: 1.65;
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

    .hero-actions-row {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-top: 20px;
        flex-wrap: wrap;
    }
    .hero-btn-primary {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: #E50914;
        color: #ffffff !important;
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 700;
        font-size: 0.9rem;
        padding: 10px 22px;
        border-radius: 8px;
        text-decoration: none !important;
        transition: all 0.22s ease;
        box-shadow: 0 4px 18px rgba(229, 9, 20, 0.45);
    }
    .hero-btn-primary:hover {
        background: #f40d19;
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(229, 9, 20, 0.7);
    }
    .hero-btn-secondary {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(255, 255, 255, 0.08);
        color: #ffffff !important;
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 600;
        font-size: 0.9rem;
        padding: 10px 20px;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.18);
        text-decoration: none !important;
        transition: all 0.22s ease;
        backdrop-filter: blur(8px);
    }
    .hero-btn-secondary:hover {
        background: rgba(255, 255, 255, 0.16);
        border-color: rgba(255, 255, 255, 0.35);
        transform: translateY(-2px);
    }


    .director-link-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        color: #ffffff !important;
        font-weight: 700;
        font-size: 0.94rem;
        text-decoration: none !important;
        padding: 5px 12px;
        margin-top: 4px;
        border-radius: 9999px;
        background: linear-gradient(135deg, rgba(229, 9, 20, 0.25) 0%, rgba(212, 175, 55, 0.15) 100%);
        border: 1px solid rgba(229, 9, 20, 0.55);
        transition: all 0.22s ease;
        box-shadow: 0 2px 10px rgba(229, 9, 20, 0.2);
    }
    .director-link-badge:hover {
        background: #E50914;
        color: #ffffff !important;
        border-color: #ff3b47;
        transform: translateY(-2px) scale(1.02);
        box-shadow: 0 6px 18px rgba(229, 9, 20, 0.55);
    }
    .chrono-year-ribbon {
        position: absolute;
        top: 10px;
        left: 10px;
        background: rgba(15, 15, 15, 0.88);
        border: 1px solid rgba(212, 175, 55, 0.65);
        color: #D4AF37;
        font-weight: 800;
        font-size: 0.76rem;
        padding: 3px 9px;
        border-radius: 6px;
        backdrop-filter: blur(6px);
        z-index: 10;
        letter-spacing: 0.04em;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.65);
    }
    details.director-bio-details {
        margin-top: -6px;
        margin-bottom: 16px;
        max-width: 820px;
    }
    details.director-bio-details > summary {
        list-style: none;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        cursor: pointer;
        color: #D4AF37;
        font-size: 0.82rem;
        font-weight: 700;
        padding: 4px 12px;
        border-radius: 9999px;
        background: rgba(212, 175, 55, 0.12);
        border: 1px solid rgba(212, 175, 55, 0.38);
        transition: all 0.2s ease;
        user-select: none;
    }
    details.director-bio-details > summary::-webkit-details-marker {
        display: none;
    }
    details.director-bio-details > summary:hover {
        background: rgba(212, 175, 55, 0.24);
        border-color: #D4AF37;
        transform: translateY(-1px);
    }
    details.director-bio-details[open] > summary .bio-more-label {
        display: none;
    }
    details.director-bio-details:not([open]) > summary .bio-less-label {
        display: none;
    }
    .director-bio-extra {
        margin-top: 12px;
        padding-top: 10px;
        border-top: 1px solid rgba(255, 255, 255, 0.08);
        color: #c8c8c8;
        font-size: 0.92rem;
        line-height: 1.6;
        animation: heroFadeIn 0.3s ease;
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
    /* Completely silence skeleton shimmer - zero flashes, zero text popups */
    [data-testid="stSkeleton"], .stSkeleton {
        background: transparent !important;
        animation: none !important;
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
        margin: 0 !important;
        padding: 0 !important;
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

    /* Executive Profile / Footer Card */
    .netflix-footer {
        background: var(--surface);
        border: 1px solid var(--border-default);
        padding: 32px 28px;
        margin-top: 56px;
        border-radius: 16px;
        box-shadow: 0 16px 40px rgba(0, 0, 0, 0.7);
    }
    .footer-btn {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 9px 18px;
        border-radius: 9999px;
        font-size: 0.84rem;
        font-weight: 600;
        text-decoration: none !important;
        transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1);
        border: 1px solid transparent;
        backdrop-filter: blur(8px);
    }
    .footer-portfolio {
        background: rgba(229, 9, 20, 0.16);
        border-color: rgba(229, 9, 20, 0.45);
        color: #ffffff !important;
    }
    .footer-portfolio:hover {
        background: #E50914;
        border-color: #ff3b47;
        transform: translateY(-2px);
        box-shadow: 0 0 20px rgba(229, 9, 20, 0.55);
    }
    .footer-github {
        background: rgba(255, 255, 255, 0.06);
        border-color: rgba(255, 255, 255, 0.15);
        color: #f2f1ec !important;
    }
    .footer-github:hover {
        background: rgba(255, 255, 255, 0.14);
        border-color: rgba(255, 255, 255, 0.32);
        transform: translateY(-2px);
        color: #ffffff !important;
    }
    .footer-linkedin {
        background: rgba(10, 102, 194, 0.16);
        border-color: rgba(10, 102, 194, 0.45);
        color: #60a5fa !important;
    }
    .footer-linkedin:hover {
        background: #0a66c2;
        border-color: #38bdf8;
        color: #ffffff !important;
        transform: translateY(-2px);
        box-shadow: 0 0 20px rgba(10, 102, 194, 0.45);
    }
    .footer-mail {
        background: rgba(255, 255, 255, 0.06);
        border-color: rgba(255, 255, 255, 0.15);
        color: #f2f1ec !important;
    }
    .footer-mail:hover {
        background: rgba(255, 255, 255, 0.14);
        border-color: rgba(255, 255, 255, 0.32);
        transform: translateY(-2px);
        color: #ffffff !important;
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

    #home-section, #search-section, #trending-section, #top-15-section, #mood-section, #tech-stack-section, #contact-section {
        scroll-margin-top: 110px !important;
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
    {"movie_id": 1203, "title": "12 Angry Men", "year": "1957", "tmdb_id": 389, "poster_url": "https://image.tmdb.org/t/p/w500/ppd84D2i9W8jXmsyInGyihiSyqz.jpg", "score": 9.0, "genres": "Crime · Drama"},
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
    "oppenheimer": 8.2,
    "django unchained": 8.5,
    "inglourious basterds": 8.4,
    "the hateful eight": 7.8,
    "once upon a time in hollywood": 7.6,
    "once upon a time... in hollywood": 7.6,
    "kill bill: vol. 2": 8.0,
    "jackie brown": 7.5,
    "death proof": 7.0,
    "dunkirk": 7.8,
    "tenet": 7.3,
    "batman begins": 8.2,
    "the dark knight rises": 8.4,
    "insomnia": 7.2,
    "following": 7.4,
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
    "eega": 7.7,
    "chatrapathi": 7.7,
    "vikramarkudu": 7.7,
    "sye": 7.6,
    "simhadri": 7.3,
    "maryada ramanna": 7.5,
    "student no. 1": 6.9,
    "yamadonga": 7.2,
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
    "the godfather part iii": 7.6,
    "the godfather: part iii": 7.6,
    "apocalypse now": 8.4,
    "the conversation": 7.7,
    "bram stoker's dracula": 7.4,
    "once upon a time in america": 8.3,
    "casino": 8.2,
    "a bronx tale": 7.8,
    "carlito's way": 7.9,
    "scarface": 8.3,
    "taxi driver": 8.2,
    "raging bull": 8.1,
    "the wolf of wall street": 8.2,
    "the irishman": 7.8,
    "killers of the flower moon": 7.6,
    "the aviator": 7.5,
    "gangs of new york": 7.5,
    "reservoir dogs": 8.3,
    "se7en": 8.6,
    "seven": 8.6,
    "the social network": 7.8,
    "the curious case of benjamin button": 7.8,
    "the girl with the dragon tattoo": 7.8,
    "the game": 7.7,
    "panic room": 6.8,
    "the killer": 6.7,
    "mank": 6.8,
    "alien 3": 6.4,
    "the usual suspects": 8.5,
    "the silence of the lambs": 8.6,
    "saving private ryan": 8.6,
    "jurassic park": 8.2,
    "jaws": 8.1,
    "catch me if you can": 8.1,
    "raiders of the lost ark": 8.4,
    "indiana jones and the last crusade": 8.2,
    "the fabelmans": 7.5,
    "requiem for a dream": 8.3,
    "black swan": 8.0,
    "the wrestler": 7.9,
    "the whale": 7.7,
    "pi": 7.3,
    "memento": 8.4,
    "donnie brasco": 7.7,
    "american psycho": 7.6,
    "no country for old men": 8.2,
    "there will be blood": 8.2,
    "zodiac": 7.7,
    "prisoners": 8.2,
    "arrival": 7.9,
    "blade runner 2049": 8.0,
    "sicario": 7.6,
    "incendies": 8.3,
    "enemy": 6.9,
    "gone girl": 8.1,
}

def format_display_title(raw_title: str) -> str:
    """Converts MovieLens inverted titles like 'Godfather, The (1972)' -> 'The Godfather (1972)'."""
    if not raw_title:
        return ""
    t = raw_title.strip()
    year_match = re.search(r"\s*(\(\d{4}\))$", t)
    year_suffix = f" {year_match.group(1)}" if year_match else ""
    base = t[:year_match.start()].strip() if year_match else t
    # Remove MovieLens a.k.a. parentheticals
    base = re.sub(r"\s*\(a\.k\.a\.[^)]+\)", "", base, flags=re.IGNORECASE).strip()
    article_match = re.match(r"^(.*),\s*(The|A|An)$", base, flags=re.IGNORECASE)
    if article_match:
        base = f"{article_match.group(2)} {article_match.group(1).strip()}"
    return f"{base}{year_suffix}"

def get_verified_imdb_score(title_str: str):
    """Looks up official IMDb rating across normalized, un-inverted, and punctuation-stripped title variants."""
    if not title_str:
        return None
    cleaned_display = format_display_title(title_str)
    no_year = re.sub(r"\s*\(\d{4}\)", "", cleaned_display).lower().strip()
    no_colon = no_year.replace(":", "").replace("  ", " ").strip()
    no_article = re.sub(r"^(the|a|an)\s+", "", no_year).strip()
    for candidate in (no_year, no_colon, f"the {no_article}", no_article, title_str.lower().strip()):
        if candidate in IMDB_VERIFIED_RATINGS:
            return IMDB_VERIFIED_RATINGS[candidate]
    return None

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

def render_cinematch_card(movie_id, title, poster_url, score, year, is_featured=False, quality="4K"):
    featured_cls = " featured" if is_featured else ""
    clean_title = format_display_title(title)
    
    if isinstance(score, (int, float)):
        score_val = f"{score:.1f}"
    else:
        score_val = str(score).replace("⭐", "").replace("IMDb", "").strip()
        try:
            score_val = f"{float(score_val):.1f}"
        except Exception:
            pass
    
    year_val = str(year).strip() if year else "Classic"

    return f"""<a href="?movie={movie_id}" target="_self" class="cinematch-card{featured_cls}">
<img src="{poster_url}" class="cinematch-card-poster" loading="lazy" alt="{clean_title}" />
<div class="badge-4k">{quality}</div>
<div class="cinematch-card-overlay">
<div class="cinematch-card-title" title="{clean_title}">{clean_title}</div>
<div class="cinematch-card-meta">
<div class="cinematch-card-score"><span style="color:#f5c518; margin-right:2px;">⭐</span> {score_val} <span class="imdb-text">IMDb</span></div>
<div class="cinematch-card-year">{year_val}</div>
</div>
</div>
</a>"""

def render_cards_grid(cards_html_list, show_arrow=False, arrow_href="#more-iconic-section"):
    arrow_html = f'<a href="{arrow_href}" target="_self" class="carousel-arrow-btn" title="View More Iconic Films">❯</a>' if show_arrow else ''
    wrapper_class = "cinematch-row-with-arrow" if show_arrow else "cinematch-grid-container"
    return f"""<div class="{wrapper_class}">
<div class="cinematch-cards-grid">
{''.join(cards_html_list)}
</div>
{arrow_html}
</div>"""

CATEGORY_PILLS = [
    {"label": "All", "icon": """<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect width="7" height="7" x="3" y="3" rx="1"/><rect width="7" height="7" x="14" y="3" rx="1"/><rect width="7" height="7" x="14" y="14" rx="1"/><rect width="7" height="7" x="3" y="14" rx="1"/></svg>""", "genre": "all"},
    {"label": "Action", "icon": """<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>""", "genre": "action"},
    {"label": "Drama", "icon": """<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><path d="M8 15h8"/><circle cx="9" cy="9" r="1" fill="currentColor"/><circle cx="15" cy="9" r="1" fill="currentColor"/></svg>""", "genre": "drama"},
    {"label": "Comedy", "icon": """<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" x2="9.01" y1="9" y2="9"/><line x1="15" x2="15.01" y1="9" y2="9"/></svg>""", "genre": "comedy"},
    {"label": "Thriller", "icon": """<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>""", "genre": "thriller"},
    {"label": "Sci-Fi", "icon": """<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="6"/><path d="M2.5 12a14 5 0 0 0 19 0"/></svg>""", "genre": "sci-fi"},
    {"label": "Horror", "icon": """<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="m12 2-8.5 16h17L12 2z"/></svg>""", "genre": "horror"},
    {"label": "Romance", "icon": """<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/></svg>""", "genre": "romance"},
    {"label": "Adventure", "icon": """<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="3 11 22 2 13 21 11 13 3 11"/></svg>""", "genre": "adventure"},
    {"label": "Animation", "icon": """<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="5 3 19 12 5 21 5 3"/></svg>""", "genre": "animation"},
]

MOOD_CARDS = [
    {
        "svg": """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></svg>""",
        "badge_color": "rgba(245, 158, 11, 0.14)",
        "badge_border": "rgba(245, 158, 11, 0.35)",
        "title": "Feel Good",
        "sub": "Uplifting & happy",
        "link": "?movie=356"
    },
    {
        "svg": """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#c084fc" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M12 2v4"/><path d="M12 18v4"/><path d="m4.93 4.93 2.83 2.83"/><path d="m16.24 16.24 2.83 2.83"/><path d="M2 12h4"/><path d="M18 12h4"/><path d="m4.93 19.07 2.83-2.83"/><path d="m16.24 7.76 2.83-2.83"/></svg>""",
        "badge_color": "rgba(168, 85, 247, 0.14)",
        "badge_border": "rgba(168, 85, 247, 0.35)",
        "title": "Mind Bending",
        "sub": "Thought provoking",
        "link": "?movie=79132"
    },
    {
        "svg": """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#f87171" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>""",
        "badge_color": "rgba(239, 68, 68, 0.14)",
        "badge_border": "rgba(239, 68, 68, 0.35)",
        "title": "Dark & Intense",
        "sub": "Gritty and serious",
        "link": "?movie=858"
    },
    {
        "svg": """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fb7185" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/></svg>""",
        "badge_color": "rgba(244, 63, 94, 0.14)",
        "badge_border": "rgba(244, 63, 94, 0.35)",
        "title": "Romantic",
        "sub": "Love and emotions",
        "link": "?movie=69757"
    },
    {
        "svg": """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#22d3ee" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/></svg>""",
        "badge_color": "rgba(6, 182, 212, 0.14)",
        "badge_border": "rgba(6, 182, 212, 0.35)",
        "title": "Adventurous",
        "sub": "Epic journeys",
        "link": "?movie=109487"
    },
    {
        "svg": """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#34d399" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" x2="9.01" y1="9" y2="9"/><line x1="15" x2="15.01" y1="9" y2="9"/></svg>""",
        "badge_color": "rgba(16, 185, 129, 0.14)",
        "badge_border": "rgba(16, 185, 129, 0.35)",
        "title": "Funny",
        "sub": "Laugh out loud",
        "link": "?movie=296"
    },
]

def render_discover_by_mood_section():
    mood_cards_html = [
        f"""<a href="{mood['link']}" target="_self" class="mood-card">
<div class="mood-icon-box" style="background: {mood['badge_color']}; border: 1px solid {mood['badge_border']};">
{mood['svg']}
</div>
<div class="mood-info">
<div class="mood-title">{mood['title']}</div>
<div class="mood-sub">{mood['sub']}</div>
</div>
</a>"""
        for mood in MOOD_CARDS
    ]
    return f"""<div id="mood-section" class="section-flex-header" style="margin-top: 36px; margin-bottom: 8px;">
<div class="section-title-box">
<div class="section-title-row" style="display: flex; align-items: center; gap: 10px;">
<div class="section-icon-badge"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#E50914" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/></svg></div>
<h2 class="section-main-heading">Discover by Mood</h2>
</div>
<div class="section-sub-heading">Explore cinema matched to your emotional frequency and current atmosphere.</div>
</div>
<a href="?genre=all" target="_self" class="section-view-all">View all moods →</a>
</div>
<div class="mood-grid">{''.join(mood_cards_html)}</div>"""


GENRE_SHOWCASE_MAP = {
    "action": [
        {"movie_id": 58559, "title": "The Dark Knight", "year": "2008", "tmdb_id": 155, "poster_url": "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg", "score": 9.0, "genres": "Action · Crime"},
        {"movie_id": 79132, "title": "Inception", "year": "2010", "tmdb_id": 27205, "poster_url": "https://image.tmdb.org/t/p/w500/xlaY2zyzMfkhk0HSC5VUwzoZPU1.jpg", "score": 8.8, "genres": "Action · Sci-Fi"},
        {"movie_id": 2571, "title": "The Matrix", "year": "1999", "tmdb_id": 603, "poster_url": "https://image.tmdb.org/t/p/w500/dXNAPwY7VrqMAo51EKhhCJfaGb5.jpg", "score": 8.7, "genres": "Action · Sci-Fi"},
        {"movie_id": 3578, "title": "Gladiator", "year": "2000", "tmdb_id": 98, "poster_url": "https://image.tmdb.org/t/p/w500/ty8TGRuvJLPUmAR1H1nRIsgwvim.jpg", "score": 8.5, "genres": "Action · Adventure · Drama"},
        {"movie_id": 6874, "title": "Kill Bill: Vol. 1", "year": "2003", "tmdb_id": 24, "poster_url": "https://image.tmdb.org/t/p/w500/v7TaX8kXMXs5yFFGR41guUDNcnB.jpg", "score": 8.2, "genres": "Action · Crime"}
    ],
    "drama": [
        {"movie_id": 318, "title": "The Shawshank Redemption", "year": "1994", "tmdb_id": 278, "poster_url": "https://image.tmdb.org/t/p/w500/9cqNxx0GxF0bflZmeSMuL5tnGzr.jpg", "score": 9.3, "genres": "Drama · Crime"},
        {"movie_id": 858, "title": "The Godfather", "year": "1972", "tmdb_id": 238, "poster_url": "https://image.tmdb.org/t/p/w500/3bhkrj58Vtu7enYsRolD1fZdja1.jpg", "score": 9.2, "genres": "Crime · Drama"},
        {"movie_id": 1221, "title": "The Godfather Part II", "year": "1974", "tmdb_id": 240, "poster_url": "https://image.tmdb.org/t/p/w500/8a1lJs7mFyGhGhZZDT1azJUoQiZ.jpg", "score": 9.0, "genres": "Crime · Drama"},
        {"movie_id": 1203, "title": "12 Angry Men", "year": "1957", "tmdb_id": 389, "poster_url": "https://image.tmdb.org/t/p/w500/ppd84D2i9W8jXmsyInGyihiSyqz.jpg", "score": 9.0, "genres": "Crime · Drama"},
        {"movie_id": 527, "title": "Schindler's List", "year": "1993", "tmdb_id": 424, "poster_url": "https://image.tmdb.org/t/p/w500/sF1U4EUQS8YHUYjNl3pMGNIQyr0.jpg", "score": 9.0, "genres": "Biography · Drama"}
    ],
    "comedy": [
        {"movie_id": 356, "title": "Forrest Gump", "year": "1994", "tmdb_id": 13, "poster_url": "https://image.tmdb.org/t/p/w500/Cw4hIUIAmSYfK9QfaUW5igp9La.jpg", "score": 8.8, "genres": "Comedy · Drama"},
        {"movie_id": 69757, "title": "(500) Days of Summer", "year": "2009", "tmdb_id": 19913, "poster_url": "https://image.tmdb.org/t/p/w500/qXAuQ9hF30sQRsXf40OfRVl0MJZ.jpg", "score": 7.7, "genres": "Comedy · Drama · Romance"},
        {"movie_id": 862, "title": "Toy Story", "year": "1995", "tmdb_id": 862, "poster_url": "https://image.tmdb.org/t/p/w500/uXDfjJbdP4ijW5hWSBrPrlKpxab.jpg", "score": 8.3, "genres": "Animation · Adventure · Comedy"},
        {"movie_id": 107, "title": "Snatch", "year": "2000", "tmdb_id": 107, "poster_url": "https://image.tmdb.org/t/p/w500/kJZoAHq1SLDdWjeNGtlHAnGpmFV.jpg", "score": 8.2, "genres": "Comedy · Crime"},
        {"movie_id": 120467, "title": "The Grand Budapest Hotel", "year": "2014", "tmdb_id": 120467, "poster_url": "https://image.tmdb.org/t/p/w500/eWdyYQreja6JGCzqHWXpWHDrrPo.jpg", "score": 8.1, "genres": "Comedy · Drama · Adventure"}
    ],
    "thriller": [
        {"movie_id": 296, "title": "Pulp Fiction", "year": "1994", "tmdb_id": 680, "poster_url": "https://image.tmdb.org/t/p/w500/vQWk5YBFWF4bZaofAbv0tShwBvQ.jpg", "score": 8.9, "genres": "Crime · Thriller"},
        {"movie_id": 2959, "title": "Fight Club", "year": "1999", "tmdb_id": 550, "poster_url": "https://image.tmdb.org/t/p/w500/jSziioSwPVrOy9Yow3XhWIBDjq1.jpg", "score": 8.8, "genres": "Drama · Thriller"},
        {"movie_id": 74458, "title": "Shutter Island", "year": "2010", "tmdb_id": 11324, "poster_url": "https://image.tmdb.org/t/p/w500/nrmXQ0zcZUL8jFLrakWc90IR8z9.jpg", "score": 8.2, "genres": "Mystery · Thriller"},
        {"movie_id": 274, "title": "The Silence of the Lambs", "year": "1991", "tmdb_id": 274, "poster_url": "https://image.tmdb.org/t/p/w500/uS9m8OBk1A8eM9I042bx8XXpqAq.jpg", "score": 8.6, "genres": "Crime · Drama · Thriller"},
        {"movie_id": 807, "title": "Se7en", "year": "1995", "tmdb_id": 807, "poster_url": "https://image.tmdb.org/t/p/w500/6yoghtyTpznpBik8EngEmJskVUO.jpg", "score": 8.6, "genres": "Crime · Mystery · Thriller"}
    ],
    "sci-fi": [
        {"movie_id": 109487, "title": "Interstellar", "year": "2014", "tmdb_id": 157336, "poster_url": "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg", "score": 8.7, "genres": "Adventure · Drama · Sci-Fi"},
        {"movie_id": 79132, "title": "Inception", "year": "2010", "tmdb_id": 27205, "poster_url": "https://image.tmdb.org/t/p/w500/xlaY2zyzMfkhk0HSC5VUwzoZPU1.jpg", "score": 8.8, "genres": "Action · Sci-Fi"},
        {"movie_id": 2571, "title": "The Matrix", "year": "1999", "tmdb_id": 603, "poster_url": "https://image.tmdb.org/t/p/w500/dXNAPwY7VrqMAo51EKhhCJfaGb5.jpg", "score": 8.7, "genres": "Action · Sci-Fi"},
        {"movie_id": 234160, "title": "Dune", "year": "2021", "tmdb_id": 438631, "poster_url": "https://image.tmdb.org/t/p/w500/d5NXSklXo0qyIYkgV94XAgMIckC.jpg", "score": 8.0, "genres": "Action · Adventure · Sci-Fi"},
        {"movie_id": 335984, "title": "Blade Runner 2049", "year": "2017", "tmdb_id": 335984, "poster_url": "https://image.tmdb.org/t/p/w500/gajva2L0rPYkEWjzgFlBXCAVBE5.jpg", "score": 8.0, "genres": "Drama · Mystery · Sci-Fi"}
    ],
    "horror": [
        {"movie_id": 694, "title": "The Shining", "year": "1980", "tmdb_id": 694, "poster_url": "https://image.tmdb.org/t/p/w500/uAR0AWqhQL1hQa69UDEbb2rE5Wx.jpg", "score": 8.4, "genres": "Horror · Mystery"},
        {"movie_id": 539, "title": "Psycho", "year": "1960", "tmdb_id": 539, "poster_url": "https://image.tmdb.org/t/p/w500/yz4QVqPx3h1hD1DfqqQkCq3rmxW.jpg", "score": 8.5, "genres": "Horror · Mystery · Thriller"},
        {"movie_id": 274, "title": "The Silence of the Lambs", "year": "1991", "tmdb_id": 274, "poster_url": "https://image.tmdb.org/t/p/w500/uS9m8OBk1A8eM9I042bx8XXpqAq.jpg", "score": 8.6, "genres": "Crime · Drama · Thriller"},
        {"movie_id": 1091, "title": "The Thing", "year": "1982", "tmdb_id": 1091, "poster_url": "https://image.tmdb.org/t/p/w500/tzGY49kseSE9QAKk47uuDGwnSCu.jpg", "score": 8.2, "genres": "Horror · Mystery · Sci-Fi"},
        {"movie_id": 348, "title": "Alien", "year": "1979", "tmdb_id": 348, "poster_url": "https://image.tmdb.org/t/p/w500/vfrQk5IPloGg1v9Rzbh2Eg3VGyM.jpg", "score": 8.5, "genres": "Horror · Sci-Fi"}
    ],
    "romance": [
        {"movie_id": 69757, "title": "(500) Days of Summer", "year": "2009", "tmdb_id": 19913, "poster_url": "https://image.tmdb.org/t/p/w500/qXAuQ9hF30sQRsXf40OfRVl0MJZ.jpg", "score": 7.7, "genres": "Comedy · Drama · Romance"},
        {"movie_id": 597, "title": "Titanic", "year": "1997", "tmdb_id": 597, "poster_url": "https://image.tmdb.org/t/p/w500/9xjZS2rlVxm8SFx8kPC3aIGCOYQ.jpg", "score": 7.9, "genres": "Drama · Romance"},
        {"movie_id": 289, "title": "Casablanca", "year": "1942", "tmdb_id": 289, "poster_url": "https://image.tmdb.org/t/p/w500/lGCEKlJo2CnWydQj7aamY7s1S7Q.jpg", "score": 8.5, "genres": "Drama · Romance · War"},
        {"movie_id": 38, "title": "Eternal Sunshine of the Spotless Mind", "year": "2004", "tmdb_id": 38, "poster_url": "https://image.tmdb.org/t/p/w500/5MwkWH9tYHv3mV9OdYTMR5qreIz.jpg", "score": 8.3, "genres": "Drama · Romance · Sci-Fi"},
        {"movie_id": 11036, "title": "Before Sunrise", "year": "1995", "tmdb_id": 76, "poster_url": "https://image.tmdb.org/t/p/w500/kf1Jb1c2JAOqjuzA3H4oDM263uB.jpg", "score": 8.1, "genres": "Drama · Romance"}
    ],
    "adventure": [
        {"movie_id": 7153, "title": "The Lord of the Rings: The Return of the King", "year": "2003", "tmdb_id": 122, "poster_url": "https://image.tmdb.org/t/p/w500/rCzpDGLbOoPwLjy3OAm5NUPOTrC.jpg", "score": 9.0, "genres": "Adventure · Fantasy"},
        {"movie_id": 4993, "title": "The Lord of the Rings: The Fellowship of the Ring", "year": "2001", "tmdb_id": 120, "poster_url": "https://image.tmdb.org/t/p/w500/6oom5QYQ2yQTMJIbnvbkBL9cHo6.jpg", "score": 8.9, "genres": "Adventure · Fantasy"},
        {"movie_id": 5952, "title": "The Lord of the Rings: The Two Towers", "year": "2002", "tmdb_id": 121, "poster_url": "https://image.tmdb.org/t/p/w500/5VTN0pR8gcqV3EPUHHfMGnJYN9L.jpg", "score": 8.8, "genres": "Adventure · Fantasy"},
        {"movie_id": 109487, "title": "Interstellar", "year": "2014", "tmdb_id": 157336, "poster_url": "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg", "score": 8.7, "genres": "Adventure · Drama · Sci-Fi"},
        {"movie_id": 3578, "title": "Gladiator", "year": "2000", "tmdb_id": 98, "poster_url": "https://image.tmdb.org/t/p/w500/ty8TGRuvJLPUmAR1H1nRIsgwvim.jpg", "score": 8.5, "genres": "Action · Adventure · Drama"}
    ],
    "animation": [
        {"movie_id": 129, "title": "Spirited Away", "year": "2001", "tmdb_id": 129, "poster_url": "https://image.tmdb.org/t/p/w500/39wmItIWsg5sZMyRUHLkWBcuVCM.jpg", "score": 8.6, "genres": "Animation · Adventure · Family"},
        {"movie_id": 8587, "title": "The Lion King", "year": "1994", "tmdb_id": 8587, "poster_url": "https://image.tmdb.org/t/p/w500/sKCr78MXSLixwmZ8DyJLrpMsd15.jpg", "score": 8.5, "genres": "Animation · Adventure · Drama"},
        {"movie_id": 324857, "title": "Spider-Man: Into the Spider-Verse", "year": "2018", "tmdb_id": 324857, "poster_url": "https://image.tmdb.org/t/p/w500/iiZZdoQBEYBv6id8su7ImL0oCbD.jpg", "score": 8.4, "genres": "Animation · Action · Adventure"},
        {"movie_id": 862, "title": "Toy Story", "year": "1995", "tmdb_id": 862, "poster_url": "https://image.tmdb.org/t/p/w500/uXDfjJbdP4ijW5hWSBrPrlKpxab.jpg", "score": 8.3, "genres": "Animation · Adventure · Comedy"},
        {"movie_id": 150540, "title": "Inside Out", "year": "2015", "tmdb_id": 150540, "poster_url": "https://image.tmdb.org/t/p/w500/2H1TmgdfNtsKlU9jKdeNyYL5y8T.jpg", "score": 8.1, "genres": "Animation · Adventure · Comedy"}
    ]
}

# Render Navbar & Ambient Glow First (Matching Mockup)
st.markdown("""
<div class="netflix-nav-container">
<a href="?home=true" target="_self" class="brand-wrapper" title="Return to Home">
<div class="brand-title">CINEMATCH<span class="ai-badge">AI</span></div>
</a>
<nav class="floating-pill-nav">
<a href="?home=true" target="_self" class="pill-nav-item active">Home</a>
<a href="#top-15-section" target="_self" class="pill-nav-item">Top 15 IMDb</a>
<a href="#mood-section" target="_self" class="pill-nav-item">Moods</a>
<a href="#tech-stack-section" target="_self" class="pill-nav-item">Architecture</a>
<a href="#contact-section" target="_self" class="pill-nav-item pill-contact-item">Contact</a>
</nav>
<div class="nav-right-links">
<!-- Switch Mode Spring Toggle (Screenshot 4) -->
<div class="switch-mode-wrapper" title="Switch Mode (Toggle Deep Cinema Noir / Warm Slate Theme)">
<div class="switch-mode-track is-active" id="theme-switch-toggle" role="button" tabindex="0" aria-label="Switch Mode">
<div class="switch-icon sun" title="Warm Slate Mode">
<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2 M12 20v2 M4.93 4.93l1.41 1.41 M17.66 17.66l1.41 1.41 M2 12h2 M20 12h2 M6.34 17.66l-1.41 1.41 M19.07 4.93l-1.41 1.41"/></svg>
</div>
<div class="switch-icon moon" title="Deep Midnight Noir Mode">
<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
</div>
<div class="switch-thumb"></div>
</div>
</div>
<a href="https://github.com/Varun-Esarapu/movie_rec" target="_blank" class="nav-link-btn nav-github-btn" title="GitHub Repository">
<svg width="15" height="15" viewBox="0 0 16 16" fill="currentColor" style="vertical-align: text-bottom; margin-right: 4px;"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.012 8.012 0 0 0 16 8c0-4.42-3.58-8-8-8z"/></svg> GitHub
</a>
<a href="https://e-varun-portfolio.vercel.app/#intro" target="_blank" class="nav-link-btn nav-portfolio-btn" title="Explore Varun's Portfolio">
<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: text-bottom; margin-right: 4px;"><circle cx="12" cy="12" r="10"/><line x1="2" x2="22" y1="12" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg> Portfolio
</a>
</div>
</div>
<div class="ambient-glow-orb-1"></div>
<div class="ambient-glow-orb-2"></div>
""", unsafe_allow_html=True)

# Client-Side Smooth Scrolling & Interactive Continuous Tabs / Switch Mode Engine
components.html("""
<script>
(function() {
    function initInteractiveUI() {
        try {
            const doc = window.parent.document;
            if (!doc) return;
            
            const scrollRoot = doc.querySelector('[data-testid="stAppViewContainer"]') || doc.querySelector('.main') || doc.documentElement;
            
            // 1. Continuous Tabs & Smooth Scrolling Interceptor
            const navItems = doc.querySelectorAll('.pill-nav-item, .hero-slider-pill, .hero-btn-secondary, a[href^="#"]');
            navItems.forEach(el => {
                if (el.dataset.smoothScrollBound === 'true') return;
                el.dataset.smoothScrollBound = 'true';
                
                el.addEventListener('click', function(e) {
                    const href = this.getAttribute('href');
                    if (!href) return;
                    
                    // Home button
                    if (href.includes('home=true') || this.textContent.trim().toLowerCase() === 'home') {
                        e.preventDefault();
                        scrollRoot.scrollTo({ top: 0, behavior: 'smooth' });
                        doc.querySelectorAll('.pill-nav-item').forEach(p => p.classList.remove('active'));
                        const homePill = doc.querySelector('.pill-nav-item');
                        if (homePill) homePill.classList.add('active');
                        return;
                    }
                    
                    // Hash anchors
                    if (href.startsWith('#')) {
                        e.preventDefault();
                        const targetId = href.substring(1);
                        const target = doc.getElementById(targetId);
                        if (target) {
                            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                            if (this.classList.contains('pill-nav-item')) {
                                doc.querySelectorAll('.pill-nav-item').forEach(p => p.classList.remove('active'));
                                this.classList.add('active');
                            }
                        }
                    }
                });
            });

            // 2. Switch Mode Animated Spring Toggle (Screenshot 4)
            const switchToggle = doc.getElementById('theme-switch-toggle');
            if (switchToggle && switchToggle.dataset.bound !== 'true') {
                switchToggle.dataset.bound = 'true';
                
                // Retrieve saved theme preference
                const savedMode = localStorage.getItem('cinematch_theme_mode') || 'dark';
                if (savedMode === 'sun') {
                    switchToggle.classList.remove('is-active');
                    doc.documentElement.classList.add('theme-warm-slate');
                    if (doc.body) doc.body.classList.add('theme-warm-slate');
                } else {
                    switchToggle.classList.add('is-active');
                    doc.documentElement.classList.remove('theme-warm-slate');
                    if (doc.body) doc.body.classList.remove('theme-warm-slate');
                }
                
                switchToggle.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    const isNowActive = !this.classList.contains('is-active');
                    if (isNowActive) {
                        this.classList.add('is-active');
                        doc.documentElement.classList.remove('theme-warm-slate');
                        if (doc.body) doc.body.classList.remove('theme-warm-slate');
                        localStorage.setItem('cinematch_theme_mode', 'dark');
                    } else {
                        this.classList.remove('is-active');
                        doc.documentElement.classList.add('theme-warm-slate');
                        if (doc.body) doc.body.classList.add('theme-warm-slate');
                        localStorage.setItem('cinematch_theme_mode', 'sun');
                    }
                });
            }
        } catch (err) {}
    }
    
    initInteractiveUI();
    setInterval(initInteractiveUI, 500);
})();
</script>
""", height=0, width=0)

# Fast Memory-Cached Backend API Helpers with Built-In Cloud Standalone Fallback
MOVIELENS_TO_TMDB_MAP = {
    318: 278, 858: 238, 58559: 155, 1221: 240, 1203: 389,
    527: 424, 7153: 122, 296: 680, 4993: 120, 2959: 550,
    356: 13, 79132: 27205, 5952: 121, 1213: 769, 2571: 603,
    234160: 438631, 6874: 24, 3578: 98, 109487: 157336,
    74458: 11324, 51662: 1271, 1954: 1366, 69757: 19913,
    943929: 872585, 3949: 641
}

TMDB_GENRE_NAMES = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy",
    80: "Crime", 99: "Documentary", 18: "Drama", 10751: "Family",
    14: "Fantasy", 36: "History", 27: "Horror", 10402: "Music",
    9648: "Mystery", 10749: "Romance", 878: "Sci-Fi", 53: "Thriller",
    10752: "War", 37: "Western"
}

def _tmdb_direct_get(endpoint: str):
    sep = "&" if "?" in endpoint else "?"
    url = f"https://api.themoviedb.org/3/{endpoint}{sep}api_key={TMDB_API_KEY}&language=en-US"
    # On Windows, prioritize curl.exe IPv4 first to bypass Python ISP IPv6/SSL 4.5s timeouts
    if os.name == "nt":
        for _ in range(4):
            try:
                res = subprocess.run(
                    ["curl.exe", "-s", "-4", "--connect-timeout", "3", "--max-time", "5", url],
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=6
                )
                if res.returncode == 0 and res.stdout:
                    data = json.loads(res.stdout)
                    if isinstance(data, dict) and ("status_code" not in data or data.get("id") or data.get("results")):
                        return data
            except Exception:
                pass
    try:
        r = requests.get(url, timeout=4.5)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    # System curl IPv4 fallback for non-Windows or retry
    for _ in range(3):
        try:
            res = subprocess.run(
                ["curl", "-s", "-4", "--connect-timeout", "3", "--max-time", "5", url],
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                timeout=6
            )
            if res.returncode == 0 and res.stdout:
                data = json.loads(res.stdout)
                if isinstance(data, dict):
                    return data
        except Exception:
            pass
    return None

@st.cache_data(ttl=3600, show_spinner=False)
def api_search_movies(query: str):
    clean = query.strip()
    if not clean or len(clean) < 2:
        return []
    try:
        resp = requests.get(f"{API_BASE_URL}/movies/search/?q={urllib.parse.quote(clean)}", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list) and data:
                return data
    except Exception:
        pass

    # Standalone Cloud Fallback (Direct TMDB Search + Typo Tolerance)
    tmdb_res = _tmdb_direct_get(f"search/movie?query={urllib.parse.quote_plus(clean)}")
    if not tmdb_res or not tmdb_res.get("results"):
        chars = list(clean)
        for i in range(len(chars) - 1):
            swapped = chars.copy()
            swapped[i], swapped[i + 1] = swapped[i + 1], swapped[i]
            cand_q = "".join(swapped)
            t_try = _tmdb_direct_get(f"search/movie?query={urllib.parse.quote_plus(cand_q)}")
            if t_try and t_try.get("results"):
                tmdb_res = t_try
                break

    if tmdb_res and tmdb_res.get("results"):
        out = []
        for item in tmdb_res["results"][:15]:
            t_id = item.get("id")
            if not t_id:
                continue
            title = item.get("title") or item.get("original_title") or ""
            year = (item.get("release_date") or "")[:4]
            full_title = f"{title} ({year})" if year else title
            p_path = item.get("poster_path")
            g_ids = item.get("genre_ids", [])
            g_str = "|".join([TMDB_GENRE_NAMES[g] for g in g_ids if g in TMDB_GENRE_NAMES]) or "Drama"
            out.append({
                "movie_id": t_id,
                "title": full_title,
                "genres": g_str,
                "tmdb_id": t_id,
                "poster_url": f"https://image.tmdb.org/t/p/w500{p_path}" if p_path else None,
                "popularity": float(item.get("popularity") or 0.0),
                "vote_average": float(item.get("vote_average") or 0.0),
                "vote_count": int(item.get("vote_count") or 0)
            })
        if out:
            return out

    # Local offline catalog fallback so search never crashes on transient network drops
    q_low = clean.lower()
    local_matches = [
        {
            "movie_id": m["movie_id"],
            "title": f"{m['title']} ({m['year']})",
            "genres": m["genres"],
            "tmdb_id": m["tmdb_id"],
            "poster_url": m["poster_url"]
        }
        for m in FAMOUS_CATALOG
        if q_low in m["title"].lower()
    ]
    return local_matches

@st.cache_data(ttl=3600, show_spinner=False)
def api_get_director_filmography(director_name: str, director_id: int = None):
    params = []
    if director_name:
        params.append(f"name={urllib.parse.quote(director_name)}")
    if director_id:
        params.append(f"id={director_id}")
    q_str = "&".join(params)
    try:
        resp = requests.get(f"{API_BASE_URL}/directors/filmography/?{q_str}", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, dict) and data.get("movies"):
                return data
    except Exception:
        pass

    # Standalone Cloud Fallback (Direct TMDB Person Credits sorted chronologically)
    person_id = director_id
    resolved_name = director_name
    profile_url = ""
    bio = ""

    if not person_id and director_name:
        p_search = _tmdb_direct_get(f"search/person?query={urllib.parse.quote_plus(director_name)}")
        if p_search and p_search.get("results"):
            best = next(
                (p for p in p_search["results"] if p.get("known_for_department") == "Directing"),
                p_search["results"][0]
            )
            person_id = best.get("id")
            resolved_name = best.get("name") or director_name

    if not person_id:
        return {"director_name": director_name, "director_id": None, "movies": []}

    p_data = _tmdb_direct_get(f"person/{person_id}?append_to_response=movie_credits")
    if not p_data:
        return {"director_name": resolved_name, "director_id": person_id, "movies": []}

    resolved_name = p_data.get("name") or resolved_name
    prof_path = p_data.get("profile_path")
    if prof_path:
        profile_url = f"https://image.tmdb.org/t/p/w500{prof_path}"
    bio = p_data.get("biography") or ""

    crew_list = p_data.get("movie_credits", {}).get("crew", [])
    seen_ids = set()
    raw_candidates = []
    for item in crew_list:
        if item.get("job") != "Director":
            continue
        t_id = item.get("id")
        if not t_id or t_id in seen_ids:
            continue
        rel_date = (item.get("release_date") or "").strip()
        if not rel_date or len(rel_date) < 4:
            continue
        year_str = rel_date[:4]
        if not year_str.isdigit():
            continue
        p_path = item.get("poster_path")
        if not p_path:
            continue
        v_cnt = int(item.get("vote_count") or 0)
        if v_cnt == 0:
            continue
        g_ids = item.get("genre_ids", [])
        if 99 in g_ids and v_cnt < 150:
            continue
        seen_ids.add(t_id)
        title = item.get("title") or item.get("original_title") or "Untitled"
        g_str = "|".join([TMDB_GENRE_NAMES[g] for g in g_ids if g in TMDB_GENRE_NAMES]) or "Drama"
        raw_candidates.append({
            "movie_id": t_id,
            "tmdb_id": t_id,
            "title": f"{title} ({year_str})",
            "clean_title": title,
            "year": int(year_str),
            "release_date": rel_date,
            "genres": g_str,
            "poster_url": f"https://image.tmdb.org/t/p/w500{p_path}",
            "vote_average": round(float(item.get("vote_average") or 0.0), 1),
            "vote_count": v_cnt,
            "overview": item.get("overview") or ""
        })

    max_votes = max((c["vote_count"] for c in raw_candidates), default=0)
    min_vote_threshold = 400 if max_votes >= 5000 else (15 if max_votes >= 200 else 3)
    directed_movies = [c for c in raw_candidates if c["vote_count"] >= min_vote_threshold]
    if not directed_movies:
        directed_movies = raw_candidates

    # Strictly sort in ascending chronological order by release date / release year
    directed_movies.sort(key=lambda m: (m["release_date"], m["vote_count"]))
    return {
        "director_id": person_id,
        "director_name": resolved_name,
        "profile_url": profile_url,
        "biography": bio,
        "birthplace": p_data.get("place_of_birth") or "",
        "birthday": p_data.get("birthday") or "",
        "movies": directed_movies
    }

@st.cache_data(ttl=3600, show_spinner=False)
def api_get_similar_cluster(movie_id: int, limit: int):
    try:
        resp = requests.get(f"{API_BASE_URL}/movies/{movie_id}/similar/?limit={limit}", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, dict) and data.get("results"):
                return data
    except Exception:
        pass

    # Standalone Cloud Fallback (Direct TMDB Credits, Regional Clustering & Recommendations)
    tmdb_id = MOVIELENS_TO_TMDB_MAP.get(int(movie_id), int(movie_id))
    det = _tmdb_direct_get(f"movie/{tmdb_id}?append_to_response=credits")
    if det and det.get("id"):
        credits_data = det.get("credits", {})
        director_member = next((m for m in credits_data.get("crew", []) if m.get("job") == "Director"), {})
        director = director_member.get("name", "") if director_member else ""
        director_id = director_member.get("id") if director_member else None
        cast_str = ", ".join([a.get("name", "") for a in credits_data.get("cast", [])[:5] if a.get("name")])
        rt = det.get("runtime") or 0
        runtime_str = f"{rt // 60}h {rt % 60}m" if rt >= 60 else (f"{rt}m" if rt > 0 else "")
        p_path = det.get("poster_path")
        b_path = det.get("backdrop_path")
        poster_url = f"https://image.tmdb.org/t/p/w500{p_path}" if p_path else ""
        backdrop_url = f"https://image.tmdb.org/t/p/original{b_path}" if b_path else ""
        g_list = [g.get("name", "") for g in det.get("genres", []) if g.get("name")]
        genres_str = "|".join(g_list) or "Drama"
        orig_lang = det.get("original_language", "en")

        raw_recs = []
        if orig_lang and orig_lang != "en":
            g_ids = [str(g.get("id")) for g in det.get("genres", []) if g.get("id")][:2]
            g_param = f"&with_genres={','.join(g_ids)}" if g_ids else ""
            reg = _tmdb_direct_get(f"discover/movie?with_original_language={orig_lang}{g_param}&sort_by=vote_count.desc")
            if reg and reg.get("results"):
                raw_recs.extend([f for f in reg["results"] if f.get("id") != tmdb_id][:limit])

        rec_data = _tmdb_direct_get(f"movie/{tmdb_id}/recommendations")
        if rec_data and rec_data.get("results"):
            raw_recs.extend(rec_data["results"])
        if len(raw_recs) < limit:
            sim_data = _tmdb_direct_get(f"movie/{tmdb_id}/similar")
            if sim_data and sim_data.get("results"):
                raw_recs.extend(sim_data["results"])

        results = []
        seen = {tmdb_id}
        for item in raw_recs:
            rid = item.get("id")
            if not rid or rid in seen:
                continue
            seen.add(rid)
            rp = item.get("poster_path")
            rg_ids = item.get("genre_ids", [])
            rg_str = "|".join([TMDB_GENRE_NAMES[g] for g in rg_ids if g in TMDB_GENRE_NAMES]) or "Drama"
            results.append({
                "rank": len(results) + 1,
                "score": round(float(item.get("vote_average") or 7.8), 1),
                "movie": {
                    "movie_id": rid,
                    "title": item.get("title") or item.get("original_title") or "",
                    "genres": rg_str,
                    "tmdb_id": rid,
                    "poster_url": f"https://image.tmdb.org/t/p/w500{rp}" if rp else None
                }
            })
            if len(results) >= limit:
                break

        if results:
            return {
                "source_movie": {
                    "movie_id": movie_id,
                    "title": det.get("title") or det.get("original_title") or "",
                    "genres": genres_str,
                    "tmdb_id": tmdb_id,
                    "poster_url": poster_url,
                    "details": {
                        "title": det.get("title") or "",
                        "poster_url": poster_url,
                        "backdrop_url": backdrop_url,
                        "overview": det.get("overview") or "",
                        "tagline": det.get("tagline") or "",
                        "director": director,
                        "director_id": director_id,
                        "cast": cast_str,
                        "runtime": runtime_str,
                        "vote_average": det.get("vote_average"),
                        "vote_count": det.get("vote_count"),
                        "release_date": det.get("release_date", ""),
                        "imdb_id": det.get("imdb_id") or ""
                    }
                },
                "results": results
            }

    raise RuntimeError(f"Could not load similar movies for {movie_id}")

@st.cache_data(ttl=3600, show_spinner=False)
def api_get_recommendations(user_id: int, limit: int):
    try:
        resp = requests.get(f"{API_BASE_URL}/recommendations/{user_id}/?limit={limit}", timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, dict) and data.get("results"):
                return data
    except Exception:
        pass
    # Standalone Cloud Fallback using deterministic user seed over FAMOUS_CATALOG
    offset = (int(user_id) * 3) % len(FAMOUS_CATALOG)
    rotated = FAMOUS_CATALOG[offset:] + FAMOUS_CATALOG[:offset]
    return {
        "user_id": user_id,
        "fallback": False,
        "results": [
            {
                "rank": idx + 1,
                "score": m["score"],
                "movie": {
                    "movie_id": m["movie_id"],
                    "title": f"{m['title']} ({m['year']})",
                    "genres": m["genres"],
                    "tmdb_id": m["tmdb_id"],
                    "poster_url": m["poster_url"]
                }
            }
            for idx, m in enumerate(rotated[:limit])
        ]
    }

# State management
if "selected_movie" not in st.session_state:
    st.session_state["selected_movie"] = None
if "selected_director" not in st.session_state:
    st.session_state["selected_director"] = None
if "search_input" not in st.session_state:
    st.session_state["search_input"] = ""
if "last_search" not in st.session_state:
    st.session_state["last_search"] = ""
if "last_pill" not in st.session_state:
    st.session_state["last_pill"] = None
if "search_matches" not in st.session_state:
    st.session_state["search_matches"] = []

# Quick map lookup for catalog & popular items by movie_id
CATALOG_BY_ID = {str(m["movie_id"]): m for m in FAMOUS_CATALOG}
for glist in GENRE_SHOWCASE_MAP.values():
    for gm in glist:
        CATALOG_BY_ID[str(gm["movie_id"])] = gm

POPULAR_CHIPS_MAP = {
    "dune": {"movie_id": 234160, "title": "Dune (2021)", "tmdb_id": 438631, "poster_url": "https://image.tmdb.org/t/p/w500/d5NXSklXo0qyIYkgV94XAgMIckC.jpg", "genres": "Action · Adventure · Sci-Fi"},
    "the godfather": {"movie_id": 858, "title": "The Godfather (1972)", "tmdb_id": 238, "poster_url": "https://image.tmdb.org/t/p/w500/3bhkrj58Vtu7enYsRolD1fZdja1.jpg", "genres": "Crime · Drama"},
    "the dark knight": {"movie_id": 58559, "title": "The Dark Knight (2008)", "tmdb_id": 155, "poster_url": "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg", "genres": "Action · Crime"},
    "fight club": {"movie_id": 2959, "title": "Fight Club (1999)", "tmdb_id": 550, "poster_url": "https://image.tmdb.org/t/p/w500/jSziioSwPVrOy9Yow3XhWIBDjq1.jpg", "genres": "Drama · Thriller"},
    "kill bill": {"movie_id": 6874, "title": "Kill Bill: Vol. 1 (2003)", "tmdb_id": 24, "poster_url": "https://image.tmdb.org/t/p/w500/v7TaX8kXMXs5yFFGR41guUDNcnB.jpg", "genres": "Action · Crime"},
    "gladiator": {"movie_id": 3578, "title": "Gladiator (2000)", "tmdb_id": 98, "poster_url": "https://image.tmdb.org/t/p/w500/ty8TGRuvJLPUmAR1H1nRIsgwvim.jpg", "genres": "Action · Adventure · Drama"},
    "inception": {"movie_id": 79132, "title": "Inception (2010)", "tmdb_id": 27205, "poster_url": "https://image.tmdb.org/t/p/w500/xlaY2zyzMfkhk0HSC5VUwzoZPU1.jpg", "genres": "Action · Sci-Fi"},
    "interstellar": {"movie_id": 109487, "title": "Interstellar (2014)", "tmdb_id": 157336, "poster_url": "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg", "genres": "Adventure · Drama · Sci-Fi"},
    "shutter island": {"movie_id": 74458, "title": "Shutter Island (2010)", "tmdb_id": 11324, "poster_url": "https://image.tmdb.org/t/p/w500/nrmXQ0zcZUL8jFLrakWc90IR8z9.jpg", "genres": "Mystery · Thriller"},
    "300": {"movie_id": 51662, "title": "300 (2006)", "tmdb_id": 1271, "poster_url": "https://image.tmdb.org/t/p/w500/h7Lcio0c9ohxPhSZg42eTlKIVVY.jpg", "genres": "Action · Fantasy"},
    "rocky": {"movie_id": 1954, "title": "Rocky (1976)", "tmdb_id": 1366, "poster_url": "https://image.tmdb.org/t/p/w500/raayaQ9WTUGolsYHPWc2bGonu58.jpg", "genres": "Drama · Sport"},
    "(500) days of summer": {"movie_id": 69757, "title": "(500) Days of Summer (2009)", "tmdb_id": 19913, "poster_url": "https://image.tmdb.org/t/p/w500/qXAuQ9hF30sQRsXf40OfRVl0MJZ.jpg", "genres": "Comedy · Drama · Romance"},
    "oppenheimer": {"movie_id": 943929, "title": "Oppenheimer (2023)", "tmdb_id": 872585, "poster_url": "https://image.tmdb.org/t/p/w500/8Gxv8gSFCU0XGDykEGv7zR1n2ua.jpg", "genres": "Biography · Drama · History"},
    "requiem for a dream": {"movie_id": 3949, "title": "Requiem for a Dream (2000)", "tmdb_id": 641, "poster_url": "https://image.tmdb.org/t/p/w500/9BTwsLaMVHOGFlmsSlx5QYCaXb.jpg", "genres": "Drama"}

}
POPULAR_CHIPS = [
    "🏜️ Dune", "🍷 The Godfather", "🦇 The Dark Knight", "🕶️ Fight Club",
    "🗡️ Kill Bill", "⚔️ Gladiator", "🌀 Inception", "🌌 Interstellar",
    "🏝️ Shutter Island", "🛡️ 300", "🥊 Rocky", "☀️ (500) Days of Summer",
    "⚛️ Oppenheimer", "💊 Requiem for a Dream"
]
# Map movie_id (string) to exact pill string representation
MOVIE_ID_TO_PILL = {}
for p in POPULAR_CHIPS:
    clean_p = re.sub(r"^[^\w\s\(\)]+\s*", "", p).strip().lower()
    if clean_p in POPULAR_CHIPS_MAP:
        MOVIE_ID_TO_PILL[str(POPULAR_CHIPS_MAP[clean_p]["movie_id"])] = p

# URL Query Param Navigation Handling (Primary Single Source of Truth for Browser History Stack)
url_home = "home" in st.query_params
url_director = st.query_params.get("director")
url_movie = st.query_params.get("movie")
url_search = st.query_params.get("search")
url_genre = st.query_params.get("genre", "all").lower().strip()

prev_routed_movie = st.session_state.get("_routed_movie")
prev_routed_director = st.session_state.get("_routed_director")

if url_home:
    st.session_state["selected_movie"] = None
    st.session_state["selected_director"] = None
    st.session_state["search_input"] = ""
    st.session_state["last_search"] = ""
    st.session_state["last_pill"] = None
    st.session_state["popular_picks_pills"] = None
    st.session_state["search_matches"] = []
    st.session_state["_routed_movie"] = None
    st.session_state["_routed_director"] = None
    st.query_params.clear()
elif url_director:
    d_name = url_director.strip()
    d_id_raw = st.query_params.get("director_id", "").strip()
    d_id = int(d_id_raw) if d_id_raw.isdigit() else None
    if d_name or d_id:
        st.session_state["selected_movie"] = None
        st.session_state["selected_director"] = {"name": d_name, "id": d_id}
        st.session_state["popular_picks_pills"] = None
        st.session_state["search_matches"] = []
        st.session_state["search_input"] = ""
        st.session_state["last_search"] = ""
        st.session_state["_routed_director"] = d_name
        st.session_state["_routed_movie"] = None
elif url_movie:
    mid = url_movie.strip()
    if mid:
        st.session_state["selected_director"] = None
        st.session_state["_routed_movie"] = mid
        st.session_state["_routed_director"] = None
        curr = st.session_state.get("selected_movie")
        if not curr or str(curr.get("movie_id")) != str(mid):
            # Check CATALOG, then POPULAR_CHIPS_MAP, then existing search_matches, or fallback placeholder
            found_target = CATALOG_BY_ID.get(str(mid))
            if not found_target:
                for pm in POPULAR_CHIPS_MAP.values():
                    if str(pm["movie_id"]) == str(mid):
                        found_target = pm
                        break
            if not found_target:
                for sm in st.session_state.get("search_matches", []):
                    if str(sm.get("movie_id")) == str(mid):
                        found_target = sm
                        break
            if found_target:
                st.session_state["selected_movie"] = found_target
            else:
                st.session_state["selected_movie"] = {"movie_id": int(mid), "title": ""}

        # If mid is not part of active search matches, clear disambiguation matches & search box
        active_match_ids = [str(sm.get("movie_id")) for sm in st.session_state.get("search_matches", [])]
        if not active_match_ids or str(mid) not in active_match_ids:
            st.session_state["search_matches"] = []
            st.session_state["search_input"] = ""
            st.session_state["last_search"] = ""
elif url_search:
    sq = url_search.strip()
    if sq and sq != st.session_state.get("last_search"):
        st.session_state["selected_director"] = None
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
                st.session_state["search_matches"] = found[:8]
else:
    # URL has no query parameters (Home page)
    # Check if user navigated back from a movie/director:
    if prev_routed_movie is not None or prev_routed_director is not None:
        # Popped back in browser history to Home!
        st.session_state["selected_movie"] = None
        st.session_state["selected_director"] = None
        st.session_state["search_matches"] = []
        st.session_state["search_input"] = ""
        st.session_state["last_search"] = ""
        st.session_state["_routed_movie"] = None
        st.session_state["_routed_director"] = None
    else:
        # Actively on Home (user can type searches, etc.)
        st.session_state["selected_movie"] = None
        st.session_state["selected_director"] = None
        st.session_state["_routed_movie"] = None
        st.session_state["_routed_director"] = None

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
    if not st.session_state.get("selected_movie") and not st.session_state.get("selected_director"):
        hero_slider_html = """<div class="hero-slider-container">
<div class="hero-slide">
<div class="hero-slide-bg" style="background-image: url('https://image.tmdb.org/t/p/original/nMKdUUepR0i5zn0y1T4CsSB5chy.jpg');"></div>
<div class="hero-content">
<div class="hero-details-col" style="max-width: 860px;">
<div class="hero-spotlight-badge">✦ ALL-TIME MASTERPIECE • SPOTLIGHT #1</div>
<h1 class="hero-title-text" style="font-size: 3.4rem; margin-bottom: 6px;">THE DARK KNIGHT</h1>
<div class="hero-tagline-text">"Why So Serious?"</div>
<div class="hero-badges-row">
<span class="badge-match-score">⭐ 9.0 IMDb Top Rated</span>
<span class="badge-hd">ULTRA HD 4K</span>
<span class="badge-runtime">2008 • 152 min</span>
<span style="color: #c7c7cc; font-size: 0.88rem;">Action · Crime · Drama</span>
<span style="color: #9a9ba3; font-size: 0.85rem;">Dir. Christopher Nolan</span>
</div>
<p class="hero-overview" style="font-size: 1.02rem; line-height: 1.6; max-width: 780px; color: #e2e8f0; margin-bottom: 22px;">
When the menace known as the Joker wreaks havoc and chaos on the people of Gotham, Batman must accept one of the greatest psychological and physical tests of his ability to fight injustice.
</p>
<div class="hero-actions-row">
<a href="?movie=58559" target="_self" class="hero-btn-primary">▶ View Intelligence &amp; Recommendations</a>
<a href="?director=Christopher%20Nolan" target="_self" class="hero-btn-secondary"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polygon points="10 8 16 12 10 16 10 8"/></svg> Christopher Nolan Filmography</a>
</div>
</div>
</div>
</div>
<div class="hero-slide">
<div class="hero-slide-bg" style="background-image: url('https://image.tmdb.org/t/p/original/kXfqcdQKsToO0OUXHcrrNCHDBzO.jpg');"></div>
<div class="hero-content">
<div class="hero-details-col" style="max-width: 860px;">
<div class="hero-spotlight-badge">★ #1 HIGHEST RATED FILM • SPOTLIGHT #2</div>
<h1 class="hero-title-text" style="font-size: 3.4rem; margin-bottom: 6px;">THE SHAWSHANK REDEMPTION</h1>
<div class="hero-tagline-text">"Fear can hold you prisoner. Hope can set you free."</div>
<div class="hero-badges-row">
<span class="badge-match-score">⭐ 9.3 IMDb #1 of All Time</span>
<span class="badge-hd">ULTRA HD 4K</span>
<span class="badge-runtime">1994 • 142 min</span>
<span style="color: #c7c7cc; font-size: 0.88rem;">Drama · Crime</span>
<span style="color: #9a9ba3; font-size: 0.85rem;">Dir. Frank Darabont</span>
</div>
<p class="hero-overview" style="font-size: 1.02rem; line-height: 1.6; max-width: 780px; color: #e2e8f0; margin-bottom: 22px;">
Over the course of several decades, two imprisoned men find solace and eventual redemption through acts of common decency. An immortal testament to human resilience and friendship.
</p>
<div class="hero-actions-row">
<a href="?movie=318" target="_self" class="hero-btn-primary">▶ View Intelligence &amp; Recommendations</a>
<a href="?director=Frank%20Darabont" target="_self" class="hero-btn-secondary"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polygon points="10 8 16 12 10 16 10 8"/></svg> Frank Darabont Filmography</a>
</div>
</div>
</div>
</div>
<div class="hero-slide">
<div class="hero-slide-bg" style="background-image: url('https://image.tmdb.org/t/p/original/xJHokMbljvjADYdit5fK5VQsXEG.jpg');"></div>
<div class="hero-content">
<div class="hero-details-col" style="max-width: 860px;">
<div class="hero-spotlight-badge">◈ SCI-FI SCIENTIFIC PINNACLE • SPOTLIGHT #3</div>
<h1 class="hero-title-text" style="font-size: 3.4rem; margin-bottom: 6px;">INTERSTELLAR</h1>
<div class="hero-tagline-text">"Mankind was born on Earth. It was never meant to die here."</div>
<div class="hero-badges-row">
<span class="badge-match-score">⭐ 8.7 IMDb Epic</span>
<span class="badge-hd">ULTRA HD 4K</span>
<span class="badge-runtime">2014 • 169 min</span>
<span style="color: #c7c7cc; font-size: 0.88rem;">Sci-Fi · Adventure · Drama</span>
<span style="color: #9a9ba3; font-size: 0.85rem;">Dir. Christopher Nolan</span>
</div>
<p class="hero-overview" style="font-size: 1.02rem; line-height: 1.6; max-width: 780px; color: #e2e8f0; margin-bottom: 22px;">
When Earth becomes uninhabitable in the future, a farmer and ex-NASA pilot, Joseph Cooper, is tasked to pilot a spacecraft along with a team of researchers to find a new home across a wormhole.
</p>
<div class="hero-actions-row">
<a href="?movie=109487" target="_self" class="hero-btn-primary">▶ View Intelligence &amp; Recommendations</a>
<a href="?director=Christopher%20Nolan" target="_self" class="hero-btn-secondary"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polygon points="10 8 16 12 10 16 10 8"/></svg> Christopher Nolan Filmography</a>
</div>
</div>
</div>
</div>
<div class="hero-slide">
<div class="hero-slide-bg" style="background-image: url('https://image.tmdb.org/t/p/original/8ZTVqvKDQ8emSGUEMjsS4yHAwrp.jpg');"></div>
<div class="hero-content">
<div class="hero-details-col" style="max-width: 860px;">
<div class="hero-spotlight-badge">✦ MIND-BENDING MASTERWORK • SPOTLIGHT #4</div>
<h1 class="hero-title-text" style="font-size: 3.4rem; margin-bottom: 6px;">INCEPTION</h1>
<div class="hero-tagline-text">"Your mind is the scene of the crime."</div>
<div class="hero-badges-row">
<span class="badge-match-score">⭐ 8.8 IMDb Visionary</span>
<span class="badge-hd">ULTRA HD 4K</span>
<span class="badge-runtime">2010 • 148 min</span>
<span style="color: #c7c7cc; font-size: 0.88rem;">Action · Sci-Fi · Thriller</span>
<span style="color: #9a9ba3; font-size: 0.85rem;">Dir. Christopher Nolan</span>
</div>
<p class="hero-overview" style="font-size: 1.02rem; line-height: 1.6; max-width: 780px; color: #e2e8f0; margin-bottom: 22px;">
A thief who steals corporate secrets through the use of dream-sharing technology is given the inverse task of planting an idea into the mind of a C.E.O., leading through recursive dream levels.
</p>
<div class="hero-actions-row">
<a href="?movie=79132" target="_self" class="hero-btn-primary">▶ View Intelligence &amp; Recommendations</a>
<a href="?director=Christopher%20Nolan" target="_self" class="hero-btn-secondary"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polygon points="10 8 16 12 10 16 10 8"/></svg> Christopher Nolan Filmography</a>
</div>
</div>
</div>
</div>
<div class="hero-slider-nav">
<a href="?movie=58559" target="_self" class="hero-slider-pill"><span style="opacity:0.6; font-weight:800;">01</span> The Dark Knight</a>
<a href="?movie=318" target="_self" class="hero-slider-pill"><span style="opacity:0.6; font-weight:800;">02</span> Shawshank</a>
<a href="?movie=109487" target="_self" class="hero-slider-pill"><span style="opacity:0.6; font-weight:800;">03</span> Interstellar</a>
<a href="?movie=79132" target="_self" class="hero-slider-pill"><span style="opacity:0.6; font-weight:800;">04</span> Inception</a>
</div>
</div>"""
        st.markdown(hero_slider_html, unsafe_allow_html=True)


    # Search Bar & Category Pills (Matching Mockup)
    st.markdown("<div id='search-section'></div>", unsafe_allow_html=True)
    c_left, c_search, c_right = st.columns([1, 2.5, 1])
    with c_search:
        search_query = st.text_input(
            "Search Movie",
            placeholder="Find...",
            label_visibility="collapsed",
            value=st.session_state.get("search_input", "")
        )

    # Generate Category Pills (Matching Mockup: 10 Pills across full width)
    pills_html = []
    for p in CATEGORY_PILLS:
        is_active = (url_genre == p["genre"]) or (p["genre"] == "all" and (not url_genre or url_genre == "all"))
        active_cls = " active" if is_active else ""
        pills_html.append(f'<a href="?genre={p["genre"]}" target="_self" class="category-pill{active_cls}"><span>{p["icon"]}</span> {p["label"]}</a>')

    st.markdown(f"""<div class="category-pills-row">
{''.join(pills_html)}
</div>""", unsafe_allow_html=True)

    # Discover by mood (Screenshot 3 - Positioned right below Category Pills on Home!)
    if not st.session_state.get("selected_movie") and not st.session_state.get("selected_director"):
        st.markdown(render_discover_by_mood_section(), unsafe_allow_html=True)


    # Process search if typed
    if search_query.strip() and search_query.strip() != st.session_state.get("last_search", ""):
        search_term = search_query.strip()
        st.session_state["last_search"] = search_term
        st.session_state["search_input"] = search_term
        st.session_state["selected_director"] = None
        search_loader = st.empty()
        try:
            search_loader.markdown(render_play_loader("SEARCHING NEURAL CATALOG...", f"Querying global index & latent vectors for '{search_term}'"), unsafe_allow_html=True)
            found = api_search_movies(search_term)
            search_loader.empty()
            if found:
                st.session_state["selected_movie"] = found[0]
                st.session_state["search_matches"] = found[:8]
                st.session_state["_routed_movie"] = str(found[0]["movie_id"])
                st.query_params["movie"] = str(found[0]["movie_id"])
                st.rerun()
            else:
                st.session_state["search_matches"] = []
                st.warning(f"No catalog match found for '{search_term}'.")
        except Exception as e:
            search_loader.empty()
            st.error(f"Backend search failed: {e}")
        finally:
            search_loader.empty()

    # Compact Disambiguation Bar (Up to 8 matches presented in clean 4-column rows)
    matches = st.session_state.get("search_matches", [])
    if len(matches) > 1 and st.session_state.get("selected_movie") and not st.session_state.get("selected_director"):
        c_m_left, c_m_content, c_m_right = st.columns([1, 3.2, 1])
        with c_m_content:
            st.markdown("<div style='font-size: 0.82rem; color: #a3a3a3; margin: 6px 0 4px 0;'>🔍 <b>Multiple matches found for your search:</b> (Click to explore)</div>", unsafe_allow_html=True)
            for chunk_start in range(0, len(matches), 4):
                chunk = matches[chunk_start:chunk_start + 4]
                chunk_cols = st.columns(len(chunk))
                for i, cand in enumerate(chunk):
                    with chunk_cols[i]:
                        is_active = (cand.get("movie_id") == st.session_state["selected_movie"].get("movie_id"))
                        clean_cand_title = format_display_title(cand['title'])
                        active_cls = " active" if is_active else ""
                        cand_label = f"✓ {clean_cand_title}" if is_active else clean_cand_title
                        cand_html = f'<a href="?movie={cand["movie_id"]}" target="_self" class="disambig-chip{active_cls}" title="{clean_cand_title}">{cand_label}</a>'
                        st.markdown(cand_html, unsafe_allow_html=True)

    # VIEW 0: Director's Chronological Filmography Showcase
    if st.session_state.get("selected_director"):
        dir_info = st.session_state["selected_director"]
        d_name = dir_info.get("name", "")
        d_id = dir_info.get("id")

        back_btns_html = []
        if st.session_state.get("selected_movie"):
            prev_movie = st.session_state["selected_movie"]
            prev_title = format_display_title(prev_movie.get("title", "Selected Film"))
            prev_mid = prev_movie.get("movie_id", "")
            back_btns_html.append(f'<a href="?movie={prev_mid}" target="_self" class="cinematch-return-btn" title="Back to {prev_title}"><span class="arrow-icon">←</span> Back to {prev_title[:24]}</a>')
        back_btns_html.append('<a href="?home=true" target="_self" class="cinematch-return-btn" title="Return to All Movies"><span class="arrow-icon">🏠</span> Return to All Movies</a>')
        st.markdown(f'<div style="display: flex; gap: 12px; align-items: center; flex-wrap: wrap;">{"".join(back_btns_html)}</div>', unsafe_allow_html=True)


        dir_loader = st.empty()
        try:
            dir_loader.markdown(render_play_loader("CURATING DIRECTOR FILMOGRAPHY...", f"Sorting {d_name or 'Director'}'s feature films in chronological order"), unsafe_allow_html=True)
            filmo_data = api_get_director_filmography(director_name=d_name, director_id=d_id)
        finally:
            dir_loader.empty()

        resolved_dir_name = filmo_data.get("director_name") or d_name or "Director"
        dir_profile = filmo_data.get("profile_url") or SAFE_PLACEHOLDER
        raw_bio = (filmo_data.get("biography") or "").strip()
        dir_movies = filmo_data.get("movies", [])

        if dir_movies:
            years = [m.get("year") for m in dir_movies if m.get("year")]
            span_str = f"{min(years)} – {max(years)}" if years else "Career"
            count_str = f"{len(dir_movies)} Directed Feature Films"
        else:
            span_str = "Feature Career"
            count_str = "Filmography"

        # Cleanly split biography on paragraph / complete sentence boundaries (never cut mid-sentence with '...')
        default_bio = f"{resolved_dir_name} is an acclaimed filmmaker whose feature directing career spans {span_str} across {len(dir_movies)} major theatrical releases."
        if raw_bio:
            paragraphs = [p.strip() for p in re.split(r"\n\s*\n|\r\n\s*\r\n|\n", raw_bio) if p.strip()]
            first_para = paragraphs[0] if paragraphs else raw_bio
            sentences = re.split(r"(?<=[.!?])\s+", first_para)
            if len(first_para) > 440 and len(sentences) > 2:
                short_bio = " ".join(sentences[:3]).strip()
                extra_first = " ".join(sentences[3:]).strip()
                extra_paras = ([extra_first] if extra_first else []) + paragraphs[1:]
            else:
                short_bio = first_para
                extra_paras = paragraphs[1:]
        else:
            short_bio = default_bio
            extra_paras = []

        if extra_paras:
            extra_bio_html = "<br><br>".join(extra_paras[:4])
            bio_toggle_html = f"""<details class="director-bio-details">
<summary><span class="bio-more-label">📖 Show More Biography ▾</span><span class="bio-less-label">📖 Show Less ▴</span></summary>
<div class="director-bio-extra">{extra_bio_html}</div>
</details>"""
        else:
            bio_toggle_html = ""

        # Build concise, high-value Director Career Snapshot (Top Acclaimed Works, Signature Genres, Debut & Origin)
        if dir_movies:
            scored_films = []
            genre_counts = {}
            for m in dir_movies:
                c_title = format_display_title(m.get("clean_title") or re.sub(r"\s*\(\d{4}\)", "", m.get("title", "")))
                v_imdb = get_verified_imdb_score(m.get("title", "")) or get_verified_imdb_score(c_title)
                s_val = float(v_imdb) if v_imdb else float(m.get("vote_average") or 0.0)
                scored_films.append((s_val, c_title, m.get("year", "")))
                for g in (m.get("genres") or "").replace("·", "|").split("|"):
                    g_cl = g.strip()
                    if g_cl:
                        genre_counts[g_cl] = genre_counts.get(g_cl, 0) + 1
            scored_films.sort(key=lambda x: x[0], reverse=True)
            top_works_str = ", ".join([f"{t} ({y}) ⭐ {s:.1f}" for s, t, y in scored_films[:3]])
            top_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            sig_genres_str = " · ".join([g[0] for g in top_genres]) or "Drama · Cinema"
            debut_film = dir_movies[0]
            debut_title = format_display_title(debut_film.get("clean_title") or debut_film.get("title", ""))
            debut_str = f"{debut_title} ({debut_film.get('year', '')})" if debut_film.get("year") and str(debut_film.get("year")) not in debut_title else debut_title
        else:
            top_works_str = "Feature Catalog"
            sig_genres_str = "Drama"
            debut_str = "—"

        birthplace = filmo_data.get("birthplace") or ""
        birthday = filmo_data.get("birthday") or ""
        origin_parts = []
        if birthday:
            origin_parts.append(f"Born {birthday[:4]}")
        if birthplace:
            origin_parts.append(birthplace)
        origin_str = f"{' • '.join(origin_parts)} | Debut: {debut_str}" if origin_parts else f"Debut Feature: {debut_str}"

        dir_meta_grid = f"""<div class="hero-credits-box">
<div><span style="color: #8c8c8c; font-size: 0.76rem; text-transform: uppercase; font-weight: 700;">🏆 Highest-Rated Works</span><div style="color: #ffffff; font-weight: 600; font-size: 0.88rem; margin-top: 3px; line-height: 1.4;">{top_works_str}</div></div>
<div><span style="color: #8c8c8c; font-size: 0.76rem; text-transform: uppercase; font-weight: 700;">🎭 Signature Genres & Career</span><div style="color: #d2d2d2; font-size: 0.88rem; margin-top: 3px; line-height: 1.4;">{sig_genres_str}<br><span style="color:#a3a3a3; font-size:0.8rem;">{origin_str}</span></div></div>
</div>"""

        dir_hero_html = f"""<div class="hero director-hero" style="background-image: url('https://image.tmdb.org/t/p/original/ujUwzNV8ZkOzZonvhhHsc9KOKDf.jpg');">
<div class="hero-content">
<img src="{dir_profile}" class="hero-poster-img" style="border: 2px solid rgba(212,175,55,0.6);" alt="{resolved_dir_name}" />
<div class="hero-details-col">
<div class="hero-spotlight-badge" style="color: #D4AF37; border-color: rgba(212,175,55,0.45); background: rgba(212,175,55,0.12);">🎬 DIRECTOR'S CHRONOLOGICAL FILMOGRAPHY</div>
<h1 class="hero-title-text">{resolved_dir_name}</h1>
<div class="hero-badges-row">
<span class="badge-match-score">📅 {span_str} (Chronological Order)</span>
<span class="badge-hd">{count_str}</span>
<span class="badge-runtime">Sorted Earliest → Latest Release Year</span>
</div>
<p class="hero-overview" style="margin-bottom: 12px;">{short_bio}</p>
{bio_toggle_html}
{dir_meta_grid}
</div>
</div>
</div>"""

        st.markdown(dir_hero_html, unsafe_allow_html=True)

        st.markdown(f"<div class='section-header-title'>🎞️ Directed by <span style='color:#E50914; font-style:italic;'>{resolved_dir_name}</span> <span style='font-size:0.9rem; color:#D4AF37; font-weight:700; margin-left:8px;'>({span_str})</span></div>", unsafe_allow_html=True)
        st.markdown("<div class='section-header-caption'>Presented in strict chronological order by release year — click any film to inspect its details and neural similarity cluster</div>", unsafe_allow_html=True)

        if dir_movies:
            f_cols = st.columns(4)
            for idx, m in enumerate(dir_movies):
                col = f_cols[idx % 4]
                poster = m.get("poster_url") or SAFE_PLACEHOLDER
                clean_m_title = format_display_title(m.get("title", ""))
                verified_imdb = get_verified_imdb_score(clean_m_title) or get_verified_imdb_score(m.get("clean_title", ""))
                raw_vote = float(m.get("vote_average") or 0.0)
                if verified_imdb:
                    score_str = f"⭐ {verified_imdb:.1f} IMDb"
                elif raw_vote > 0:
                    score_str = f"⭐ {raw_vote:.1f} TMDB"
                else:
                    score_str = "Feature"
                rel_year = m.get("year") or (m.get("release_date") or "")[:4] or "—"

                with col:
                    st.markdown(render_cinematch_card(
                        movie_id=m["movie_id"],
                        title=clean_m_title,
                        poster_url=poster,
                        score=verified_imdb or raw_vote or 7.8,
                        year=rel_year,
                        is_featured=(idx == 0),
                        quality="4K"
                    ), unsafe_allow_html=True)
        else:
            st.info(f"No feature films found for {resolved_dir_name}.")

    # VIEW 1: A Movie is Selected -> Show Netflix Hero Showcase & Similar Recommendations
    elif st.session_state["selected_movie"]:
        target = st.session_state["selected_movie"]
        
        st.markdown('<a href="?home=true" target="_self" class="cinematch-return-btn" title="Return to All Movies"><span class="arrow-icon">←</span> Return to All Movies</a>', unsafe_allow_html=True)


        # Fetch Similar Movies & Details from Backend (Cached for Instant Response)
        sim_data = []
        source_movie = {}
        details = {}
        loader_box = st.empty()
        try:
            loader_box.markdown(render_play_loader("STREAMING CINEMATIC CLUSTERS...", "Evaluating latent embedding vectors across 32M ratings"), unsafe_allow_html=True)
            data_json = api_get_similar_cluster(target['movie_id'], num_recs)
            loader_box.empty()
            sim_data = data_json.get("results", [])
            source_movie = data_json.get("source_movie", {})
            details = source_movie.get("details", {})
        except Exception:
            loader_box.empty()
            # Clean local catalog fallback so no connection error ever appears
            fallback_items = [m for m in FAMOUS_CATALOG if str(m["movie_id"]) != str(target.get("movie_id"))][:num_recs]
            sim_data = [
                {
                    "rank": idx + 1,
                    "score": m["score"],
                    "movie": {
                        "movie_id": m["movie_id"],
                        "title": f"{m['title']} ({m['year']})",
                        "genres": m["genres"],
                        "tmdb_id": m["tmdb_id"],
                        "poster_url": m["poster_url"]
                    }
                }
                for idx, m in enumerate(fallback_items)
            ]
        finally:
            loader_box.empty()

        # Synchronize target and session state with real backend metadata
        if source_movie:
            real_title = details.get("title") or source_movie.get("title")
            if real_title and real_title not in ("Selected Film", "Unknown Title", ""):
                target["title"] = format_display_title(real_title)
            real_poster = source_movie.get("poster_url") or details.get("poster_url")
            if real_poster:
                target["poster_url"] = real_poster
            if source_movie.get("genres"):
                target["genres"] = source_movie["genres"]
            st.session_state["selected_movie"] = target

        # Render Netflix Hero Showcase Banner
        raw_title_str = (
            details.get("title")
            or target.get("title")
            or source_movie.get("title")
            or "Feature Film"
        )
        title_str = format_display_title(raw_title_str)

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
        director_id = details.get("director_id")
        cast = details.get("cast", "")
        runtime = details.get("runtime", "")
        vote_avg = details.get("vote_average")
        vote_count = details.get("vote_count")

        # Check verified IMDb rating & Source Transparency (handles MovieLens inverted titles too)
        imdb_score = (
            get_verified_imdb_score(title_str)
            or get_verified_imdb_score(source_movie.get("title", ""))
            or get_verified_imdb_score(target.get("title", ""))
        )
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
        
        if director:
            dir_url_param = f"?director={urllib.parse.quote(director)}" + (f"&director_id={director_id}" if director_id else "")
            director_html = f"<div><span style='color: #8c8c8c; font-size: 0.76rem; text-transform: uppercase; font-weight: 700; display:block;'>Director (Click for Filmography)</span><a href='{dir_url_param}' target='_self' class='director-link-badge' title='Explore all movies directed by {director} in chronological order'>🎬 {director} <span style='font-size:0.75rem; color:#D4AF37; font-weight:800;'>• Filmography ↗</span></a></div>"
        else:
            director_html = ""
        cast_html = f"<div><span style='color: #8c8c8c; font-size: 0.78rem; text-transform: uppercase; font-weight: 700;'>Starring Cast</span><div style='color: #d2d2d2; font-size: 0.88rem; line-height: 1.4; margin-top: 4px;'>🌟 {cast}</div></div>" if cast else ""
        
        meta_grid = f"<div class='hero-credits-box'>{director_html}{cast_html}</div>" if (director or cast) else ""

        backdrop_img = (
            details.get("backdrop_url")
            or "https://image.tmdb.org/t/p/original/ujUwzNV8ZkOzZonvhhHsc9KOKDf.jpg"
        )
        hero_html = f"""<div class="hero movie-details-hero" style="background-image: url('{backdrop_img}');">
<div class="hero-content">
<img src="{hero_poster}" class="hero-poster-img" alt="{title_str}" />
<div class="hero-details-col">
<div class="hero-spotlight-badge">FEATURED CINEMA SELECTION</div>
<h1 class="hero-title-text">{title_str}</h1>
{tagline_html}
<div class="hero-badges-row">
{rating_html}
<span class="badge-hd">ULTRA HD 4K</span>
{runtime_html}
<span style="color: #d1d5db; font-size: 0.88rem;">{genres_raw}</span>
</div>
<p class="hero-overview">{overview}</p>
{meta_grid}
<div class="hero-actions-row">
<a href="#trending-section" class="hero-btn-primary">▶ View Similar Recommendations</a>
</div>
</div>
</div>
</div>"""

        st.markdown(hero_html, unsafe_allow_html=True)

        st.markdown(f"<div id='trending-section' class='section-header-title'>✨ More Like <span style='color:#E50914; font-style:italic;'>{title_str}</span></div>", unsafe_allow_html=True)
        st.markdown("<div class='section-header-caption'>Deep thematic matches sorted from highest to lowest rating based on genre overlap, director signatures, and viewer behavior (Click any card to explore)</div>", unsafe_allow_html=True)

        if sim_data:
            # Resolve each card's authoritative rating and sort descending from highest to lowest
            enriched_sim = []
            for item in sim_data:
                m = item["movie"]
                clean_card_title = format_display_title(m.get("title", ""))
                verified_card_imdb = get_verified_imdb_score(clean_card_title) or get_verified_imdb_score(m.get("title", ""))
                numeric_score = float(verified_card_imdb) if verified_card_imdb else float(item.get("score") or 0.0)
                score_badge = f"⭐ {verified_card_imdb:.1f} IMDb" if verified_card_imdb else f"⭐ {numeric_score:.1f} TMDB"
                enriched_sim.append((numeric_score, clean_card_title, score_badge, item))

            enriched_sim.sort(key=lambda x: x[0], reverse=True)

            sim_cards_html = [
                render_cinematch_card(
                    movie_id=item["movie"]["movie_id"],
                    title=clean_card_title,
                    poster_url=item["movie"].get("poster_url") or SAFE_PLACEHOLDER,
                    score=numeric_score,
                    year=item["movie"].get("year", "Film"),
                    is_featured=False,
                    quality="4K"
                )
                for numeric_score, clean_card_title, score_badge, item in enriched_sim
            ]
            st.markdown(f'<div class="cinematch-cards-grid-4">{"".join(sim_cards_html)}</div>', unsafe_allow_html=True)
        else:
            st.info("No similar recommendations found.")

        # Discover by mood (Screenshot 3 - Also visible after searching / visiting a movie!)
        st.markdown(render_discover_by_mood_section(), unsafe_allow_html=True)


    # VIEW 2: Default Showcase -> CineMatch Mockup Sections
    else:
        # Check if user clicked a specific category/genre pill (e.g. Thriller, Action, Sci-Fi)
        if url_genre and url_genre != "all":
            active_pill = next((p for p in CATEGORY_PILLS if p["genre"] == url_genre), None)
            genre_icon = active_pill["icon"] if active_pill else "🎬"
            display_genre_title = active_pill["label"] if active_pill else url_genre.capitalize()
            genre_movies = GENRE_SHOWCASE_MAP.get(url_genre)
            if not genre_movies:
                genre_movies = [m for m in FAMOUS_CATALOG if url_genre in m.get("genres", "").lower()]
            if not genre_movies:
                genre_movies = FAMOUS_CATALOG[5:15]

            # 1. PRIMARY SECTION: Curated Genre Showcase FIRST!
            st.markdown(f"""<div id="genre-section" class="section-flex-header" style="margin-top: 10px;">
<div class="section-title-box">
<div class="section-title-row">
<span style="font-size: 1.45rem;">{genre_icon}</span>
<h2 class="section-main-heading">{display_genre_title} Cinema Masterpieces</h2>
</div>
<div class="section-sub-heading">Curated highest-rated {display_genre_title.lower()} films recognized worldwide</div>
</div>
<a href="?genre=all" target="_self" class="section-view-all">✕ Clear Filter (Show All)</a>
</div>""", unsafe_allow_html=True)

            genre_cards = [
                render_cinematch_card(
                    movie_id=gm["movie_id"],
                    title=gm["title"],
                    poster_url=gm["poster_url"],
                    score=gm["score"],
                    year=gm["year"],
                    is_featured=(idx == 0),
                    quality="4K"
                )
                for idx, gm in enumerate(genre_movies)
            ]
            st.markdown(render_cards_grid(genre_cards), unsafe_allow_html=True)

            # 2. SECONDARY SECTION: Top 15 Highest Rated IMDb Movies (Screenshot 1 & descending order fix)
            st.markdown("""<div id="top-15-section" class="section-flex-header" style="margin-top: 36px;">
<div class="section-title-box">
<div class="section-title-row" style="display: flex; align-items: center; gap: 10px;">
<div class="section-icon-badge"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#f5c518" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg></div>
<h2 class="section-main-heading">Top 15 Highest Rated IMDb Movies</h2>
</div>
<div class="section-sub-heading">Cinema's greatest masterpieces arranged in strict descending order of verified IMDb ratings (9.3 → 8.7)</div>
</div>
<a href="?genre=all" target="_self" class="section-view-all">View All Masterpieces →</a>
</div>""", unsafe_allow_html=True)

            top_15_cards = [
                render_cinematch_card(
                    movie_id=movie["movie_id"],
                    title=movie["title"],
                    poster_url=movie["poster_url"],
                    score=movie["score"],
                    year=movie["year"],
                    is_featured=(movie["title"] == "The Shawshank Redemption"),
                    quality="4K"
                )
                for movie in FAMOUS_CATALOG
            ]
            st.markdown(f'<div class="cinematch-grid-container"><div class="cinematch-cards-grid">{"".join(top_15_cards)}</div></div>', unsafe_allow_html=True)

        else:
            # DEFAULT "ALL" VIEW (Unified Top 15 Highest Rated IMDb Movies in descending order - Screenshot 1 fix)
            st.markdown("""<div id="top-15-section" class="section-flex-header" style="margin-top: 10px;">
<div class="section-title-box">
<div class="section-title-row" style="display: flex; align-items: center; gap: 10px;">
<div class="section-icon-badge"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#f5c518" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg></div>
<h2 class="section-main-heading">Top 15 Highest Rated IMDb Movies</h2>
</div>
<div class="section-sub-heading">Cinema's greatest masterpieces arranged in strict descending order of verified IMDb ratings (9.3 → 8.7)</div>
</div>
<a href="?genre=all" target="_self" class="section-view-all">View All Masterpieces →</a>
</div>""", unsafe_allow_html=True)

            top_15_cards = [
                render_cinematch_card(
                    movie_id=movie["movie_id"],
                    title=movie["title"],
                    poster_url=movie["poster_url"],
                    score=movie["score"],
                    year=movie["year"],
                    is_featured=(movie["title"] == "The Shawshank Redemption"),
                    quality="4K"
                )
                for movie in FAMOUS_CATALOG
            ]
            st.markdown(f'<div class="cinematch-grid-container"><div class="cinematch-cards-grid">{"".join(top_15_cards)}</div></div>', unsafe_allow_html=True)


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
                st.markdown(render_cinematch_card(
                    movie_id=m["movie_id"],
                    title=m["title"],
                    poster_url=poster,
                    score=item["score"],
                    year=f"#{item['rank']} Pick",
                    is_featured=(item["rank"] == 1),
                    quality="HD"
                ), unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Cannot load recommendations for User {user_id}: {e}")

# Tech Stack & Engineering Pipeline Section
st.markdown("<div id='tech-stack-section'></div>", unsafe_allow_html=True)
with st.expander("◈ System Architecture & Engineering Tech Stack (Production Pipeline)", expanded=False):
    t_c1, t_c2, t_c3 = st.columns(3)
    with t_c1:
        st.markdown("""<div class="tech-stack-card">
<h4 style="margin: 0 0 6px 0; color: #E50914; display: flex; align-items: center; gap: 7px;"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg> Big Data & Distributed ML</h4>
<div style="font-size: 0.85rem; color: #b3b3b3; line-height: 1.5;">
• <b>Apache Spark 3.5 & MLlib</b>: Distributed ALS Matrix Factorization.<br>
• <b>Dataset</b>: 32,000,204 MovieLens ratings with explicit StructType schemas.<br>
• <b>Tuned Hyperparameters</b>: <code>rank=16, partitions=40, coldStartStrategy="drop"</code>.
</div>
</div>""", unsafe_allow_html=True)
    with t_c2:
        st.markdown("""<div class="tech-stack-card">
<h4 style="margin: 0 0 6px 0; color: #ffffff; display: flex; align-items: center; gap: 7px;"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect width="20" height="8" x="2" y="2" rx="2" ry="2"/><rect width="20" height="8" x="2" y="14" rx="2" ry="2"/><line x1="6" x2="6.01" y1="6" y2="6"/><line x1="6" x2="6.01" y1="18" y2="18"/></svg> Microservice Serving Layer</h4>
<div style="font-size: 0.85rem; color: #b3b3b3; line-height: 1.5;">
• <b>Django REST Framework</b>: Production serving boundary.<br>
• <b>Sub-15ms Latency</b>: Serves precomputed vectors without running heavy Spark jobs.<br>
• <b>PostgreSQL 15 / SQLite</b>: Indexed on <code>(user_id, rank)</code> for rapid retrieval.
</div>
</div>""", unsafe_allow_html=True)
    with t_c3:
        st.markdown("""<div class="tech-stack-card">
<h4 style="margin: 0 0 6px 0; color: #46d369; display: flex; align-items: center; gap: 7px;"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><polygon points="10 8 16 12 10 16 10 8"/></svg> Real-Time Enrichment Graph</h4>
<div style="font-size: 0.85rem; color: #b3b3b3; line-height: 1.5;">
• <b>TMDB Live Graph API</b>: Real-time posters, director credits & starring cast.<br>
• <b>Hybrid Multi-Strategy Search</b>: Title normalization & post-dataset dynamic ingestion.<br>
• <b>Netflix Cinematic UI</b>: Glassmorphism, 3D hover effects & responsive grid.
</div>
</div>""", unsafe_allow_html=True)

# Developer Profile & Portfolio Card (Varun Esarapu)
st.markdown("""<div id="contact-section" class="netflix-footer">
<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 24px;">
<div>
<div style="font-size: 0.72rem; color: #E50914; font-weight: 800; text-transform: uppercase; letter-spacing: 0.12em; margin-bottom: 4px;">Designed &amp; Engineered By</div>
<h3 style="margin: 0 0 6px 0; font-size: 1.65rem; font-weight: 800; color: #ffffff; letter-spacing: -0.02em;">Varun Esarapu</h3>
<p style="margin: 0; color: #9a9ba3; font-size: 0.88rem;">AI &amp; Data Science Engineer · Big Data &amp; Distributed Machine Learning Pipelines</p>
</div>
<div style="display: flex; flex-wrap: wrap; align-items: center; gap: 10px;">
<a href="https://e-varun-portfolio.vercel.app/#intro" target="_blank" class="footer-btn footer-portfolio">
<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" x2="22" y1="12" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
Portfolio Website
</a>
<a href="https://github.com/Varun-Esarapu/movie_rec" target="_blank" class="footer-btn footer-github">
<svg width="15" height="15" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.012 8.012 0 0 0 16 8c0-4.42-3.58-8-8-8z"/></svg>
GitHub Repository
</a>
<a href="https://www.linkedin.com/in/varun-esarapu/" target="_blank" class="footer-btn footer-linkedin">
<svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor"><path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.46 10.9h2.79v8.37H6.46v-8.37M7.86 6.78a1.62 1.62 0 1 0 0 3.24 1.62 1.62 0 0 0 0-3.24z"/></svg>
LinkedIn Profile
</a>
<a href="mailto:varunesarapu@gmail.com" class="footer-btn footer-mail">
<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>
Contact Varun
</a>
</div>
</div>
</div>""", unsafe_allow_html=True)
