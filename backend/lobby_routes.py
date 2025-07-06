from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import secrets
from datetime import datetime

from database import get_db
from auth import get_current_user
from models import User, QuizSession, SessionParticipant, Subject, Group, Flashcard
from schemas import SessionResponse

router = APIRouter(prefix="/api/lobby", tags=["lobby"])

def generate_join_code():
    """Generate a unique join code"""
    return ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(6))

@router.post("/create")
async def create_lobby(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new lobby or return existing one"""
    subject_name = data.get("subject_name")
    group_name = data.get("group_name")
    
    # Get subject - first find the group
    group = db.query(Group).filter(Group.name == group_name).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Then find subject in that group
    subject = db.query(Subject).filter(
        Subject.name == subject_name,
        Subject.group_id == group.id
    ).first()
    
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    # Create new session (multiple sessions per subject are allowed)
    session = QuizSession(
        subject_id=subject.id,
        group_id=subject.group_id,
        host_user_id=current_user.id,
        join_code=generate_join_code(),
        status="waiting"
    )
    db.add(session)
    db.commit()
    
    # Add host as participant
    host_participant = SessionParticipant(
        session_id=session.id,
        user_id=current_user.id,
        is_host=True,
        joined_at=datetime.utcnow()
    )
    db.add(host_participant)
    db.commit()
    
    
    # Get participants (just host for now)
    participants = [{
        "user_id": current_user.id,
        "username": current_user.username,
        "is_host": True
    }]
    
    # We already have the group object from above
    
    return {
        "session": {
            "id": session.id,
            "join_code": session.join_code,
            "host": {"id": current_user.id, "username": current_user.username},
            "group": {"id": group.id, "name": group.name},
            "subject": {"id": subject.id, "name": subject.name}
        },
        "participants": participants
    }

@router.post("/join")
async def join_lobby_with_code(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Join a lobby using join code"""
    join_code = data.get("join_code")
    
    session = db.query(QuizSession).filter(
        QuizSession.join_code == join_code,
        QuizSession.status == "waiting"
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Invalid join code")
    
    # Check if already participant
    existing = db.query(SessionParticipant).filter(
        SessionParticipant.session_id == session.id,
        SessionParticipant.user_id == current_user.id
    ).first()
    
    if not existing and current_user.id != session.host_user_id:
        # Add as participant
        participant = SessionParticipant(
            session_id=session.id,
            user_id=current_user.id,
            joined_at=datetime.utcnow()
        )
        db.add(participant)
        db.commit()
        
        print(f"\n🔔 NEW PARTICIPANT JOINED:")
        print(f"   User: {current_user.username} (ID: {current_user.id})")
        print(f"   Session: {session.id}")
        print(f"   Join Code: {join_code}")
        print(f"   Time: {datetime.utcnow()}")
    
    # Get all participants
    participants = get_session_participants(db, session)
    
    # Get related objects
    subject = db.query(Subject).filter(Subject.id == session.subject_id).first()
    group = db.query(Group).filter(Group.id == session.group_id).first()
    host = db.query(User).filter(User.id == session.host_user_id).first()
    
    return {
        "session": {
            "id": session.id,
            "join_code": session.join_code,
            "host": {"id": host.id, "username": host.username},
            "group": {"id": group.id, "name": group.name},
            "subject": {"id": subject.id, "name": subject.name}
        },
        "participants": participants
    }

@router.post("/join-existing")
async def join_existing_session(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Join an existing session by subject/group"""
    subject_name = data.get("subject_name")
    group_name = data.get("group_name")
    
    # Get subject
    subject = db.query(Subject).join(Group).filter(
        Subject.name == subject_name,
        Group.name == group_name
    ).first()
    
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    # Find active session
    session = db.query(QuizSession).filter(
        QuizSession.subject_id == subject.id,
        QuizSession.status == "waiting"
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="No active session")
    
    # Add as participant if not already
    if current_user.id != session.host_user_id:
        existing = db.query(SessionParticipant).filter(
            SessionParticipant.session_id == session.id,
            SessionParticipant.user_id == current_user.id
        ).first()
        
        if not existing:
            participant = SessionParticipant(
                session_id=session.id,
                user_id=current_user.id,
                joined_at=datetime.utcnow()
            )
            db.add(participant)
            db.commit()
    
    # Get all participants
    participants = get_session_participants(db, session)
    
    # Get related objects
    group = db.query(Group).filter(Group.id == session.group_id).first()
    host = db.query(User).filter(User.id == session.host_user_id).first()
    
    return {
        "session": {
            "id": session.id,
            "join_code": session.join_code,
            "host": {"id": host.id, "username": host.username},
            "group": {"id": group.id, "name": group.name},
            "subject": {"id": subject.id, "name": subject.name}
        },
        "participants": participants
    }

@router.get("/{session_id}/participants")
async def get_lobby_participants(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current participants in lobby"""
    session = db.query(QuizSession).filter(QuizSession.id == session_id).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    participants = get_session_participants(db, session)
    
    # Log current participants
    print(f"\n📊 PARTICIPANT CHECK for Session {session_id}:")
    print(f"   Requested by: {current_user.username}")
    print(f"   Total participants: {len(participants)}")
    for p in participants:
        role = "HOST" if p.get("is_host") else "PARTICIPANT"
        print(f"   - {p['username']} ({role})")
    
    return {"participants": participants}

@router.post("/{session_id}/leave")
async def leave_lobby(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Leave a lobby"""
    session = db.query(QuizSession).filter(QuizSession.id == session_id).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # If host leaves, only delete session if not playing
    if current_user.id == session.host_user_id:
        if session.status == "waiting":
            # Delete all participants
            db.query(SessionParticipant).filter(
                SessionParticipant.session_id == session_id
            ).delete()
            # Delete session
            db.delete(session)
        # If game is playing/finished, don't delete session
    else:
        # Just remove participant
        db.query(SessionParticipant).filter(
            SessionParticipant.session_id == session_id,
            SessionParticipant.user_id == current_user.id
        ).delete()
    
    db.commit()
    return {"status": "left"}

@router.post("/{session_id}/start")
async def start_game(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start the game (host only)"""
    session = db.query(QuizSession).filter(QuizSession.id == session_id).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if current_user.id != session.host_user_id:
        raise HTTPException(status_code=403, detail="Only host can start game")
    
    # Log all connected participants
    print("\n" + "="*50)
    print(f"🎮 GAME START REQUEST for Session: {session_id}")
    print("="*50)
    
    # Get all participants from DB
    all_participants = db.query(SessionParticipant).filter(
        SessionParticipant.session_id == session_id
    ).all()
    
    print(f"\n📋 PARTICIPANTS IN SESSION (from DB):")
    print(f"   Total count: {len(all_participants)}")
    
    for idx, participant in enumerate(all_participants):
        user = db.query(User).filter(User.id == participant.user_id).first()
        role = "HOST" if participant.is_host else "PARTICIPANT"
        print(f"   {idx+1}. {user.username} (ID: {user.id}) - {role}")
    
    print("\n✅ All participants who could start playing:")
    participant_names = []
    for participant in all_participants:
        user = db.query(User).filter(User.id == participant.user_id).first()
        participant_names.append(user.username)
    print(f"   {', '.join(participant_names)}")
    print("="*50 + "\n")
    
    # Check if we have flashcards
    flashcard_count = db.query(Flashcard).filter(
        Flashcard.subject_id == session.subject_id
    ).count()
    
    if flashcard_count == 0:
        raise HTTPException(status_code=400, detail="Keine Karteikarten vorhanden")
    
    # Update session status
    session.status = "playing"
    db.commit()
    
    # Note: We don't broadcast via WebSocket here because:
    # 1. Lobby uses polling, not WebSocket
    # 2. Participants will see status change to "playing" via polling
    # 3. WebSocket connection is only established when entering the game
    
    print("\n💡 INFO: Lobby participants will be notified via polling")
    print("   They will see status change from 'waiting' to 'playing'")
    print("   and automatically redirect to the game page")
    
    return {"status": "started", "game_id": session.id}

@router.get("/{session_id}")
async def get_session_details(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get session details (for Game component compatibility)"""
    session = db.query(QuizSession).filter(QuizSession.id == session_id).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Auto-join: Add user as participant if not already in session and session is waiting
    if session.status == "waiting" and current_user.id != session.host_user_id:
        existing = db.query(SessionParticipant).filter(
            SessionParticipant.session_id == session.id,
            SessionParticipant.user_id == current_user.id
        ).first()
        
        if not existing:
            # Check if user is member of the group
            from models import UserGroupAssociation
            is_group_member = db.query(UserGroupAssociation).filter(
                UserGroupAssociation.user_id == current_user.id,
                UserGroupAssociation.group_id == session.group_id
            ).first()
            
            if is_group_member:
                # Auto-join the session
                participant = SessionParticipant(
                    session_id=session.id,
                    user_id=current_user.id,
                    is_host=False,
                    joined_at=datetime.utcnow()
                )
                db.add(participant)
                db.commit()
                
                print(f"\n🔔 AUTO-JOINED via URL:")
                print(f"   User: {current_user.username} (ID: {current_user.id})")
                print(f"   Session: {session.id}")
                print(f"   Time: {datetime.utcnow()}")
    
    # Get related objects
    subject = db.query(Subject).filter(Subject.id == session.subject_id).first()
    group = db.query(Group).filter(Group.id == session.group_id).first()
    host = db.query(User).filter(User.id == session.host_user_id).first()
    
    # Get flashcard count
    flashcard_count = db.query(Flashcard).filter(
        Flashcard.subject_id == session.subject_id
    ).count()
    
    participants = get_session_participants(db, session)
    
    return {
        "id": session.id,
        "subject": {"id": subject.id, "name": subject.name},
        "group": {"id": group.id, "name": group.name},
        "host": {"id": host.id, "username": host.username},
        "participants": participants,
        "status": session.status,
        "join_code": session.join_code,
        "created_at": session.created_at.isoformat(),
        "flashcard_count": flashcard_count
    }

def get_session_participants(db: Session, session: QuizSession) -> List[dict]:
    """Get all participants for a session"""
    participants = []
    
    # Add host
    host = db.query(User).filter(User.id == session.host_user_id).first()
    if host:
        participants.append({
            "user_id": host.id,
            "username": host.username,
            "is_host": True
        })
    
    # Add other participants
    session_participants = db.query(SessionParticipant).filter(
        SessionParticipant.session_id == session.id
    ).all()
    
    for sp in session_participants:
        user = db.query(User).filter(User.id == sp.user_id).first()
        if user and user.id != session.host_user_id:
            participants.append({
                "user_id": user.id,
                "username": user.username,
                "is_host": False
            })
    
    return participants