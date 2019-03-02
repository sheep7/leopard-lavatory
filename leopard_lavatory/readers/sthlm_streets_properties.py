#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Class SthlmStreetsFastigheter

Crawling a list of all street addresses and property names from kartor.stockholm.se
"""
import json
import logging

from sqlalchemy import func

from leopard_lavatory.readers.base_reader import BaseReader
from leopard_lavatory.storage.db_sthlm_addresses import database_session, add_raw_entry, Query, Character, RawEntry, \
    parse_entry, Entry

LOG = logging.getLogger(__name__)


class SthlmStreetsProperties(BaseReader):
    """
    Reading from kartor.stockholm.se website.
    """
    url = 'https://kartor.stockholm.se'
    map_path = '/bios/dpwebmap/cust_sth/sbk/sthlm_sse/DPWebMap.html'
    suggestions_path = '/bios/webquery/app/baggis/web/web_query' \
                       '?section=search*all' \
                       '&resulttype=json' \
                       '&outcoordsys=EPSG:5850' \
                       '&1={prefix}' \
                       '&maxrows={maxrows}'

    max_rows = 100
    characters = list('ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÅ -:ÉÜ')

    def get_first_page(self):
        """Request front page to initiate session."""

        # get frontpage
        url = self.url
        LOG.debug('GET {}'.format(url))
        self.browser.open(url)
        # get page that frontpage would redirect to
        url = self.url + self.map_path
        LOG.debug('GET {}'.format(url))
        self.browser.open(url)
        current_page = self.browser.get_current_page()
        LOG.debug('Got page with title "{}"'.format(current_page.title.text.strip()))

    def get_suggestion_list(self, prefix, max_rows=10):
        """Request the suggestions for a given prefix and parse it into number of rows, streets and
        properties.

        This expects the website to return a json with both street addresses and fastighet names.
        Args:
            prefix (str): prefix for the suggestions, eg one letter
            max_rows (int): maximum number of suggestions that should be returned
        Returns:
            Tuple[int, dict, dict]: result as tuple containing num_rows, streets and properties:
                num_rows (int) - total number of returned results from website
                streets (dict) - dict with streets addresses (name and number) as keys and raw
                                 result rows as value
                properties (dict) - dict with property names (including numbers) as keys and raw
                                    result rows as value
        Throws:
            ConnectionError: when the connection to the API failed
        """
        url = self.url + self.suggestions_path.format(prefix=prefix, maxrows=max_rows)
        LOG.debug(f'Requesting suggestions for prefix "{prefix}" (max {max_rows} rows).')
        response = self.browser.open(url)
        LOG.debug(response.content)

        j = json.loads(response.content)
        num_rows = j['rows']
        streets = {}
        properties = {}
        for row in j['dbrows']:
            if row['SYMBOL'] == 'fa fa-square-o':
                assert row['RESULT'] not in properties
                properties[row['RESULT']] = row
            elif row['SYMBOL'] == 'fa fa-map-marker':
                assert row['RESULT'] not in streets
                streets[row['RESULT']] = row
            else:
                LOG.error('Result row with unknown type {}:\n {}'.format(row['SYMBOL'], row))

        return num_rows, streets, properties

    def load_characters(self, dbs):
        """Load previously stored additional characters from database."""
        extra_characters = dbs.query(Character).all()
        for character in extra_characters:
            if character.character not in self.characters:
                self.characters.append(character.character)
                LOG.info(f'Loaded extra character {character.character} from database.')
            else:
                LOG.error(f'Loaded extra character {character.character} from database but it was already in base set.')

    def update_characters(self, dbs, name):
        """Check if the given name contains characters not in the known list of characters yet and add them if so."""
        ignore = list('0123456789')
        for character in name:
            if character not in self.characters and character not in ignore:
                self.characters.append(character)
                new_character = Character(character=character)
                dbs.add(new_character)
                LOG.info(f'Encountered new character in name: {character} (in {name})')

    def expand_query(self, dbs, query):
        """Add new queries by appending a character to the given prefix for all known characters."""
        no_double = list(' :')
        expand_characters = list('0123456789') if query.full_entry else self.characters
        for character in expand_characters:
            skip = False
            for double_character in no_double:
                if query.prefix.endswith(double_character) and character == double_character:
                    skip = True
            if skip:
                continue
            status = Query.TBD
            if character == ' ':
                if query.prefix == '':
                    # skip space as first character
                    continue
                # mark query as expand only because its result are all known already (space in the end doesn't matter)
                status = Query.EXPAND_ONLY
            new_query = Query(prefix=query.prefix + character, status=status, full_entry=query.full_entry)
            dbs.add(new_query)
        dbs.commit()

    def process_result_entry(self, dbs, name, values, prefix):
        """Process one raw result from a query."""
        self.update_characters(dbs, name)
        raw_entry = add_raw_entry(dbs, name, values, prefix)
        new_entry = parse_entry(dbs, raw_entry)
        if new_entry:
            # first time seeing this street/property name, so add a query to explore all number entries for it
            new_query = Query(prefix=new_entry + ' ', status=Query.TBD, full_entry=True)
            dbs.add(new_query)

    def get_one(self, dbs, query):
        """Process one query."""
        prefix = query.prefix
        LOG.info(f'{prefix}  (processing query)')

        if query.status == Query.EXPAND_ONLY:
            LOG.info(f' EXP-O  Expanding expand-only query "{prefix}".')
            query.status = Query.EXPANDED
            self.expand_query(dbs, query)
            dbs.commit()
            return

        try:
            num_rows, streets, properties = self.get_suggestion_list(prefix, self.max_rows)
            query.num_results = num_rows

            if num_rows == 0:
                query.status = Query.DEAD_END
                LOG.info(f' DEAD  Got 0 results, marking prefix "{prefix}" as dead end.')
                return

            LOG.info(f'{num_rows}  rows received ({len(streets)} streets and {len(properties)} properties).')

            for name, values in streets.items():
                self.process_result_entry(dbs, name, values, prefix)
            for name, values in properties.items():
                self.process_result_entry(dbs, name, values, prefix)

            if num_rows < self.max_rows:
                query.status = Query.LEAF
                LOG.info(f' LEAF  Marking query "{prefix}" as leaf. (returned less than max rows, so a complete list)')
            else:
                LOG.info(f' EXPA  Expanding query "{prefix}". (returned max rows, so probably an incomplete list)')
                query.status = Query.EXPANDED
                self.expand_query(dbs, query)

            dbs.commit()
        except ConnectionError as e:
            LOG.warning(f' ERR  Query could not be completed, leaving it in status TBD (ConnectionError: {e})')

    def log_stats(self, dbs):
        num_raw_entries = dbs.query(RawEntry.id).filter(RawEntry.first == 1).count()
        entry_stats = dbs.query(Entry.address_type, func.count(Entry.address_type)).group_by(Entry.address_type).all()
        query_stats = dbs.query(Query.status, func.count(Query.status)).group_by(Query.status).all()
        extra_chars = [c.character for c in dbs.query(Character).all()]
        LOG.info(f'    {num_raw_entries} raw, {entry_stats} entries. queries: {query_stats}. chars: {extra_chars}')

    def search(self):
        """Iterate through queries with status to-be-done (TBD) and execute them (and expand them into new queries
        if necessary)"""
        with database_session() as dbs:
            num_queries = dbs.query(Query.id).count()
            if num_queries == 0:
                # initialize: add one new one-character query for each character from the known list of characters.
                self.expand_query(dbs, Query(prefix='', full_entry=False))
            self.load_characters(dbs)
            while True:
                try:
                    query = dbs.query(Query). \
                        filter(Query.status == Query.TBD). \
                        order_by(Query.full_entry.desc(), Query.created_at.asc()). \
                        limit(1). \
                        one_or_none()
                    if not query:
                        LOG.info('=======================================================\n'
                                 '= DONE! (no more queries with status TBD in database) =\n'
                                 '=======================================================')
                        break
                    self.get_one(dbs, query)
                    self.log_stats(dbs)
                    self.random_sleep()
                except (KeyboardInterrupt, SystemExit):
                    break


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    r = SthlmStreetsProperties()
    r.set_avg_delay_seconds(0)
    r.get_first_page()
    r.search()
