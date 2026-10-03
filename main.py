import streamlit as st
import tensorflow as tf
import numpy as np
import pandas as pd
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Embedding, Flatten, Dot, Input
import requests
from sklearn.metrics.pairwise import cosine_similarity

# -------- PAGE CONFIG --------
st.set_page_config(page_title="Movie Recommendation System", layout="wide")

# -------- CONFIG --------
TMDB_API_KEY = "3a1ff8b883fd4c71a563201decf380b1"

# -------- HEADER --------
st.markdown("""
<h1 style='text-align:center;'>🎬 Movie Recommendation System</h1>
<p style='text-align:center; color:gray;'>Discover movies using AI + TMDB</p>
<hr>
""", unsafe_allow_html=True)

# -------- SIDEBAR --------
st.sidebar.header("⚙️ Settings")
num_rec = st.sidebar.slider("Number of recommendations", 3, 10, 4)

# -------- LOAD DATA --------
@st.cache_data
def load_data():
    data_url = "https://files.grouplens.org/datasets/movielens/ml-100k/u.data"
    column_names = ['userId', 'movieId', 'rating', 'TimeStamp']

    data = pd.read_csv(data_url, sep='\t', names=column_names)
    data['userId'] -= 1
    data['movieId'] -= 1

    item_url = "https://files.grouplens.org/datasets/movielens/ml-100k/u.item"
    movie_columns = ['movieId', 'title'] + [f'col_{i}' for i in range(22)]

    movies = pd.read_csv(item_url, sep='|', encoding='latin-1', names=movie_columns)
    movies['movieId'] -= 1

    return data, movies

data, movies = load_data()

# -------- GENRE SIMILARITY --------
genre_matrix = movies.iloc[:, 5:].values
similarity = cosine_similarity(genre_matrix)

# -------- MODEL --------
@st.cache_resource
def build_model(data):
    num_users = data['userId'].nunique()
    num_movies = data['movieId'].nunique()

    user_input = Input(shape=[1])
    movie_input = Input(shape=[1])

    user_embedding = Embedding(num_users, 50)(user_input)
    movie_embedding = Embedding(num_movies, 50, name='movie_embedding')(movie_input)

    user_vec = Flatten()(user_embedding)
    movie_vec = Flatten()(movie_embedding)

    dot_prod = Dot(axes=1)([user_vec, movie_vec])

    model = Model(inputs=[user_input, movie_input], outputs=dot_prod)
    model.compile(optimizer='adam', loss='mse')

    model.fit([data['userId'], data['movieId']], data['rating'],
              epochs=2, batch_size=64, verbose=0)

    return model

model = build_model(data)

# -------- RECOMMENDER --------
def recommend_movies(movie_id, num_rec=5):
    movie_emb = model.get_layer('movie_embedding').get_weights()[0]

    genre_scores = similarity[movie_id]
    target_vec = movie_emb[movie_id]
    embed_scores = movie_emb.dot(target_vec)

    genre_scores = genre_scores / np.max(genre_scores)
    embed_scores = embed_scores / np.max(embed_scores)

    final_scores = 0.4 * genre_scores + 0.6 * embed_scores

    same_genre = genre_scores > 0.5
    final_scores = final_scores * same_genre

    final_scores[movie_id] = -np.inf

    top_ids = np.argsort(final_scores)[-num_rec:][::-1]

    recs = movies.iloc[top_ids].copy()
    recs['movieId'] += 1

    return recs[['movieId', 'title']]

# -------- TITLE FIX --------
def format_title(title):
    if ', The' in title:
        return 'The ' + title.replace(', The', '')
    elif ', A' in title:
        return 'A ' + title.replace(', A', '')
    return title

# -------- TMDB --------
@st.cache_data
def get_movie_details(title):
    try:
        title_clean = title.split('(')[0].replace(", The", "").replace(", A", "").strip()

        year = ""
        if '(' in title:
            year = title.split('(')[-1].replace(')', '').strip()

        url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={title_clean}&year={year}"

        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            return None, None, None

        data = response.json()
        results = data.get('results', [])

        movie = None
        for m in results:
            if title_clean.lower() in m.get('title', '').lower():
                movie = m
                break

        if not movie and results:
            movie = sorted(results, key=lambda x: x.get('popularity', 0), reverse=True)[0]

        if not movie:
            return None, None, None

        poster = movie.get('poster_path')
        rating = movie.get('vote_average')
        overview = movie.get('overview')

        poster_url = f"https://image.tmdb.org/t/p/w500{poster}" if poster else None

        return poster_url, rating, overview

    except:
        return None, None, None

# -------- UI --------
movie_name = st.text_input("🔍 Search for a movie...", placeholder="e.g. Shawshank Redemption, Pulp Fiction , etc.")

if not movie_name:
    st.info("Start by searching for a movie 🎬")

if movie_name:
    results = movies[movies['title'].str.contains(movie_name, case=False)]

    if results.empty:
        st.warning("No matching movies found.")
    else:
        selected = st.selectbox("Select a movie:", results['title'].tolist())
        st.success(f"🎯 Selected: {format_title(selected)}")

        selected_id = results[results['title'] == selected]['movieId'].values[0]

        # -------- SELECTED MOVIE --------
        poster, rating, overview = get_movie_details(selected)

        st.markdown("## 🎯 Selected Movie")

        col1, col2 = st.columns([1, 3])

        with col1:
            if poster:
                st.image(poster, use_container_width=True)
            else:
                st.image("https://via.placeholder.com/300x450?text=No+Poster", use_container_width=True)

        with col2:
            st.markdown(f"## 🎬 {format_title(selected)}")

            if rating:
                st.markdown(f"⭐ **{rating}/10**")

            if overview:
                st.write(overview[:400] + "...")
            else:
                st.write("No description available.")

        st.markdown("---")

        # -------- RECOMMENDATIONS --------
        if st.button("🎬 Get Recommendations"):
            with st.spinner("🍿 Cooking recommendations for you..."):
                recs = recommend_movies(selected_id, num_rec=num_rec)

            st.subheader("Recommended Movies")

            cols = st.columns(3)

            for i in range(len(recs)):
                row = recs.iloc[i]
                poster, rating, overview = get_movie_details(row['title'])

                with cols[i % 3]:
                    if i == 0:
                        st.markdown("🔥 **Top Pick**")

                    if poster:
                        st.image(poster, use_container_width=True)
                    else:
                        st.image("https://via.placeholder.com/300x450?text=No+Poster", use_container_width=True)

                    st.markdown(f"**{format_title(row['title'])}**")

                    if rating:
                        st.caption(f"⭐ {rating}")

                    if overview:
                        st.caption(overview[:100] + "...")