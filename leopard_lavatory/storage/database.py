"""
Database class, general interface for storing different objects.
"""
import logging
import sqlite3


class Database:
    """Database, saving objects to and reading them from persistent storage."""

    def __init__(self, database_filename='database.sqlite'):
        self.conn = sqlite3.connect(database_filename)
        self.c = self.conn.cursor()
        self.log = logging.getLogger(self.__class__.__name__)
        self.log.debug('Connected to sqlite database in file ' + database_filename)

    def commit(self):
        """Commit changes to database."""
        self.conn.commit()
