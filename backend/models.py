from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    user_groups = relationship("UserGroupAssociation", back_populates="user")

class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    group_users = relationship("UserGroupAssociation", back_populates="group", cascade="all, delete-orphan")
    subjects = relationship("Subject", back_populates="group",cascade="all, delete-orphan")

class UserGroupAssociation(Base):
    __tablename__ = "user_group_associations"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    group_id = Column(Integer, ForeignKey("groups.id"))
    user = relationship("User", back_populates="user_groups")
    group = relationship("Group", back_populates="group_users")

class Invitation(Base):
    __tablename__ = "invitations"
    id = Column(Integer, primary_key=True, index=True)
    from_user_id = Column(Integer, ForeignKey("users.id"))
    to_user_id = Column(Integer, ForeignKey("users.id"))
    group_id = Column(Integer, ForeignKey("groups.id"))
    from_user = relationship("User", foreign_keys=[from_user_id])
    to_user = relationship("User", foreign_keys=[to_user_id])
    group = relationship("Group")

class Subject(Base):
    __tablename__ = "subjects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), index=True)
    group = relationship("Group", back_populates="subjects")
    flashcards = relationship("Flashcard", back_populates="subject", cascade="all, delete-orphan")

class Flashcard(Base):
    __tablename__ = "flashcards"
    id = Column(Integer, primary_key=True, index=True)
    question = Column(String)
    subject_id = Column(Integer, ForeignKey("subjects.id"), index=True)
    subject = relationship("Subject", back_populates="flashcards")
    answers = relationship("Answer", back_populates="flashcard", cascade="all, delete-orphan")

class Answer(Base):
    __tablename__ = "answers"
    id = Column(Integer, primary_key=True, index=True)
    antwort = Column(String)
    is_correct = Column(Boolean, default=False)
    flashcard_id = Column(Integer, ForeignKey("flashcards.id"), index=True)
    flashcard = relationship("Flashcard", back_populates="answers")
