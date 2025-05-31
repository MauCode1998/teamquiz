import React, {useState} from 'react';
import { useNavigate, Link } from "react-router-dom";
import Button from '@mui/joy/Button';
import Input from '@mui/joy/Input';
import Card from '@mui/joy/Card';
import Alert from '@mui/joy/Alert';
import Typography from '@mui/joy/Typography';
import { useAuth } from './AuthContext';



function LoginBox() {
    const navigation = useNavigate();
    const { login } = useAuth();
    const [benutzername, setBenutzername] = useState("");
    const [passwort, setPasswort] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    async function validateLogin() {
        setError("");
        setLoading(true);
        
        const result = await login(benutzername, passwort);
        
        if (result.success) {
            navigation("/groups");
        } else {
            setError(result.error);
            setLoading(false);
        }
    }
    
    return(
        <div className = 'loginPage'>
            <Card sx = {{width:"20rem"}}>
            <h2 className='loginBoxTitle'>Login</h2>
            
            {error && (
                <Alert color="danger" sx={{ mb: 2 }}>
                    {error}
                </Alert>
            )}
            
            <label>Benutzername</label>
            <Input 
                placeholder='Benutzername'
                value={benutzername}
                onChange = {(e)=> setBenutzername(e.target.value)}
                disabled={loading}
            />
            
            <label>Passwort</label>
            <Input 
                placeholder='Passwort'
                value={passwort}
                type = "password"
                onChange = {(e)=> setPasswort(e.target.value)}
                disabled={loading}
                onKeyPress={(e) => e.key === 'Enter' && validateLogin()}
            />

            <Button 
              variant="solid" 
              color="primary"
              sx = {{marginTop: "0.5rem"}} 
              onClick = {() => validateLogin()}
              loading={loading}
              disabled={loading}
            >
              Anmelden
            </Button>
            
            <Typography level="body-sm" sx={{ mt: 2, textAlign: 'center' }}>
                Noch kein Konto?{' '}
                <Link to="/register" style={{ textDecoration: 'none' }}>
                    Jetzt registrieren
                </Link>
            </Typography>
            </Card>
        </div>
    );
}

export default LoginBox