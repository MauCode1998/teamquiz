import React, {useState} from 'react';
import { useNavigate } from "react-router-dom";
import Button from '@mui/joy/Button';
import Input from '@mui/joy/Input';
import Card from '@mui/joy/Card';



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
            <Card sx = {{width:"20rem"}}>
            <h2 className='loginBoxTitle'>Login</h2>
            <label>Benutzername</label>
            <Input 
                placeholder='Benutzername'
                value={benutzername}
                onChange = {(e)=> setBenutzername(e.target.value)}
            />
            
            <label>Passwort</label>
            <Input 
                placeholder='Passwort'
                value={passwort}
                type = "password"
                onChange = {(e)=> setPasswort(e.target.value)}
            />

            <Button 
              variant="solid" 
              color="primary"
              sx = {{marginTop: "0.5rem;"}} 
              onClick = {() => validateLogin()}>Anmelden</Button>
            </Card>
        </div>
    );
}

export default LoginBox