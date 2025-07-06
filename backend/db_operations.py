from database import SessionLocal,engine,Base
from models import User,Group,Invitation,Flashcard,Answer,UserGroupAssociation,Subject,QuizSession,GameState,Vote,ChatMessage
from datetime import datetime
import random

Base.metadata.create_all(bind=engine)

##### BENUTZERAKTIONEN #####
def create_user(username:str,password:str):
    db = SessionLocal()
    neuer_nutzer = User(username=username,password=password)

    #username muss einzigartig sein
    if is_username_taken(username):
        return "Username wird schon verwendet"

    try:
        db.add(neuer_nutzer)
        db.commit()
        db.refresh(neuer_nutzer)
        db.close()
        print("Neuer User angelegt.")
        return neuer_nutzer
    except Exception as e:
        print("Fehler beim Nutzer anlegen.",e)
        
def create_invitation(from_username,to_username,groupname):
    db = SessionLocal()
    group_id = get_group_id(groupname)
    from_user_id = get_user_id(from_username)
    taken= is_username_taken(to_username)
    to_user_id = get_user_id(to_username)

    if taken:
        neue_einladung = Invitation(group_id=group_id,from_user_id=from_user_id,to_user_id=to_user_id)
        print(neue_einladung)
        db.add(neue_einladung)
        db.commit()
        db.refresh(neue_einladung)
        db.close()
    else:
        print("Nutzer der eingeladen werden sollte wurde nicht gefunden!")
        db.close()

def delete_invitation(invitation_id):
    db = SessionLocal()
    invitation = db.query(Invitation).filter(Invitation.id == invitation_id).first()
    if invitation:
        db.delete(invitation)
        db.commit()
    db.close()

def get_invitations(username):
    db = SessionLocal()
    user_id = get_user_id(username)
    invitations = db.query(Invitation).filter(Invitation.to_user_id == user_id).all()
    invitation_list = [{"id": invitation.id, "From":get_username_by_id(invitation.from_user_id),"To":get_group_name_by_id(invitation.group_id)} for invitation in invitations]
    db.close()

    return invitation_list


def is_username_taken(username):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    if user is not None:
        db.close()
        return True
    else:
        db.close()
        return False
    

def get_user_id(username):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    if user is not None:
        db.close()
        return user.id
    else:
        db.close()
        return user



def get_username_by_id(id):
    db = SessionLocal()
    user = db.query(User).filter(User.id== id).first()
    db.close()
    return user.username
    






##### GRUPPENAKTIONEN #####
def is_groupname_taken(groupname):
    db = SessionLocal()

    gruppenname = db.query(Group).filter(Group.name == groupname).first()
    if gruppenname is not None:
        db.close()
        return True
    else:
        db.close()
        return False
    


def create_group(gruppenname,username):
    db = SessionLocal()
    neue_Gruppe = Group(name=gruppenname)

    if is_groupname_taken(gruppenname):
        db.close()
        return "Gruppenname schon vergeben"
    
    try:
        db.add(neue_Gruppe)
        db.commit()
        db.refresh(neue_Gruppe)
        db.close()
        add_user_to_group(username,gruppenname)
        print("Gruppe",gruppenname,"erfolgreich angelegt.")
        return neue_Gruppe
    
    except Exception as e:
        print("Fehler beim Gruppe anlegen",e)

def delete_group(gruppenname):
    db = SessionLocal()

    if not is_groupname_taken(gruppenname):
        return "Die Gruppe existiert nicht."

    zu_loeschende_gruppe = db.query(Group).filter(Group.name == gruppenname).first()

    db.delete(zu_loeschende_gruppe)
    db.commit()
    db.close()


def get_user_groups(username: str):
    db = SessionLocal()
    
    user = db.query(User).filter(User.username == username).first()  # Nutzer abrufen
    
    if not user:
        db.close()
        return {"message": "Benutzer nicht gefunden", "groups": []}
    
    # Liste von Gruppen als JSON-Format
    groups = [{"id": assoc.group.id, "name": assoc.group.name} for assoc in user.user_groups if assoc.group is not None]

    db.close()
    
    return {"groups": groups}  




