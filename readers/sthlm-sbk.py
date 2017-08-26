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
       'search_button_name': 'ctl00$FullContentRegion$ContentRegion$SecondaryContentRegion$SearchPropertyAndCase$SearchButton',
       'search_button_value': 'Sök'}


def fetchResults(address_query_value, cfg):
    """
    Fetch the website with the search form, enter the query value
    and return the resulting html response.
    mechanize handles all the post/redirect/get [1] confusion nicely
    for us.
    [1] https://en.wikipedia.org/wiki/Post/Redirect/Get
    """
    b = Browser()
    b.addheaders = [('User-agent', cfg['user_agent_string'])]

    # avoid 404 roundtrip because of their missing robots.txt
    b.set_handle_robots(False)

    #########debug##################################################3
    # Log information about HTTP redirects and Refreshes.
    b.set_debug_redirects(True)
    # Print HTTP headers.
    b.set_debug_http(True)
    # To make sure you're seeing all debug output:
    logger = logging.getLogger("mechanize")
    logger.addHandler(logging.StreamHandler(sys.stdout))
    logger.setLevel(logging.INFO)
    #########debug##################################################3

    b.open(cfg['url'])
    assert b.viewing_html()
    logger.info("Got page with title %s" % b.title())

    # fill form
    b.select_form(name=cfg['form_name'])
    b[cfg['address_field_name']] = address_query_value 

    # manual fix: add search button value to post data
    request = b.form.click()
    data = request.get_data() + '&' + urllib.urlencode({cfg['search_button_name']: cfg['search_button_value']}) 
    request.add_data(data)

    # send form
    b.open(request)

    return b.response().read()


def parseResponse(html):
    """Parse the html for a result table and return
    the table content in json friendly format"""

    s = BeautifulSoup(html, 'lxml')

    all_rows = s.find_all('tr')

    cases = {}
    for row in all_rows:
        cells = row.find_all('td')
        # use only rows with 5 columns and a specific class to distinguish them from other table elements
        if len(cells) == 5 and cells[0].get('class') == ['DataGridItemCell']:
            case_id = cells[0].find_all('a')[0].string
            case = {}
            case['fastighet']   = cells[1].string.strip()
            case['type']        = cells[2].string.strip() 
            case['description'] = cells[3].string.strip() 
            case['date']        = cells[4].string.strip() 
            cases[case_id] = case

    return cases


def main():
    html = fetchResults('Brunnsgatan 1',cfg)
    cases = parseResponse(html)

    print "Found %s results:" % len(cases)
    print json.dumps(cases, indent=2)


if __name__ == "__main__":
    main()

