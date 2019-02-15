"""
Database class, general interface for storing different objects.
"""
import logging
import re
from contextlib import contextmanager
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy import create_engine, Column
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import sessionmaker, relationship

DB_URI = 'sqlite:///db_sthlm_addresses.sqlite'
LOG_ALL_SQL_STATEMENTS = False

LOG = logging.getLogger(__name__)


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
        fields = ', '.join(f'{k}={v}' for k, v in self.__dict__.items() if not k.startswith('_'))
        return f'<{self.__class__.__name__} ({fields})>'


# mix the custom Base table class above with the sqlalchemy declarative base
Base = declarative_base(cls=Base)


class Query(Base):
    """Queries (prefixes) used for getting entries"""
    # Query status constants
    TBD = -1  # query was not executed yet
    DEAD_END = 0  # query returned 0 results
    LEAF = 1  # query returned a non-zero, complete list of results (less than the maximum)
    EXPANDED = 2  # query returned the maximum number of results so it was expanded into subqueries

    prefix = Column(String(255))
    full_entry = Column(Boolean, default=False) # True if prefix is a full entry result (without number but one trailing space)
    num_results = Column(Integer, default=-1)
    status = Column(Integer, default=TBD)


class Character(Base):
    """Extra characters used in entries"""
    character = Column(String(255))


class RawEntry(Base):
    """Raw entry as returned from suggestions."""
    name = Column(String(255))
    key = Column(String(255))
    result = Column(String(255))
    section = Column(String(255))
    symbol = Column(String(255))
    x = Column(String(255))
    y = Column(String(255))

    query = Column(String(255))  # query uses to get the entry
    first = Column(Integer)  # 1 if it's the first entry with that name, 0 if it's a duplicate


class Entry(Base):
    """Street/Property without number."""
    # address  entry type constants
    UNKNOWN = -1
    STREET = 0
    PROPERTY = 1

    name = Column(String(255), unique=True)
    address_type = Column(Integer)

    x_min = Column(Float)
    x_max = Column(Float)
    y_min = Column(Float)
    y_max = Column(Float)

    numbers = relationship('EntryNumber', back_populates='entry')


class EntryNumber(Base):
    """House/Property number (for a street address with x/y coordinates)"""
    name = Column(String(255))
    x = Column(Float)
    y = Column(Float)

    entry_id = Column(Integer, ForeignKey('entry.id'))
    entry = relationship('Entry', back_populates='numbers')


# create db engine
engine = create_engine(DB_URI, echo=LOG_ALL_SQL_STATEMENTS)

# create session factory and a global session
Session = sessionmaker(bind=engine)


@contextmanager
def database_session():
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


def same_values(entry1, entry2):
    """Compare the values of two entries, excluding id, created_at and modified_at"""

    def same_value(val1, val2):
        return val1 == val2 or (not val1 and not val2)

    for a in ['name', 'key', 'result', 'section', 'symbol', 'x', 'y']:
        if not same_value(getattr(entry1, a), getattr(entry2, a)):
            return False

    return True


def add_raw_entry(dbs, name, values, query):
    """Add a new raw entry to the database.

    Args:
        dbs (sqlalchemy.orm.session.Session): database session
        name (str): name of the entry (key in raw return json)
        values (dict): json object representing the values in the return json
        query (str): the query string that returned the entry

    Returns:
        RawEntry: the newly created database record
    """
    new_entry = RawEntry(name=name, key=values.get('KEY'), result=values.get('RESULT'), section=values.get('SECTION'),
                         symbol=values.get('SYMBOL'), x=values.get('X'), y=values.get('Y'), query=query, first=1)

    existing_entry = dbs.query(RawEntry).filter(RawEntry.name == name).filter(RawEntry.first == 1).one_or_none()
    if existing_entry:
        if not same_values(existing_entry, new_entry):
            LOG.warning(f'Different values for same address. \nOld: {existing_entry}\nNew: {new_entry}')
        new_entry.first = 0
    else:
        LOG.debug(f'New entry: {new_entry}')

    dbs.add(new_entry)

    return new_entry


def parse_entry(dbs, raw_entry):
    """Parse a raw entry and add an Entry and EntryNumber records to the database. Returns the name of the entry
    if it was new, None otherwise.

    Args:
        dbs (sqlalchemy.orm.session.Session): database session
        raw_entry (RawEntry): the raw entry to parse

    Returns:
        Union(str, NoneType): name of the entry if it was new, None otherwise
    """
    regexp = re.compile('(?P<name>.*) (?P<number>[0-9A-Z:]{1,5})')
    match = re.fullmatch(regexp, raw_entry.name)

    if not match:
        LOG.warning(f'Could not parse {raw_entry.name}')
        return None

    entry_name = match.group('name')
    entry_number = match.group('number')
    entry_type = {'fa fa-square-o': Entry.PROPERTY,
                  'fa fa-map-marker': Entry.STREET}.get(raw_entry.symbol, Entry.UNKNOWN)
    x = float(raw_entry.x) if raw_entry.x else None
    y = float(raw_entry.y) if raw_entry.y else None

    existing_entry = dbs.query(Entry).filter(Entry.name == entry_name).one_or_none()
    if existing_entry:
        # check if same entry number exists already
        for existing_entry_number in existing_entry.numbers:
            if existing_entry_number.name == entry_number:
                LOG.debug(f'Entry {entry_name} already had an existing_entry_number entry for {entry_number}: '
                            f'{existing_entry_number}')
                if existing_entry_number.x != x or existing_entry_number.y != y:
                    LOG.warning(f'Got same number entry with different x/y coordinates.\n'
                                f'  Old {existing_entry_number}\nNew {raw_entry}')
                return None

        # add new number
        new_number = EntryNumber(name=entry_number, x=x, y=y, entry_id=existing_entry.id, entry=existing_entry)
        dbs.add(new_number)

        # update x/y_min/max
        if x and y:
            if x < existing_entry.x_min:
                existing_entry.x_min = x
            if x > existing_entry.x_max:
                existing_entry.x_max = x
            if y < existing_entry.y_min:
                existing_entry.y_min = y
            if y > existing_entry.y_max:
                existing_entry.y_max = y

        LOG.debug(f'Added {entry_number} to entry {entry_name}')
        return None

    else:
        new_entry = Entry(name=entry_name, address_type=entry_type, x_min=x, x_max=x, y_min=y, y_max=y)
        dbs.add(new_entry)
        new_number = EntryNumber(name=entry_number, x=x, y=y, entry_id=new_entry.id, entry=new_entry)
        dbs.add(new_number)
        LOG.debug(f'New entry {entry_name} with first number {entry_number}')
        return entry_name