def get_group_id(gruppenname):
    db = SessionLocal()
    group = db.query(Group).filter(Group.name == gruppenname).first()
    if group is not None:
        group_id = group.id
        db.close()
        return group_id
    else:
        db.close()
        return False
    


def get_group_name_by_id(id):
    db = SessionLocal()
    group_name = db.query(Group).filter(Group.id == id).first().name
    db.close()
    return group_name
    


def add_user_to_group(username:str,groupname:str):
    db = SessionLocal()
    user_id = get_user_id(username)
    group_id = get_group_id(groupname)

    #checken ob user existiert
    if not is_username_taken(username):
        db.close()
        return "User nicht gefunden"
    if not is_groupname_taken(groupname):
        db.close()
        return "Groupname nicht gefunden"
    
    if is_user_in_group(username,groupname):
        db.close()
        return "Nutzer ist bereits in der Gruppe"

    try:
        new_association = UserGroupAssociation(user_id= user_id,group_id= group_id)
        db.add(new_association)
        db.commit()
        db.refresh(new_association)
        db.close()
        print("Nutzer hinzugefügt")

    except Exception as e:
        db.close()
        return f"Fehler beim hinzufügen des Nutzers zur gruppe {e}"

def delete_user_from_group(username:str,groupname:str):
    db = SessionLocal()
    user_id = get_user_id(username)
    group_id = get_group_id(groupname)

    #checken ob user existiert
    if not is_username_taken(username):
        return "User nicht gefunden"
    if not is_groupname_taken(groupname):
        return "Groupname nicht gefunden"

    try:
        zu_loeschende_association = db.query(UserGroupAssociation).filter(UserGroupAssociation.user_id == user_id, UserGroupAssociation.group_id == group_id).first()
        db.delete(zu_loeschende_association)
        db.commit()
        db.close()
        print("Nutzer hinzugefügt")

    except Exception as e:
        return f"Fehler beim hinzufügen des Nutzers zur gruppe {e}"
    

def is_user_in_group(username,groupname):
    db = SessionLocal()
    group = db.query(Group).filter(Group.name == groupname).first()

    if group is not None:
        result = username in [userassociation.user.username for userassociation in group.group_users]
        db.close()
        return result
    else:
        db.close()
        return False  # Changed from string to False for consistency
        

def is_subject_in_group(subjectname,group_id):
    db = SessionLocal()
    subject = db.query(Subject).filter(Subject.name == subjectname, Subject.group_id == group_id).first()
    print(f"Checking if subject '{subjectname}' exists in group {group_id}: {subject is not None}")

    if subject is not None:
       db.close()
       return True
    else:
       db.close()
       return False
    

def get_group(name):
    db = SessionLocal()
    group = db.query(Group).filter(Group.name == name).first()

    
    if group is not None:
        subjects = [subjectobject.name for subjectobject in group.subjects]
        print(f"Group '{name}' has {len(subjects)} subjects: {subjects}")
        
        group_details = {
        "name":name,
        "id":group.id,
        "users":[userassociation.user.username for userassociation in group.group_users],
        "subjects": subjects
        
    }
        db.close()
        return group_details
    else:
        db.close()
        return "Gruppe wurde nicht gefunden"
    

#### Subject Funktionen #####
def add_subject_to_group(subjectname,groupname):
    db = SessionLocal()
    group_id = get_group_id(groupname)
    print(f"Adding subject '{subjectname}' to group '{groupname}' (ID: {group_id})")
    
    if is_subject_in_group(subjectname=subjectname,group_id=group_id):
        print(f"Subject '{subjectname}' already exists in group '{groupname}'")
        db.close()
        return "Subject ist bereits in der Gruppe angelegt"
    
    try:
        new_subject = Subject(name=subjectname,group_id=group_id)
        db.add(new_subject)
        db.commit()
        db.refresh(new_subject)
        print(f"Successfully created subject '{subjectname}' with ID: {new_subject.id}")
        db.close()
        return None  # Success
    except Exception as e:
        print("Fehler beim anlegen des Subjects",e)
        db.rollback()
        db.close()
        return f"Fehler: {e}"


