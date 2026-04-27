import pickle
import numpy as np
import pandas as pd
from app import app
from models import Movie, Rating
from hybrid_recommender import HybridRecommender

def train_hybrid_model():
    """Train the hybrid recommendation model"""
    print("🎬 Training Hybrid Recommendation Model...")
    
    with app.app_context():
        # Load data from database
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
        
        print(f"📊 Loaded {len(ratings_df)} ratings and {len(movies_df)} movies")
        
        # Initialize hybrid recommender
        recommender = HybridRecommender()
        
        # Load existing SVD model
        try:
            recommender.load_svd_model("svd_model.pkl")
            print("✅ Loaded existing SVD model")
        except FileNotFoundError:
            print("❌ SVD model not found. Please train SVD model first.")
            return
        
        # Build content-based similarity
        recommender.build_content_similarity(movies_df)
        print("✅ Built content-based similarity matrix")
        
        # Save the hybrid model
        recommender.save_model("hybrid_model.pkl")
        print("✅ Hybrid model saved as hybrid_model.pkl")
        
        # Test the model
        print("\n🧪 Testing hybrid recommendations...")
        test_users = ratings_df['userId'].unique()[:3]  # Test with first 3 users
        
        for user_id in test_users:
            recommendations = recommender.get_hybrid_recommendations(
                user_id, ratings_df, top_n=5
            )
            
            print(f"\nUser {user_id} Recommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec['title']} (Score: {rec['hybrid_score']:.2f})")
        
        print("\n🎉 Hybrid model training completed successfully!")

if __name__ == "__main__":
    train_hybrid_model()
