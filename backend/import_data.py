import pandas as pd
import os
from app import app
from models import db, Movie, Rating

movies_path = "../dataset/movies.csv"
ratings_path = "../dataset/ratings.csv"

print("Movies path:", os.path.abspath(movies_path))
print("Ratings path:", os.path.abspath(ratings_path))
print("Movies exists:", os.path.exists(movies_path))
print("Ratings exists:", os.path.exists(ratings_path))

with app.app_context():
    movies_df = pd.read_csv(movies_path)
    ratings_df = pd.read_csv(ratings_path)

    print("Movies columns:", movies_df.columns.tolist())
    print("Ratings columns:", ratings_df.columns.tolist())

    Rating.query.delete()
    Movie.query.delete()
    db.session.commit()

    movies = []
    for _, row in movies_df.iterrows():
        movies.append(
            Movie(
                id=int(row["movieId"]),
                title=str(row["title"]),
                genres=str(row["genres"])
            )
        )

    db.session.bulk_save_objects(movies)
    db.session.commit()
    print(f"Inserted {len(movies)} movies")

    ratings = []
    for _, row in ratings_df.iterrows():
        ratings.append(
            Rating(
                user_id=int(row["userId"]),
                movie_id=int(row["movieId"]),
                rating=float(row["rating"]),
                timestamp=int(row["timestamp"])
            )
        )

    db.session.bulk_save_objects(ratings)
    db.session.commit()
    print(f"Inserted {len(ratings)} ratings")

    print("✅ Import completed successfully")