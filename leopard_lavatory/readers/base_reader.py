#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This file holds a minimal working example.
"""

import sys
import time
import random
import logging
import mechanicalsoup


class BaseReader:
    """
    Providing common functionality for all readers.

    A StatfulBrowser from mechanicalsoup.
    Random sleep function for rate limiting.
    """

    def __init__(self, log_level=logging.INFO, avg_delay_seconds=5,
                 user_agent_string='Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.0.6'):
        self.avg_delay_seconds = avg_delay_seconds

        browser = mechanicalsoup.StatefulBrowser()
        browser.set_user_agent(user_agent_string)
        browser.set_debug(log_level == logging.DEBUG)
        self.browser = browser

        logger = logging.getLogger(self.__class__.__name__)
        logger.addHandler(logging.StreamHandler(sys.stdout))
        logger.setLevel(log_level)
        self.logger = logger

    def random_sleep(self):
        """Wait random number of seconds to avoid rate-limiting"""

        seconds = random.uniform(1, int(self.avg_delay_seconds) * 2)
        self.logger.debug('Waiting {:.2} seconds to avoid rate limiting.'.format(seconds))
        time.sleep(seconds)

    def set_avg_delay_seconds(self, avg_delay_seconds):
        """Set the average number of seconds to sleep when calling random_sleep()."""
        self.avg_delay_seconds = avg_delay_seconds