def delete_subject_from_group(subjectname,group_id):
    db = SessionLocal()
    try:
        print(f"DEBUG: Deleting subject '{subjectname}' from group_id {group_id}")
        
        zu_loeschendes_subject = db.query(Subject).filter(Subject.name == subjectname, Subject.group_id == group_id).first()
        
        if not zu_loeschendes_subject:
            print(f"DEBUG: Subject '{subjectname}' not found in group {group_id}")
            return "Subject existiert nicht in der Gruppe"
        
        print(f"DEBUG: Found subject to delete: '{zu_loeschendes_subject.name}' (ID: {zu_loeschendes_subject.id})")
        
        db.delete(zu_loeschendes_subject)
        db.commit()
        print(f"DEBUG: Successfully deleted subject '{subjectname}'")
        return "Subject erfolgreich gelöscht"
        
    except Exception as e:
        db.rollback()
        print("Fehler beim löschen des Subjects",e)
        return f"Fehler: {e}"
    finally:
        db.close()

def update_subject_name(old_subjectname, new_subjectname, group_id):
    """Update/rename a subject in a group"""
    db = SessionLocal()
    try:
        print(f"DEBUG: Updating subject '{old_subjectname}' to '{new_subjectname}' in group_id {group_id}")
        
        # Check if subject exists
        subject = db.query(Subject).filter(Subject.name == old_subjectname, Subject.group_id == group_id).first()
        if not subject:
            print(f"DEBUG: Subject '{old_subjectname}' not found in group {group_id}")
            return "Subject existiert nicht in der Gruppe"
        
        print(f"DEBUG: Found subject with current name: '{subject.name}', ID: {subject.id}")
        
        # Check if new name already exists in group (excluding current subject)
        existing_subject = db.query(Subject).filter(
            Subject.name == new_subjectname, 
            Subject.group_id == group_id,
            Subject.id != subject.id  # Exclude current subject
        ).first()
        if existing_subject:
            print(f"DEBUG: Subject with name '{new_subjectname}' already exists (ID: {existing_subject.id})")
            return "Ein Fach mit diesem Namen existiert bereits in der Gruppe"
        
        # Update subject name - use merge to ensure proper update
        subject.name = new_subjectname
        db.merge(subject)  # Use merge instead of direct commit
        db.commit()
        
        return "Subject erfolgreich umbenannt"
        
    except Exception as e:
        db.rollback()
        print("Fehler beim umbenennen des Subjects", e)
        return f"Fehler: {e}"
    finally:
        db.close()

def get_subject_id(subjectname, groupname):
    db = SessionLocal()
    group_id = get_group_id(groupname)

    subject = db.query(Subject).filter(
    Subject.name == subjectname,
    Subject.group_id == group_id
        ).first()


    if subject is not None:
        subject_id = subject.id
        db.close()
        return subject_id
    else:
        db.close()
        return "Subject konnte nicht gefunden werden"

def get_subject_cards(subjectname, groupname):
    db = SessionLocal()
    group_id = get_group_id(groupname)  # Gruppe-ID holen
    print(f"Looking for subject '{subjectname}' in group with ID: {group_id}")
    
    subject = db.query(Subject).filter(Subject.name == subjectname, Subject.group_id == group_id).first()
    print(f"Subject found: {subject}")

    if not subject:
        print(f"Subject '{subjectname}' not found in group '{groupname}' (ID: {group_id})")
        db.close()
        return False

    
    flashcards = db.query(Flashcard).filter(Flashcard.subject_id == subject.id).all()

   
    subject_cards = {
        "subject_id": subject.id,
        "subject_name": subject.name,
        "flashcards": [
            {
                "flashcard_id": flashcard.id,
                "question": flashcard.question,
                "answers": [
                    {"answer_id": answer.id, "text": answer.antwort, "is_correct": answer.is_correct}
                    for answer in flashcard.answers
                ]
            }
            for flashcard in flashcards
        ]
    }

    db.close()
    return subject_cards




