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
            <Card sx={{
                width: "24rem",
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                borderRadius: '30px',
                boxShadow: '0 20px 60px rgba(102, 126, 234, 0.4)',
                color: '#FFF',
                border: 'none'
            }}>
            <h2 className='loginBoxTitle' style={{
                textAlign: 'center',
                fontSize: '2.5rem',
                fontWeight: 'bold',
                textShadow: '0 3px 6px rgba(0,0,0,0.3)',
                margin: '1rem 0 2rem 0'
            }}>🔐 Login</h2>
            
            {error && (
                <Alert sx={{
                    mb: 2,
                    background: 'rgba(255,255,255,0.95)',
                    color: '#C0392B',
                    borderRadius: '12px',
                    border: 'none'
                }}>
                    {error}
                </Alert>
            )}
            
            <div style={{
                background: 'rgba(255,255,255,0.1)',
                borderRadius: '20px',
                padding: '2rem',
                backdropFilter: 'blur(10px)'
            }}>
                <label style={{
                    color: '#FFF',
                    fontWeight: 'bold',
                    fontSize: '1.1rem',
                    textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                    display: 'block',
                    marginBottom: '8px'
                }}>👤 Benutzername</label>
                <Input 
                    placeholder='Benutzername eingeben...'
                    value={benutzername}
                    onChange = {(e)=> setBenutzername(e.target.value)}
                    disabled={loading}
                    sx={{
                        background: 'rgba(255,255,255,0.95)',
                        borderRadius: '12px',
                        border: 'none',
                        mb: 2,
                        fontSize: '1rem'
                    }}
                />
                
                <label style={{
                    color: '#FFF',
                    fontWeight: 'bold',
                    fontSize: '1.1rem',
                    textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                    display: 'block',
                    marginBottom: '8px'
                }}>🔒 Passwort</label>
                <Input 
                    placeholder='Passwort eingeben...'
                    value={passwort}
                    type = "password"
                    onChange = {(e)=> setPasswort(e.target.value)}
                    disabled={loading}
                    onKeyPress={(e) => e.key === 'Enter' && validateLogin()}
                    sx={{
                        background: 'rgba(255,255,255,0.95)',
                        borderRadius: '12px',
                        border: 'none',
                        mb: 3,
                        fontSize: '1rem'
                    }}
                />

                <Button 
                  onClick = {() => validateLogin()}
                  loading={loading}
                  disabled={loading}
                  fullWidth
                  sx={{
                    background: 'linear-gradient(135deg, #4ECDC4 0%, #44A08D 100%)',
                    color: '#FFF',
                    fontWeight: 'bold',
                    borderRadius: '15px',
                    fontSize: '1.2rem',
                    padding: '12px',
                    boxShadow: '0 6px 20px rgba(78, 205, 196, 0.4)',
                    '&:hover': {
                        background: 'linear-gradient(135deg, #44A08D 0%, #3d8f7a 100%)',
                        transform: 'translateY(-2px)',
                        boxShadow: '0 8px 25px rgba(78, 205, 196, 0.6)'
                    }
                  }}
                >
                  🚀 Anmelden
                </Button>
                
                <Typography level="h4" sx={{ 
                    mt: 3, 
                    textAlign: 'center',
                    color: '#FFF',
                    textShadow: '0 2px 4px rgba(0,0,0,0.3)'
                }}>
                    Noch kein Konto?{' '}
                    <Link to="/register" style={{ 
                        color: '#4ECDC4',
                        textDecoration: 'none',
                        fontWeight: 'bold',
                        textShadow: '0 2px 4px rgba(0,0,0,0.3)'
                    }}>
                        Jetzt registrieren 📝
                    </Link>
                </Typography>
            </div>
            </Card>
        </div>
    );
}

export default LoginBox