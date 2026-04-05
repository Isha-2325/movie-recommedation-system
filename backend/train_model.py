import pickle
import numpy as np
import pandas as pd
from app import app
from models import Movie, Rating

MODEL_PATH = "svd_model.pkl"

def train_svd(ratings_df, n_factors=50):
    user_item_matrix = ratings_df.pivot(index='userId', columns='movieId', values='rating').fillna(0)

    user_ids = user_item_matrix.index.tolist()
    movie_ids = user_item_matrix.columns.tolist()

    matrix = user_item_matrix.values
    U, sigma, Vt = np.linalg.svd(matrix, full_matrices=False)

    sigma = sigma[:n_factors]
    U = U[:, :n_factors]
    Vt = Vt[:n_factors, :]

    sigma_diag = np.diag(sigma)
    reconstructed = np.dot(np.dot(U, sigma_diag), Vt)

    return reconstructed, user_ids, movie_ids

with app.app_context():
    ratings = Rating.query.all()
    movies = Movie.query.all()

    ratings_df = pd.DataFrame([
        {"userId": r.user_id, "movieId": r.movie_id, "rating": r.rating}
        for r in ratings
    ])

    movies_df = pd.DataFrame([
        {"movieId": m.id, "title": m.title, "genres": m.genres}
        for m in movies
    ])

    print("Ratings loaded:", len(ratings_df))
    print("Movies loaded:", len(movies_df))

    reconstructed, user_ids, movie_ids = train_svd(ratings_df, n_factors=50)

    model_data = {
        "reconstructed_matrix": reconstructed,
        "user_ids": user_ids,
        "movie_ids": movie_ids
    }

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model_data, f)

    print("✅ Model trained and saved as", MODEL_PATH)