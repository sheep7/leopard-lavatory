"""
Database class for providing autocomplete suggestions for the address input
"""
from contextlib import contextmanager
from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy import create_engine, Column
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import sessionmaker

NUM_SUGGESTIONS = 10
DB_URI = 'sqlite:///leopardlavatory_autocomplete.sqlite'
LOG_ALL_SQL_STATEMENTS = False


class Base(object):
    """Define base table class.

    It uses the class name as table name and defines three default columns added to all tables:
    id, created_at and modified at."""

    # noinspection PyMethodParameters
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.now)
    modified_at = Column(DateTime, onupdate=datetime.now)

    def __repr__(self):
        """Make a pretty string representation of the object for debugging and logging."""
        fields = ', '.join(f"{k}={v}" for k, v in self.__dict__.items() if not k.startswith('_'))
        return f"<{self.__class__.__name__} ({fields})>"


# mix the custom Base table class above with the sqlalchemy declarative base
Base = declarative_base(cls=Base)


class Suggestion(Base):
    """Suggestion table and object."""
    input = Column(String(255), unique=True)
    suggestions_json_str = Column(String)


# create db engine
engine = create_engine(DB_URI, echo=LOG_ALL_SQL_STATEMENTS)

# create session factory
Session = sessionmaker(bind=engine)


@contextmanager
def autocomplete_db_session():
    """Provide a transactional scope around a series of operations."""
    dbs = Session()
    try:
        yield dbs
        dbs.commit()
    except:
        dbs.rollback()
        raise
    finally:
        dbs.close()


# create all tables if they not exist yet
Base.metadata.create_all(engine)


def add_suggestion(dbs, prefix, suggestions_json_str):
    """Add a new suggestion entry

    Args:
        dbs (sqlalchemy.orm.session.Session): database session
        prefix (str): the autocomplete prefix (partial user input)
        suggestions_json_str (str): json str representing the suggestions for the prefix
    """
    suggestion = Suggestion(prefix=prefix, suggestions_json_str=suggestions_json_str)
    dbs.add(suggestion)


def get_suggestions(dbs, prefix):
    """Return the suggestions for the given prefix or None if there are no suggestions for the prefix
    Args:
        dbs (sqlalchemy.orm.session.Session): database session
        prefix (str): the autocomplete prefix (partial user input)
    Returns:
        str: json str representing the suggestions for the prefix
    """
    suggestion = dbs.query(Suggestion).filter(Suggestion.prefix == prefix).one_or_none()
    if suggestion is None:
        return None
    return suggestion.suggestions_json_str


def get_all_suggestions(dbs):
    """Returns a dictionary mapping all prefixes to suggestions (to keep in memory for lower autocomplete latency)
    Args:
        dbs (sqlalchemy.orm.session.Session): database session
    Returns:
        dict: dictionary mapping prefix strings to json strings representing the suggestions for the prefix
    """
    all_suggestions = dbs.query(Suggestion).all()
    suggestions_dict = dict()
    for suggestion in all_suggestions:
        suggestions_dict[suggestion.prefix] = suggestion.suggestions_json_str
    return suggestions_dict
