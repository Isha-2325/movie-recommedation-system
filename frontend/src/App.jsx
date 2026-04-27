import { useEffect, useState } from "react";
import "./App.css";

function App() {
  const [recommendations, setRecommendations] = useState([]);
  const [movies, setMovies] = useState([]);
  const [users, setUsers] = useState([]);
  const [userRatings, setUserRatings] = useState([]);
  const [selectedUser, setSelectedUser] = useState(1);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [showRatings, setShowRatings] = useState(false);
  const [ratingModal, setRatingModal] = useState({ show: false, movie: null, rating: 3 });

  useEffect(() => {
    fetchUsers();
  }, []);

  useEffect(() => {
    if (selectedUser) {
      fetchRecommendations(selectedUser);
      fetchUserRatings(selectedUser);
    }
  }, [selectedUser]);

  useEffect(() => {
    fetchMovies(1, searchTerm);
  }, [searchTerm]);

  const fetchUsers = async () => {
    try {
      const res = await fetch("/api/users");
      const data = await res.json();
      setUsers(data);
    } catch (err) {
      console.error("Users error:", err);
    }
  };

  const fetchRecommendations = async (userId) => {
    try {
      setLoading(true);
      const res = await fetch(`/api/recommendations/${userId}`);
      const data = await res.json();
      setRecommendations(data.recommendations || []);
    } catch (err) {
      console.error("Recommendations error:", err);
      setRecommendations([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchMovies = async (page = 1, search = "") => {
    try {
      const url = search ? `/api/movies?page=${page}&limit=20&search=${search}` : `/api/movies?page=${page}&limit=20`;
      const res = await fetch(url);
      const data = await res.json();
      setMovies(data.movies || []);
    } catch (err) {
      console.error("Movies error:", err);
    }
  };

  const fetchUserRatings = async (userId) => {
    try {
      const res = await fetch(`/api/ratings/${userId}`);
      const data = await res.json();
      setUserRatings(data.ratings || []);
    } catch (err) {
      console.error("User ratings error:", err);
    }
  };

  const handleRating = async (movieId, rating) => {
    try {
      const res = await fetch("/api/ratings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: selectedUser,
          movie_id: movieId,
          rating: rating
        })
      });
      
      if (res.ok) {
        setRatingModal({ show: false, movie: null, rating: 3 });
        fetchUserRatings(selectedUser);
        fetchRecommendations(selectedUser);
      }
    } catch (err) {
      console.error("Rating error:", err);
    }
  };

  const openRatingModal = (movie) => {
    const existingRating = userRatings.find(r => r.movieId === movie.movieId);
    setRatingModal({
      show: true,
      movie: movie,
      rating: existingRating ? existingRating.rating : 3
    });
  };

  if (loading && !recommendations.length) {
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
          <div className="nav-controls">
            <select 
              className="user-select" 
              value={selectedUser} 
              onChange={(e) => setSelectedUser(parseInt(e.target.value))}
            >
              {users.map(user => (
                <option key={user.userId} value={user.userId}>
                  {user.username}
                </option>
              ))}
            </select>
            <button 
              className={`nav-btn ${showRatings ? 'active' : ''}`}
              onClick={() => setShowRatings(!showRatings)}
            >
              {showRatings ? 'Recommendations' : 'My Ratings'}
            </button>
          </div>
        </div>
      </header>

      <section className="hero">
        <div className="hero-content">
          <h1>{showRatings ? 'Your Ratings' : 'Top Picks for You'}</h1>
          <p>
            {showRatings 
              ? 'Manage and view your movie ratings'
              : 'Personalized recommendations powered by SVD matrix factorization.'}
          </p>
        </div>
      </section>

      <main className="main-content">
        {!showRatings ? (
          <section className="section">
            <h2 className="section-title">Recommended for You</h2>
            {recommendations.length === 0 ? (
              <div className="no-data">
                <p>No recommendations available. Try rating some movies first!</p>
              </div>
            ) : (
              <div className="movie-row">
                {recommendations.map((movie) => (
                  <MovieCard 
                    key={movie.movieId} 
                    movie={movie} 
                    onRate={openRatingModal}
                    showRateButton={true}
                  />
                ))}
              </div>
            )}
          </section>
        ) : (
          <section className="section">
            <h2 className="section-title">Your Ratings</h2>
            {userRatings.length === 0 ? (
              <div className="no-data">
                <p>You haven't rated any movies yet. Start rating to get personalized recommendations!</p>
              </div>
            ) : (
              <div className="movie-row">
                {userRatings.map((movie) => (
                  <MovieCard 
                    key={movie.movieId} 
                    movie={movie} 
                    onRate={openRatingModal}
                    showRateButton={true}
                  />
                ))}
              </div>
            )}
          </section>
        )}

        <section className="section">
          <div className="section-header">
            <h2 className="section-title">Browse Movies</h2>
            <input
              type="text"
              className="search-input"
              placeholder="Search movies..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          {movies.length === 0 ? (
            <div className="no-data">
              <p>No movies found. Try a different search term.</p>
            </div>
          ) : (
            <div className="movie-row">
              {movies.map((movie) => (
                <MovieCard 
                  key={movie.movieId} 
                  movie={movie} 
                  onRate={openRatingModal}
                  showRateButton={true}
                />
              ))}
            </div>
          )}
        </section>
      </main>

      {ratingModal.show && (
        <div className="modal-overlay" onClick={() => setRatingModal({ show: false, movie: null, rating: 3 })}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Rate "{ratingModal.movie.title}"</h3>
            <div className="rating-input">
              <input
                type="range"
                min="0.5"
                max="5"
                step="0.5"
                value={ratingModal.rating}
                onChange={(e) => setRatingModal({ ...ratingModal, rating: parseFloat(e.target.value) })}
              />
              <span className="rating-value">{ratingModal.rating} ⭐</span>
            </div>
            <div className="modal-actions">
              <button 
                className="btn btn-primary"
                onClick={() => handleRating(ratingModal.movie.movieId, ratingModal.rating)}
              >
                Save Rating
              </button>
              <button 
                className="btn btn-secondary"
                onClick={() => setRatingModal({ show: false, movie: null, rating: 3 })}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function MovieCard({ movie, onRate, showRateButton = false }) {
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
        {(movie.predicted_rating || movie.rating) && (
          <div className="rating-overlay">
            <span>⭐ {(movie.predicted_rating || movie.rating).toFixed(1)}</span>
          </div>
        )}
      </div>

      <div className="movie-info">
        <h3 className="movie-title">{movie.title}</h3>
        <p className="movie-genres">{formatGenres(movie.genres)}</p>
        {showRateButton && (
          <button 
            className="rate-btn"
            onClick={() => onRate(movie)}
          >
            Rate Movie
          </button>
        )}
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
