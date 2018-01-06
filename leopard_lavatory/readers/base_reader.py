#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import random
import logging
import mechanicalsoup


class BaseReader:

    delay_seconds_avg = 5
    user_agent_string = 'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.0.6'

    def __init__(self, log_level=logging.INFO):

        browser = mechanicalsoup.StatefulBrowser()
        browser.set_user_agent(self.user_agent_string)
        browser.set_debug(log_level == logging.DEBUG)
        self.browser = browser

        logger = logging.getLogger(self.__class__.__name__)
        logger.addHandler(logging.StreamHandler(sys.stdout))
        logger.setLevel(log_level)
        self.logger = logger

    def random_sleep(self):
        """Wait random number of seconds to avoid rate-limiting"""

        seconds = random.uniform(1, int(self.delay_seconds_avg)*2)
        self.logger.debug('Waiting {:.2} seconds to avoid rate limiting.'.format(seconds))
        time.sleep(seconds)
