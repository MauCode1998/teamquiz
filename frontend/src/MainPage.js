import React from 'react'
import Card from '@mui/joy/Card';
import Typography from '@mui/joy/Typography';
import Box from '@mui/joy/Box';
import Button from '@mui/joy/Button';
import { useNavigate } from 'react-router-dom';

function MainPage() {
    const navigate = useNavigate();
    
    return (
        <Box sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '80vh',
            padding: '2rem',
            gap: 3
        }}>
            <Card sx={{
                background: 'linear-gradient(135deg, #4ECDC4 0%, #44A08D 100%)',
                borderRadius: '30px',
                boxShadow: '0 20px 60px rgba(78, 205, 196, 0.4)',
                color: '#FFF',
                border: 'none',
                textAlign: 'center',
                maxWidth: '600px',
                p: 4
            }}>
                <Typography level="h2" sx={{
                    fontSize: '2.5rem',
                    fontWeight: 'bold',
                    textShadow: '0 3px 6px rgba(0,0,0,0.3)',
                    mb: 3
                }}>
                    🚀 Hier stehen coole Dinge! 🚀
                </Typography>
                
                <Typography level="h4" sx={{
                    fontWeight: 'bold',
                    textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                    background: 'rgba(255,255,255,0.15)',
                    borderRadius: '15px',
                    p: 2,
                    backdropFilter: 'blur(10px)',
                    mb: 3
                }}>
                    🎆 Willkommen in der Hauptseite! 🎆
                </Typography>
                
                <Box sx={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr',
                    gap: 2,
                    mt: 3
                }}>
                    <Box sx={{
                        background: 'rgba(255,255,255,0.15)',
                        borderRadius: '15px',
                        p: 2,
                        backdropFilter: 'blur(10px)'
                    }}>
                        <Typography level="h3" sx={{ mb: 1 }}>🎮</Typography>
                        <Typography level="body1" sx={{ fontWeight: 'bold' }}>Spiele starten</Typography>
                    </Box>
                    
                    <Box sx={{
                        background: 'rgba(255,255,255,0.15)',
                        borderRadius: '15px',
                        p: 2,
                        backdropFilter: 'blur(10px)'
                    }}>
                        <Typography level="h3" sx={{ mb: 1 }}>🔥</Typography>
                        <Typography level="body1" sx={{ fontWeight: 'bold' }}>Live Challenges</Typography>
                    </Box>
                    
                    <Box sx={{
                        background: 'rgba(255,255,255,0.15)',
                        borderRadius: '15px',
                        p: 2,
                        backdropFilter: 'blur(10px)'
                    }}>
                        <Typography level="h3" sx={{ mb: 1 }}>🏆</Typography>
                        <Typography level="body1" sx={{ fontWeight: 'bold' }}>Bestenlisten</Typography>
                    </Box>
                    
                    <Box sx={{
                        background: 'rgba(255,255,255,0.15)',
                        borderRadius: '15px',
                        p: 2,
                        backdropFilter: 'blur(10px)'
                    }}>
                        <Typography level="h3" sx={{ mb: 1 }}>✨</Typography>
                        <Typography level="body1" sx={{ fontWeight: 'bold' }}>Achievements</Typography>
                    </Box>
                </Box>
            </Card>
            
            <Button 
                onClick={() => navigate('/groups')}
                sx={{
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    color: '#FFF',
                    fontWeight: 'bold',
                    borderRadius: '20px',
                    fontSize: '1.2rem',
                    padding: '12px 30px',
                    boxShadow: '0 8px 25px rgba(102, 126, 234, 0.4)',
                    '&:hover': {
                        background: 'linear-gradient(135deg, #764ba2 0%, #667eea 100%)',
                        transform: 'translateY(-3px)',
                        boxShadow: '0 12px 35px rgba(102, 126, 234, 0.6)'
                    }
                }}
            >
                🏠 Zu den Gruppen
            </Button>
        </Box>
    );
}

export default MainPage;