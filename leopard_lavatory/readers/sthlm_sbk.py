#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Class SBKReader.

Reading from Stockholms Stadsbyggndskontor website.
"""

from leopard_lavatory.readers.base_reader import BaseReader


class SBKReader(BaseReader):
    """Reader for the website of the Stockholm stadsbyggnadskontor (insynsbk.stockholm.se)."""

    url = 'http://insynsbk.stockholm.se/Byggochplantjansten/Arenden/'
    form_name = '#aspnetForm'
    field_name_prefix = 'ctl00$FullContentRegion$ContentRegion$SecondaryContentRegion$'
    event_target_field_name = 'CaseList$CaseGrid'
    address_field_name = 'SearchPropertyAndCase$SearchProperty$AddressInput'
    fastighetsbeteckning_field_name = 'SearchPropertyAndCase$SearchProperty$PropertyIdInput'
    search_button_name = 'SearchPropertyAndCase$SearchButton'
    search_button_value = 'Sök'

    def __init__(self, ignore_bostadsanpassning=True):
        self.ignore_bostadsanpassning = ignore_bostadsanpassning

    def parse_page(self, page):
        """Parse the page for a result table and return the table content in json friendly format.
        Args:
            page (bs4.BeautifulSoup): BeautifulSoup object representation of the page
        Returns:
            list[dict]: a list of the cases, each case is represented as a dict
        """
        all_rows = page.find_all('tr')

        cases = []
        for row in all_rows:
            cells = row.find_all('td')
            # use only rows with 5 columns and a specific class to distinguish them from other table
            #  elements
            if len(cells) == 5 and cells[0].get('class') == ['DataGridItemCell']:
                case_id = cells[0].find_all('a')[0].string
                self.log.debug('Found case with ID: %s', case_id)
                case = {'id': case_id,
                        'fastighet': cells[1].string.strip(),
                        'type': cells[2].string.strip(),
                        'description': cells[3].string.strip(),
                        'date': cells[4].string.strip()}
                if self.ignore_bostadsanpassning and case['type'] == "61 Bostadsanpassningsbidrag":
                    self.log.debug('Case is bostadsannpassningsbidrag, ignoring (because ignore_bostadsanpassning is True')
                else:
                    cases.append(case)

        return cases

    def get_first_page(self, address_query_value):
        """Requests the search page and issues a query with the given values. Returns the cases
        found on the first page of results.
        Args:
            address_query_value (str): the address query string
        Returns:
            list[dict]: a list of the cases, each case is represented as a dict
        """

        # requesting page with search form
        self.log.debug('Requesting %s', self.url)
        self.browser.open(self.url)
        current_page = self.browser.get_current_page()
        self.log.debug('Got page with title "%s"', current_page.title.text.strip())

        # fill form
        self.browser.select_form(self.form_name)
        self.browser[self.field_name_prefix + self.address_field_name] = address_query_value

        # get form to add the search_button key value pair (stupid ASP.NET)
        form = self.browser.get_current_form()
        form.new_control('input', self.field_name_prefix + self.search_button_name,
                         self.search_button_value)

        # send search request
        self.log.debug('Requesting first page of search results for address %s',
                       address_query_value)
        self.browser.submit_selected()

        current_page = self.browser.get_current_page()
        self.log.debug('Got page with title "%s"', current_page.title.text.strip())

        return self.parse_page(current_page)

    def get_next_page(self):
        """Request the next result page and return cases found on that.
        Returns:
            list[dict]: a list of the cases, each case is represented as a dict
        """

        self.browser.select_form(self.form_name)

        self.browser.new_control('hidden', '__EVENTTARGET', self.field_name_prefix +
                                 self.event_target_field_name)
        self.browser.new_control('hidden', '__EVENTARGUMENT', 'Page$Next')

        self.log.info('Requesting next page of search results')
        self.browser.submit_selected()

        current_page = self.browser.get_current_page()
        self.log.debug('Got page with title "%s"', current_page.title.text.strip())

        return self.parse_page(current_page)

    def get_cases(self, address_query_value, newer_than_case=None):
        """Get all cases newer than the case id provided in `newer_than_case`
        (diarienummer). This traverses arbitrarily many pages until the `newer_than_case` is
        found or all cases have been listed.
        Args:
            address_query_value (str): address query string
            newer_than_case (str): case id where to stop the backward search
        Returns:
            list[dict]: a list of the cases, each case is represented as a dict
        """

        cases = self.get_first_page(address_query_value)
        self.log.debug('[1] found %s cases', len(cases))

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

            self.random_sleep()

            # proceed to next page
            cases = self.get_next_page()
            self.log.debug('found %s cases', len(cases))

            # update state
            previous_case_ids = new_case_ids
