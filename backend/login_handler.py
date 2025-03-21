from db_operations import get_user

mock_token = "abc"

def login_interaktion_db(benutzername,kennwort):
    print("Main login aufgerufen")
    user_dict = get_user(benutzername)
    print(user_dict)

    if user_dict == None:
        print("User existiert nicht")
        return False
    print("Ist nicht none")
    if kennwort == user_dict.get("password",""):
        print("Korrektes Kennwort!")
        return True
    else:
        print("Falsches Kennwort")
        return False
    
