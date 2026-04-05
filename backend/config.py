from urllib.parse import quote_plus

password = quote_plus("isha@8087228075#")

class Config:
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://root:{password}@localhost:3306/movie_recommender"
    SQLALCHEMY_TRACK_MODIFICATIONS = False