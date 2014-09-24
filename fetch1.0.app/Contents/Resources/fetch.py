# Raymond Ho
# Sept 17, 2014

from bs4 import BeautifulSoup  # Used to parse HTML
from urllib import request, parse  # Used to generate URLs and open links
import subprocess  # Open sub processes..
import timeit

# This implements the GUI application for Fetch.
import os, os.path
from tkinter import *


WINDOWS = OSX = False
if os.name == 'nt':
    WINDOWS = True
elif os.name == 'posix':
    OSX = True


BASEURL = 'http://thepiratebay.se/'

# The Top 100 Movies on TPB
TOPHDMOVIES = BASEURL + 'top/207'

# A wrapper function, uses DRY method.


def linksInSoup(soupObject, startsWith='', contains='', count='list'):
    """
            Finds links in a BeautifulSoup object.
            If the link starts with 'startsWith', or 'contains' is IN the link,
            then the link will be appended to a list.
            If 'count' is 'single', break loop and return first one found.
            Else, exhaust loop, and return a list of all matches.
    """

    results = []

    for link in soupObject.findAll('a'):
        href = link.get('href')
        try:
            if startsWith and href.startswith(startsWith):
                results.append(href)
            elif contains and contains in href:
                results.append(href)

        except:
            continue

    if count == 'single':
        return results[0]
    return results


def getLinks(link):
    """ Returns a list of (title, link, downloadlink)} of a provided link """

    listSoup = BeautifulSoup(request.urlopen(link))

    # All download links are in a list.
    downloadLinks = linksInSoup(listSoup, 'magnet', '')

    results = []

    # Get all torrent links from TPB specific URL
    counter = 0
    for link in listSoup.findAll('a', {'class': 'detLink'}):

        linkto = BASEURL + link.get('href')
        triple = (link.string, linkto, downloadLinks[counter])
        results.append(triple)
        counter += 1

    return results


def downloader(link):
    """ Attempts to download from a link depending on your OS. """

    if WINDOWS:
        os.startfile(link)
    elif OSX:
        subprocess.call(['open', link])
    else:
        print('Your OS may not be supported at this time.')


def getSubtitles(title, language='english'):
    """ Get a list of Subtitles, return first one."""

    SUBSCENE = 'http://subscene.com/'
    SUBSCENELIST = SUBSCENE + '/subtitles/title?q=' + parse.quote_plus(title)

    subSoup = BeautifulSoup(request.urlopen(SUBSCENELIST).read())

    subList = linksInSoup(subSoup, '', language)
    # Append the full URL for every item in list
    subList = [SUBSCENE + x for x in subList]

    def downloadSubtitle(subSceneLink):
        """ Download a specific subtitle from a specific SubScene URL """

        subDownloadSoup = BeautifulSoup(request.urlopen(subSceneLink).read())

        # Base URL + the download link
        result = SUBSCENE + \
            linksInSoup(subDownloadSoup, '/subtitle/download', '', 'single')

        downloader(result)

    return downloadSubtitle(subList[0])


def imdbURL(title):
    """ Returns the IMDB link given a title"""

    # Strip periods, and replace with spaces.
    title = ''.join([x.replace('.', ' ') for x in list(title)])

    IMDB = 'http://www.imdb.com/find?q=' + parse.quote_plus(title) + '&s=tt'
    imdbSoup = BeautifulSoup(request.urlopen(IMDB).read())

    result = linksInSoup(imdbSoup, '/title', '', 'single')

    # Alternative option. Faster?
    # result = imdbSoup.find('td', {'class': 'result_text'})
    # title = result.get_text().strip()
    # url =  result.a['href']
    return 'http://www.imdb.com' + result


def imdbIcon(url):
    """ Returns a link to an icon of a specific movie from IMDb """

    linkSoup = BeautifulSoup(request.urlopen(url).read())
    link = linkSoup.find(itemprop='image')
    return (link['src'])


def mainMovies():

    movies = getLinks(TOPHDMOVIES)
    return movies