def add_answers_to_flashcard(karteikarten_id:int,antwortdict:dict):
    db = SessionLocal()
    print(antwortdict)
    for antwort in antwortdict:
        neue_antwort = Answer(antwort=antwort["text"], is_correct=antwort["is_correct"], flashcard_id=karteikarten_id)
        db.add(neue_antwort)

    db.commit()
    db.close()




##### Karteikarten Funktionen #####
def create_flashcard(subjectname:str,groupname:str,frage:str,antwortdict:dict):
    db = SessionLocal()
    try:
        subject_id = get_subject_id(subjectname=subjectname,groupname=groupname)
        if isinstance(subject_id, str):  # Subject doesn't exist, create it
            print(f"Subject '{subjectname}' doesn't exist in group '{groupname}', creating it...")
            create_result = add_subject_to_group(subjectname, groupname)
            if create_result:
                print(f"Subject creation failed: {create_result}")
                return False
            subject_id = get_subject_id(subjectname=subjectname,groupname=groupname)
            if isinstance(subject_id, str):  # Still failed
                return False
            
        karteikarte = Flashcard(question=frage,subject_id=subject_id)
        
        db.add(karteikarte)
        db.commit()
        db.refresh(karteikarte)
        add_answers_to_flashcard(karteikarte.id,antwortdict)
        return True
    except Exception as e:
        print(f"Error creating flashcard: {e}")
        return False
    finally:
        db.close()

    



def update_flashcard(flashcard_id: int, frage: str, antwortdict: dict):
    """Update an existing flashcard with new question and answers"""
    db = SessionLocal()
    
    try:
        # Flashcard abrufen
        flashcard = db.query(Flashcard).filter(Flashcard.id == flashcard_id).first()
        
        if not flashcard:
            db.close()
            return f"Fehler: Flashcard mit ID {flashcard_id} wurde nicht gefunden."
        
        # Update question
        flashcard.question = frage
        
        # Delete existing answers
        db.query(Answer).filter(Answer.flashcard_id == flashcard_id).delete()
        
        # Add new answers
        for answer_data in antwortdict:
            new_answer = Answer(
                antwort=answer_data["text"],
                is_correct=answer_data["is_correct"],
                flashcard_id=flashcard_id
            )
            db.add(new_answer)
        
        db.commit()
        return f"Flashcard mit ID {flashcard_id} wurde aktualisiert."
        
    except Exception as e:
        db.rollback()
        return f"Fehler beim Aktualisieren der Flashcard: {e}"
    finally:
        db.close()

def delete_flashcard(flashcard_id: int):
    db = SessionLocal()
    try:
        # Flashcard abrufen
        flashcard = db.query(Flashcard).filter(Flashcard.id == flashcard_id).first()
        
        if not flashcard:
            return f"Fehler: Flashcard mit ID {flashcard_id} wurde nicht gefunden."
        
        db.delete(flashcard) 
        db.commit()
        return f"Flashcard mit ID {flashcard_id} wurde gelöscht."
    except Exception as e:
        db.rollback()
        return f"Fehler beim Löschen der Flashcard: {e}"
    finally:
        db.close()





##### GAME OPERATIONS #####

