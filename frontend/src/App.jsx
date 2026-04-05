import { useEffect, useState } from "react";
import "./App.css";

function App() {
  const [recommendations, setRecommendations] = useState([]);
  const [movies, setMovies] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/recommendations/1")
      .then((res) => res.json())
      .then((data) => {
        setRecommendations(data.recommendations || []);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Recommendations error:", err);
        setLoading(false);
      });

    fetch("/api/movies")
      .then((res) => res.json())
      .then((data) => setMovies(data || []))
      .catch((err) => console.error("Movies error:", err));
  }, []);

  if (loading) {
    return (
      <div className="app">
        <div className="loading">Loading your recommendations...</div>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="navbar">
        <div className="nav-content">
          <h1 className="logo">MovieFlix</h1>
          <select className="user-select" defaultValue="1">
            <option value="1">User 1</option>
          </select>
        </div>
      </header>

      <section className="hero">
        <div className="hero-content">
          <h1>Top Picks for You</h1>
          <p>
            Personalized recommendations powered by SVD matrix factorization.
          </p>
        </div>
      </section>

      <main className="main-content">
        <section className="section">
          <h2 className="section-title">Recommended for You</h2>
          <div className="movie-row">
            {recommendations.map((movie) => (
              <MovieCard key={movie.movieId} movie={movie} />
            ))}
          </div>
        </section>

        <section className="section">
          <h2 className="section-title">Browse Movies</h2>
          <div className="movie-row">
            {movies.slice(0, 10).map((movie) => (
              <MovieCard key={movie.movieId} movie={movie} />
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}

function MovieCard({ movie }) {
  const posterUrl = `https://image.tmdb.org/t/p/w342/${getPosterPath(movie.title)}`;

  return (
    <div className="movie-card">
      <div className="movie-poster">
        <img
          src={posterUrl}
          alt={movie.title}
          loading="lazy"
          onError={(e) => {
            e.currentTarget.src =
              "https://image.tmdb.org/t/p/w342/6KErczPA16QIAMYoKZhwCcCgOiP.jpg";
          }}
        />
        {movie.predicted_rating && (
          <div className="rating-overlay">
            <span>⭐ {movie.predicted_rating.toFixed(1)}</span>
          </div>
        )}
      </div>

      <div className="movie-info">
        <h3 className="movie-title">{movie.title}</h3>
        <p className="movie-genres">{formatGenres(movie.genres)}</p>
      </div>
    </div>
  );
}

function formatGenres(genres) {
  if (!genres) return "Unknown";
  return genres.split("|").join(" • ");
}

function getPosterPath(title) {
  const posterMap = {
    "Die Hard (1988)": "eG5nTiL8J0PrV93fE72UODy2hKw.jpg",
    "Godfather: Part II, The (1974)": "vUzVOXEvPNc9VjevN40uMcH9sVG.jpg",
    "Jaws (1975)": "4VlXxmK8qYF9B8LNQoFsxNymNcz.jpg",
    "Breakfast Club, The (1985)": "rTux3V3RtR1Y8GvTNrvKvfoJxw3.jpg",
    "Godfather, The (1972)": "3bhkrj58Vtu7enYsRolD1fZdja1.jpg",
    "Stand by Me (1986)": "s8dFWe8nh9Gvv67pu1fM8xxeMUn.jpg",
    "Christmas Story, A (1983)": "qN4rlUEUC62cIFfSlEb4C9V32jI.jpg",
    "Lady and the Tramp (1955)": "kNEKNe8mwdmF6f24mv2Hr2pHMPH.jpg",
    "Snatch (2000)": "8ieaEyNWvVXi63fHriN4xOl4nzp.jpg",
    "Little Mermaid, The (1989)": "hraMS9Tu62Y5xkbezcH12y7nTr2.jpg",
    "Toy Story (1995)": "uXDfjJbdP4ijW5hWSBrPrlKpxab.jpg",
    "Jumanji (1995)": "vzmL6fP7aPKNKPRTFnZmiUfciyV.jpg",
    "Grumpier Old Men (1995)": "nGT2ajczV5fC6ZwWL7aHTXOJYYb.jpg",
    "Waiting to Exhale (1995)": "4wjGMw6A8ryFhV4VqF7TvdbA3Jn.jpg",
  };

  return posterMap[title] || "6KErczPA16QIAMYoKZhwCcCgOiP.jpg";
}

export default App;
