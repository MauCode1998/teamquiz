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