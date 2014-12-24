""" This is the search engine for Old Pirate Bay torrent tracker """
#VERSION: 1.2
#AUTHOR: Douman (custparasite@gmx.se)
#CONTRIBUTORS: Pedro (japabrasuka@gmail.com)

from novaprinter import prettyPrinter
from HTMLParser import HTMLParser
from helpers import download_file
from httplib import HTTPSConnection as https

class old_pirate_bay(object):
    """ Class for search engine """
    url = "https://oldpiratebay.org"
    name = "The Pirate Bay by ISOhunt"
    supported_categories = {'all'      : '',
                            'anime'    : '&iht=1',
                            'software' : '&iht=2',
                            'games'    : '&iht=3',
                            'movies'   : '&iht=5',
                            'music'    : '&iht=6',
                            'tv'       : '&iht=8',
                            'books'    : '&iht=9'}

    def download_torrent(self, info):
        print(download_file(info))

    class MyHtmlParseWithBlackJack(HTMLParser):
        """ Sub-class for parsing of search results """
        def __init__(self, res, url):
            HTMLParser.__init__(self)
            self.url = url
            self.res = res
            self.first_look = True
            self.current_item = None
            self.search_results = False #True when <tbody>, with search results, is reached
            self.search_entry = False #True when <tr>, with torrent entry, is reached
            self.desc_found = False
            self.result_state = None #set to value of dict key for handle_data() to save
            self.more_results = False #True when there are several pages of results
            self.save_next_link = False #True when link to page with next results is found

        def handle_starttag(self, tag, attrs):
            #torrent entry
            if self.search_entry:
                params = dict(attrs)
                if tag == "a":
                    href_link = params['href'].strip()
                    if href_link.startswith('magnet'):
                        self.current_item['link'] = href_link
                    elif href_link.startswith('/torrent'):
                        self.current_item['desc_link'] = href_link
                        self.desc_found = True

                elif tag == "td":
                    class_name = ''
                    if 'class' in params:
                        class_name = params['class']
                    else:
                        return

                    if class_name.startswith('size'):
                        self.result_state = 'size'
                    elif class_name.startswith('seed'):
                        self.result_state = 'seeds'
                    elif class_name.startswith('leech'):
                        self.result_state = 'leech'

                elif self.desc_found and tag == "span":
                    self.desc_found = False
                    self.result_state = 'name'

            #torrents table
            elif self.search_results:
                if tag == "tr":
                    self.search_entry = True
                    self.current_item = {}
                    self.current_item['engine_url'] = self.url

            #links to additional results
            elif self.more_results:
                params = dict(attrs)
                if tag == "li":
                    if params['class'] == 'page':
                        self.save_next_link = True
                elif tag == "a" and self.save_next_link:
                    self.res.append(params['href'].strip())
                    self.save_next_link = False

            else:
                #found table with search results
                if tag == "tbody":
                    self.search_results = True
                #found links to next pages with results
                elif self.first_look and tag == "div":
                    params = dict(attrs)
                    if "class" in params:
                        if params['class'] == "pagination":
                            self.more_results = True

        def handle_endtag(self, tag):
            if self.search_entry:
                if tag == "tr":
                    self.search_entry = False
                    self.result_state = None
                    prettyPrinter(self.current_item)
                    self.current_item = {}
            elif self.search_results:
                if tag == "tbody":
                    self.search_results = False
            elif self.more_results:
                if tag == "div":
                    self.more_results = False

        def handle_data(self, data):
            if self.result_state is not None:
                self.current_item[self.result_state] = data.strip()
                self.result_state = None

    def search(self, query, cat='all'):
        """ Performs search via this engine """
        #connect to tracker and get initial results
        #TODO: handle ssl problem?
        connection = https("oldpiratebay.org")

        cat = cat.lower()
        query = "".join(("/search.php?q=", query, self.supported_categories[cat]))
        connection.request("GET", query)
        response = connection.getresponse()

        list_searches = []
        parser = self.MyHtmlParseWithBlackJack(list_searches, self.url)
        parser.feed(response.read().decode('utf-8'))
        parser.close()

        parser.first_look = False
        #continue if there are more results(no more than 10 pages)
        for next_query in list_searches:
            connection.request("GET", next_query)
            response = connection.getresponse()
            parser.feed(response.read().decode('utf-8'))
            parser.close()
        connection.close()
