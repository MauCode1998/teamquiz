from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
import uvicorn
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from db_operations import *
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from database import get_db, engine
from auth import hash_password, verify_password, create_access_token, create_refresh_token, get_current_user, validate_refresh_token
from schemas import UserCreate, UserLogin, Token, TokenRefresh, UserResponse, FlashcardCreate
from models import User, RefreshToken, Base
from datetime import datetime, timezone
import os


app = FastAPI()

# Create all database tables (especially important for test database)
Base.metadata.create_all(bind=engine)

class GruppenRequest(BaseModel):
    gruppen_name:str

class FachRequest(BaseModel):
    fach_name:str
    gruppen_name:str

class FachRenameRequest(BaseModel):
    old_fach_name: str
    new_fach_name: str
    gruppen_name: str

class FachDeleteRequest(BaseModel):
    fach_name: str
    gruppen_name: str

class KarteiKarteRequest(BaseModel):
    Fach:str
    Gruppe:str
    Frage:str
    Antwort1:str
    Antwort2:str
    Antwort3:str
    Antwort4:str


# Token storage is now handled by JWT and database

# Serve React static files
app.mount("/static", StaticFiles(directory="../frontend/build/static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  
    allow_headers=["*", "Authorization", "Content-Type"],
    expose_headers=["*"]
)


@app.post("/register", response_model=Token)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    
    if existing_user:
        if existing_user.username == user_data.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Create new user
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
    
    # Create tokens
    access_token = create_access_token(data={"sub": new_user.username})
    refresh_token_str, expires_at = create_refresh_token()
    
    # Save refresh token
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
    user = db.query(User).filter(User.username == form_data.username).first()
    
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
    
    # Create tokens
    access_token = create_access_token(data={"sub": user.username})
    refresh_token_str, expires_at = create_refresh_token()
    
    # Save refresh token
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
    
    # Create new access token
    access_token = create_access_token(data={"sub": user.username})
    
    return {
        "access_token": access_token,
        "refresh_token": token_data.refresh_token,
        "token_type": "bearer"
    }

@app.post("/logout")
async def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Logout and invalidate tokens"""
    # Delete all refresh tokens for this user
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


@app.post("/karteikarte-erstellen")
async def erstelle_karteikarte(karteikartenrequest: KarteiKarteRequest, current_user: User = Depends(get_current_user)):
    print("gruppe wird erstellt!")
    gruppenname = karteikartenrequest.Gruppe
    fachname = karteikartenrequest.Fach
    frage = karteikartenrequest.Frage
    antwort1 = karteikartenrequest.Antwort1
    antwort2 = karteikartenrequest.Antwort2
    antwort3 = karteikartenrequest.Antwort3
    antwort4 = karteikartenrequest.Antwort4

    antwortdict = [{"text":antwort1,"is_correct":False},{"text":antwort2,"is_correct":False},{"text":antwort3,"is_correct":False},{"text":antwort4,"is_correct":True}]

    username = current_user.username

    neue_karteikarte = create_flashcard(subjectname=fachname,groupname=gruppenname,frage=frage,antwortdict=antwortdict)
    print(neue_karteikarte)
    print("KARTE ERSTELLT,YAY!!")
    print("gruppe",gruppenname)
    print("fach",fachname)
  

    return {"message":"Success!","content":"Karte erfolgreich angelegt"}


@app.post("/flashcard/create")
async def create_flashcard_new(flashcard_data: FlashcardCreate, current_user: User = Depends(get_current_user)):
    """Create a new flashcard with proper answer marking"""
    print(f"Creating flashcard: {flashcard_data.frage}")
    print(f"Subject: {flashcard_data.fach}, Group: {flashcard_data.gruppe}")
    print(f"Answers: {flashcard_data.antworten}")
    
    # Check if user is member of the group
    is_member = is_user_in_group(current_user.username, flashcard_data.gruppe)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this group"
        )
    
    # Transform answers to match database format
    antworten_for_db = [
        {"text": answer["text"], "is_correct": answer["is_correct"]}
        for answer in flashcard_data.antworten
    ]
    
    # Create flashcard
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
    print("gruppe wird erstellt!")
    print(fachrequest)
    username = current_user.username

    result = add_subject_to_group(fachrequest.fach_name,fachrequest.gruppen_name)
    print(result)

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
    
    # Get group ID
    group_id = get_group_id(rename_request.gruppen_name)
    if not group_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gruppe '{rename_request.gruppen_name}' nicht gefunden"
        )
    
    # Check if user is in group
    if not is_user_in_group(username, rename_request.gruppen_name):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sie sind nicht berechtigt, Fächer in dieser Gruppe zu bearbeiten"
        )
    
    # Validate input
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
    
    # Get group ID
    group_id = get_group_id(delete_request.gruppen_name)
    if not group_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gruppe '{delete_request.gruppen_name}' nicht gefunden"
        )
    
    # Check if user is in group
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
    ##achtung! es muss hier eigentlihc noch geguckt werden ob der user teil der gruppe ist###

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

        #gucken, ob user der letzte member ist
      
     
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
    #halfassed login überprüfung lol
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
    
    # Check if sender is member of the group
    is_member = is_user_in_group(from_username, groupname)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this group"
        )
    
    # Check if target user exists
    db = next(get_db())
    target_user = db.query(User).filter(User.username == to_username).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if user is already in the group
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
    
    # Get invitation details
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
    
    # Add user to group
    try:
        add_user_to_group(username, invitation['To'])
        # Delete the invitation
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
    
    # Get invitation details
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
    
    # Delete the invitation
    try:
        delete_invitation(invitation_action.invitation_id)
        return {"message": "success", "content": "Invitation rejected"}
    except Exception as e:
        print(f"Error rejecting invitation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reject invitation"
        )
    
    
# Old login endpoint removed - using JWT /login endpoint instead

# Old token function removed - using JWT authentication instead


# Catch-all handler to serve React app for client-side routing
@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    # If it's an API route, let it pass through (should be handled by API endpoints above)
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    # For all other routes, serve the React index.html
    index_file = "../frontend/build/index.html"
    if os.path.exists(index_file):
        return FileResponse(index_file)
    else:
        raise HTTPException(status_code=404, detail="Frontend build not found. Run 'npm run build' in frontend directory.")

if __name__ == '__main__':
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
