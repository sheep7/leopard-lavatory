"""
Database class, general interface for storing different objects.
"""
import json
from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy import create_engine, Column, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import sessionmaker, relationship

from leopard_lavatory.utils import create_token
from contextlib import contextmanager

DB_URI = 'sqlite:///leopardlavatory.sqlite'
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

# user_watchjob table: many-to-many relation table to relate users to watchjobs
user_watchjob = Table('user_watchjob', Base.metadata,
                      Column('user_id', ForeignKey('user.id'), primary_key=True),
                      Column('watchjob_id', ForeignKey('watchjob.id'), primary_key=True))


class User(Base):
    """User table and object."""
    email = Column(String(255), unique=True)
    delete_token = Column(String(255), default=create_token)
    watchjobs = relationship('Watchjob', secondary=user_watchjob, back_populates='users')


class Watchjob(Base):
    """Watchjob table and object"""
    query = Column(String(255))
    last_case_id = Column(Integer, default=0)
    users = relationship('User', secondary=user_watchjob, back_populates='watchjobs')


class UserRequest(Base):
    """UserRequest table and object"""
    email = Column(String(255))
    query = Column(String(255))
    confirm_token = Column(String(255), default=create_token)


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


def add_user_watchjob(dbs, user_email, watchjob_query):
    """Add a new user and watchjob to the database and relate them.

    Args:
        dbs (sqlalchemy.orm.session.Session): database session
        user_email (str): Email address of the new user.
        watchjob_query (dict): json object representing the search query of the watchjob.
    """
    new_user = User(email=user_email)
    new_watchjob = Watchjob(query=json.dumps(watchjob_query))
    new_user.watchjobs.append(new_watchjob)
    dbs.add(new_user)
    dbs.add(new_watchjob)
    return new_user, new_watchjob


def add_request(dbs, user_email, watchjob_query):
    """Adds a new request to the database.

    Args:
        dbs (sqlalchemy.orm.session.Session): database session
        user_email (str): email address of the user
        watchjob_query (dict): the search query as json object
    """
    new_request = UserRequest(email=user_email, query=json.dumps(watchjob_query))
    dbs.add(new_request)

    # persist so that the token gets generated #TODO: check if that is still needed
    dbs.flush()

    return new_request.confirm_token


def get_all_watchjobs(dbs):
    """Return all watchjob entries from database.
    Returns:
        dbs (sqlalchemy.orm.dbs.Session): database session
        List[Watchjob]: list of all watchjobs
    """
    return dbs.query(Watchjob).all()


def get_watchjob(dbs, watchjob_id):
    """Return the specified watchjob from database.
    Returns:
        dbs (sqlalchemy.orm.session.Session): database session
        watchjob (Watchjob): the watchjob
    """
    return dbs.query(Watchjob).filter(Watchjob.id == watchjob_id).first()


def get_all_requests(dbs):
    """Return all user request entries from the database.
    Returns:
        dbs (sqlalchemy.orm.session.Session): database session
        List[UserRequest]: list of all user requests
    """
    return dbs.query(UserRequest).all()
