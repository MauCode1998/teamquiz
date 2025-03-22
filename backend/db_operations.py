from database import SessionLocal,engine,Base
from models import User,Group,Invitation,Flashcard,Answer,UserGroupAssociation,Subject
from sqlalchemy.orm import Session

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
    pass

def get_invitations(username):
    db = SessionLocal()
    user_id = get_user_id(username)
    invitations = db.query(Invitation).filter(Invitation.to_user_id == user_id).all()
    invitation_list = [{"From":get_username_by_id(invitation.from_user_id),"To":get_group_name_by_id(invitation.group_id)} for invitation in invitations]
    db.close()

    return invitation_list


def is_username_taken(username):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    if user != None:
        db.close()
        return True
    else:
        db.close()
        return False
    

def get_user_id(username):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    if user != None:
        db.close()
        return user.id
    else:
        db.close()
        return user


def get_user(username):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()

    

    if user != None:
        user_dict = {
        "username":user.username,
        "password":user.password
    }
        db.close()
        return user_dict
    else:
        return user

def get_username_by_id(id):
    db = SessionLocal()
    user = db.query(User).filter(User.id== id).first()
    db.close()
    return user.username
    


def get_users():
    db = SessionLocal()
    users = db.query(User).all()
    db.close()
    return users




##### GRUPPENAKTIONEN #####
def is_groupname_taken(groupname):
    db = SessionLocal()

    gruppenname = db.query(Group).filter(Group.name == groupname).first()
    if gruppenname != None:
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


def get_groups():
    db = SessionLocal()
    groups = db.query(User).all()
    db.close()
    return groups

def get_user_groups(username: str):
    db = SessionLocal()
    
    user = db.query(User).filter(User.username == username).first()  # Nutzer abrufen
    
    if not user:
        db.close()
        return {"message": "Benutzer nicht gefunden", "groups": []}

    # Liste von Gruppen als JSON-Format
    groups = [{"id": assoc.group.id, "name": assoc.group.name} for assoc in user.user_groups]

    db.close()
    
    return {"groups": groups}  




def get_group_id(gruppenname):
    db = SessionLocal()
    group = db.query(Group).filter(Group.name == gruppenname).first()
    if group != None:
        return group.id
    else:
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
        zu_loeschende_association = db.query(UserGroupAssociation).filter(UserGroupAssociation.user_id == user_id and UserGroupAssociation.group_id == group_id).first()
        db.delete(zu_loeschende_association)
        db.commit()
        db.close()
        print("Nutzer hinzugefügt")

    except Exception as e:
        return f"Fehler beim hinzufügen des Nutzers zur gruppe {e}"
    

def is_user_in_group(username,groupname):
    db = SessionLocal()
    group = db.query(Group).filter(Group.name == groupname).first()

    if group != None:
        if username not in [userassociation.user.username for userassociation in group.group_users]:
            return False
        else:
            return "Gruppe wurde nicht gefunden"
        

def is_subject_in_group(subjectname,group_id):
    db = SessionLocal()
    subject = db.query(Subject).filter(Subject.name == subjectname and Subject.group_id == group_id).first()


    if subject != None:
       return True
    else:
       return False
    

def get_group(name):
    db = SessionLocal()
    group = db.query(Group).filter(Group.name == name).first()

    
    if group != None:
    
        group_details = {
        "name":name,
        "id":group.id,
        "users":[userassociation.user.username for userassociation in group.group_users],
        "subjects": [subjectobject.name for subjectobject in group.subjects]
        
    }
        return group_details
    else:
        return "Gruppe wurde nicht gefunden"
    

#### Subject Funktionen #####
def add_subject_to_group(subjectname,groupname):
    db = SessionLocal()
    group_id = get_group_id(groupname)
    new_subject = Subject(name=subjectname,group_id=group_id)
    
    if is_subject_in_group(subjectname=subjectname,group_id=group_id):
        return "Subject ist bereits in der Gruppe angelegt"
    
    try:
        db.add(new_subject)
        db.commit()
        db.refresh(new_subject)
        db.close()
    except Exception as e:
        print("Fehler beim anlegen des Subjects",e)


def delete_subject_from_group(subjectname,group_id):
    db = SessionLocal()
    zu_loeschendes_subject = db.query(Subject).filter(Subject.name == subjectname and Subject.group_id == group_id).first()
    
    if not is_subject_in_group(subjectname=subjectname,group_id=group_id):
        return "Subject existiert nicht in der Gruppe"
    
    try:
        db.delete(zu_loeschendes_subject)
        db.commit()
        db.close()
    except Exception as e:
        print("Fehler beim anlegen des Subjects",e)

def get_subject_id(subjectname,groupname):
    
    db = SessionLocal()
    group_id = get_group_id(groupname)
    
    id = db.query(Subject).filter(Subject.name == subjectname and Subject.group_id == group_id).first()

    if id != None:
        return id.id
    else:
        return "Subject konnte nicht gefunden werden"

def get_subject_cards(subjectname, groupname):
    db = SessionLocal()
    group_id = get_group_id(groupname)  # Gruppe-ID holen
    subject = db.query(Subject).filter(Subject.name == subjectname, Subject.group_id == group_id).first()

    if not subject:
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
        neue_antwort = Answer(antwort =antwort["text"],is_correct = antwort["is_correct"],flashcard_id=karteikarten_id)
        db.add(neue_antwort)

    db.commit()
    db.close()




##### Karteikarten Funktionen #####
def create_flashcard(subjectname:str,groupname:str,frage:str,antwortdict:dict):
    db = SessionLocal()
    subject_id = get_subject_id(subjectname=subjectname,groupname=groupname)
    karteikarte = Flashcard(question=frage,subject_id=subject_id)
    
    db.add(karteikarte)
    db.commit()
    db.refresh(karteikarte)
    db.close()

    add_answers_to_flashcard(karteikarte.id,antwortdict)



def delete_flashcard(flashcard_id: int):
    db = SessionLocal()
    # Flashcard abrufen
    flashcard = db.query(Flashcard).filter(Flashcard.id == flashcard_id).first()

    if not flashcard:
        db.close()
        return f"Fehler: Flashcard mit ID {flashcard_id} wurde nicht gefunden."

    try:
        db.delete(flashcard) 
        db.commit()
        return f"Flashcard mit ID {flashcard_id} wurde gelöscht."
    except Exception as e:
        db.rollback()
        return f"Fehler beim Löschen der Flashcard: {e}"
    finally:
        db.close()





if __name__ == '__main__':
    #print(add_subject_to_group("OOP mit deiner Mum","Bango"))
    #create_flashcard("OOP mit deiner Mum","Bango","Wer ist cool?",[{"text":"deine mum","is_correct":True}])
    #print(add_answers_to_flashcard("1",[{"text":"Kissen rocken","is_correct":False},{"text":"Kissen pocken","is_correct":False},{"text":"Kissen mocken","is_correct":True}]))
    #print([user.username for user in get_users()])
    #print(create_invitation("Hongfa","Mau","Bango"))
    print(get_invitations("Hongfa"))
    #print(get_group_name(1))
    pass