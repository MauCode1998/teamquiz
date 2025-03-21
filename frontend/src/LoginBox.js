import React, {useState} from 'react';
import { useNavigate } from "react-router-dom";


function LoginBox() {
    const navigation = useNavigate();
    const [benutzername, setBenutzername] = useState("");
    const [passwort, setPasswort] = useState("");

    function validateLogin() {
        
        if (benutzername == "Mau" && passwort == "1") {
            navigation("/gruppen")
        }
    }
    
    return(
        <div className = 'loginPage'>
            <div className = 'loginBox'>
            <h2 className='loginBoxTitle'>Login</h2>
            <label>Benutzername</label>
            <input 
                placeholder='Benutzername'
                value={benutzername}
                onChange = {(e)=> setBenutzername(e.target.value)}
            />
            
            <label>Passwort</label>
            <input 
                placeholder='Passwort'
                value={passwort}
                onChange = {(e)=> setPasswort(e.target.value)}
            />

            <button className ='anmeldebutton' onClick = {() => validateLogin()}>Anmelden</button>
            </div>
        </div>
    );
}

export default LoginBox