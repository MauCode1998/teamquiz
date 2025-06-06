import React, {useState} from 'react';
import { useNavigate, Link } from "react-router-dom";
import Button from '@mui/joy/Button';
import Input from '@mui/joy/Input';
import Card from '@mui/joy/Card';
import Alert from '@mui/joy/Alert';
import Typography from '@mui/joy/Typography';
import Box from '@mui/joy/Box';
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
                width: { xs: '90%', sm: '24rem', md: '26rem' },
                maxWidth: '26rem',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                borderRadius: { xs: '20px', sm: '25px', md: '30px' },
                boxShadow: '0 20px 60px rgba(102, 126, 234, 0.4)',
                color: '#FFF',
                border: 'none',
                padding: { xs: '1.5rem', sm: '2rem', md: '2.5rem' },
                mx: 'auto'
            }}>
            <Typography level="h2" sx={{
                textAlign: 'center',
                fontSize: { xs: '1.75rem', sm: '2rem', md: '2.5rem' },
                fontWeight: 'bold',
                textShadow: '0 3px 6px rgba(0,0,0,0.3)',
                mb: { xs: 2, sm: 3 }
            }}>🔐 Login</Typography>
            
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
            
            <Box sx={{
                background: 'rgba(255,255,255,0.1)',
                borderRadius: '20px',
                padding: { xs: '1.5rem', sm: '2rem' },
                backdropFilter: 'blur(10px)'
            }}>
                <Typography level="body1" sx={{
                    color: '#FFF',
                    fontWeight: 'bold',
                    fontSize: { xs: '1rem', sm: '1.1rem' },
                    textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                    display: 'block',
                    mb: 1
                }}>👤 Benutzername</Typography>
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
                        fontSize: { xs: '0.9rem', sm: '1rem' },
                        padding: { xs: '0.75rem', sm: '1rem' }
                    }}
                />
                
                <Typography level="body1" sx={{
                    color: '#FFF',
                    fontWeight: 'bold',
                    fontSize: { xs: '1rem', sm: '1.1rem' },
                    textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                    display: 'block',
                    mb: 1
                }}>🔒 Passwort</Typography>
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
                        fontSize: { xs: '0.9rem', sm: '1rem' },
                        padding: { xs: '0.75rem', sm: '1rem' }
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
                    fontSize: { xs: '1rem', sm: '1.1rem', md: '1.2rem' },
                    padding: { xs: '10px', sm: '12px' },
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
                
                <Typography level="body1" sx={{ 
                    mt: 3, 
                    textAlign: 'center',
                    color: '#FFF',
                    textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                    fontSize: { xs: '0.9rem', sm: '1rem' }
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
            </Box>
            </Card>
        </div>
    );
}

export default LoginBox