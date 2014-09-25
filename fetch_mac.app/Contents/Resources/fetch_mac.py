# Raymond Ho
# Sept 17, 2014

""" A GUI application created in Python that will get top HD movies from ThePirateBay,
provide links to the movie's IMDb and torrent page, allow instant subtitle download
along with the movie download, and display the movie icon. Created in Python.
"""

from urllib import request, parse  # Used to generate URLs and open links
from bs4 import BeautifulSoup  # Used to parse HTML
import subprocess  # Open sub processes..
import time
import os
import os.path
from tkinter import *

# Determine OS
WINDOWS = OSX = False
if os.name == 'nt':
    WINDOWS = True
elif os.name == 'posix':
    OSX = True

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

    if count == 'single':
        return results[0]
    return results


def downloader(link):
    """ Attempts to download from a link depending on your OS. """

    if WINDOWS:
        os.startfile(link)
    elif OSX:
        subprocess.call(['open', link])
    else:
        print('Your OS may not be supported at this time.')


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~ END HELPER FUNCTIONS ~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~ BEGIN MOVIE CLASS ~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class Movie():

    def get_subtitles(self, language='english'):
        """ Get a list of Subtitles for that movie"""

        subscene = 'http://subscene.com/'
        subscene_list = subscene + '/subtitles/title?q=' + parse.quote_plus(self.title)

        sub_soup = BeautifulSoup(request.urlopen(subscene_list).read())

        sub_list = links_in_soup(sub_soup, '', language)
        # Append the full URL for every item in list
        sub_list = [subscene + x for x in sub_list]

        subscene_link = sub_list[0]  # The first one.
        sub_download_soup = BeautifulSoup(request.urlopen(subscene_link).read())

        # Base URL + the download link
        result = subscene + links_in_soup(sub_download_soup, '/subtitle/download', '', 'single')

        downloader(result)

    def get_imdb_url(self):
        """ Returns the IMDb link given a title, updates imdb url """

        # In case we have it already.
        if self.imdb_url:
            print('IMDb url found. Returning.')
            return self.imdb_url

        # Strip periods, and replace with spaces.
        title = ''.join([x.replace('.', ' ') for x in list(self.title)])

        imdb = 'http://www.imdb.com/find?q=' + parse.quote_plus(title) + '&s=tt'
        imdb_soup = BeautifulSoup(request.urlopen(imdb).read())

        result = links_in_soup(imdb_soup, '/title', '', 'single')

        self.imdb_url = 'http://www.imdb.com' + result
        return self.imdb_url

    def get_imdb_icon(self):
        """ Returns a link to an icon of a specific movie from IMDb """

        link_soup = BeautifulSoup(request.urlopen(self.imdb_url).read())
        link = link_soup.find(itemprop='image')
        return link['src']

    def download_imdb_icon(self):
        """ Given the IMDb icon, download it and convert it into a GIF (Tkinter compatible)
        This was made 100x faster by simply checking if the file exists before fetching it again """

        dir_title = PICDIR + '/' + self.title
        dir_title_jpg = dir_title + '.jpg'
        dir_title_gif = dir_title + '.gif'

        # GIF File not there. Fetch it.
        if not os.path.isfile(dir_title_gif):
            print('File was not found, receiving..')

            photo_link = self.get_imdb_icon()

            # Save as JPG, convert to GIF after.
            request.urlretrieve(photo_link, dir_title_jpg)

            if OSX:
                # Change to GIF so Tkinter can use it.
                subprocess.call(['sips', '-s', 'format', 'gif', dir_title_jpg, '--out', dir_title_gif])
                os.remove(dir_title_jpg)
            elif WINDOWS:
                return
                #import PIL.Image
                #im = PIL.Image.open(dir_title_jpg).save(dir_title_gif)

        self.dir_title_gif = dir_title_gif

    def __init__(self, title, torrent_link, download):
        self.title = title
        self.torrent_link = torrent_link
        self.download = download
        self.imdb_url = None  # Defined by get_imdb_url()
        self.dir_title_gif = None # Defined by download_imdb_icon()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~ END MOVIE CLASS ~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

