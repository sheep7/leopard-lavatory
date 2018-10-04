"""
Database class, general interface for storing different objects.
"""
import json
from datetime import datetime
from secrets import token_urlsafe

from sqlalchemy import DateTime, Integer, String
from sqlalchemy import create_engine, Column, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import sessionmaker, relationship

DB_URI = 'sqlite:///leopardlavatory.sqlite'
TOKEN_BYTES = 42
LOG_ALL_SQL_STATEMENTS=False


def create_token():
    """Create a new url safe, high-entropy string that can be used as access token for for
    example confirm, delete or modify operations.

    Returns:
        str: url safe, cryptographically secure token
    """
    return token_urlsafe(nbytes=TOKEN_BYTES)


class Base(object):
    """Define base table class.

    It uses the class name as table name and defines three default columns added to all tables:
    id, created_at and modified at."""

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
SESSION = Session()

# create all tables if they not exist yet
Base.metadata.create_all(engine)


def add_user_watchjob(user_email, watchjob_query):
    """Add a new user and watchjob to the database and relate them.

    Args:
        user_email (str): Email address of the new user.
        watchjob_query (json): json object representing the search query of the watchjob.
    """
    s = Session()
    new_user = User(email=user_email)
    new_watchjob = Watchjob(query=json.dumps(watchjob_query))
    new_user.watchjobs.append(new_watchjob)
    SESSION.add(new_user)
    SESSION.add(new_watchjob)
    SESSION.commit()
    return new_user, new_watchjob


def relate_user_watchjob(user, watchjob):
    """Relate an existing user to an existing watchjob.

    Args:
        user (User): the user object
        watchjob (Watchjob): the watchjob object
    """
    user.watchjobs.append(watchjob)
    SESSION.commit()

def get_all_watchjobs():
    return SESSION.query(Watchjob).all()

def delete_user(user):
    SESSION.delete(user)
    SESSION.commit()


def delete_watchjob(watchjob):
    SESSION.delete(watchjob)
    SESSION.commit()
