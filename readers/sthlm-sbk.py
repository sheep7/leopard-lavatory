#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mechanize import Browser
from bs4 import BeautifulSoup
import json
import logging
import sys
import urllib
import random
import time


cfg = {'url': 'http://insynsbk.stockholm.se/Byggochplantjansten/Arenden/',
       'user_agent_string': 'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.0.6',
       'delay_seconds_avg': 5,
       'form_name': 'aspnetForm',
       'address_field_name': 'ctl00$FullContentRegion$ContentRegion$SecondaryContentRegion$SearchPropertyAndCase$SearchProperty$AddressInput',
       'fastighetsbeteckning_field_name': 'ctl00$FullContentRegion$ContentRegion$SecondaryContentRegion$SearchPropertyAndCase$SearchProperty$PropertyIdInput',
       'search_button_name': 'ctl00$FullContentRegion$ContentRegion$SecondaryContentRegion$SearchPropertyAndCase$SearchButton',
       'search_button_value': 'Sök'}

class SBKReader:
    def __init__(self, logLevel=logging.INFO):
        self.b = Browser()
        self.b.addheaders = [('User-agent', cfg['user_agent_string'])]

        logger = logging.getLogger("mechanize")
        logger.addHandler(logging.StreamHandler(sys.stdout))
        logger.setLevel(logLevel)
        self.logger = logger

        # avoid 404 roundtrip because of their missing robots.txt
        self.b.set_handle_robots(False)

        if logLevel == logging.DEBUG:
            # Log information about HTTP redirects and Refreshes.
            self.b.set_debug_redirects(True)
            # Print HTTP headers.
            self.b.set_debug_http(True)

    def search(self, address_query_value):
        self.logger.info("Requesting %s" % cfg['url'])
        self.b.open(cfg['url'])
        assert self.b.viewing_html()
        self.logger.info("Got page with title %s" % self.b.title())

        # fill form
        self.b.select_form(name=cfg['form_name'])
        self.b.form.set_all_readonly(False)

        self.b.form[cfg['address_field_name']] = address_query_value

        self.logger.info("Requesting first page of search results for address=%s" % address_query_value)
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
        self.logger.info("Requesting next page of search results")
        self.b.open(request)

        assert self.b.viewing_html()
        self.logger.info("Got next page with title %s" % self.b.title())

        return self.parseResponse(self.b.response().read())

    def lastPage(self):
        self.b.select_form(name=cfg['form_name'])
        self.b.form.set_all_readonly(False)

        self.b.form.new_control("hidden", "__EVENTTARGET", { "value": "ctl00$FullContentRegion$ContentRegion$SecondaryContentRegion$CaseList$CaseGrid", "id": "__EVENTTARGET" })
        self.b.form.new_control("hidden", "__EVENTARGUMENT", { "value": "Page$Last", "id": "__EVENTARGUMENT" })

        request = self.b.form.click()
        self.logger.info("Requesting last page")
        self.b.open(request)

        assert self.b.viewing_html()
        self.logger.info("Got last page with title %s" % self.b.title())

        return self.parseResponse(self.b.response().read())


    def getUpdates(self, address_query_value, lastResult=None):
        """Get all results after lastResult (identified by Diarienummer, ie case ID). This traverses arbitrarily many
        pages to find the last result. """
        cases = self.search(address_query_value)

        resultCases = []

        # set to save ids of previous page, to detect whether we reached the last page
        # (when visiting the next page of the last page, we get the same results)
        previousCaseIds = set()

        while True:
            newCaseIds = set([case['id'] for case in cases])

            # stop if we don't get new cases
            if newCaseIds == previousCaseIds:
                return resultCases

            # read cases into result
            for case in cases:
                if case['id'] == lastResult:
                    # if we reached the last known result, stop looking
                    return resultCases
                else:
                    resultCases.append(case)

            # wait random number of seconds to avoid rate-limiting
            seconds = random.uniform(1,int(cfg['delay_seconds_avg'])*2)
            self.logger.info("Waiting %s seconds to avoid rate limiting." % seconds)
            time.sleep(seconds)

            # proceed to next page
            cases = self.nextPage()

            # update state
            previousCaseIds = newCaseIds


    def parseResponse(self, responseHTML):
        """Parse the html for a result table and return
        the table content in json friendly format"""

        s = BeautifulSoup(responseHTML, 'lxml')

        # TODO more specific criteria?
        all_rows = s.find_all('tr')

        cases = []
        for row in all_rows:
            cells = row.find_all('td')
            # use only rows with 5 columns and a specific class to distinguish them from other table elements
            if len(cells) == 5 and cells[0].get('class') == ['DataGridItemCell']:
                case_id = cells[0].find_all('a')[0].string
                self.logger.debug("Found case with ID: %s" % case_id)
                case = {}
                case['id']          = case_id
                case['fastighet']   = cells[1].string.strip()
                case['type']        = cells[2].string.strip()
                case['description'] = cells[3].string.strip()
                case['date']        = cells[4].string.strip()
                cases.append(case)

        return cases


def main():
    reader = SBKReader()

    # get all results for Brunnsgatan 1, newer than 2008-09660
    cases = reader.getUpdates("Brunnsgatan 1", "2008-09960")

    print "Found %s results:" % len(cases)
    print json.dumps(cases, indent=2)


if __name__ == "__main__":
    main()

