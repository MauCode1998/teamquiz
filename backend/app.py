from fastapi import FastAPI, HTTPException, Depends, status, WebSocket, WebSocketDisconnect
from fastapi.exceptions import RequestValidationError
from typing import List
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
import uvicorn
from schemas import (
    GruppenRequest,
    FachRequest,
    FachRenameRequest,
    FachDeleteRequest
)
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from db_operations import (
    create_group,
    is_user_in_group,
    create_flashcard,
    add_subject_to_group,
    get_group_id,update_subject_name,
    delete_group,
    get_group,
    delete_user_from_group,get_user_groups,
    get_subject_cards,
    delete_subject_from_group,get_invitations,
    create_invitation,
    add_user_to_group,
    delete_invitation,
    update_flashcard,
    delete_flashcard,
    start_game,
    get_game_state,
    cast_vote,
    get_question_votes,
    end_question,
    next_question,
    add_chat_message,
    calculate_final_result,
    get_chat_messages
)
import os
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from database import get_db, engine
from auth import hash_password, verify_password, create_access_token, create_refresh_token, get_current_user, validate_refresh_token, verify_token_websocket
from schemas import (
    UserCreate, Token, TokenRefresh, UserResponse, 
    FlashcardCreate, FlashcardUpdate, FlashcardDelete,
    SessionCreate, SessionResponse, SessionDetails, SessionJoin,
    InvitationSend, InvitationResponse, PendingInvitation, VoteCreate, 
    ChatMessageCreate
    
)
from models import (
    User, RefreshToken, Base, QuizSession, SessionParticipant,
    LobbyInvitation, Subject, Group, Flashcard
)
from datetime import datetime
import json
import random
import string
from websocket_manager import manager
from lobby_routes import router as lobby_router


app = FastAPI()

Base.metadata.create_all(bind=engine)

if os.path.exists("../frontend/build/static"):
    app.mount("/static", StaticFiles(directory="../frontend/build/static"), name="static")
    app.mount("/js", StaticFiles(directory="../frontend/build/static/js"), name="js")
    app.mount("/css", StaticFiles(directory="../frontend/build/static/css"), name="css")
elif os.path.exists("frontend/build/static"):
    app.mount("/static", StaticFiles(directory="frontend/build/static"), name="static")
    app.mount("/js", StaticFiles(directory="frontend/build/static/js"), name="js")
    app.mount("/css", StaticFiles(directory="frontend/build/static/css"), name="css")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  
    allow_headers=["*", "Authorization", "Content-Type"],
    expose_headers=["*"]
)

app.include_router(lobby_router)


def cleanup_old_sessions():
    """Clean up all existing sessions on server startup"""
    from database import SessionLocal
    from models import QuizSession, SessionParticipant, GameState, Vote, ChatMessage
    
    db = SessionLocal()
    try:
        db.query(Vote).delete()
        db.query(ChatMessage).delete()
        db.query(GameState).delete()
        db.query(SessionParticipant).delete()
        db.query(QuizSession).delete()
        
        db.commit()
        
       
        
    except Exception:
        db.rollback()
    finally:
        db.close()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": str(exc.body)}
    )


@app.post("/register", response_model=Token)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    existing_user = db.query(User).filter(
        (User.username.ilike(user_data.username)) | (User.email == user_data.email)
    ).first()
    
    if existing_user:
        if existing_user.username.lower() == user_data.username.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    hashed_password = hash_password(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password,
        is_active=True,
        is_verified=False
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    access_token = create_access_token(data={"sub": new_user.username})
    refresh_token_str, expires_at = create_refresh_token()
    
    refresh_token = RefreshToken(
        token=refresh_token_str,
        user_id=new_user.id,
        expires_at=expires_at
    )
    db.add(refresh_token)
    db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token_str,
        "token_type": "bearer"
    }

@app.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login with username and password"""
    user = db.query(User).filter(User.username.ilike(form_data.username)).first()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    access_token = create_access_token(data={"sub": user.username})
    refresh_token_str, expires_at = create_refresh_token()
    
    refresh_token = RefreshToken(
        token=refresh_token_str,
        user_id=user.id,
        expires_at=expires_at
    )
    db.add(refresh_token)
    db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token_str,
        "token_type": "bearer"
    }

@app.post("/refresh", response_model=Token)
async def refresh_token(token_data: TokenRefresh, db: Session = Depends(get_db)):
    """Get new access token using refresh token"""
    user = validate_refresh_token(token_data.refresh_token, db)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    access_token = create_access_token(data={"sub": user.username})
    
    return {
        "access_token": access_token,
        "refresh_token": token_data.refresh_token,
        "token_type": "bearer"
    }

@app.post("/logout")
async def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Logout and invalidate tokens"""
    db.query(RefreshToken).filter(RefreshToken.user_id == current_user.id).delete()
    db.commit()
    
    return {"message": "Successfully logged out"}

@app.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return current_user
        

@app.post("/gruppe-erstellen")
async def create_new_group(gruppenrequest: GruppenRequest, current_user: User = Depends(get_current_user)):
    print("gruppe wird erstellt!")
    print(gruppenrequest)
    username = current_user.username
    neue_gruppe = create_group(gruppenrequest.gruppen_name,username)
    print(neue_gruppe)

    return {"message":"Success!","content":"Gruppe erfolgreich angelegt"}