def start_game(session_id: str) -> dict:
    """Start the game and prepare first question"""
    db = SessionLocal()
    try:
        game_state = db.query(GameState).filter(GameState.session_id == session_id).first()
        if not game_state:
            # Create new game state
            session = db.query(QuizSession).filter(QuizSession.id == session_id).first()
            if not session:
                return {"error": "Session nicht gefunden"}
                
            flashcard_count = db.query(Flashcard).filter(Flashcard.subject_id == session.subject_id).count()
            max_possible_score = flashcard_count * 100
            
            game_state = GameState(
                session_id=session_id,
                max_possible_score=max_possible_score,
                status="waiting"
            )
            db.add(game_state)
            db.commit()
            db.refresh(game_state)
            
        # Get all flashcards for this session's subject
        session = db.query(QuizSession).filter(QuizSession.id == session_id).first()
        flashcards = db.query(Flashcard).filter(Flashcard.subject_id == session.subject_id).all()
        
        if not flashcards:
            return {"error": "Keine Karteikarten gefunden"}
            
        # Start with first flashcard
        first_flashcard = flashcards[0]
        game_state.status = "question_active"
        game_state.started_at = datetime.utcnow()
        game_state.current_flashcard_id = first_flashcard.id
        game_state.current_question_index = 0
        game_state.question_started_at = datetime.utcnow()
        
        db.commit()
        
        # Convert to dictionary before closing session
        game_state_dict = {
            "session_id": game_state.session_id,
            "current_question_index": game_state.current_question_index,
            "current_flashcard_id": game_state.current_flashcard_id,
            "total_score": game_state.total_score,
            "max_possible_score": game_state.max_possible_score,
            "status": game_state.status,
            "question_started_at": game_state.question_started_at.isoformat() if game_state.question_started_at else None,
            "started_at": game_state.started_at.isoformat() if game_state.started_at else None,
            "flashcard_count": len(flashcards)
        }
        
        return {
            "game_state": game_state_dict,
            "question": prepare_question_data(first_flashcard, 0, len(flashcards)),
            "flashcard_count": len(flashcards)
        }
    finally:
        db.close()


def prepare_question_data(flashcard: Flashcard, question_index: int, total_questions: int) -> dict:
    """Prepare question data for frontend (without revealing correct answer)"""
    answers = [{"id": answer.id, "text": answer.antwort} for answer in flashcard.answers]
    
    return {
        "flashcard_id": flashcard.id,
        "question": flashcard.question,
        "answers": answers,
        "question_index": question_index,
        "total_questions": total_questions
    }


def cast_vote(session_id: str, user_id: int, flashcard_id: int, answer_id: int) -> int:
    """Cast or update a user's vote for current question"""
    db = SessionLocal()
    try:
        # Check if user already voted for this question
        existing_vote = db.query(Vote).filter(
            Vote.session_id == session_id,
            Vote.user_id == user_id,
            Vote.flashcard_id == flashcard_id
        ).first()
        
        if existing_vote:
            # Update existing vote
            existing_vote.answer_id = answer_id
            existing_vote.voted_at = datetime.utcnow()
            db.commit()
            vote_id = existing_vote.id
            return vote_id
        else:
            # Create new vote
            vote = Vote(
                session_id=session_id,
                user_id=user_id,
                flashcard_id=flashcard_id,
                answer_id=answer_id
            )
            db.add(vote)
            db.commit()
            db.refresh(vote)
            vote_id = vote.id
            return vote_id
    finally:
        db.close()


def get_question_votes(session_id: str, flashcard_id: int) -> dict:
    """Get all votes for current question with counts"""
    db = SessionLocal()
    try:
        votes = db.query(Vote).filter(
            Vote.session_id == session_id,
            Vote.flashcard_id == flashcard_id
        ).all()
        
        # Count votes per answer
        vote_counts = {}
        vote_details = []
        
        for vote in votes:
            # Count votes
            if str(vote.answer_id) not in vote_counts:
                vote_counts[str(vote.answer_id)] = 0
            vote_counts[str(vote.answer_id)] += 1
            
            # Vote details with username
            user = db.query(User).filter(User.id == vote.user_id).first()
            vote_details.append({
                "user_id": vote.user_id,
                "username": user.username if user else "Unknown",
                "answer_id": vote.answer_id,
                "voted_at": vote.voted_at.isoformat() if vote.voted_at else None
            })
        
        return {
            "flashcard_id": flashcard_id,
            "votes": vote_details,
            "vote_counts": vote_counts
        }
    finally:
        db.close()


