"""
WatchJob class, representing the results from a query specified by a reader and search parameters.

TODO: look at inline todos further down
TODO: Create Alert class: watchjob + email address + most recent change that was delivered
"""
import json
import logging
import sys


class WatchJob:
    """Representing the results from a query specified by a reader and search parameters."""

    def __init__(self, street_address: str = None, fastighet_name: str = None,
                 log_level: int = logging.INFO):
        """
        Create a new WatchJob from address information and a notification email.

        The fields :street_address: and :fastighet_name: will be used for the search query. If both
        are specified they are considered to form a logical AND, so only cases that match both will
        be returned.

        :type street_address: str
        :type fastighet_name: str
        """
        self.search_parameters = {}
        if street_address is not None:
            self.search_parameters['street_address'] = street_address
        if fastighet_name is not None:
            self.search_parameters['fastighet_name'] = fastighet_name

        self.last_run = None

        logger = logging.getLogger(self.__class__.__name__)
        logger.addHandler(logging.StreamHandler(sys.stdout))
        logger.setLevel(log_level)
        self.logger = logger

    def serialize_search_parameters(self):
        """Convert the search parameters json into a string that can be stored in a database."""
        return json.dumps(self.search_parameters)

    def deserialize_search_parameters(self, search_parameters_str):
        """
        Deserialize a string into a search parameter json dict.
        :param search_parameters_str: a string representing a json of search parameters
        """
        search_parameters_dict = json.loads(search_parameters_str)
        street_address = search_parameters_dict.get('street_address', None)
        fastighet_name = search_parameters_dict.get('fastighet_name', None)
        if street_address is not None:
            self.search_parameters['street_address'] = street_address
        if fastighet_name is not None:
            self.search_parameters['fastighet_name'] = fastighet_name

    def run(self):
        """
        Run watch job.
        :return:
        """
        # TODO: call right reader and safe result back in database?


def get_all_watch_jobs() -> [WatchJob]:
    """
    Returns all watch jobs.
    """
    all_watch_jobs = []
    # TODO: fetch all watch_jobs from database
    return all_watch_jobs


def run_all_watch_jobs():
    """
    Get all watch jobs and run them.
    """
    all_watch_jobs = get_all_watch_jobs()
    for watch_job in all_watch_jobs:
        run_watch_job(watch_job)


def run_watch_job(watch_job: WatchJob):
    """
    Run a watch job.
    :param watch_job:
    """
    logging.debug('Running watch job %s', str(watch_job))
    watch_job.run()


def create_watch_job(house_description, notification_email):
    """
    Create a new watch job object from a house description and notification email address.
    :param house_description:
    :param notification_email:
    """
    logging.debug('Creating watch job from description %s for email %s', house_description,
                  notification_email)
    # TODO: implement


if __name__ == '__main__':
    # TODO: implement test watch job using create_watch_job()
    pass