@app.post("/flashcard/create")
async def create_flashcard_new(flashcard_data: FlashcardCreate, current_user: User = Depends(get_current_user)):
    """Create a new flashcard with proper answer marking"""
    print(f"Creating flashcard: {flashcard_data.frage}")
    print(f"Subject: {flashcard_data.fach}, Group: {flashcard_data.gruppe}")
    print(f"Answers: {flashcard_data.antworten}")
    
    is_member = is_user_in_group(current_user.username, flashcard_data.gruppe)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this group"
        )
    
    antworten_for_db = [
        {"text": answer["text"], "is_correct": answer["is_correct"]}
        for answer in flashcard_data.antworten
    ]
    
    neue_karteikarte = create_flashcard(
        subjectname=flashcard_data.fach,
        groupname=flashcard_data.gruppe,
        frage=flashcard_data.frage,
        antwortdict=antworten_for_db
    )
    
    if neue_karteikarte:
        return {"message": "Success!", "content": "Karteikarte erfolgreich erstellt"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fehler beim Erstellen der Karteikarte"
        )


@app.post("/fach-erstellen")
async def create_new_fach(fachrequest: FachRequest, current_user: User = Depends(get_current_user)):

    result = add_subject_to_group(fachrequest.fach_name,fachrequest.gruppen_name)
    if result == "Subject ist bereits in der Gruppe angelegt":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Das Fach '{fachrequest.fach_name}' existiert bereits in dieser Gruppe"
        )
    elif result and isinstance(result, str):  # Other error message
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Erstellen des Fachs: {result}"
        )

    return {"message":"Success!","content":"Fach wurde erfolgreich angelegt"}


@app.put("/fach-umbenennen")
async def rename_fach(rename_request: FachRenameRequest, current_user: User = Depends(get_current_user)):
    print(f"Fach umbenennen: {rename_request.old_fach_name} -> {rename_request.new_fach_name}")
    username = current_user.username
    
    group_id = get_group_id(rename_request.gruppen_name)
    if not group_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gruppe '{rename_request.gruppen_name}' nicht gefunden"
        )
    
    if not is_user_in_group(username, rename_request.gruppen_name):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sie sind nicht berechtigt, Fächer in dieser Gruppe zu bearbeiten"
        )
    
    if not rename_request.new_fach_name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Der neue Fachname darf nicht leer sein"
        )
    
    result = update_subject_name(rename_request.old_fach_name, rename_request.new_fach_name.strip(), group_id)
    print(result)
    
    if result == "Subject existiert nicht in der Gruppe":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Das Fach '{rename_request.old_fach_name}' existiert nicht in dieser Gruppe"
        )
    elif result == "Ein Fach mit diesem Namen existiert bereits in der Gruppe":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ein Fach mit dem Namen '{rename_request.new_fach_name}' existiert bereits in dieser Gruppe"
        )
    elif result and isinstance(result, str) and result.startswith("Fehler"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Umbenennen des Fachs: {result}"
        )
    
    return {"message": "Success!", "content": f"Fach wurde erfolgreich von '{rename_request.old_fach_name}' zu '{rename_request.new_fach_name}' umbenannt"}


@app.delete("/fach-loeschen")
async def delete_fach(delete_request: FachDeleteRequest, current_user: User = Depends(get_current_user)):
    print(f"Fach löschen: {delete_request.fach_name} aus Gruppe {delete_request.gruppen_name}")
    username = current_user.username
    
    group_id = get_group_id(delete_request.gruppen_name)
    if not group_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gruppe '{delete_request.gruppen_name}' nicht gefunden"
        )
    
    if not is_user_in_group(username, delete_request.gruppen_name):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sie sind nicht berechtigt, Fächer in dieser Gruppe zu löschen"
        )
    
    result = delete_subject_from_group(delete_request.fach_name, group_id)
    print(result)
    
    if result == "Subject existiert nicht in der Gruppe":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Das Fach '{delete_request.fach_name}' existiert nicht in dieser Gruppe"
        )
    elif result and isinstance(result, str) and result.startswith("Fehler"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Löschen des Fachs: {result}"
        )
    
    return {"message": "Success!", "content": f"Fach '{delete_request.fach_name}' wurde erfolgreich gelöscht"}


@app.delete("/delete-group")
async def delete_group_route(gruppenrequest: GruppenRequest, current_user: User = Depends(get_current_user)):
    print("gruppe wird gelöscht!")
    print(gruppenrequest)
    username = current_user.username

    is_member = is_user_in_group(username,gruppenrequest.gruppen_name)
    if is_member:
        gelöschte_gruppe = delete_group(gruppenrequest.gruppen_name)
        print(gelöschte_gruppe)

        return {"message":"Success!","content":"Gruppe erfolgreich gelöscht"}
    else:
        return {"message":"Fail!","content":"Gruppe konnte nicht gelöscht werden"}

