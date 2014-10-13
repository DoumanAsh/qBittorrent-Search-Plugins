#VERSION: 0.7
#Author: Douman (custparasite@gmx.se)

#Note: python2 version

from novaprinter import prettyPrinter
from helpers import download_file
from HTMLParser import HTMLParser
import urllib2

class tokyotoshokan(object):
    def __init__(self):
        self.url = 'http://tokyotosho.info'
        self.name = 'Tokyo Toshokan'
        self.supported_categories = {'all': '0', 'anime': '1', 'games': '14' }
        #self.supported_categories = {'all': '0', 'anime': '1', 'anime(non-english)': '10',
        #                        'manga': '3', 'drama': '8', 'music': '2',
        #                        'music video': '9', 'raw': '7', 'hentai': '4',
        #                        'eroge': '14', 'batch': '11', 'jav': '15', 'other': '5'}
        #
    def download_torrent(self, info):
        print(download_file(info))

    class MyHtmlParseWithBlackJack(HTMLParser):
        def __init__(self, results, url, searchIndexes):
            HTMLParser.__init__(self)
            self.item_found = False
            self.item_found_numbers = 0
            self.item_name_found = False
            self.item_size_found = False
            self.item_stats_found = False
            self.item_stats_seed_found = False
            self.item_stats_leech_found = False
            self.current_item = None
            self.results = results
            self.url = url
            self.searchIndexes = searchIndexes
            self.searchNumber = 1

        def handle_starttag(self, tag, attrs):
            params = dict(attrs)
            if self.item_found:
                if tag == 'a':
                    if params['href'].startswith('magnet:'):
                        self.current_item['link'] = params['href']
                        self.item_found_numbers += 1
                    if params.get('type') == 'application/x-bittorrent':
                        self.item_name_found = True
                        self.current_item['name']  = ''
                        return
                elif tag == 'td':
                    if params.get('class') == 'desc-bot':
                        self.item_size_found = True
                        return
                    if params.get('class') == 'stats':
                        self.item_stats_found = True
                        return
                elif self.item_stats_found:
                    if tag == 'span':
                        if not self.item_stats_seed_found:
                            self.item_stats_seed_found = True
                            return
                        if not self.item_stats_leech_found:
                            self.item_stats_leech_found = True
                            return
            else:
                if tag == 'table':
                    if params.get('class') == 'listing':
                        self.item_found = True
                        self.current_item = {}
                elif tag == 'a':
                    if self.searchNumber < 5:
                        #save up to 5 next search results
                        if params['href'].startswith("?lastid="):
                            self.searchIndexes.append(''.join((self.url, '/search.php', params['href'])))
                            self.searchNumber += 1

        def handle_endtag(self, tag):
            if tag == 'a' and self.item_name_found:
                self.item_name_found = False
                self.item_found_numbers += 1
                return
            if self.item_found_numbers == 5:
                self.current_item['engine_url'] = self.url
                print(self.current_item)
                prettyPrinter(self.current_item)
                self.results += 1
                self.item_found_numbers = 0
                self.item_name_found = False
                self.item_size_found = False
                self.item_stats_found = False
                self.item_stats_seed_found = False
                self.item_stats_leech_found = False
                return
            if tag == 'table':
                if self.item_found:
                    self.item_found = False
                    self.item_found_numbers = 0
                    self.item_name_found = False
                    self.item_size_found = False
                    self.item_stats_found = False
                    self.item_stats_seed_found = False
                    self.item_stats_leech_found = False
                
        def handle_data(self, data):
            if self.item_name_found:
                self.current_item['name'] += data
            if self.item_size_found:
                self.current_item['size'] = 'unknown'
                #due to utf-8 encoding
                temp = data.split()
                if 'Size:' in temp: 
                    self.current_item['size'] = temp[temp.index('Size:') + 1]
                    self.item_found_numbers += 1
                    self.item_size_found = False
            if self.item_stats_leech_found:
                if data.isdigit():
                    self.current_item['leech'] = data
                    self.item_found_numbers += 1
                    self.item_stats_seed_found = False
                    self.item_stats_leech_found = False
            elif self.item_stats_seed_found:
                if data.isdigit():
                    self.current_item['seeds'] = data
                    self.item_found_numbers += 1

    def search(self, query, cat='all'):
        dat = ''
        results = 0
        searchIndexes = []
        parser = self.MyHtmlParseWithBlackJack(results, self.url, searchIndexes)
        dat = urllib2.urlopen('{0}/search.php?terms={1}&type={2}&size_min=&size_max=&username='.format(self.url, query.replace(' ', '+'), self.supported_categories[cat]))
        parser.feed(dat.read().decode('utf-8'))
        parser.close()
        for searchIn in searchIndexes:
            dat = urllib2.urlopen(searchIn)
            parser.feed(dat.read().decode('utf-8'))
            parser.close()
