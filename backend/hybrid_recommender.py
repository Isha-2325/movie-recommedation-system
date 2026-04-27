import pickle
import numpy as np
import pandas as pd
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class HybridRecommender:
    def __init__(self):
        self.svd_model = None
        self.content_similarity = None
        self.movies_df = None
        self.tfidf_vectorizer = None
        
    def load_svd_model(self, model_path="svd_model.pkl"):
        """Load the pre-trained SVD model"""
        with open(model_path, "rb") as f:
            self.svd_model = pickle.load(f)
    
    def build_content_similarity(self, movies_df):
        """Build content-based similarity matrix using genres"""
        self.movies_df = movies_df.copy()
        
        # Create TF-IDF vectors from genres
        self.tfidf_vectorizer = TfidfVectorizer(token_pattern=r'[^|]+')
        genre_matrix = self.tfidf_vectorizer.fit_transform(
            movies_df['genres'].fillna('').values
        )
        
        # Calculate cosine similarity
        self.content_similarity = cosine_similarity(genre_matrix)
        
        # Create movie ID to index mapping
        self.movie_id_to_idx = {movie_id: idx for idx, movie_id in enumerate(movies_df['movieId'])}
        self.idx_to_movie_id = {idx: movie_id for idx, movie_id in enumerate(movies_df['movieId'])}
    
    def get_content_based_recommendations(self, movie_id, top_n=10):
        """Get content-based recommendations for a movie"""
        if movie_id not in self.movie_id_to_idx:
            return []
        
        movie_idx = self.movie_id_to_idx[movie_id]
        similarity_scores = list(enumerate(self.content_similarity[movie_idx]))
        
        # Sort by similarity score (excluding the movie itself)
        similarity_scores.sort(key=lambda x: x[1], reverse=True)
        similarity_scores = similarity_scores[1:top_n+1]
        
        recommendations = []
        for idx, score in similarity_scores:
            movie_id = self.idx_to_movie_id[idx]
            movie = self.movies_df[self.movies_df['movieId'] == movie_id].iloc[0]
            recommendations.append({
                'movieId': movie_id,
                'title': movie['title'],
                'genres': movie['genres'],
                'similarity_score': score
            })
        
        return recommendations
    
    def get_collaborative_recommendations(self, user_id, top_n=10):
        """Get collaborative filtering recommendations using SVD"""
        if not self.svd_model:
            return []
        
        reconstructed_matrix = self.svd_model["reconstructed_matrix"]
        user_ids = self.svd_model["user_ids"]
        movie_ids = self.svd_model["movie_ids"]
        
        if user_id not in user_ids:
            return []
        
        user_index = user_ids.index(user_id)
        user_predictions = reconstructed_matrix[user_index]
        
        recommendations = []
        for idx, movie_id in enumerate(movie_ids):
            recommendations.append({
                'movieId': movie_id,
                'predicted_rating': float(user_predictions[idx])
            })
        
        recommendations.sort(key=lambda x: x["predicted_rating"], reverse=True)
        return recommendations[:top_n]
    
    def get_popular_movies(self, ratings_df, top_n=10):
        """Get popular movies based on average ratings and number of ratings"""
        movie_stats = ratings_df.groupby('movieId').agg({
            'rating': ['mean', 'count']
        }).round(2)
        
        movie_stats.columns = ['avg_rating', 'rating_count']
        movie_stats = movie_stats[movie_stats['rating_count'] >= 10]  # Minimum 10 ratings
        movie_stats = movie_stats.sort_values(['avg_rating', 'rating_count'], ascending=False)
        
        popular_movies = []
        for movie_id, row in movie_stats.head(top_n).iterrows():
            movie = self.movies_df[self.movies_df['movieId'] == movie_id].iloc[0]
            popular_movies.append({
                'movieId': movie_id,
                'title': movie['title'],
                'genres': movie['genres'],
                'avg_rating': row['avg_rating'],
                'rating_count': row['rating_count']
            })
        
        return popular_movies
    
    def get_hybrid_recommendations(self, user_id, ratings_df, top_n=10, 
                                 svd_weight=0.6, content_weight=0.3, popularity_weight=0.1):
        """Get hybrid recommendations combining multiple approaches"""
        # Get collaborative filtering recommendations
        collab_recs = self.get_collaborative_recommendations(user_id, top_n * 2)
        
        # Get user's highly rated movies for content-based recommendations
        user_ratings = ratings_df[ratings_df['userId'] == user_id]
        high_rated_movies = user_ratings[user_ratings['rating'] >= 4.0]
        
        content_recs = []
        if not high_rated_movies.empty:
            # Get content recommendations based on user's favorite movies
            for _, movie_row in high_rated_movies.head(3).iterrows():
                movie_recs = self.get_content_based_recommendations(
                    movie_row['movieId'], top_n // 3
                )
                content_recs.extend(movie_recs)
        
        # Get popular movies as fallback
        popular_recs = self.get_popular_movies(ratings_df, top_n // 2)
        
        # Combine and score recommendations
        combined_scores = defaultdict(float)
        movie_info = {}
        
        # Add collaborative filtering scores
        for rec in collab_recs:
            movie_id = rec['movieId']
            combined_scores[movie_id] += svd_weight * rec['predicted_rating']
            movie_info[movie_id] = rec
        
        # Add content-based scores
        for rec in content_recs:
            movie_id = rec['movieId']
            combined_scores[movie_id] += content_weight * rec['similarity_score'] * 5
            if movie_id not in movie_info:
                movie_info[movie_id] = rec
        
        # Add popularity scores
        for rec in popular_recs:
            movie_id = rec['movieId']
            combined_scores[movie_id] += popularity_weight * rec['avg_rating']
            if movie_id not in movie_info:
                movie_info[movie_id] = rec
        
        # Filter out movies user has already rated
        rated_movies = set(user_ratings['movieId'])
        final_recommendations = []
        
        for movie_id, score in sorted(combined_scores.items(), key=lambda x: x[1], reverse=True):
            if movie_id not in rated_movies and len(final_recommendations) < top_n:
                rec = movie_info[movie_id].copy()
                rec['hybrid_score'] = score
                final_recommendations.append(rec)
        
        return final_recommendations
    
    def save_model(self, path="hybrid_model.pkl"):
        """Save the hybrid recommender model"""
        model_data = {
            'svd_model': self.svd_model,
            'content_similarity': self.content_similarity,
            'movies_df': self.movies_df,
            'tfidf_vectorizer': self.tfidf_vectorizer,
            'movie_id_to_idx': self.movie_id_to_idx,
            'idx_to_movie_id': self.idx_to_movie_id
        }
        with open(path, "wb") as f:
            pickle.dump(model_data, f)
    
    def load_model(self, path="hybrid_model.pkl"):
        """Load the hybrid recommender model"""
        with open(path, "rb") as f:
            model_data = pickle.load(f)
        
        self.svd_model = model_data['svd_model']
        self.content_similarity = model_data['content_similarity']
        self.movies_df = model_data['movies_df']
        self.tfidf_vectorizer = model_data['tfidf_vectorizer']
        self.movie_id_to_idx = model_data['movie_id_to_idx']
        self.idx_to_movie_id = model_data['idx_to_movie_id']
