from sqlalchemy import Column, Float, Integer, String, Text, ForeignKey, DateTime, UniqueConstraint, LargeBinary
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.types import TypeDecorator
import uuid
import datetime
import json

Base = declarative_base()

# Utility for storing list[list[float]] as JSON
class JSONList(TypeDecorator):
    impl = Text

    def process_bind_param(self, value, dialect):
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        return json.loads(value)

# Table 1: Users
class User(Base):
    __tablename__ = 'users'

    user_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    first_name = Column(Text, nullable=False)
    last_name = Column(Text, nullable=False)
    email = Column(Text, nullable=False, unique=True)
    password_hash = Column(Text, nullable=False)  # <- Added for storing hashed password

# Table 2: MissingPersonsFrames
class MissingPersonsFrame(Base):
    __tablename__ = 'missing_persons_frames'

    missing_person_id = Column(String(36), ForeignKey("missing_persons.missing_person_id"), primary_key=True)
    frame_id = Column(Text, primary_key=True)
    missing_frame_id = Column(Integer, primary_key=True)
    cam_id = Column(Text, primary_key=True)
    timestamp = Column(Text)
    box = Column(JSONList)
    score = Column(Float)
    missing_person = relationship("MissingPersons", back_populates="frames")  # no change

# Table 3: MissingPersons
class MissingPersons(Base):
    __tablename__ = 'missing_persons'

    missing_person_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    first_name = Column(Text, nullable=False)
    last_name = Column(Text, nullable=False)
    details = Column(Text)
    photo = Column(LargeBinary)

    frames = relationship("MissingPersonsFrame", back_populates="missing_person")  # fixed