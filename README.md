# 🍿 CineMatch AI — Distributed Movie Recommendation Engine

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![Apache Spark](https://img.shields.io/badge/Apache%20Spark-3.5-orange.svg)](https://spark.apache.org/)
[![Django REST Framework](https://img.shields.io/badge/Django-5.0-green.svg)](https://www.django-rest-framework.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> An end-to-end distributed machine learning movie discovery platform trained on **32 Million MovieLens ratings**, served via **Django REST Framework**, enriched in real-time with **The Movie Database (TMDB)**, and presented in an authentic **Netflix-styled glassmorphism UI**.

---

## 👨‍💻 Engineered By
**Varun Esarapu** — *AI & Data Science Engineer*  
🌐 **Portfolio**: [https://e-varun-portfolio.vercel.app/#intro](https://e-varun-portfolio.vercel.app/#intro)  
🐙 **GitHub**: [https://github.com/Varun-Esarapu](https://github.com/Varun-Esarapu)  
💼 **LinkedIn**: [https://www.linkedin.com/in/varun-esarapu/](https://www.linkedin.com/in/varun-esarapu/)  
✉️ **Email**: `esarapuvarun88596@gmail.com`

---

## 🏛️ System Architecture

```
                          [ 32M MovieLens Dataset ]
                                      │
                                      ▼
                        [ Apache Spark 3.5 MLlib ]
                     (ALS Matrix Factorization: rank=16)
                                      │
                                      ▼
                   [ Partitioned Parquet / PostgreSQL ]
                                      │
                                      ▼
                      [ Django REST Framework API ]
                     (Sub-15ms In-Memory Serving)
                                      │
                                      ├──◄── [ TMDB Graph API ]
                                      │     (Live Metadata & Credits)
                                      ▼
                         [ Streamlit Netflix UI ]
                     (3D Hover, Floating Pill Navbar)
```

---

## ⚡ Core Engineering Highlights

### 1. Distributed Big Data & PySpark MLlib ALS
- **Dataset Scale**: Ingested and processed **32,000,204 user interactions** and 87,000+ films from MovieLens without Out-Of-Memory (OOM) failures.
- **Tuned Spark Runtime**:
  - `spark.driver.memory: 6g`
  - `spark.executor.memory: 6g`
  - `spark.sql.shuffle.partitions: 40`
  - `spark.driver.maxResultSize: 2g`
- **Matrix Factorization**: Trained distributed Alternating Least Squares (`rank=16`, `coldStartStrategy="drop"`, `implicitPrefs=False`).
- **Batch Export**: Computed top-20 offline recommendations for 330,975 users and exported to partitioned Parquet files and PostgreSQL via JDBC.

### 2. High-Performance Decoupled Serving Boundary (Django REST Framework)
- Completely decouples client requests from heavy Spark compute, guaranteeing **sub-15ms response times**.
- Endpoints:
  - `GET /api/v1/recommendations/<user_id>/`: Retrieves precomputed ALS recommendations.
  - `GET /api/v1/movies/search/?q=<query>`: Multi-strategy hybrid search combining TMDB global graph search with local database title normalization.
  - `GET /api/v1/movies/<movie_id>/similar/`: Fetches similarity clusters with full plot synopsis, director credits, top starring cast, and runtime in a single call via `append_to_response=credits`.

### 3. Authentic Netflix Cinematic UI & Floating Capsule Navbar
- **Centered Floating Pill Navbar**: Exact replica of Varun's portfolio navigation with blurred glassmorphism, gold active indicators, and top scroll progress tracking.
- **Top 15 IMDb Rated & Iconic Showcase**: Hand-curated, verified masterpieces including *The Shawshank Redemption*, *The Godfather*, *The Dark Knight*, *Pulp Fiction*, *Fight Club*, *Forrest Gump*, and *Inception*.
- **Interactive 3D Cards**: Hover zoom expansion (`scale(1.07)`), ambient red border glow, and one-click discovery.
- **Smart Disambiguation**: Intelligently handles title variations (e.g. *The Heat* vs *Heat*, *(500) Days of Summer*, *Oppenheimer*).

---

## 🚀 Quickstart & Local Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Varun-Esarapu/movie_rec.git
cd movie_rec
```

### 2. Set Up the Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate   # On Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

### 3. Set Up the Frontend
```bash
# In a new terminal window:
cd frontend
python -m venv venv
venv\Scripts\activate   # On Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py --server.port 8501
```
Open **[http://localhost:8501](http://localhost:8501)** in your browser.

---

## ☁️ Production Deployment

### Backend (Render / Railway)
- **Root Directory**: `backend`
- **Build Command**: `pip install -r requirements.txt && python manage.py migrate`
- **Start Command**: `gunicorn recommender_core.wsgi:application --bind 0.0.0.0:$PORT`
- **Environment Variables**:
  - `PYTHON_VERSION`: `3.11.9`
  - `TMDB_API_KEY`: `your_tmdb_api_key`
  - `DEBUG`: `False`
  - `ALLOWED_HOSTS`: `*`

### Frontend (Streamlit Community Cloud)
- **Repository**: `Varun-Esarapu/movie_rec`
- **Branch**: `main`
- **Main file path**: `frontend/app.py`
- **Secrets / Config**:
  ```toml
  API_BASE_URL = "https://your-backend-service.onrender.com/api/v1"
  TMDB_API_KEY = "your_tmdb_api_key"
  ```

---

## 📜 License
Distributed under the MIT License. See `LICENSE` for more information.