#title = 'Transformers.Age.of.Extinction.2014.1080p.WEB-DL.DD51.H264-RARBG'
#URL = imdbURL(title)
#print ('Timing functions...')
#times = 10
#print ('Get Movies: ', timeit.Timer('getLinks(TOPHDMOVIES)', 'from __main__ import TOPHDMOVIES,getLinks').timeit(times))
#print ('Get URL   : ', timeit.Timer('imdbURL(title)', 'from __main__ import title,imdbURL').timeit(times))
#print ('Get Sub   : ', timeit.Timer('getSubtitles(title)', 'from __main__ import title,getSubtitles').timeit(times))
#print ('Get Pic   : ', timeit.Timer('imdbIcon(URL)', 'from __main__ import URL,imdbIcon').timeit(times))


# ~~~~~~~~~~~~~~~~~~~ Begin GUI Stuff ~~~~~~~~~~~~~~~~~~ #

class Application(Frame):

    def createList(self, data):

        self.titleLabel = Label(self, text='Movies:')
        self.titleLabel.pack()

        self.movieList = Listbox(
            self, width=60, height=10,
            selectmode=BROWSE,
        )

        self.movieList.pack(fill='both', expand=True)

        for movie in data:
            title = movie[0]
            self.movieList.insert(END, title)

        # Preselect index 0 of list.
        self.movieList.select_set(0)
        
        # Store the data locally.
        self.data = data

    def createElse(self):

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

    def updateList(self):

        selected = self.movieList.curselection()
        if selected != self.current:
            self.listChanged(selected)
            self.current = selected
        # No '()' to prevent infinite recursion
        self.after(250, self.updateList)

    def listChanged(self, selected):
        ''' If the list changes, this function is called
        to update the labels and buttons to reflect changes'''

        index = int(selected[0])

        # Pull information from local data.
        title, url, download = self.data[index]

        if title not in imdbMap:
            imdbMap[title] = imdbURL(title)
        else:
            print('Found in map, dont gotta find the same URL again, yay!')

        def newIMDbLink(event):
            downloader(imdbMap[title])

        def newTorrentLink():
            downloader(url)

        def newTorrentDownload():
            downloader(download)

            if self.subtitleVar.get() == 1:
                getSubtitles(title)

        def updateImage():
            
            """ Given the IMDB icon, download it and convert it into a GIF (Tkinter compatible)"""

            ''' This was made 100x faster by simply checking if the file
                exists before fetching it again..'''

            dirTitle = PICDIR + '/' + title

            # GIF File not there. Fetch it.
            if not os.path.isfile(dirTitle+ '.gif'):
                print('File was not found, receiving..')
                photoLink = imdbIcon(imdbMap[title])
                # Save as JPG, convert to GIF after.
                request.urlretrieve(photoLink, dirTitle+'.jpg')

                if OSX:
                    #Change to GIF so Tkinter can use it.
                    subprocess.call(['sips', '-s', 'format', 'gif', dirTitle+'.jpg', '--out', dirTitle+'.gif'])

            photo = PhotoImage(file=PICDIR + '/' + title + '.gif')
            self.moviePicture.config(
                image=photo,
                compound=BOTTOM,
            )
            self.moviePicture.bind('<Button-1>', newIMDbLink)
            self.moviePicture.bind(
                '<Enter>',
                lambda event, h=self.moviePicture: h.configure(bg="blue"))

            self.moviePicture.bind(
                '<Leave>',
                lambda event, e=self.moviePicture: e.configure(bg="black"))
            self.moviePicture.image = photo  # This is for reference.


        updateImage()
        self.torrentDownloadButton.configure(command=newTorrentDownload)
        self.torrentLinkButton.configure(command=newTorrentLink)

    def __init__(self, data, master=None):

        Frame.__init__(self, master)
        master.minsize(width=500, height=650)
        master.maxsize(width=500, height=650)
        self.pack(padx=20, pady=10)
        self.createList(data)
        self.createElse()
        self.current = None
        self.updateList()

# Create directory to store movie icons.
PICDIR = 'pics'
if not os.path.exists('pics'):
    os.makedirs('pics')

# Instead of fetching the same imdb URL over and over,
# Conveniently store it in a map to access it anytime.
imdbMap = {}

root = Tk()
root.wm_title('Fetch, by Raymond Ho')

movies = mainMovies()

app = Application(movies, master=root)
app.mainloop()
