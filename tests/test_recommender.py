# tests/test_recommender.py
import unittest
from src.recommender import Recommender

class TestRecommender(unittest.TestCase):

    def setUp(self):
        self.recommender = Recommender()

    def test_hybrid_score(self):
        movie_data = {
            'overview': 'A thrilling adventure in space.',
            'genres': ['Adventure', 'Sci-Fi'],
            'keywords': ['space', 'thrill'],
            'cast': ['Actor A', 'Actor B'],
            'director': 'Director A',
            'vote_average': 8.0,
            'vote_count': 1000
        }
        score = self.recommender.calculate_hybrid_score(movie_data)
        self.assertIsInstance(score, float)

    def test_apply_filters(self):
        movies = [
            {'year': 2020, 'vote_average': 7.5, 'vote_count': 500, 'runtime': 120},
            {'year': 2019, 'vote_average': 6.0, 'vote_count': 300, 'runtime': 90},
            {'year': 2021, 'vote_average': 8.0, 'vote_count': 1500, 'runtime': 150}
        ]
        filtered_movies = self.recommender.apply_filters(movies, year_range=(2020, 2021), min_rating=7.0, min_votes=400)
        self.assertEqual(len(filtered_movies), 2)

    def test_recommend_movies(self):
        user_watchlist = ['Movie A', 'Movie B']
        recommendations = self.recommender.recommend_movies(user_watchlist)
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)

if __name__ == '__main__':
    unittest.main()