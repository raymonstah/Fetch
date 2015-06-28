# Raymond Ho | Jun 20, 2015
# This is used to test all of the functions of fetch.py to ensure
# that everything is working correctly.

from selenium import webdriver
import unittest
import fetch
import sqlite3

class TestFetch(unittest.TestCase):

	def setUp(self):
		# pass
		self.movies = fetch.get_torrent_links()

	# @unittest.skip('Skip test')
	def test_movies_length(self):
		self.assertIsNotNone(len(self.movies), msg='Torrent links error.')

	# @unittest.skip('Skip test')
	def test_subtitles(self):
		subs = self.movies[0].get_subtitles()
		self.assertIn('http://subscene.com/subtitle/download', subs)
		# Download them.
		#driver = webdriver.Firefox().get(subs)

	# @unittest.skip('Skip test')
	def test_imdb_url(self):
		imdb_url = self.movies[0].get_imdb_url()
		self.assertIn('http://www.imdb.com/title/', imdb_url)
		# Test web page
		#driver = webdriver.Firefox().get(imdb_url)

	# @unittest.skip('Skip test')
	def test_imdb_icon(self):
		imdb_icon = self.movies[0].get_imdb_icon()
		self.assertIn('http://ia.media-imdb.com/images/', imdb_icon)
		#driver = webdriver.Firefox().get(imdb_icon)

	# @unittest.skip('Skip test')
	def test_create_movie_db(self):
		fetch.create_movie_db()
		conn = sqlite3.connect('fetched_movies.db')
		c = conn.cursor()
		c.execute('''PRAGMA table_info(Movies)''')
		self.assertNotEqual([], c.fetchall())

	# @unittest.skip('Skip test')
	def test_populate_db(self):
		fetch.insert_into_db(self.movies[0])
		conn = sqlite3.connect('fetched_movies.db')
		c = conn.cursor()
		c.execute('''Select name from Movies LIMIT 1''')
		self.assertTrue(len(c.fetchall()) > 0)

		
if __name__ == '__main__':
	unittest.main()