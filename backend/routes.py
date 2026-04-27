from flask import jsonify, request
import pickle
import pandas as pd
from models import Movie, Rating, User
from datetime import datetime
from hybrid_recommender import HybridRecommender

MODEL_PATH = "svd_model.pkl"
HYBRID_MODEL_PATH = "hybrid_model.pkl"

# Initialize hybrid recommender
hybrid_recommender = HybridRecommender()

def load_model():
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)

def load_hybrid_model():
    try:
        hybrid_recommender.load_model(HYBRID_MODEL_PATH)
        return True
    except FileNotFoundError:
        # Fallback to SVD model if hybrid model doesn't exist
        return False

def get_recommendations_for_user(user_id, top_n=10, use_hybrid=True):
    try:
        if use_hybrid and load_hybrid_model():
            # Use hybrid recommender
            ratings = Rating.query.all()
            ratings_df = pd.DataFrame([
                {"userId": r.user_id, "movieId": r.movie_id, "rating": r.rating}
                for r in ratings
            ])
            
            recommendations = hybrid_recommender.get_hybrid_recommendations(
                user_id, ratings_df, top_n
            )
            
            # Add movie details
            result = []
            for rec in recommendations:
                movie = Movie.query.get(rec['movieId'])
                if movie:
                    result.append({
                        "movieId": movie.id,
                        "title": movie.title,
                        "genres": movie.genres,
                        "predicted_rating": rec.get('hybrid_score', 0)
                    })
            return result
        else:
            # Fallback to original SVD implementation
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
    except Exception as e:
        print(f"Error getting recommendations for user {user_id}: {str(e)}")
        return []

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
        try:
            use_hybrid = request.args.get('hybrid', 'true').lower() == 'true'
            recs = get_recommendations_for_user(user_id, use_hybrid=use_hybrid)
            return jsonify({
                "user_id": user_id,
                "recommendations": recs,
                "count": len(recs),
                "algorithm": "hybrid" if use_hybrid else "svd"
            })
        except Exception as e:
            return jsonify({
                "error": "Failed to get recommendations",
                "message": str(e)
            }), 500

    @app.route("/api/recommendations/<int:user_id>/content")
    def content_recommendations(user_id):
        try:
            if not load_hybrid_model():
                return jsonify({
                    "error": "Hybrid model not available"
                }), 501
            
            # Get user's highest rated movie
            user_ratings = Rating.query.filter_by(user_id=user_id).order_by(Rating.rating.desc()).first()
            if not user_ratings:
                return jsonify({
                    "user_id": user_id,
                    "recommendations": [],
                    "message": "No ratings found for content-based recommendations"
                })
            
            recommendations = hybrid_recommender.get_content_based_recommendations(
                user_ratings.movie_id, top_n=10
            )
            
            result = []
            for rec in recommendations:
                movie = Movie.query.get(rec['movieId'])
                if movie:
                    result.append({
                        "movieId": movie.id,
                        "title": movie.title,
                        "genres": movie.genres,
                        "similarity_score": rec['similarity_score']
                    })
            
            return jsonify({
                "user_id": user_id,
                "recommendations": result,
                "count": len(result),
                "algorithm": "content-based"
            })
        except Exception as e:
            return jsonify({
                "error": "Failed to get content recommendations",
                "message": str(e)
            }), 500

    @app.route("/api/movies")
    def get_movies():
        try:
            page = request.args.get('page', 1, type=int)
            limit = request.args.get('limit', 20, type=int)
            search = request.args.get('search', '')
            
            query = Movie.query
            if search:
                query = query.filter(Movie.title.ilike(f'%{search}%'))
            
            movies = query.offset((page - 1) * limit).limit(limit).all()
            
            return jsonify({
                "movies": [{
                    "movieId": movie.id,
                    "title": movie.title,
                    "genres": movie.genres
                } for movie in movies],
                "page": page,
                "limit": limit,
                "total": query.count()
            })
        except Exception as e:
            return jsonify({
                "error": "Failed to fetch movies",
                "message": str(e)
            }), 500

    @app.route("/api/users")
    def get_users():
        try:
            users = User.query.limit(100).all()
            return jsonify([{
                "userId": user.id,
                "username": user.username,
                "email": user.email
            } for user in users])
        except Exception as e:
            return jsonify({
                "error": "Failed to fetch users",
                "message": str(e)
            }), 500

    @app.route("/api/ratings", methods=["POST"])
    def add_rating():
        try:
            data = request.get_json()
            
            if not data or 'user_id' not in data or 'movie_id' not in data or 'rating' not in data:
                return jsonify({
                    "error": "Missing required fields",
                    "required": ["user_id", "movie_id", "rating"]
                }), 400
            
            user_id = data['user_id']
            movie_id = data['movie_id']
            rating = float(data['rating'])
            
            if rating < 0.5 or rating > 5.0:
                return jsonify({
                    "error": "Rating must be between 0.5 and 5.0"
                }), 400
            
            existing_rating = Rating.query.filter_by(
                user_id=user_id, 
                movie_id=movie_id
            ).first()
            
            if existing_rating:
                existing_rating.rating = rating
                existing_rating.timestamp = int(datetime.now().timestamp())
                message = "Rating updated successfully"
            else:
                new_rating = Rating(
                    user_id=user_id,
                    movie_id=movie_id,
                    rating=rating,
                    timestamp=int(datetime.now().timestamp())
                )
                db.session.add(new_rating)
                message = "Rating added successfully"
            
            db.session.commit()
            
            return jsonify({
                "message": message,
                "user_id": user_id,
                "movie_id": movie_id,
                "rating": rating
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({
                "error": "Failed to save rating",
                "message": str(e)
            }), 500

    @app.route("/api/ratings/<int:user_id>")
    def get_user_ratings(user_id):
        try:
            ratings = Rating.query.filter_by(user_id=user_id).all()
            result = []
            
            for rating in ratings:
                movie = Movie.query.get(rating.movie_id)
                if movie:
                    result.append({
                        "movieId": rating.movie_id,
                        "title": movie.title,
                        "genres": movie.genres,
                        "rating": rating.rating,
                        "timestamp": rating.timestamp
                    })
            
            return jsonify({
                "user_id": user_id,
                "ratings": result,
                "count": len(result)
            })
        except Exception as e:
            return jsonify({
                "error": "Failed to fetch user ratings",
                "message": str(e)
            }), 500