import React from "react"
import Card from '@mui/joy/Card';
import Typography from '@mui/joy/Typography';
import Box from '@mui/joy/Box';

function Startseite() {
    return(
        <Box sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '70vh',
            padding: '2rem'
        }}>
            <Card sx={{
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                borderRadius: '30px',
                boxShadow: '0 20px 60px rgba(102, 126, 234, 0.4)',
                color: '#FFF',
                border: 'none',
                textAlign: 'center',
                maxWidth: '800px',
                p: 4
            }}>
                <Typography level="h1" sx={{
                    fontSize: '3rem',
                    fontWeight: 'bold',
                    textShadow: '0 4px 8px rgba(0,0,0,0.3)',
                    mb: 2,
                    background: 'linear-gradient(45deg, #FFD700, #FFA500, #FF6347)',
                    backgroundClip: 'text',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))'
                }}>
                    🎆 Willkommen bei TeamQuiz! 🎆
                </Typography>
                
                <Typography level="h3" sx={{
                    fontWeight: 'bold',
                    textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                    background: 'rgba(255,255,255,0.1)',
                    borderRadius: '15px',
                    p: 2,
                    backdropFilter: 'blur(10px)'
                }}>
                    🤝 Die kollaborative Art zu lernen! 📚
                </Typography>
                
                <Box sx={{
                    mt: 3,
                    display: 'flex',
                    justifyContent: 'center',
                    gap: 2,
                    flexWrap: 'wrap'
                }}>
                    <Box sx={{
                        background: 'rgba(255,255,255,0.15)',
                        borderRadius: '12px',
                        p: 2,
                        backdropFilter: 'blur(10px)',
                        textAlign: 'center'
                    }}>
                        <Typography level="h4" sx={{ color: '#FFD700', mb: 1 }}>🏆</Typography>
                        <Typography level="body1" sx={{ fontWeight: 'bold' }}>Quiz zusammen spielen</Typography>
                    </Box>
                    
                    <Box sx={{
                        background: 'rgba(255,255,255,0.15)',
                        borderRadius: '12px',
                        p: 2,
                        backdropFilter: 'blur(10px)',
                        textAlign: 'center'
                    }}>
                        <Typography level="h4" sx={{ color: '#4ECDC4', mb: 1 }}>📝</Typography>
                        <Typography level="body1" sx={{ fontWeight: 'bold' }}>Karteikarten erstellen</Typography>
                    </Box>
                    
                    <Box sx={{
                        background: 'rgba(255,255,255,0.15)',
                        borderRadius: '12px',
                        p: 2,
                        backdropFilter: 'blur(10px)',
                        textAlign: 'center'
                    }}>
                        <Typography level="h4" sx={{ color: '#96CEB4', mb: 1 }}>👥</Typography>
                        <Typography level="body1" sx={{ fontWeight: 'bold' }}>Gruppen bilden</Typography>
                    </Box>
                </Box>
            </Card>
        </Box>
    );
}

export default Startseite