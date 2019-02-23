"""Testing reader and storage for sthlm_streets_properties."""
import pytest

from leopard_lavatory.readers.sthlm_streets_properties import SthlmStreetsProperties


class TestSthlmStreetsProperties:

    @pytest.mark.skip(reason='makes http request, skip for performance by default')
    def test_get_b_suggestion_10(self):
        sp_reader = SthlmStreetsProperties()
        sp_reader.get_first_page()
        # noinspection PyArgumentEqualDefault
        n, s, p = sp_reader.get_suggestion_list('B', 10)
        assert n == len(s) + len(p) == 10
