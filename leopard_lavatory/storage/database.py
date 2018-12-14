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
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

# create all tables if they not exist yet
Base.metadata.create_all(engine)


def add_user_watchjob(user_email, watchjob_query):
    """Add a new user and watchjob to the database and relate them.

    Args:
        user_email (str): Email address of the new user.
        watchjob_query (dict): json object representing the search query of the watchjob.
    """
    with session_scope() as session:
        new_user = User(email=user_email)
        new_watchjob = Watchjob(query=json.dumps(watchjob_query))
        new_user.watchjobs.append(new_watchjob)
        session.add(new_user)
        session.add(new_watchjob)
        return new_user, new_watchjob


def add_request(user_email, watchjob_query):
    """Adds a new request to the database.

    Args:
        user_email (str): email address of the user
        watchjob_query (dict): the search query as json object
    """
    with session_scope() as session:
        new_request = UserRequest(email=user_email, query=json.dumps(watchjob_query))
        session.add(new_request)

        # persist so that the token gets generated
        session.flush()

        return new_request.confirm_token


def relate_user_watchjob(user, watchjob):
    """Relate an existing user to an existing watchjob.

    Args:
        user (User): the user object
        watchjob (Watchjob): the watchjob object
    """
    with session_scope() as session:
        user.watchjobs.append(watchjob)


def get_all_watchjobs():
    """Return all watchjob entries from database.
    Returns:
        List[Watchjob]: list of all watchjobs
    """
    with session_scope() as session:
        return session.query(Watchjob).all()


def get_watchjob(watchjob_id):
    """Return the specified watchjob from database.
    Returns:
        watchjob (Watchjob): the watchjob
    """
    with session_scope() as session:
        return session.query(Watchjob).filter(Watchjob.id == watchjob_id).first()


def update_last_case_id(watchjob, last_case_id):
    """Update the last case ID on a watchjob
    Args:
        watchjob: the watchjob to update
        last_case_id: the new last_case_id
    """
    with session_scope() as session:
        watchjob.last_case_id = last_case_id
        return session.commit()

def get_all_requests():
    """Return all user request entries from the database.
    Returns:
        List[UserRequest]: list of all user requests
    """
    with session_scope() as session:
        return session.query(UserRequest).all()


def delete_user(user):
    """Delete the given user from the database.
    Args:
        user (User): the user to delete
    """
    with session_scope() as session:
        session.delete(user)


def delete_watchjob(watchjob):
    """Delete the given watchjob from the database.
    Args:
        watchjob (Watchjob): the watchjob to delete
    """
    with session_scope() as session:
        session.delete(watchjob)
