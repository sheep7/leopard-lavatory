#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Minimal working example of the currently implemented functionality.
"""

import json
import logging
from leopard_lavatory.readers.sthlm_sbk import SBKReader


def main():
    """Call SBKReader and print results for an example query."""
    reader = SBKReader(log_level=logging.DEBUG)

    address = 'Brunnsgatan 1'
    newer_than_case = '2008-09960'
    print('Getting all results for address {}, newer than case {}'.format(address, newer_than_case))
    test_cases = reader.get_cases(address, newer_than_case)

    print('Found {} results:'.format(len(test_cases)))
    print(json.dumps(test_cases, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
