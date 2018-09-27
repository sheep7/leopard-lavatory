"""
Database class, general interface for storing different objects.
"""
import logging

from leopard_lavatory.storage.database import Database


class WatchJobStorage(Database):
    """Database, saving objects to and reading them from persistent storage."""

    def __init__(self):
        super().__init__(database_filename='watch_job.db')

    def create_tables(self):
        """
        Create all tables. Should only be run for a new database.
        """
        query = '''CREATE TABLE watch_jobs (
                id INTEGER PRIMARY KEY ASC,
                reader TEXT,
                parameters TEXT)'''
        self.c.execute(query)
        self.log.debug(query)
        self.commit()

    def get_all_watch_jobs(self):
        """
        Returns all watch_job records from the database.
        """
        query = 'SELECT id, reader, parameters FROM watch_jobs'
        result = self.c.execute(query)
        # TODO: RETURN


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s %(name)s: %(message)s')
    db = WatchJobStorage()
    db.create_tables()
    watch_jobs = db.get_all_watch_jobs()
    print(watch_jobs)
