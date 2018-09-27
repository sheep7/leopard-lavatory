#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Class SthlmStreetsFastigheter

Crawling a list of all street addresses and fastighet names from kartor.stockholm.se
"""
import json
import logging

from leopard_lavatory.readers.base_reader import BaseReader


class SthlmStreetsProperties(BaseReader):
    """
    Reading from kartor.stockholm.se website.
    """
    url = 'https://kartor.stockholm.se'
    map_path = '/bios/dpwebmap/cust_sth/sbk/sthlm_sse/DPWebMap.html'
    suggestions_path = '/bios/webquery/app/baggis/web/web_query' \
                       '?section=search*all' \
                       '&resulttype=json' \
                       '&outcoordsys=EPSG:5850' \
                       '&1={prefix}' \
                       '&maxrows={maxrows}'

    def get_first_page(self):
        """Request front page to initiate session."""
        # get frontpage
        url = self.url
        self.logger.debug('GET {}'.format(url))
        self.browser.open(url)
        # get page that frontpage would redirect to
        url = self.url + self.map_path
        self.logger.debug('GET {}'.format(url))
        self.browser.open(url)
        current_page = self.browser.get_current_page()
        self.logger.debug('Got page with title "{}"'.format(current_page.title.text.strip()))

    def get_suggestion_list(self, prefix, max_rows=10):
        """Request the suggestions for a given prefix and parse it into number of rows, streets and
        properties.

        This expects the website to return a json with both street addresses and fastighet names.
        Returns:
            num_rows (int): total number of returned results from website
            streets (dict): dict with streets addresses (name and number) as keys and raw result
                            rows as value
            properties (dict): dict with property names (including numbers) as keys and raw result
                               rows as value
        """
        url = self.url + self.suggestions_path.format(prefix=prefix, maxrows=max_rows)
        self.logger.debug('Requesting suggestions for prefix {} (max {} rows).'.format(prefix,
                                                                                       max_rows))
        response = self.browser.open(url)
        self.logger.debug(response.content)

        j = json.loads(response.content)
        num_rows = j['rows']
        streets = {}
        properties = {}
        for row in j['dbrows']:
            if row['SYMBOL'] == 'fa fa-square-o':
                assert row['RESULT'] not in properties
                properties[row['RESULT']] = row
            elif row['SYMBOL'] == 'fa fa-map-marker':
                assert row['RESULT'] not in streets
                streets[row['RESULT']] = row
            else:
                self.logger.error('Result row with unknown type {}:\n {}'.format(row['SYMBOL'],
                                                                                 row))

        return num_rows, streets, properties

    def get_all(self):
        """ Request all street addresses and fastigheter"""
        self.get_first_page()
        max_rows = 100000
        for prefix in list('ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÅ'):
            self.random_sleep()
            num_rows, streets, properties = self.get_suggestion_list(prefix, max_rows)
            if not num_rows < max_rows:
                self.logger.error('Probably missed results due to too low max_row value. Got {} '
                                  'rows and requested max {} rows.'.format(num_rows, max_rows))
            print(streets.keys())
            print(properties.keys())
            break


if __name__ == '__main__':
    s = SthlmStreetsProperties(log_level=logging.DEBUG)
    s.get_first_page()
