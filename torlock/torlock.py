""" This is the search engine for Torlock torrent tracker """
#VERSION: 1.0
#AUTHOR: Douman (custparasite@gmx.se)

try:
    #python3
    from html.parser import HTMLParser
    from http.client import HTTPConnection as http
except ImportError:
    #python2
    from HTMLParser import HTMLParser
    from httplib import HTTPConnection as http

#qbt
from novaprinter import prettyPrinter
from helpers import download_file

class torlock(object):
    """ Class for search engine """
    def __init__(self):
        self.url = "http://www.torlock.com"
        self.name = "Torlock"
        self.supported_categories = {'all'      : 'all',
                                     'anime'    : 'anime',
                                     'software' : 'software',
                                     'games'    : 'game',
                                     'movies'   : 'movie',
                                     'music'    : 'music',
                                     'tv'       : 'television',
                                     'books'    : 'ebooks'}

    def download_torrent(self, info):
        print(download_file(info))

    class MyHtmlParseWithBlackJack(HTMLParser):
        """ Sub-class for parsing results """
        def __init__(self, list_searches):
            HTMLParser.__init__(self)
            self.look_searches = True #whatever to look or not for next search pages
            self.found_pag = False #when next results are found
            self.list_searches = list_searches
            self.engine_url = None
            self.article_found = False #true when <article> with results is found
            self.item_found = False
            self.current_item = None #dict for found item
            self.item_name = None #key's name in current_item dict
            self.parser_class = {"ts"  : "size",
                                 "tul" : "seeds",
                                 "tdl" : "leech"}

        def handle_starttag(self, tag, attrs):
            if self.item_found:
                if tag == "td":
                    params = dict(attrs)
                    try:
                        self.item_name = self.parser_class[params["class"]]
                    except KeyError:
                        self.item_name = None

            elif self.look_searches and tag == "div":
                try:
                    self.found_pag = "pag" in attrs[0]
                except IndexError:
                    self.found_pag = False


            elif self.article_found and tag == "a":
                params = dict(attrs)
                try:
                    link = params["href"]
                except KeyError:
                    link = None

                if link is not None:
                    if link.startswith("/torrent"):
                        self.current_item["desc_link"] = link
                        self.current_item["link"] = "".join(("http://www.torlock.com/tor/", link.split('/')[1], ".torrent"))
                        self.current_item["engine_url"] = self.engine_url
                        self.item_found = True
                        self.item_name = "name"
                    elif self.found_pag:
                        if link.startswith("http"):
                            self.list_searches.append(link)

            elif tag == "article":
                self.article_found = True
                self.current_item = {}

        def handle_data(self, data):
            if self.item_name:
                self.current_item[self.item_name] = data
                self.item_name = None

        def handle_endtag(self, tag):
            if tag == "article":
                self.article_found = False
            elif self.item_found and tag == "tr":
                self.item_found = False
                prettyPrinter(self.current_item)
                self.current_item = {}

    def search(self, query, cat='all'):
        """ Performs search """
        connection = http("www.torlock.com")

        cat = cat.lower()
        #/[category]/torrents/[query].html?sort=seeds
        query = "".join((self.url, "/", self.supported_categories[cat], "/torrents/", query, ".html?sort=seeds"))
        connection.request("GET", query)
        response = connection.getresponse()
        if response.status != 200:
            return

        list_searches = []
        parser = self.MyHtmlParseWithBlackJack(list_searches)
        parser.engine_url = self.url
        parser.feed(response.read().decode('utf-8'))
        parser.close()

        #run through additional pages with results if any...
        parser.look_searches = False
        print(list_searches)
        for page in list_searches:
            connection.request("GET", page)
            response = connection.getresponse()
            parser.feed(response.read().decode('utf-8'))
            parser.close()

        connection.close()
        return
