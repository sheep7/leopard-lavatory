#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mechanize import Browser
from bs4 import BeautifulSoup
import json
import logging
import sys
import urllib


cfg = {'url': 'http://insynsbk.stockholm.se/Byggochplantjansten/Arenden/',
       'user_agent_string': 'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.0.6',
       'form_name': 'aspnetForm',
       'address_field_name': 'ctl00$FullContentRegion$ContentRegion$SecondaryContentRegion$SearchPropertyAndCase$SearchProperty$AddressInput',
       'fastighetsbeteckning_field_name': 'ctl00$FullContentRegion$ContentRegion$SecondaryContentRegion$SearchPropertyAndCase$SearchProperty$PropertyIdInput',
       'search_button_name': 'ctl00$FullContentRegion$ContentRegion$SecondaryContentRegion$SearchPropertyAndCase$SearchButton',
       'search_button_value': 'Sök'}

class SBKReader:
    def __init__(self, debug=True):
        self.b = Browser()
        self.b.addheaders = [('User-agent', cfg['user_agent_string'])]

        logger = logging.getLogger("mechanize")
        logger.addHandler(logging.StreamHandler(sys.stdout))
        logger.setLevel(logging.INFO)
        self.logger = logger

        # avoid 404 roundtrip because of their missing robots.txt
        self.b.set_handle_robots(False)

        if debug:
            #########debug##################################################3
            # Log information about HTTP redirects and Refreshes.
            self.b.set_debug_redirects(True)
            # Print HTTP headers.
            self.b.set_debug_http(True)
            # To make sure you're seeing all debug output:
            #########debug##################################################3

    def search(self, address_query_value):
        self.b.open(cfg['url'])
        assert self.b.viewing_html()
        self.logger.info("Got page with title %s" % self.b.title())

        # fill form
        self.b.select_form(name=cfg['form_name'])
        self.b.form.set_all_readonly(False)

        self.b.form[cfg['address_field_name']] = address_query_value

        request = self.b.form.click()

        data = request.get_data() + '&' + urllib.urlencode({cfg['search_button_name']: cfg['search_button_value']})
        request.add_data(data)

        # send form
        self.b.open(request)

        assert self.b.viewing_html()
        self.logger.info("Got page with title %s" % self.b.title())

        return self.parseResponse(self.b.response().read())


    def nextPage(self):
        self.b.select_form(name=cfg['form_name'])
        self.b.form.set_all_readonly(False)

        self.b.form.new_control("hidden", "__EVENTTARGET", { "value": "ctl00$FullContentRegion$ContentRegion$SecondaryContentRegion$CaseList$CaseGrid", "id": "__EVENTTARGET" })
        self.b.form.new_control("hidden", "__EVENTARGUMENT", { "value": "Page$Next", "id": "__EVENTARGUMENT" })

        request = self.b.form.click()
        self.b.open(request)

        assert self.b.viewing_html()
        self.logger.info("Got page with title %s" % self.b.title())

        return self.parseResponse(self.b.response().read())


    def parseResponse(self, responseHTML):
        """Parse the html for a result table and return
        the table content in json friendly format"""

        s = BeautifulSoup(responseHTML, 'lxml')

        # TODO more specific criteria?
        all_rows = s.find_all('tr')

        cases = {}
        for row in all_rows:
            cells = row.find_all('td')
            # use only rows with 5 columns and a specific class to distinguish them from other table elements
            if len(cells) == 5 and cells[0].get('class') == ['DataGridItemCell']:
                case_id = cells[0].find_all('a')[0].string
                print "Found case with ID: %s" % case_id
                case = {}
                case['fastighet']   = cells[1].string.strip()
                case['type']        = cells[2].string.strip()
                case['description'] = cells[3].string.strip()
                case['date']        = cells[4].string.strip()
                cases[case_id] = case

        return cases


def main():
    reader = SBKReader()
    cases = reader.search("Brunnsgatan 1")

    print "Found %s results:" % len(cases)
    print json.dumps(cases, indent=2)

    cases = reader.nextPage()

    print "Found %s results:" % len(cases)
    print json.dumps(cases, indent=2)


if __name__ == "__main__":
    main()