@app.delete("/leave-group")
async def leave_group_route(gruppenrequest: GruppenRequest, current_user: User = Depends(get_current_user)):
    print("gruppe wird verlassen!")
    print(gruppenrequest)
    username = current_user.username
    is_member = is_user_in_group(username,gruppenrequest.gruppen_name)
    if is_member:

      
     
        if len(get_group(gruppenrequest.gruppen_name)["users"]) == 1:
            gelöschte_gruppe = delete_group(gruppenrequest.gruppen_name)
            print(gelöschte_gruppe)
            print("Nur noch ein user. Gruppe wird gelöscht.")

            return {"message":"Success!","content":"Gruppe erfolgreich gelöscht"}
        else:
            
            gelöschte_gruppe = delete_user_from_group(username,gruppenrequest.gruppen_name)
            print(gelöschte_gruppe)

            return {"message":"Success!","content":"User ist aus der gruppe gelöscht"}
    else:
        return {"message":"Fail!","content":"Gruppe konnte nicht gelöscht werden"}





    
@app.get("/get-specific-group/")
async def get_gruppen_specifics(name: str, current_user: User = Depends(get_current_user)):
    user = current_user.username
    print(user)
    gruppen_info = get_group(name)
    print(gruppen_info)
    return {"message":"Success","content":gruppen_info}


@app.get("/get-gruppeninfo")
async def get_gruppen_info(current_user: User = Depends(get_current_user)):
    user = current_user.username
    gruppen = get_user_groups(user)
    print(gruppen)

    return {"message":"success","content":gruppen}

@app.get("/get-subject-cards/")
async def get_subject_cards_by_name(subjectname:str="OOP mit deiner Mum",gruppenname: str = "Bango"):
    print(f"Getting subject cards for: '{subjectname}' in group: '{gruppenname}'")
    cards: dict = get_subject_cards(subjectname,gruppenname)
    print(f"Cards result: {cards}")
    if not cards:
        print(f"Subject '{subjectname}' not found in group '{gruppenname}'")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Das Fach '{subjectname}' existiert nicht in der Gruppe '{gruppenname}'"
        )
    
    return {"message":"success","content":cards}

@app.get("/get-invitations")
async def get_those_invitations(current_user: User = Depends(get_current_user)):
    print("Einladungen abgefragt")
  
    username = current_user.username
    invitations = get_invitations(username)
    print("Alle Einladungen")

    return {"message":"success","content":invitations}

class InvitationRequest(BaseModel):
    gruppen_name: str
    username: str

@app.post("/send-invitation")
async def send_invitation_route(invitation_request: InvitationRequest, current_user: User = Depends(get_current_user)):
    """Send invitation to user to join group"""
    print(f"Sending invitation to {invitation_request.username} for group {invitation_request.gruppen_name}")
    
    from_username = current_user.username
    to_username = invitation_request.username
    groupname = invitation_request.gruppen_name
    
    is_member = is_user_in_group(from_username, groupname)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this group"
        )
    
    db = next(get_db())
    target_user = db.query(User).filter(User.username == to_username).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if is_user_in_group(to_username, groupname):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this group"
        )
    
    try:
        invitation = create_invitation(from_username, to_username, groupname)
        return {"message": "success", "content": invitation}
    except Exception as e:
        print(f"Error creating invitation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create invitation"
        )

class InvitationActionRequest(BaseModel):
    invitation_id: int

@app.post("/accept-invitation")
async def accept_invitation_route(invitation_action: InvitationActionRequest, current_user: User = Depends(get_current_user)):
    """Accept invitation and add user to group"""
    print(f"Accepting invitation {invitation_action.invitation_id}")
    
    username = current_user.username
    
    invitations = get_invitations(username)
    invitation = None
    for inv in invitations:
        if inv['id'] == invitation_action.invitation_id:
            invitation = inv
            break
    
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )
    
    try:
        add_user_to_group(username, invitation['To'])
        delete_invitation(invitation_action.invitation_id)
        return {"message": "success", "content": "User added to group"}
    except Exception as e:
        print(f"Error accepting invitation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to accept invitation"
        )

@app.post("/reject-invitation")
async def reject_invitation_route(invitation_action: InvitationActionRequest, current_user: User = Depends(get_current_user)):
    """Reject invitation and delete it"""
    print(f"Rejecting invitation {invitation_action.invitation_id}")
    
    username = current_user.username
    
    invitations = get_invitations(username)
    invitation = None
    for inv in invitations:
        if inv['id'] == invitation_action.invitation_id:
            invitation = inv
            break
    
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )
    
    try:
        delete_invitation(invitation_action.invitation_id)
        return {"message": "success", "content": "Invitation rejected"}
    except Exception as e:
        print(f"Error rejecting invitation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reject invitation"
        )

@app.put("/flashcard/update")
async def update_flashcard_endpoint(flashcard_data: FlashcardUpdate, current_user: User = Depends(get_current_user)):
    """Update an existing flashcard"""
    print(f"Updating flashcard ID: {flashcard_data.flashcard_id}")
    print(f"New question: {flashcard_data.frage}")
    print(f"New answers: {flashcard_data.antworten}")
    
    antworten_for_db = [
        {"text": answer["text"], "is_correct": answer["is_correct"]}
        for answer in flashcard_data.antworten
    ]
    
    result = update_flashcard(
        flashcard_id=flashcard_data.flashcard_id,
        frage=flashcard_data.frage,
        antwortdict=antworten_for_db
    )
    
    if "erfolgreich" in result or "aktualisiert" in result:
        return {"message": "Success!", "content": "Karteikarte erfolgreich aktualisiert"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result
        )

