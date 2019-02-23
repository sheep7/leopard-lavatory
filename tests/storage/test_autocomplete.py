"""Test storage package."""

from leopard_lavatory.storage.autocomplete import *


class TestAutocomplete:

    def test_add_suggestions(self):
        with autocomplete_db_session() as dbs:
            test_prefix = 'street-a'
            test_result = '{"street-a 1": [42.1,13.7], "street a 1b": [42.2,13.7]}'
            add_suggestion(dbs, test_prefix, test_result)

            suggestion = dbs.query(Suggestion).filter(Suggestion.prefix == test_prefix).one_or_none()

            assert suggestion.suggestions_json_str == test_result

            # clean up database
            dbs.delete(suggestion)