def get_links(link):
    """ Returns a list of (title, link, download_link) of a provided link """

    list_soup = BeautifulSoup(request.urlopen(link).read())

    # All download links are in a list.

    results = []

    # Get all torrent links from TPB specific URL
    # Iterate two lists at once (one to find movies, other to find downloads)
    for link, torrent in zip(list_soup.findAll('a', {'class': 'detLink'}),
                                links_in_soup(list_soup, 'magnet', '')):
        link_to = BASEURL + link.get('href')
        results.append(Movie(link.string, link_to, torrent))

    return results


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~ BEGIN GUI CLASS ~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

class Application(Frame):
    def create_list(self):
        """ Create label, and listbox """
        self.titleLabel = Label(self, text='Movies:')
        self.titleLabel.pack()

        self.movieList = Listbox(
            self, width=60, height=10,
            selectmode=BROWSE,
        )

        self.movieList.pack(fill='both', expand=True)

        for movie in self.data:
            self.movieList.insert(END, movie.title)

        # Preselect index 0 of list.
        self.movieList.select_set(0)

    def create_rest(self):
        """ Create buttons, labels, checkbox """
        self.torrentLinkButton = Button(self, text='Torrent link')
        self.torrentLinkButton.pack()

        self.moviePicture = Label(self, bg='black')
        self.moviePicture.pack(pady=10)

        self.subtitleVar = IntVar()
        self.subtitlesCheck = Checkbutton(self,
                                          text='Include Subtitles',
                                          variable=self.subtitleVar)
        self.subtitlesCheck.select()
        self.subtitlesCheck.pack()

        self.torrentDownloadButton = Button(self, text='Download Torrent')
        self.torrentDownloadButton.pack()

    def update_list(self):

        selected = self.movieList.curselection()
        if selected != self.current:
            self.list_changed(selected)
            self.current = selected
        # No '()' to prevent infinite recursion
        self.after(250, self.update_list)

    def list_changed(self, selected):
        """ If the list changes, this function is called
        to update the labels and buttons to reflect changes """

        index = int(selected[0])

        # Pull information from local data.
        movie = self.data[index]

        def update_download():
            downloader(movie.download)

            if self.subtitleVar.get() == 1:
                movie.get_subtitles()

        def update_image():

            movie.get_imdb_url()
            movie.download_imdb_icon()
            # Load the image for Tkinter use.
            photo = PhotoImage(file=movie.dir_title_gif)
            # Editing the moviePicture Label.
            self.moviePicture.config(
                image=photo,
                compound=BOTTOM,
            )
            # Add Hover stuff.
            self.moviePicture.bind('<Button-1>', lambda x: downloader(movie.imdb_url))
            self.moviePicture.bind('<Enter>', lambda event, i=self.moviePicture: i.configure(bg="blue"))
            self.moviePicture.bind('<Leave>', lambda event, i=self.moviePicture: i.configure(bg="black"))
            self.moviePicture.image = photo  # Must keep for reference.

        # Call the functions that update GUI.
        update_image()
        self.torrentDownloadButton.configure(command=update_download)
        self.torrentLinkButton.configure(command=lambda: downloader(movie.torrent_link))

    def __init__(self, data, master=None):

        Frame.__init__(self, master)
        master.minsize(width=500, height=650)
        master.maxsize(width=500, height=650)
        self.pack(padx=20, pady=10)

        # Allow access to data
        self.data = data

        # To be defined later.
        self.titleLabel = self.movieList = None
        self.torrentLinkButton = self.torrentDownloadButton = self.moviePicture = None
        self.subtitleVar = self.subtitlesCheck = None

        self.create_list()
        self.create_rest()

        # Update List
        self.current = None
        self.update_list()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~ END GUI CLASS ~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

# Create directory to store movie icons.
PICDIR = 'pics'
if not os.path.exists(PICDIR):
    os.makedirs(PICDIR)

BASEURL = 'http://thepiratebay.se/'
TOPHDMOVIES = BASEURL + 'top/207'  # The Top 100 Movies on TPB

root = Tk()
root.wm_title('Fetch, by Raymond Ho')

movies = get_links(TOPHDMOVIES)

app = Application(movies, master=root)
app.mainloop()
