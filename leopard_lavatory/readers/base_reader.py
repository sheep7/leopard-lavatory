#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Class BaseReader

Provides a mechanical soup browser and a sleep random time function.
"""

import logging
import random
import time

import mechanicalsoup


class BaseReader:
    """
    Providing common functionality for all readers.

    A StatfulBrowser from mechanicalsoup.
    Random sleep function for rate limiting.
    """

    def __init__(self, avg_delay_seconds=5,
                 user_agent_string='Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.0.6'):
        self.avg_delay_seconds = avg_delay_seconds

        logger = logging.getLogger(self.__class__.__name__)
        self.log = logger

        browser = mechanicalsoup.StatefulBrowser()
        browser.set_user_agent(user_agent_string)
        browser.set_debug(self.log.level == logging.DEBUG)
        self.browser = browser

    def random_sleep(self):
        """Wait random number of seconds to avoid rate-limiting"""

        seconds = random.uniform(1, int(self.avg_delay_seconds) * 2)
        self.log.debug('Waiting {:.2} seconds to avoid rate limiting.'.format(seconds))
        time.sleep(seconds)

    def set_avg_delay_seconds(self, avg_delay_seconds):
        """Set the average number of seconds to sleep when calling random_sleep().
        Args:
            avg_delay_seconds (int): the average delay in seconds
        """
        self.avg_delay_seconds = avg_delay_seconds