def end_question(session_id: str) -> dict:
    """End current question and calculate results"""
    db = SessionLocal()
    try:
        game_state = db.query(GameState).filter(GameState.session_id == session_id).first()
        if not game_state:
            return {"error": "Spielstatus nicht gefunden"}
            
        flashcard = db.query(Flashcard).filter(Flashcard.id == game_state.current_flashcard_id).first()
        if not flashcard:
            return {"error": "Karteikarte nicht gefunden"}
            
        # Get correct answer
        correct_answer = next((answer for answer in flashcard.answers if answer.is_correct), None)
        if not correct_answer:
            return {"error": "Keine richtige Antwort gefunden"}
            
        # Get votes for this question
        votes_data = get_question_votes(session_id, flashcard.id)
        vote_counts = votes_data["vote_counts"]
        
        # Determine winning answer (most votes)
        if vote_counts:
            max_votes = max(vote_counts.values())
            answers_with_max_votes = [int(answer_id) for answer_id, count in vote_counts.items() if count == max_votes]
            winning_answer_id = random.choice(answers_with_max_votes)  # Random if tie
        else:
            winning_answer_id = None
            
        # Check if team got it right
        was_correct = winning_answer_id == correct_answer.id
        points_earned = 100 if was_correct else 0
        
        # Update score
        game_state.total_score += points_earned
        game_state.status = "question_ended"
        db.commit()
        
        return {
            "flashcard_id": flashcard.id,
            "correct_answer_id": correct_answer.id,
            "was_correct": was_correct,
            "points_earned": points_earned,
            "total_score": game_state.total_score,
            "winning_answer_id": winning_answer_id,
            "vote_counts": vote_counts
        }
    finally:
        db.close()


def next_question(session_id: str) -> dict:
    """Move to next question or end game"""
    db = SessionLocal()
    try:
        game_state = db.query(GameState).filter(GameState.session_id == session_id).first()
        session = db.query(QuizSession).filter(QuizSession.id == session_id).first()
        
        # Get all flashcards
        flashcards = db.query(Flashcard).filter(Flashcard.subject_id == session.subject_id).all()
        total_questions = len(flashcards)
        
        # Check if game should end
        next_index = game_state.current_question_index + 1
        
        # Simple logic: Only end when all questions are answered
        
        if next_index >= total_questions:
            # All questions answered
            percentage = (game_state.total_score / game_state.max_possible_score) * 100
            status = "won" if percentage >= 90 else "lost"
            game_state.status = "game_finished"
            game_state.ended_at = datetime.utcnow()
            db.commit()
            
            return {
                "game_finished": True,
                "result": {
                    "session_id": session_id,
                    "total_score": game_state.total_score,
                    "max_possible_score": game_state.max_possible_score,
                    "percentage": percentage,
                    "status": status,
                    "questions_answered": total_questions,
                    "total_questions": total_questions
                }
            }
        else:
            # Continue to next question
            next_flashcard = flashcards[next_index]
            game_state.current_question_index = next_index
            game_state.current_flashcard_id = next_flashcard.id
            game_state.question_started_at = datetime.utcnow()
            game_state.status = "question_active"
            db.commit()
            
            return {
                "game_finished": False,
                "question": prepare_question_data(next_flashcard, next_index, total_questions)
            }
    finally:
        db.close()


def get_game_state(session_id: str) -> dict:
    """Get current game state with current question"""
    db = SessionLocal()
    try:
        game_state = db.query(GameState).filter(GameState.session_id == session_id).first()
        if not game_state:
            return None
            
        session = db.query(QuizSession).filter(QuizSession.id == session_id).first()
        flashcard_count = db.query(Flashcard).filter(Flashcard.subject_id == session.subject_id).count()
        
        result = {
            "session_id": game_state.session_id,
            "current_question_index": game_state.current_question_index,
            "current_flashcard_id": game_state.current_flashcard_id,
            "total_score": game_state.total_score,
            "max_possible_score": game_state.max_possible_score,
            "status": game_state.status,
            "question_started_at": game_state.question_started_at.isoformat() if game_state.question_started_at else None,
            "flashcard_count": flashcard_count
        }
        
        # If there's a current flashcard, include the question and answers
        if game_state.current_flashcard_id:
            flashcard = db.query(Flashcard).filter(Flashcard.id == game_state.current_flashcard_id).first()
            if flashcard:
                answers = db.query(Answer).filter(Answer.flashcard_id == flashcard.id).all()
                result["current_question"] = {
                    "flashcard_id": flashcard.id,
                    "question": flashcard.question,
                    "question_index": game_state.current_question_index,
                    "total_questions": flashcard_count,
                    "answers": [
                        {
                            "id": answer.id,
                            "text": answer.antwort
                            # Don't reveal correct answer unless question is ended
                        }
                        for answer in answers
                    ]
                }
                
                # If question is ended, include the result
                if game_state.status == 'question_ended':
                    # Get question result
                    correct_answers = [a for a in answers if a.is_correct]
                    votes = db.query(Vote).filter(
                        Vote.session_id == session_id,
                        Vote.flashcard_id == game_state.current_flashcard_id
                    ).all()
                    
                    correct_votes = 0
                    for vote in votes:
                        if any(a.id == vote.answer_id for a in correct_answers):
                            correct_votes += 1
                    
                    result["question_result"] = {
                        "flashcard_id": game_state.current_flashcard_id,
                        "correct_answer_ids": [a.id for a in correct_answers],
                        "correct_votes": correct_votes,
                        "total_votes": len(votes),
                        "total_score": game_state.total_score
                    }
                    result["show_result"] = True
                else:
                    result["show_result"] = False
        
        return result
    finally:
        db.close()


