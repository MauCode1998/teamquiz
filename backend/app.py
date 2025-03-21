from fastapi import FastAPI, Response, Request, HTTPException, Depends
import uvicorn
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from login_handler import login_interaktion_db
import random
from db_operations import get_user_groups
from fastapi.responses import JSONResponse


app = FastAPI()

class LoginRequest(BaseModel):
    username: str
    password: str

token_speicher = {}  # Speichert Tokens

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
    expose_headers=["Access-Control-Allow-Origin"]
)

def generate_token(username):
    """Erzeugt ein zufälliges Token für den Nutzer"""
    while True:
        token = str(random.randint(100000, 9999999))  # Token als String
        if token not in token_speicher:
            token_speicher[token] = username
            return token

@app.post("/login/")
async def login(request: LoginRequest):
    """Login-Route, die ein Token zurückgibt"""
    benutzername = request.username
    passwort = request.password

    if login_interaktion_db(benutzername, passwort):
        token = generate_token(benutzername)
        response.set_cookie
    raise HTTPException(status_code=401, detail="Ungültige Anmeldedaten")




if __name__ == '__main__':
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
