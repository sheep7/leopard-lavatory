"""Test sthlm_sbk reader."""
import json

from leopard_lavatory.readers.sthlm_sbk import SBKReader


def test_sthlm_sbk():
    reader = SBKReader()

    address = 'Brunnsgatan 1'
    newer_than_case = '2008-09960'
    print('Getting all results for address {}, newer than case {}'.format(address, newer_than_case))
    test_cases = reader.get_cases(address, newer_than_case)

    print('Found {} results:'.format(len(test_cases)))
    print(json.dumps(test_cases, indent=2, ensure_ascii=False))

    assert len(test_cases) > 23