@app.delete("/flashcard/delete")
async def delete_flashcard_endpoint(flashcard_data: FlashcardDelete, current_user: User = Depends(get_current_user)):
    """Delete an existing flashcard"""
    print(f"Deleting flashcard ID: {flashcard_data.flashcard_id}")
    
    result = delete_flashcard(flashcard_data.flashcard_id)
    
    if "gelöscht" in result:
        return {"message": "Success!", "content": "Karteikarte erfolgreich gelöscht"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result
        )
    
    



def generate_join_code():
    """Generate a unique 6-character join code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


@app.post("/api/session/create", response_model=SessionResponse)
async def create_session(
    session_data: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new quiz session"""
    subject = db.query(Subject).filter(
        Subject.name == session_data.subject_name,
        Subject.group.has(name=session_data.group_name)
    ).first()
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found in specified group"
        )
    
    join_code = None
    while True:
        join_code = generate_join_code()
        existing = db.query(QuizSession).filter(QuizSession.join_code == join_code).first()
        if not existing:
            break
    
    session = QuizSession(
        subject_id=subject.id,
        group_id=subject.group_id,
        host_user_id=current_user.id,
        join_code=join_code,
        status="waiting"
    )
    db.add(session)
    db.commit()
    
    
    manager.join_group(current_user.id, f"lobby_{session.id}")
    print(f"🔥 CRITICAL FIX: Pre-added host {current_user.username} (ID: {current_user.id}) to lobby_{session.id} group (even without WebSocket)")
    
    participants = [{
        "user_id": current_user.id,
        "username": current_user.username,
        "is_host": True
    }]
    
    await manager.broadcast_to_group(f"lobby_{session.id}", {
        "type": "lobby_update",
        "session_id": session.id,
        "participants": participants,
        "status": session.status
    })
    
    return SessionResponse(
        session_id=session.id,
        join_code=join_code,
        websocket_url=f"/ws/{{token}}" #noqa
    )


