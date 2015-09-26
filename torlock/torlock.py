""" This is the search engine for Torlock torrent tracker """
#VERSION: 1.9
#AUTHOR: Douman (custparasite@gmx.se)

try:
    #python3
    from html.parser import HTMLParser
    from http.client import HTTPSConnection as http
except ImportError:
    #python2
    from HTMLParser import HTMLParser
    from httplib import HTTPSConnection as http

from re import compile as re_compile

#qbt
from novaprinter import prettyPrinter
from helpers import download_file

class torlock(object):
    """ Class for search engine """
    url = "https://www.torlock.com"
    def __init__(self):
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
        def __init__(self):
            HTMLParser.__init__(self)
            self.look_searches = True #whenever to look or not for next search pages
            self.engine_url = None
            self.article_found = False #true when <article> with results is found
            self.item_found = False
            self.item_bad = False #set to True for malicious links
            self.current_item = None #dict for found item
            self.item_name = None #key's name in current_item dict
            self.parser_class = {"ts"  : "size",
                                 "tul" : "seeds",
                                 "tdl" : "leech"}

        def handle_starttag(self, tag, attrs):
            if self.item_found:
                if tag == "td":
                    params = dict(attrs)
                    if "class" in params:
                        self.item_name = self.parser_class.get(params["class"], None)
                        if self.item_name:
                            self.current_item[self.item_name] = ""

            elif self.article_found and tag == "a":
                params = dict(attrs)
                try:
                    link = params["href"]
                except KeyError:
                    link = None

                if link is not None:
                    if link.startswith("/torrent"):
                        self.current_item["desc_link"] = "".join((self.engine_url, link))
                        self.current_item["link"] = "".join(("http://www.torlock.com/tor/", link.split('/')[2], ".torrent"))
                        self.current_item["engine_url"] = self.engine_url
                        self.item_found = True
                        self.item_name = "name"
                        self.current_item["name"] = ""
                        self.item_bad = "rel" in params and params["rel"] == "nofollow"

            elif tag == "article":
                self.article_found = True
                self.current_item = {}

        def handle_data(self, data):
            if self.item_name:
                self.current_item[self.item_name] += data

        def handle_endtag(self, tag):
            if tag == "article":
                self.article_found = False
            elif self.item_name and (tag == "a" or tag == "td"):
                self.item_name = None
            elif self.item_found and tag == "tr":
                self.item_found = False
                if not self.item_bad:
                    prettyPrinter(self.current_item)
                self.current_item = {}

    def search(self, query, cat='all'):
        """ Performs search """
        cat = cat.lower()
        query = query.replace("%20", "-")
        connection = http("www.torlock.com")

        additional_pages = re_compile("/{0}/torrents/{1}.html\?sort=seeds&page=[0-9]+".format(self.supported_categories[cat], query))
        #/[category]/torrents/[query].html?sort=seeds
        query = "".join((self.url, "/", self.supported_categories[cat], "/torrents/", query, ".html?sort=seeds"))
        connection.request("GET", query)
        response = connection.getresponse()
        if response.status != 200:
            return

        data = response.read().decode('utf-8')

        list_searches = additional_pages.findall(data)[:-1] #last link is next(i.e. second)

        parser = self.MyHtmlParseWithBlackJack()
        parser.engine_url = self.url
        parser.feed(data)
        parser.close()

        #run through additional pages with results if any...
        for page in map(lambda link: "".join((self.url, link)), list_searches):
            connection.request("GET", page)
            response = connection.getresponse()
            data = response.read().decode('utf-8')
            parser.feed(data)
            parser.close()

        connection.close()
        return
