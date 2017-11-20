#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import random
import logging
import mechanicalsoup


class SBKReader:

    url = 'http://insynsbk.stockholm.se/Byggochplantjansten/Arenden/'
    user_agent_string = 'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.0.6'
    delay_seconds_avg = 5
    form_name = '#aspnetForm'
    field_name_prefix = 'ctl00$FullContentRegion$ContentRegion$SecondaryContentRegion$'
    event_target_field_name = 'CaseList$CaseGrid'
    address_field_name = 'SearchPropertyAndCase$SearchProperty$AddressInput'
    fastighetsbeteckning_field_name = 'SearchPropertyAndCase$SearchProperty$PropertyIdInput'

    def __init__(self, log_level=logging.INFO):

        browser = mechanicalsoup.StatefulBrowser()
        browser.set_user_agent(self.user_agent_string)
        browser.set_debug(log_level == logging.DEBUG)
        self.browser = browser

        logger = logging.getLogger(__name__)
        logger.addHandler(logging.StreamHandler(sys.stdout))
        logger.setLevel(log_level)
        self.logger = logger

    def parse_page(self, page):
        """Parse the page for a result table and return the table content in json friendly format.

        :param page: BeautifulSoup object representation of the page
        """
        all_rows = page.find_all('tr')

        cases = []
        for row in all_rows:
            cells = row.find_all('td')
            # use only rows with 5 columns and a specific class to distinguish them from other table elements
            if len(cells) == 5 and cells[0].get('class') == ['DataGridItemCell']:
                case_id = cells[0].find_all('a')[0].string
                self.logger.debug('Found case with ID: {}'.format(case_id))
                case = {'id':          case_id,
                        'fastighet':   cells[1].string.strip(),
                        'type':        cells[2].string.strip(),
                        'description': cells[3].string.strip(),
                        'date':        cells[4].string.strip()}
                cases.append(case)

        return cases

    def get_first_page(self, address_query_value):
        """Requests the search page and issues a query with the given values. Returns the cases found on the first
        page of results."""

        # requesting page with search form
        self.logger.debug('Requesting {}'.format(self.url))
        self.browser.open(self.url)
        current_page = self.browser.get_current_page()
        self.logger.debug('Got page with title "{}"'.format(current_page.title.text.strip()))

        # fill form
        self.browser.select_form(self.form_name)
        self.browser[self.field_name_prefix + self.address_field_name] = address_query_value

        # send search request
        self.logger.debug('Requesting first page of search results for address {}'.format(address_query_value))
        self.browser.submit_selected()

        current_page = self.browser.get_current_page()
        self.logger.debug('Got page with title "{}"'.format(current_page.title.text.strip()))

        return self.parse_page(current_page)

    def get_next_page(self):
        """Request the next result page and return cases found on that."""

        self.browser.select_form(self.form_name)

        self.browser.new_control('hidden', '__EVENTTARGET', self.field_name_prefix + self.event_target_field_name)
        self.browser.new_control('hidden', '__EVENTARGUMENT', 'Page$Next')

        self.logger.info('Requesting next page of search results')
        self.browser.submit_selected()

        current_page = self.browser.get_current_page()
        self.logger.debug('Got page with title "{}"'.format(current_page.title.text.strip()))

        return self.parse_page(current_page)

    def get_cases(self, address_query_value, newer_than_case=None):
        """Get all results after lastResult (identified by diarienummer, ie case ID). This traverses arbitrarily many
        pages to find the last result. """
        cases = self.get_first_page(address_query_value)
        self.logger.debug('[1] found {} cases'.format(len(cases)))

        result_cases = []

        # set to save ids of previous page, to detect whether we reached the last page
        # (when visiting the next page of the last page, we get the same results)
        previous_case_ids = set()

        while True:
            new_case_ids = set([case['id'] for case in cases])

            # stop if we don't get new cases
            if new_case_ids == previous_case_ids:
                return result_cases

            # read cases into result
            for case in cases:
                if case['id'] == newer_than_case:
                    # if we reached the newer_than_case, don't continue
                    return result_cases
                else:
                    result_cases.append(case)

            # wait random number of seconds to avoid rate-limiting
            seconds = random.uniform(1, int(self.delay_seconds_avg)*2)
            self.logger.debug('Waiting {:.2} seconds to avoid rate limiting.'.format(seconds))
            time.sleep(seconds)

            # proceed to next page
            cases = self.get_next_page()
            self.logger.debug('found {} cases'.format(len(cases)))

            # update state
            previous_case_ids = new_case_ids
