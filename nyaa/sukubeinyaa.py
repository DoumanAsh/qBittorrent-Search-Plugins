""" This is the search engine for Sukubei Nyaa torrent tracker """
#VERSION: 1.2
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

class ParserLogic():
    """ Structure with logical elements of parser """
    def __init__(self):
        self.look_searches = True
        self.found_results = False #found element with search results
        self.found_links = False #found element with next links to results
        self.save_item_name = None #name of element to save in qbt dict
        self.save_link_name = None #name of link to save in qbt dict

    def reset(self):
        """ Reset values of structure """
        self.__init__()

class sukubeinyaa(object):
    """ Class of search engine """
    url = "http://sukebei.nyaa.se"
    name = "Sukubei Nyaa"
    supported_categories = {'all'      : '0_0',
                            'anime'    : '7_25',
                            'books'    : '7_26',
                            'pictures' : '7_28',
                            'games'    : '7_27'}

    def download_torrent(self, info):
        print(download_file(info))

    class MyHtmlParseWithBlackJack(HTMLParser):
        def __init__(self, list_searches):
            HTMLParser.__init__(self)
            self.logic = ParserLogic()
            self.engine_url = None
            self.list_searches = list_searches
            self.current_item = None
            self.link_td_class = {"tlistname"     : "desc_link",
                                  "tlistdownload" : "link"}
            self.td_class = {"tlistsize" : "size",
                             "tlistsn"   : "seeds",
                             "tlistln"   : "leech"}

        def start_handler_table(self, tag, attrs):
            """ Handler of table with search results """
            if tag == "tr":
                try:
                    if not "tlisthead" in attrs[0]:
                        self.current_item = {}
                except IndexError:
                    pass

            elif tag == "td":
                params = dict(attrs)
                try:
                    self.logic.save_item_name = self.td_class[params["class"]]
                    self.current_item[self.logic.save_item_name] = ''
                except KeyError:
                    self.logic.save_item_name = None
                    try:
                        self.logic.save_link_name = self.link_td_class[params["class"]]
                    except KeyError:
                        self.logic.save_link_name = None

            elif tag == "a":
                if self.logic.save_link_name:
                    params = dict(attrs)
                    self.current_item[self.logic.save_link_name] = params['href']
                    if self.logic.save_link_name == "desc_link":
                        self.logic.save_item_name = "name"
                        self.current_item[self.logic.save_item_name] = ''
                        self.logic.save_link_name = None

        def handle_starttag(self, tag, attrs):
            if self.logic.found_results:
                self.start_handler_table(tag, attrs)

            elif tag == "table":
                try:
                    self.logic.found_results = "tlist" in attrs[0]
                except IndexError:
                    self.logic.found_results = False

            elif self.logic.look_searches:
                if self.logic.found_links:
                    if tag == "a" and self.list_searches.__len__() < 11:
                        params = dict(attrs)
                        self.list_searches.append(params['href'])

                elif tag == "div":
                    try:
                        self.logic.found_links = "pages" in attrs[0]
                    except IndexError:
                        self.logic.found_links = False

        def handle_data(self, data):
            if self.logic.save_item_name:
                temp_str = self.current_item[self.logic.save_item_name]
                self.current_item[self.logic.save_item_name] = "".join((temp_str, data))

        def handle_endtag(self, tag):
            if self.logic.save_item_name:
                if tag == "a" or tag == "td":
                    self.logic.save_item_name = None

            elif self.logic.found_links:
                self.logic.found_links = self.logic.look_searches = not tag == "div"

            elif self.logic.found_results:
                if tag == "tr" and self.current_item is not None:
                    self.current_item["engine_url"] = self.engine_url
                    #in case if status is unknown, Nyaa will hide needed tags
                    if not "seeds" in self.current_item:
                        self.current_item["seeds"] = "Unknown"
                    if not "leech" in self.current_item:
                        self.current_item["leech"] = "Unknown"
                    prettyPrinter(self.current_item)
                    self.current_item = None
                else:
                    self.logic.found_results = not "table" == tag

    def search(self, query, cat='all'):
        """ Performs search """
        cat = cat.lower()
        #?page=search&cats=[category]&filter=0&term=[query]
        query = "".join((self.url, "/?page=search&cats=", self.supported_categories[cat], "&filter=0&term=", query))

        connection = http("www.sukubei.nyaa.se")
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
        for page in list_searches:
            connection.request("GET", page)
            response = connection.getresponse()
            parser.feed(response.read().decode('utf-8'))
            parser.close()

        connection.close()
        return