@app.get("/api/session/{session_id}", response_model=SessionDetails)
async def get_session_details(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get session details including participants"""
    session = db.query(QuizSession).filter(QuizSession.id == session_id).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    flashcard_count = db.query(Flashcard).filter(
        Flashcard.subject_id == session.subject_id
    ).count()
    
    participant_list = []
    
    host_user = db.query(User).filter(User.id == session.host_user_id).first()
    if host_user:
        participant_list.append({
            "user_id": host_user.id,
            "username": host_user.username,
            "is_host": True
        })
    
    session_participants = db.query(SessionParticipant).filter(
        SessionParticipant.session_id == session_id
    ).all()
    
    for sp in session_participants:
        participant_user = db.query(User).filter(User.id == sp.user_id).first()
        if participant_user and participant_user.id != session.host_user_id:
            participant_list.append({
                "user_id": participant_user.id,
                "username": participant_user.username,
                "is_host": False
            })
    
    subject = db.query(Subject).filter(Subject.id == session.subject_id).first()
    group = db.query(Group).filter(Group.id == session.group_id).first()
    host = db.query(User).filter(User.id == session.host_user_id).first()
    
    return {
        "id": session.id,
        "subject": {"id": subject.id, "name": subject.name},
        "group": {"id": group.id, "name": group.name},
        "host": {"id": host.id, "username": host.username},
        "participants": participant_list,
        "status": session.status,
        "join_code": session.join_code,
        "created_at": session.created_at.isoformat(),
        "flashcard_count": flashcard_count
    }


@app.post("/api/session/join")
async def join_session(
    join_data: SessionJoin,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Join a session using join code"""
    session = db.query(QuizSession).filter(
        QuizSession.join_code == join_data.join_code
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid join code"
        )
    
    
    return {"message": "Ready to join", "session_id": session.id}


@app.post("/api/invitation/send", response_model=InvitationResponse)
async def send_invitation(
    invitation_data: InvitationSend,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send invitation to another user"""
    session = db.query(QuizSession).filter(QuizSession.id == invitation_data.session_id).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    invitee = db.query(User).filter(User.username == invitation_data.invitee_username).first()
    
    if not invitee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    existing_participant = db.query(SessionParticipant).filter(
        SessionParticipant.session_id == session.id,
        SessionParticipant.user_id == invitee.id
    ).first()
    
    if existing_participant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already in lobby"
        )
    
    existing_invitation = db.query(LobbyInvitation).filter(
        LobbyInvitation.session_id == session.id,
        LobbyInvitation.invitee_id == invitee.id,
        LobbyInvitation.status == "pending"
    ).first()
    
    if existing_invitation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation already sent"
        )
    
    if invitee.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selbst-Einladung nicht erlaubt"
        )
    
    invitation = LobbyInvitation(
        session_id=session.id,
        inviter_id=current_user.id,
        invitee_id=invitee.id,
        status="pending"
    )
    db.add(invitation)
    db.commit()
    
    invitation_data = {
        "invitation_id": invitation.id,
        "session_id": session.id,
        "inviter": current_user.username,
        "subject": session.subject.name,
        "created_at": invitation.created_at.isoformat()
    }
    await manager.send_invitation_notification(invitee.id, invitation_data)
    
    return InvitationResponse(
        invitation_id=invitation.id,
        status="sent"
    )


@app.get("/api/invitations/pending", response_model=List[PendingInvitation])
async def get_pending_invitations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get pending invitations for current user"""
    invitations = db.query(LobbyInvitation).filter(
        LobbyInvitation.invitee_id == current_user.id,
        LobbyInvitation.status == "pending"
    ).all()
    
    result = []
    for inv in invitations:
        if inv.session and inv.session.subject:
            result.append(PendingInvitation(
                invitation_id=inv.id,
                session_id=inv.session_id,
                inviter=inv.inviter.username,
                subject=inv.session.subject.name,
                created_at=inv.created_at
            ))
    
    return result


@app.post("/api/invitation/accept/{invitation_id}")
async def accept_invitation(
    invitation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Accept an invitation"""
    invitation = db.query(LobbyInvitation).filter(
        LobbyInvitation.id == invitation_id,
        LobbyInvitation.invitee_id == current_user.id
    ).first()
    
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )
    
    invitation.status = "accepted"
    db.commit()
    
    
    return {
        "session_id": invitation.session_id,
        "redirect_url": f"/lobby/{invitation.session_id}"
    }


@app.post("/api/invitation/reject/{invitation_id}")
async def reject_invitation(
    invitation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reject an invitation"""
    invitation = db.query(LobbyInvitation).filter(
        LobbyInvitation.id == invitation_id,
        LobbyInvitation.invitee_id == current_user.id
    ).first()
    
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )
    
    invitation.status = "rejected"
    db.commit()
    
    return {"status": "rejected"}




@app.post("/api/session/leave/{session_id}")
async def leave_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Leave a session"""
    participant = db.query(SessionParticipant).filter(
        SessionParticipant.session_id == session_id,
        SessionParticipant.user_id == current_user.id
    ).first()
    
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not in session"
        )
    
    session = db.query(QuizSession).filter(QuizSession.id == session_id).first()
    
    db.delete(participant)
    
    if participant.is_host:
        next_participant = db.query(SessionParticipant).filter(
            SessionParticipant.session_id == session_id,
            SessionParticipant.user_id != current_user.id
        ).order_by(SessionParticipant.joined_at).first()
        
        if next_participant:
            next_participant.is_host = True
            session.host_user_id = next_participant.user_id
        else:
            db.delete(session)
    
    db.commit()
    
    if session:
        await manager.broadcast_to_group(f"lobby_{session_id}", {
            "type": "participant_left",
            "username": current_user.username,
            "user_id": current_user.id
        })
    
    return {"message": "Left session"}



@app.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """WebSocket endpoint for real-time online user tracking"""
    db = next(get_db())
    
    user = verify_token_websocket(token, db)
    if not user:
        await websocket.close(code=1008)  # Close with "Policy Violation" code
        return
    
    await manager.connect(websocket, user.id, user.username)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "join_group":
                group_name = message["group_name"]
                manager.join_group(user.id, group_name)
                
                online_users = manager.get_online_users_in_group(group_name)
                await manager.broadcast_to_group(group_name, {
                    "type": "online_users_update",
                    "group_name": group_name,
                    "online_users": online_users
                })
                
            elif message["type"] == "leave_group":
                group_name = message["group_name"]
                manager.leave_group(user.id, group_name)
                
                online_users = manager.get_online_users_in_group(group_name)
                await manager.broadcast_to_group(group_name, {
                    "type": "online_users_update", 
                    "group_name": group_name,
                    "online_users": online_users
                })
                
            elif message["type"] == "join_lobby":
                session_id = message["session_id"]
                print(f"🔥 DEBUG: User {user.username} (ID: {user.id}) joining lobby_{session_id}")
                
                session = db.query(QuizSession).filter(QuizSession.id == session_id).first()
                if not session:
                    await websocket.send_text(json.dumps({"type": "error", "message": "Session not found"}))
                    continue
                
                existing_participant = db.query(SessionParticipant).filter(
                    SessionParticipant.session_id == session_id,
                    SessionParticipant.user_id == user.id
                ).first()
                
                if not existing_participant and user.id != session.host_user_id:
                    new_participant = SessionParticipant(
                        session_id=session_id,
                        user_id=user.id,
                        joined_at=datetime.utcnow()
                    )
                    db.add(new_participant)
                    db.commit()
                    print(f"🔥 DEBUG: Added {user.username} to session participants in DB")
                
                manager.join_group(user.id, f"lobby_{session_id}")
                print(f"🔥 DEBUG: After join_group - Lobby groups: {manager.group_users}")
                
                participants = []
                
                host_user = db.query(User).filter(User.id == session.host_user_id).first()
                if host_user:
                    participants.append({
                        "user_id": host_user.id,
                        "username": host_user.username,
                        "is_host": True
                    })
                
                session_participants = db.query(SessionParticipant).filter(
                    SessionParticipant.session_id == session_id
                ).all()
                
                for sp in session_participants:
                    participant_user = db.query(User).filter(User.id == sp.user_id).first()
                    if participant_user and participant_user.id != session.host_user_id:
                        participants.append({
                            "user_id": participant_user.id,
                            "username": participant_user.username,
                            "is_host": False
                        })
                
                print(f"🔥 DEBUG: Broadcasting lobby_update with {len(participants)} participants")
                
                await manager.broadcast_to_group(f"lobby_{session_id}", {
                    "type": "lobby_update",
                    "session_id": session_id,
                    "participants": participants,
                    "status": session.status
                })
                
              
                
            elif message["type"] == "join_game":
                session_id = message["session_id"]
                print(f"🔥 DEBUG: User {user.username} (ID: {user.id}) joining game_{session_id}")
                
                session = db.query(QuizSession).filter(QuizSession.id == session_id).first()
                if not session:
                    await websocket.send_text(json.dumps({"type": "error", "message": "Session not found"}))
                    continue
                
                participant = db.query(SessionParticipant).filter(
                    SessionParticipant.session_id == session_id,
                    SessionParticipant.user_id == user.id
                ).first()
                
                if not participant:
                    session = db.query(QuizSession).filter(QuizSession.id == session_id).first()
                    if session:
                        from models import UserGroupAssociation
                        is_group_member = db.query(UserGroupAssociation).filter(
                            UserGroupAssociation.user_id == user.id,
                            UserGroupAssociation.group_id == session.group_id
                        ).first()
                        
                        if is_group_member:
                            participant = SessionParticipant(
                                session_id=session_id,
                                user_id=user.id,
                                is_host=False,
                                joined_at=datetime.utcnow()
                            )
                            db.add(participant)
                            db.commit()
                            
                        else:
                            await websocket.send_text(json.dumps({"type": "error", "message": "Not a group member"}))
                            continue
                    else:
                        await websocket.send_text(json.dumps({"type": "error", "message": "Session not found"}))
                        continue
                
                manager.leave_group(user.id, f"lobby_{session_id}")
                print(f"🔥 DEBUG: User {user.username} left lobby_{session_id}")
                
                manager.join_group(user.id, f"game_{session_id}")
                print(f"🔥 DEBUG: User {user.username} joined game_{session_id}")
                
                await websocket.send_text(json.dumps({
                    "type": "game_joined",
                    "session_id": session_id
                }))
                
            elif message["type"] == "leave_lobby":
                session_id = message["session_id"]
                print(f"🔥 DEBUG: User {user.username} leaving lobby_{session_id}")
                
                session = db.query(QuizSession).filter(QuizSession.id == session_id).first()
                if not session:
                    continue
                
                if user.id != session.host_user_id:
                    db.query(SessionParticipant).filter(
                        SessionParticipant.session_id == session_id,
                        SessionParticipant.user_id == user.id
                    ).delete()
                    db.commit()
                    print(f"🔥 DEBUG: Removed {user.username} from session participants in DB")
                
                manager.leave_group(user.id, f"lobby_{session_id}")
                
                participants = []
                
                host_user = db.query(User).filter(User.id == session.host_user_id).first()
                if host_user:
                    participants.append({
                        "user_id": host_user.id,
                        "username": host_user.username,
                        "is_host": True
                    })
                
                session_participants = db.query(SessionParticipant).filter(
                    SessionParticipant.session_id == session_id
                ).all()
                
                for sp in session_participants:
                    participant_user = db.query(User).filter(User.id == sp.user_id).first()
                    if participant_user and participant_user.id != session.host_user_id:
                        participants.append({
                            "user_id": participant_user.id,
                            "username": participant_user.username,
                            "is_host": False
                        })
                
                print(f"🔥 DEBUG: Broadcasting lobby_update with {len(participants)} participants after leave")
                
                await manager.broadcast_to_group(f"lobby_{session_id}", {
                    "type": "lobby_update",
                    "session_id": session_id,
                    "participants": participants,
                    "status": session.status
                })
                
    except WebSocketDisconnect:
        print(f"🔥 DEBUG: WebSocket disconnect for {user.username}")
        
        for group_name in list(manager.group_users.keys()):
            if group_name.startswith("lobby_") and user.id in manager.group_users.get(group_name, []):
                session_id = group_name.replace("lobby_", "")
                session = db.query(QuizSession).filter(QuizSession.id == session_id).first()
                
                if session and user.id != session.host_user_id:
                    db.query(SessionParticipant).filter(
                        SessionParticipant.session_id == session_id,
                        SessionParticipant.user_id == user.id
                    ).delete()
                    db.commit()
                    print(f"🔥 DEBUG: Removed {user.username} from session {session_id} on disconnect")
                    
                    participants = []
                    
                    host_user = db.query(User).filter(User.id == session.host_user_id).first()
                    if host_user:
                        participants.append({
                            "user_id": host_user.id,
                            "username": host_user.username,
                            "is_host": True
                        })
                    
                    session_participants = db.query(SessionParticipant).filter(
                        SessionParticipant.session_id == session_id
                    ).all()
                    
                    for sp in session_participants:
                        participant_user = db.query(User).filter(User.id == sp.user_id).first()
                        if participant_user and participant_user.id != session.host_user_id:
                            participants.append({
                                "user_id": participant_user.id,
                                "username": participant_user.username,
                                "is_host": False
                            })
                    
                    await manager.broadcast_to_group(f"lobby_{session_id}", {
                        "type": "lobby_update",
                        "session_id": session_id,
                        "participants": participants,
                        "status": session.status
                    })
        
        await manager.disconnect(user.id)
    except Exception as e:
        print(f"WebSocket error for user {user.username}: {e}")
        await manager.disconnect(user.id)

@app.get("/api/online-users/{group_name}")
async def get_online_users_api(group_name: str, current_user: User = Depends(get_current_user)):
    """REST API endpoint to get online users in a group"""
    online_users = manager.get_online_users_in_group(group_name)
    return {"online_users": online_users}



@app.post("/api/game/start/{session_id}")
async def start_game_api(session_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Start the game (Host only)"""
    try:
        session = db.query(QuizSession).filter(QuizSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session nicht gefunden")
        
        if session.host_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Nur der Host kann das Spiel starten")
        
        result = start_game(session_id)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        session.status = "in_progress"
        db.commit()
        
        game_state_dict = result["game_state"]
        game_state_dict["flashcard_count"] = result["flashcard_count"]
        
        await manager.broadcast_to_group(f"game_{session_id}", {
            "type": "game_started",
            "session_id": session_id,
            "question": result["question"],
            "game_state": game_state_dict
        })
        
        return {"message": "Spiel gestartet", "question": result["question"], "game_state": game_state_dict}
        
    except Exception as e:
        print(f"Error starting game: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Starten des Spiels")


@app.get("/api/game/state/{session_id}")
async def get_game_state_api(session_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current game state"""
    try:
        participant = db.query(SessionParticipant).filter(
            SessionParticipant.session_id == session_id,
            SessionParticipant.user_id == current_user.id
        ).first()
        
        if not participant:
            session = db.query(QuizSession).filter(QuizSession.id == session_id).first()
            if not session:
                raise HTTPException(status_code=404, detail="Session nicht gefunden")
            
            from models import UserGroupAssociation
            is_group_member = db.query(UserGroupAssociation).filter(
                UserGroupAssociation.user_id == current_user.id,
                UserGroupAssociation.group_id == session.group_id
            ).first()
            
            if is_group_member:
                participant = SessionParticipant(
                    session_id=session_id,
                    user_id=current_user.id,
                    is_host=False,
                    joined_at=datetime.utcnow()
                )
                db.add(participant)
                db.commit()
            
            else:
                raise HTTPException(status_code=403, detail="Sie sind kein Mitglied dieser Gruppe")
        
        game_state = get_game_state(session_id)
        if not game_state:
            raise HTTPException(status_code=404, detail="Spielstatus nicht gefunden")
        
        return game_state
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting game state: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Abrufen des Spielstatus")


@app.post("/api/game/vote")
async def cast_vote_api(vote_data: VoteCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Cast or update vote"""
    
    
    try:
        participant = db.query(SessionParticipant).filter(
            SessionParticipant.session_id == vote_data.session_id,
            SessionParticipant.user_id == current_user.id
        ).first()
        
        if not participant:
            print(f"❌ VOTE API DEBUG - User {current_user.id} is not participant of session {vote_data.session_id}")
            raise HTTPException(status_code=403, detail="Sie sind kein Teilnehmer dieser Session")
        
       
        
        vote = cast_vote(vote_data.session_id, current_user.id, vote_data.flashcard_id, vote_data.answer_id)
        
      
        
        votes_data = get_question_votes(vote_data.session_id, vote_data.flashcard_id)
        
        await manager.broadcast_to_group(f"game_{vote_data.session_id}", {
            "type": "vote_update",
            "flashcard_id": vote_data.flashcard_id,
            "votes": votes_data["votes"],
            "vote_counts": votes_data["vote_counts"]
        })
        
        return {"message": "Stimme abgegeben", "vote_id": vote}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ VOTE API DEBUG - Error casting vote: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Fehler beim Abstimmen")


@app.get("/api/game/votes/{session_id}/{flashcard_id}")
async def get_votes_api(session_id: str, flashcard_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get votes for current question"""
    try:
        participant = db.query(SessionParticipant).filter(
            SessionParticipant.session_id == session_id,
            SessionParticipant.user_id == current_user.id
        ).first()
        
        if not participant:
            raise HTTPException(status_code=403, detail="Sie sind kein Teilnehmer dieser Session")
        
        votes_data = get_question_votes(session_id, flashcard_id)
        return votes_data
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting votes: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Abrufen der Stimmen")


@app.post("/api/game/end-question/{session_id}")
async def end_question_api(session_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """End current question and show results (Host only)"""
    try:
        session = db.query(QuizSession).filter(QuizSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session nicht gefunden")
        
        if session.host_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Nur der Host kann das Voting beenden")
        
        result = end_question(session_id)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        await manager.broadcast_to_group(f"game_{session_id}", {
            "type": "question_ended",
            "result": result
        })
        
        return {"message": "Frage beendet", "result": result}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error ending question: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Beenden der Frage")


@app.post("/api/game/next-question/{session_id}")
async def next_question_api(session_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """End current question and move to next (Host only)"""
    try:
        session = db.query(QuizSession).filter(QuizSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session nicht gefunden")
        
        if session.host_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Nur der Host kann zur nächsten Frage wechseln")
        
        current_state = get_game_state(session_id)
        
        if current_state and current_state.get("status") == "question_active":
            question_result = end_question(session_id)
            if "error" in question_result:
                raise HTTPException(status_code=400, detail=question_result["error"])
            
            await manager.broadcast_to_group(f"game_{session_id}", {
                "type": "question_ended",
                "result": question_result
            })
        
        next_result = next_question(session_id)
        
        if next_result["game_finished"]:
            await manager.broadcast_to_group(f"game_{session_id}", {
                "type": "game_finished",
                "result": next_result["result"]
            })
            
            session.status = "finished"
            db.commit()
            
            return {"game_finished": True, "result": next_result["result"]}
        else:
            await manager.broadcast_to_group(f"game_{session_id}", {
                "type": "new_question",
                "question": next_result["question"]
            })
            
            return {"game_finished": False, "question": next_result["question"]}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error moving to next question: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Wechsel zur nächsten Frage")


@app.post("/api/game/end/{session_id}")
async def end_game_api(session_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """End the game manually (Host only)"""
    try:
        session = db.query(QuizSession).filter(QuizSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session nicht gefunden")
        
        if session.host_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Nur der Host kann das Spiel beenden")
        
        from models import GameState
        game_state = db.query(GameState).filter(GameState.session_id == session_id).first()
        if game_state:
            game_state.status = "game_finished"
            game_state.ended_at = datetime.utcnow()
        
        session.status = "finished"
        db.commit()
        
        if game_state:
            percentage = (game_state.total_score / game_state.max_possible_score) * 100 if game_state.max_possible_score > 0 else 0
            result = {
                "session_id": session_id,
                "total_score": game_state.total_score,
                "max_possible_score": game_state.max_possible_score,
                "percentage": percentage,
                "status": "ended_manually",
                "questions_answered": game_state.current_question_index,
                "total_questions": game_state.max_possible_score // 100
            }
        else:
            result = {
                "session_id": session_id,
                "status": "ended_manually"
            }
        
        await manager.broadcast_to_group(f"game_{session_id}", {
            "type": "game_finished",
            "result": result
        })
        
        return {"message": "Spiel beendet", "result": result}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error ending game: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Beenden des Spiels")


@app.post("/api/game/chat")
async def send_chat_message_api(message_data: ChatMessageCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Send chat message"""
    try:
        participant = db.query(SessionParticipant).filter(
            SessionParticipant.session_id == message_data.session_id,
            SessionParticipant.user_id == current_user.id
        ).first()
        
        if not participant:
            raise HTTPException(status_code=403, detail="Sie sind kein Teilnehmer dieser Session")
        
        chat_message = add_chat_message(message_data.session_id, current_user.id, message_data.message)
        
        await manager.broadcast_to_group(f"game_{message_data.session_id}", {
            "type": "chat_message",
            "message": {
                "id": chat_message.id,
                "user_id": current_user.id,
                "username": current_user.username,
                "message": chat_message.message,
                "sent_at": chat_message.sent_at.isoformat()
            }
        })
        
        return {"message": "Nachricht gesendet", "message_id": chat_message.id}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error sending chat message: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Senden der Nachricht")


@app.get("/api/game/result/{session_id}")
async def get_game_result_api(session_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get final game result"""
    try:
        participant = db.query(SessionParticipant).filter(
            SessionParticipant.session_id == session_id,
            SessionParticipant.user_id == current_user.id
        ).first()
        
        if not participant:
            raise HTTPException(status_code=403, detail="Sie sind kein Teilnehmer dieser Session")
        
        result = calculate_final_result(session_id)
        if not result:
            raise HTTPException(status_code=404, detail="Spielergebnis nicht gefunden")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting game result: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Abrufen des Spielergebnisses")


@app.get("/api/game/chat/{session_id}")
async def get_chat_messages_api(session_id: str, limit: int = 50, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get chat messages"""
    try:
        participant = db.query(SessionParticipant).filter(
            SessionParticipant.session_id == session_id,
            SessionParticipant.user_id == current_user.id
        ).first()
        
        if not participant:
            raise HTTPException(status_code=403, detail="Sie sind kein Teilnehmer dieser Session")
        
        messages = get_chat_messages(session_id, limit)
        return {"messages": messages}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting chat messages: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Abrufen der Chat-Nachrichten")


@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    index_file = "../frontend/build/index.html"
    if os.path.exists(index_file):
        return FileResponse(index_file)
    elif os.path.exists("frontend/build/index.html"):
        return FileResponse("frontend/build/index.html")
    else:
        raise HTTPException(status_code=404, detail="Frontend build not found. Run 'npm run build' in frontend directory.")

Base.metadata.create_all(bind=engine)

if __name__ == '__main__':
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
