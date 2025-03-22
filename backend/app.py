from fastapi import FastAPI, Response, Request, HTTPException, Depends,Header
import uvicorn
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from login_handler import login_interaktion_db
import random
from db_operations import *
from fastapi.responses import JSONResponse


app = FastAPI()

class LoginRequest(BaseModel):
    username: str
    password: str

class GruppenRequest(BaseModel):
    gruppen_name:str

class FachRequest(BaseModel):
    fach_name:str
    gruppen_name:str

token_speicher = {
    "123456789":"Mau"
}  # Speichert Tokens

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  
    allow_headers=["*", "token"],
    expose_headers=["*"]
)


def generate_token(username):
    """Erzeugt ein zufälliges Token für den Nutzer"""
    while True:
        token = str(random.randint(100000, 9999999)) 
        if token not in token_speicher:
            token_speicher[token] = username
            return token
        

@app.post("/gruppe-erstellen")
async def create_new_group(gruppenrequest: GruppenRequest,token:str=Header(None)):
    print("gruppe wird erstellt!")
    print(gruppenrequest)
    username = get_user_by_token(token)
    neue_gruppe = create_group(gruppenrequest.gruppen_name,username)
    print(neue_gruppe)

    return {"message":"Success!","content":"Gruppe erfolgreich angelegt"}



@app.post("/fach-erstellen")
async def create_new_fach(fachrequest: FachRequest,token:str=Header(None)):
    print("gruppe wird erstellt!")
    print(fachrequest)
    username = get_user_by_token(token)

    neue_gruppe = add_subject_to_group(fachrequest.fach_name,fachrequest.gruppen_name)
    print(neue_gruppe)

    return {"message":"Success!","content":"Fach wurde erfolgreich angelegt"}


@app.delete("/delete-group")
async def delete_group_route(gruppenrequest: GruppenRequest,token:str=Header(None)):
    print("gruppe wird gelöscht!")
    print(gruppenrequest)
    username = get_user_by_token(token)
    ##achtung! es muss hier eigentlihc noch geguckt werden ob der user teil der gruppe ist###

    is_member = is_user_in_group(username,gruppenrequest.gruppen_name)
    if is_member:
        gelöschte_gruppe = delete_group(gruppenrequest.gruppen_name)
        print(gelöschte_gruppe)

        return {"message":"Success!","content":"Gruppe erfolgreich gelöscht"}
    else:
        return {"message":"Fail!","content":"Gruppe konnte nicht gelöscht werden"}

@app.delete("/leave-group")
async def leave_group_route(gruppenrequest: GruppenRequest,token:str=Header(None)):
    print("gruppe wird verlassen!")
    print(gruppenrequest)
    username = get_user_by_token(token)
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
async def get_gruppen_specifics(name: str,token: str = Header(None)):
    user = get_user_by_token(token)
    print(user)
    #halfassed login überprüfung lol
    gruppen_info = get_group(name)
    print(gruppen_info)
    return {"message":"Success","content":gruppen_info}


@app.get("/get-gruppeninfo")
async def get_gruppen_info(token: str = Header(None)):
    user = get_user_by_token(token)
    gruppen = get_user_groups(user)
    print(gruppen)

    return {"message":"success","content":gruppen}

@app.get("/get-subject-cards/")
async def get_subject_cards_by_name(subjectname:str="OOP mit deiner Mum",groupname: str = "Bango"):
    print("Getsubjectname wurde gecalled!")
    cards: dict = get_subject_cards(subjectname,groupname)
    print(cards)
    if not cards:
        return {"message":"success","content":[]}
    
    return {"message":"success","content":cards}

@app.get("/get-invitations")
async def get_those_invitations(token: str = Header(None)):
    print("Einladungen abgefragt")
  
    username = get_user_by_token(token)
    invitations = get_invitations(username)
    print("Alle Einladungen")

    return {"message":"success","content":invitations}
    
    
@app.post("/login/")
async def login(request: LoginRequest):
    """Login-Route, die ein Token zurückgibt"""
    benutzername = request.username
    passwort = request.password

    if login_interaktion_db(benutzername, passwort):
        token = generate_token(benutzername)
        #response.set_cookie
    raise HTTPException(status_code=401, detail="Ungültige Anmeldedaten")


def get_user_by_token(token:str):
    user = token_speicher.get(token)
    return user


if __name__ == '__main__':
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
