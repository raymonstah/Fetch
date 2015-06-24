# Raymond Ho
# Jun 20, 2015

""" A Web application created in Python that will get top HD movies from ThePirateBay,
provide links to the movie's IMDb and torrent page, allow instant subtitle download
along with the movie download, and display the movie icon. Created in Python.
"""

from urllib import request, parse  # Used to generate URLs and open links
import requests
from bs4 import BeautifulSoup  # Used to parse HTML
import sqlite3

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~ BEGIN MOVIE CLASS ~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class Movie():

    def get_subtitles(self, language='english'):
        """ Get a list of Subtitles for that movie"""

        subscene = 'http://subscene.com'
        subscene_list = subscene + '/subtitles/title?q=' + parse.quote_plus(self.title)

        sub_soup = BeautifulSoup(request.urlopen(subscene_list).read())

        sub_list = links_in_soup(sub_soup, '', language)
        # Append the full URL for every item in list
        sub_list = [subscene + x for x in sub_list]

        subscene_link = sub_list[0]  # The first one.
        sub_download_soup = BeautifulSoup(request.urlopen(subscene_link).read())

        # Base URL + the download link
        result = subscene + links_in_soup(sub_download_soup, '/subtitle/download', '', 'single')
        return result

    def get_imdb_url(self):
        """ Returns the IMDb link given a title, updates imdb url """

        # In case we have it already.
        if self.imdb_url:
            print('IMDb url found. Returning.')
            return self.imdb_url

        # Strip periods, and replace with spaces.
        title = ''.join([x.replace('.', ' ') for x in list(self.title)])
        bad_strings = ['1080', '720']
        for bad_string in bad_strings:
            bad_index = title.find(bad_string)
            if bad_index != -1: # -1 means bad string was not found.
                title = title[:bad_index]

        imdb = 'http://www.imdb.com/find?ref_=nv_sr_fn&q=' + parse.quote_plus(title) + '&s=tt'
        imdb_soup = BeautifulSoup(requests.get(imdb).text)

        result = links_in_soup(imdb_soup, '/title', '', 'single')
        if not result:
            print (imdb)
        self.imdb_url = 'http://www.imdb.com' + result
        return self.imdb_url

    def get_imdb_icon(self):
        """ Returns a link to an icon of a specific movie from IMDb """

        if self.imdb_url is None:
            self.get_imdb_url()

        link_soup = BeautifulSoup(requests.get(self.imdb_url).text)
        link = link_soup.find(itemprop='image')['src']
        
        return link

    def __init__(self, title, torrent_link, download):
        self.title = title
        self.torrent_link = torrent_link
        self.download = download
        self.imdb_url = None  # Defined by get_imdb_url()
        self.dir_title_gif = None  # Defined by download_imdb_icon()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~ END MOVIE CLASS ~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~ START HELPER FUNCTIONS ~~~~~~~~~~~~~~~~~~~~~~~~~~~ #


def links_in_soup(soup, begins='', contains='', count='list'):
    """
        Finds links in a BeautifulSoup object.
        If the link starts with 'begins', or 'contains' is IN the link,
        then the link will be appended to a list.
        If 'count' is 'single', break loop and return first one found.
        Else, exhaust loop, and return a list of all matches.
    """

    results = []

    for link in soup.findAll('a'):
        href = link.get('href')
        try:
            if begins and href.startswith(begins):
                results.append(href)
            elif contains and contains in href:
                results.append(href)

        except AttributeError:  # Some objects has no attribute 'startswith'
            continue
    
    if not results:
        return None
    if count == 'single':
        return results[0]

    return results

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~ END HELPER FUNCTIONS ~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

# 207 = HD Movies
def get_torrent_links(base_url='http://thepiratebay.mn/', category='top/207'):
    """ Returns a list of (title, link, download_link) of a provided link """

    link = base_url + category
    list_soup = BeautifulSoup(requests.get(link).text)

    # All download links are in a list.

    results = []

    # Get all torrent links from TPB specific URL
    # Iterate two lists at once (one to find movies, other to find downloads)
    for link, torrent in zip(list_soup.findAll('a', {'class': 'detLink'}),
                             links_in_soup(list_soup, 'magnet', '')):
        link_to = base_url + link.get('href')
        results.append(Movie(link.string, link_to, torrent))

    return results


def create_database():
    print("Creating database")
    conn = sqlite3.connect('fetched_movies.db')
    c = conn.cursor()
    c.execute('''CREATE table if not exists Movies (
    name text,
    torrent_url text,
    subtitle_link text,
    subtitle_download text,
    imdb_page text,
    imdb_icon text
    )''')
    conn.commit()
    conn.close()

if __name__ == '__main__':

    movies = get_torrent_links()

