from flask import jsonify
import pickle
import pandas as pd
from models import Movie, Rating

MODEL_PATH = "svd_model.pkl"

def load_model():
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)

def get_recommendations_for_user(user_id, top_n=10):
    model_data = load_model()
    reconstructed_matrix = model_data["reconstructed_matrix"]
    user_ids = model_data["user_ids"]
    movie_ids = model_data["movie_ids"]

    if user_id not in user_ids:
        return []

    user_index = user_ids.index(user_id)
    user_predictions = reconstructed_matrix[user_index]

    rated_movie_ids = {
        r.movie_id for r in Rating.query.filter_by(user_id=user_id).all()
    }

    recommendations = []
    for idx, movie_id in enumerate(movie_ids):
        if movie_id not in rated_movie_ids:
            movie = Movie.query.get(movie_id)
            if movie:
                recommendations.append({
                    "movieId": movie.id,
                    "title": movie.title,
                    "genres": movie.genres,
                    "predicted_rating": float(user_predictions[idx])
                })

    recommendations.sort(key=lambda x: x["predicted_rating"], reverse=True)
    return recommendations[:top_n]

def register_routes(app):
    @app.route("/")
    def home():
        return jsonify({
            "message": "Movie Recommendation System API is running"
        })

    @app.route("/health")
    def health():
        return jsonify({
            "status": "ok"
        })

    @app.route("/api/recommendations/<int:user_id>")
    def recommendations(user_id):
        recs = get_recommendations_for_user(user_id)
        return jsonify({
            "user_id": user_id,
            "recommendations": recs
        })

    @app.route("/api/movies")
    def get_movies():
        movies = Movie.query.limit(50).all()
        return jsonify([
            {
                "movieId": movie.id,
                "title": movie.title,
                "genres": movie.genres
            }
            for movie in movies
        ])