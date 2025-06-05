from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    
    @field_validator('username')
    def username_must_be_valid(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if not v.isalnum():
            raise ValueError('Username must contain only letters and numbers')
        return v.lower()
    
    @field_validator('password')
    def password_must_be_strong(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenRefresh(BaseModel):
    refresh_token: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserInGroup(BaseModel):
    id: int
    username: str
    
    class Config:
        from_attributes = True

class FlashcardCreate(BaseModel):
    fach: str
    gruppe: str
    frage: str
    antworten: list[dict]  # [{"text": "...", "is_correct": true/false}, ...]
    
    @field_validator('antworten')
    def validate_answers(cls, v):
        if len(v) != 4:
            raise ValueError('Es müssen genau 4 Antworten angegeben werden')
        correct_count = sum(1 for answer in v if answer.get('is_correct', False))
        if correct_count != 1:
            raise ValueError('Es muss genau eine richtige Antwort geben')
        return v

class FlashcardUpdate(BaseModel):
    flashcard_id: int
    frage: str
    antworten: list[dict]  # [{"text": "...", "is_correct": true/false}, ...]
    
    @field_validator('antworten')
    def validate_answers(cls, v):
        if len(v) != 4:
            raise ValueError('Es müssen genau 4 Antworten angegeben werden')
        correct_count = sum(1 for answer in v if answer.get('is_correct', False))
        if correct_count != 1:
            raise ValueError('Es muss genau eine richtige Antwort geben')
        return v

class FlashcardDelete(BaseModel):
    flashcard_id: int


# Lobby/Session schemas
class SessionCreate(BaseModel):
    subject_name: str
    group_name: str


class SessionResponse(BaseModel):
    session_id: str
    join_code: str
    websocket_url: str


class ParticipantInfo(BaseModel):
    user_id: int
    username: str
    is_host: bool
    
    class Config:
        from_attributes = True


class SubjectInfo(BaseModel):
    id: int
    name: str
    
    class Config:
        from_attributes = True


class GroupInfo(BaseModel):
    id: int
    name: str
    
    class Config:
        from_attributes = True


class SessionDetails(BaseModel):
    id: str
    subject: SubjectInfo
    group: GroupInfo
    host: UserInGroup
    participants: List[ParticipantInfo]
    status: str
    join_code: str
    created_at: datetime
    flashcard_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


class SessionJoin(BaseModel):
    join_code: str


class InvitationSend(BaseModel):
    session_id: str
    invitee_username: str


class InvitationResponse(BaseModel):
    invitation_id: int
    status: str


class PendingInvitation(BaseModel):
    invitation_id: int
    session_id: str
    inviter: str
    subject: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class SessionStatusUpdate(BaseModel):
    status: str


# Game schemas
class GameStateResponse(BaseModel):
    session_id: str
    current_question_index: int
    current_flashcard_id: Optional[int]
    total_score: int
    max_possible_score: int
    status: str
    question_started_at: Optional[datetime]
    flashcard_count: int
    
    class Config:
        from_attributes = True


class QuestionResponse(BaseModel):
    flashcard_id: int
    question: str
    answers: List[dict]  # [{"id": 1, "text": "Answer text"}, ...]
    question_index: int
    total_questions: int
    
    class Config:
        from_attributes = True


class VoteCreate(BaseModel):
    session_id: str
    flashcard_id: int
    answer_id: int


class VoteResponse(BaseModel):
    user_id: int
    username: str
    answer_id: int
    voted_at: datetime
    
    class Config:
        from_attributes = True


class VotesUpdate(BaseModel):
    flashcard_id: int
    votes: List[VoteResponse]
    vote_counts: dict  # {"1": 3, "2": 1, "3": 0, "4": 2}


class QuestionResult(BaseModel):
    flashcard_id: int
    correct_answer_id: int
    was_correct: bool
    points_earned: int
    total_score: int
    winning_answer_id: int
    vote_counts: dict


class ChatMessageCreate(BaseModel):
    session_id: str
    message: str


class ChatMessageResponse(BaseModel):
    id: int
    user_id: int
    username: str
    message: str
    sent_at: datetime
    
    class Config:
        from_attributes = True


class GameResult(BaseModel):
    session_id: str
    total_score: int
    max_possible_score: int
    percentage: float
    status: str  # "won" or "lost"
    questions_answered: int
    total_questions: int