def add_chat_message(session_id: str, user_id: int, message: str) -> ChatMessage:
    """Add chat message to session"""
    db = SessionLocal()
    try:
        chat_message = ChatMessage(
            session_id=session_id,
            user_id=user_id,
            message=message
        )
        db.add(chat_message)
        db.commit()
        db.refresh(chat_message)
        return chat_message
    finally:
        db.close()


def get_chat_messages(session_id: str, limit: int = 50) -> list:
    """Get recent chat messages for session"""
    db = SessionLocal()
    try:
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.sent_at.desc()).limit(limit).all()
        
        result = []
        for msg in reversed(messages):  # Reverse to get chronological order
            user = db.query(User).filter(User.id == msg.user_id).first()
            result.append({
                "id": msg.id,
                "user_id": msg.user_id,
                "username": user.username if user else "Unknown",
                "message": msg.message,
                "sent_at": msg.sent_at
            })
        
        return result
    finally:
        db.close()




def calculate_final_result(session_id: str):
    """Calculate final game result"""
    db = SessionLocal()
    try:
        game_state = db.query(GameState).filter(GameState.session_id == session_id).first()
        if not game_state:
            return None
        
        # Use correct field names
        final_score = game_state.total_score  # was game_state.current_score
        questions_correct = final_score // 100  # 100 points per correct
        
        # Get total questions from max_possible_score (already calculated correctly)
        max_possible_score = game_state.max_possible_score  # was total_questions * 100
        total_questions = max_possible_score // 100  # Calculate from max_possible_score
        target_score = int(max_possible_score * 0.9)
        
        # Victory if reached 90% target
        victory = final_score >= target_score
        
        return {
            "final_score": final_score,
            "questions_correct": questions_correct,
            "questions_total": total_questions,
            "max_possible_score": max_possible_score,
            "target_score": target_score,
            "victory": victory,
            "percentage": (final_score / max_possible_score) * 100 if max_possible_score > 0 else 0
        }
    finally:
        db.close()





if __name__ == '__main__':
    #print(add_subject_to_group("OOP mit deiner Mum","Bango"))
    #create_flashcard("OOP mit deiner Mum","Bango","Wer ist cool?",[{"text":"deine mum","is_correct":True}])
    #print(add_answers_to_flashcard("1",[{"text":"Kissen rocken","is_correct":False},{"text":"Kissen pocken","is_correct":False},{"text":"Kissen mocken","is_correct":True}]))
    #print([user.username for user in get_users()])
    #print(create_invitation("Hongfa","Mau","Bango"))
    #print(get_invitations("Hongfa"))
    #print(get_group_name(1))
    #create_invitation("Hongfa","Mau","OOP mit Java")
    add_user_to_group("Hongfa","blabubb")
    
    #print(get_group("Bango"))
    #create_flashcard("")
    #print(get_subject_cards("H","Lach"))
    pass