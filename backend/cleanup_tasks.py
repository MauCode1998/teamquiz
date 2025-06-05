"""Background cleanup tasks for lobby sessions"""
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import SessionLocal
from models import QuizSession, SessionParticipant
import logging

logger = logging.getLogger(__name__)

async def cleanup_abandoned_sessions():
    """Clean up abandoned lobby sessions"""
    while True:
        try:
            db: Session = SessionLocal()
            
            # Find sessions older than 30 minutes in waiting status
            cutoff_time = datetime.utcnow() - timedelta(minutes=30)
            abandoned_sessions = db.query(QuizSession).filter(
                QuizSession.status == "waiting",
                QuizSession.created_at < cutoff_time
            ).all()
            
            for session in abandoned_sessions:
                logger.info(f"Cleaning up abandoned session {session.id} (created {session.created_at})")
                
                # Delete participants
                db.query(SessionParticipant).filter(
                    SessionParticipant.session_id == session.id
                ).delete()
                
                # Delete session
                db.delete(session)
            
            db.commit()
            
            # Find empty sessions (no participants and no host activity)
            empty_sessions = db.query(QuizSession).filter(
                QuizSession.status == "waiting"
            ).all()
            
            for session in empty_sessions:
                # Check if session has any participants
                participant_count = db.query(SessionParticipant).filter(
                    SessionParticipant.session_id == session.id
                ).count()
                
                # If only host and session is older than 5 minutes, delete
                if participant_count == 0 and session.created_at < datetime.utcnow() - timedelta(minutes=5):
                    logger.info(f"Cleaning up empty session {session.id}")
                    db.delete(session)
            
            db.commit()
            db.close()
            
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")
        
        # Run every 5 minutes
        await asyncio.sleep(300)

def start_cleanup_task():
    """Start the cleanup task in background"""
    asyncio.create_task(cleanup_abandoned_sessions())