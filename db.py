import enum

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import Column, Integer, String, ForeignKey, create_engine, Table

Base = declarative_base()


class DayEnum(enum.Enum):
    monday = 0
    tuesday = 1
    wednesday = 2
    thursday = 3
    friday = 4
    saturday = 5
    sunday = 6


class WeekEnum(enum.Enum):
    first = 0
    second = 1


association_table = Table(
    'association', Base.metadata,
    Column('group_id', Integer, ForeignKey('groups.id')),
    Column('lecture_id', Integer, ForeignKey('lectures.id')))


class Group(Base):
    '''A set of lectures'''
    __tablename__ = 'groups'

    id = Column(Integer, primary_key=True)
    name = Column(String)

    lectures = relationship('Lecture', secondary=association_table)


class Listener(Base):
    '''Subscriber to a group of lectures'''
    __tablename__ = 'listeners'

    # That should be used as a telegram chat id as well
    id = Column(Integer, primary_key=True)

    group_id = Column(Integer, ForeignKey('groups.id'))


class Lecture(Base):
    __tablename__ = 'lectures'

    id = Column(Integer, primary_key=True)

    # Name of the lecture
    name = Column(String)

    # Time of the lecture, `time` is minutes since the beginning of the day
    # so 10:25 will be 625 in the database
    day = Column(Integer)
    week = Column(Integer)
    time = Column(Integer)


class Database:
    def __init__(self, verbose=False):
        self.engine = create_engine('sqlite:///lectures.db', echo=verbose)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
