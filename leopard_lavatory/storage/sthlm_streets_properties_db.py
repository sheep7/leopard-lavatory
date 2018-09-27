"""
Database class, general interface for storing different objects.
"""
import logging

from leopard_lavatory.storage.database import Database


class SthlmStreetsPropertiesDb(Database):
    """Database to store Stockholm street addresses and property names."""

    def __init__(self):
        super().__init__(database_filename='sthlm_streets_properties.sqlitedb')

    def create_tables(self):
        """
        Create table. Fails if it already exists
        """
        query = '''CREATE TABLE 
                streets_properties (
                key TEXT,
                result TEXT,
                section TEXT,
                symbol TEXT,
                x TEXT,
                y TEXT)'''
        self.c.execute(query)
        self.log.debug(query)
        self.commit()

    def get_all(self):
        """ Returns all records from the database. """
        query = 'SELECT * FROM streets_properties'
        result = self.c.execute(query)
        return result.fetchall()
        # kolla https://stackoverflow.com/questions/3300464/how-can-i-get-dict-from-sqlite-query

    def insert_many(self, records):
        """Insert all provided records in database."""
        #TODO: take same format as gotten from parsing website json (or after transforming for
        #      comparing to make diffs
        query = '''INSERT INTO streets_properties VALUES (?,?,?,?,?,?)'''
        self.c.executemany(query, records)
        self.commit()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s %(name)s: %(message)s')
    db = SthlmStreetsPropertiesDb()
    # db.create_tables()
    db.insert_many( [tuple('abcdef'), tuple('ghijkl')] )
    print(db.get_all())
