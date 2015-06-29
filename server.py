import fetch
import sqlite3
from flask import Flask, render_template, g

DATABASE = 'fetched_movies.db'

app = Flask(__name__)
app.config.from_object(__name__)

def connect_db():
	return sqlite3.connect(DATABASE)

def get_db():
	db = getattr(g, '_database', None)
	if db is None:
		db = g._database = connect_db()
	return db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.route("/")
def index():
	movies = []
	cur = get_db().cursor()
	for movie in query_db('select * from Movies'):
		movie_dict = {
			"title" : movie[0],
			"torrent_url" : movie[1],
			"magnet_download" : movie[2],
			"subtitle_download" : movie[3],
			"imdb_page" : movie[4],
			"imdb_icon" : movie[5],
		}

		movies.append(movie_dict)
	# Must pass in the name as well (movies = movies)
	return render_template('index.html', movies=movies)

if __name__ == "__main__":
        fetch.run_server()
	app.debug = True
	app.run()
