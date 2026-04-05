from app import app
from models import Movie, Rating

with app.app_context():
    print("Movies in DB:", Movie.query.count())
    print("Ratings in DB:", Rating.query.count())

    first_movie = Movie.query.first()
    if first_movie:
        print("First movie:", first_movie.title)
    else:
        print("No movies found in database.")