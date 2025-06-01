from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
import uuid

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    user_groups = relationship("UserGroupAssociation", back_populates="user")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

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
    name = Column(String, index=True)  # Removed unique=True
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

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="refresh_tokens")


class QuizSession(Base):
    __tablename__ = "quiz_sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    group_id = Column(Integer, ForeignKey("groups.id"))
    host_user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="waiting")  # waiting, in_progress, finished
    created_at = Column(DateTime, default=datetime.utcnow)
    join_code = Column(String, unique=True, index=True)
    
    # Relationships
    subject = relationship("Subject")
    group = relationship("Group")
    host = relationship("User")
    participants = relationship("SessionParticipant", back_populates="session", cascade="all, delete-orphan")
    invitations = relationship("LobbyInvitation", back_populates="session", cascade="all, delete-orphan")


class SessionParticipant(Base):
    __tablename__ = "session_participants"
    
    session_id = Column(String, ForeignKey("quiz_sessions.id"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    joined_at = Column(DateTime, default=datetime.utcnow)
    score = Column(Integer, default=0)
    is_host = Column(Boolean, default=False)
    
    # Relationships
    session = relationship("QuizSession", back_populates="participants")
    user = relationship("User")


class LobbyInvitation(Base):
    __tablename__ = "lobby_invitations"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("quiz_sessions.id"))
    inviter_id = Column(Integer, ForeignKey("users.id"))
    invitee_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="pending")  # pending, accepted, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("QuizSession", back_populates="invitations")
    inviter = relationship("User", foreign_keys=[inviter_id])
    invitee = relationship("User", foreign_keys=[invitee_id])
