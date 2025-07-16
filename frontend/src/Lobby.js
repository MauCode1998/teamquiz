import React, { useState, useEffect } from "react";
import List from '@mui/joy/List';
import ListItem from '@mui/joy/ListItem';
import ListItemDecorator from '@mui/joy/ListItemDecorator';
import Button from '@mui/joy/Button';
import Card from '@mui/joy/Card';
import Box from '@mui/joy/Box';
import Grid from '@mui/joy/Grid';
import { useParams, useNavigate } from 'react-router-dom';
import api from './api/axios';
import Alert from '@mui/joy/Alert';
import Typography from '@mui/joy/Typography';
import { useAuth } from './AuthContext';
import FormControl from '@mui/joy/FormControl';
import FormLabel from '@mui/joy/FormLabel';
import Input from '@mui/joy/Input';

function Lobby() {
    const { sessionId } = useParams();
    const navigate = useNavigate();
    const [sessionData, setSessionData] = useState(null);
    const [participants, setParticipants] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const { user } = useAuth();
    const [inviteeUsername, setInviteeUsername] = useState('');
    const [inviteError, setInviteError] = useState('');
    const [inviteSuccess, setInviteSuccess] = useState('');

    // Initialize lobby
    useEffect(() => {
        if (sessionId) {
            loadSession();
        } else {
            setError('Session ID fehlt in der URL');
            setLoading(false);
        }
    }, [sessionId]);

    // Cleanup on browser close/refresh
    useEffect(() => {
        const handleBeforeUnload = () => {
            if (sessionData) {
                // Use sendBeacon for reliable cleanup even when page closes
                navigator.sendBeacon(
                    `/api/lobby/${sessionId}/leave`,
                    JSON.stringify({})
                );
            }
        };

        window.addEventListener('beforeunload', handleBeforeUnload);
        
        return () => {
            window.removeEventListener('beforeunload', handleBeforeUnload);
            // Also cleanup when component unmounts normally
            if (sessionData) {
                api.post(`/api/lobby/${sessionId}/leave`).catch(() => {});
            }
        };
    }, [sessionData]);

    const loadSession = async () => {
        try {
            const response = await api.get(`/api/lobby/${sessionId}`);
            setSessionData(response.data);
            
            // Load participants
            const participantsResponse = await api.get(`/api/lobby/${sessionId}/participants`);
            setParticipants(participantsResponse.data.participants);
            
            setLoading(false);
        } catch (error) {
            console.error('Error loading session:', error);
            setError('Session nicht gefunden');
            setLoading(false);
        }
    };

    // Simple polling for participant updates and game status
    useEffect(() => {
        if (!sessionData) return;

        const fetchUpdates = async () => {
            try {
                // Get participants
                const response = await api.get(`/api/lobby/${sessionId}/participants`);
                setParticipants(response.data.participants);
                
                // Check session status
                const sessionResponse = await api.get(`/api/lobby/${sessionId}`);
                console.log(`[LOBBY POLL] User: ${user?.username}, Session: ${sessionId}, Status: ${sessionResponse.data.status}`);
                
                if (sessionResponse.data.status === 'playing') {
                    console.log(`[LOBBY REDIRECT] ${user?.username} is being redirected to game!`);
                    navigate(`/game/${sessionId}`);
                } else if (sessionResponse.data.status === 'in_progress') {
                    // Also handle 'in_progress' status
                    console.log(`[LOBBY REDIRECT] ${user?.username} is being redirected to game (in_progress)!`);
                    navigate(`/game/${sessionId}`);
                }
            } catch (error) {
                console.error('Error fetching updates:', error);
            }
        };

        // Initial fetch
        fetchUpdates();

        // Poll every 1.5 seconds
        const interval = setInterval(fetchUpdates, 1500);
        
        return () => clearInterval(interval);
    }, [sessionData, navigate, sessionId]);

    const sendInvitation = async () => {
        if (!inviteeUsername.trim()) {
            setInviteError('Bitte geben Sie einen Benutzernamen ein');
            return;
        }
        
        setInviteError('');
        setInviteSuccess('');
        
        try {
            await api.post('/api/invitation/send', {
                session_id: sessionId,
                invitee_username: inviteeUsername
            });
            
            setInviteSuccess(`Einladung an ${inviteeUsername} gesendet!`);
            setInviteeUsername('');
            
            // Clear success message after 3 seconds
            setTimeout(() => setInviteSuccess(''), 3000);
        } catch (error) {
            if (error.response?.data?.detail) {
                setInviteError(error.response.data.detail);
            } else {
                setInviteError('Fehler beim Senden der Einladung');
            }
        }
    };

    const startQuiz = async () => {
        if (sessionData && sessionData.host.username === user?.username) {
            try {
                await api.post(`/api/lobby/${sessionId}/start`);
                // Don't navigate immediately - let polling handle it for everyone
                // This ensures all participants navigate at roughly the same time
            } catch (error) {
                console.error('Error starting quiz:', error);
                setError('Fehler beim Starten der Runde');
            }
        }
    };

    const leaveSession = async () => {
        if (sessionData) {
            try {
                await api.post(`/api/lobby/${sessionId}/leave`);
                navigate(`/groups/${sessionData.group.name}`);
            } catch (error) {
                console.error('Error leaving session:', error);
                navigate(`/groups/${sessionData.group.name}`);
            }
        }
    };

    if (loading) {
        return (
            <Box className="parent" sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
                <Box sx={{ maxWidth: '600px', mx: 'auto' }}>
                    <Card>
                        <Typography>Lade Session...</Typography>
                    </Card>
                </Box>
            </Box>
        );
    }

    return (
        <Box className="parent" sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
            <Grid 
                container 
                spacing={{ xs: 2, sm: 3 }}
                sx={{ 
                    maxWidth: { lg: '1200px' },
                    mx: 'auto'
                }}
            >
                {error && (
                    <Grid xs={12}>
                        <Alert color="danger" sx={{ mb: 2 }}>
                            {error}
                        </Alert>
                    </Grid>
                )}

                {/* Lobby Title */}
                <Grid xs={12}>
                    <Card sx={{
                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        borderRadius: '25px',
                        boxShadow: '0 15px 35px rgba(102, 126, 234, 0.4)',
                        color: '#FFF',
                        p: { xs: 2, sm: 3 }
                    }}>
                        <Typography level="h1" sx={{
                            textAlign: 'center',
                            fontSize: { xs: '1.75rem', sm: '2rem', md: '2.5rem' },
                            fontWeight: 'bold',
                            textShadow: '0 3px 6px rgba(0,0,0,0.3)',
                            mb: 1
                        }}>
                            🎮 Lobby 🎮
                        </Typography>
                        
                        <Typography level="h4" sx={{
                            textAlign: 'center',
                            fontWeight: 'bold',
                            textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                            background: 'rgba(255,255,255,0.15)',
                            borderRadius: '12px',
                            p: 2,
                            mb: 2,
                            fontSize: { xs: '1rem', sm: '1.25rem' }
                        }}>
                            📚 {sessionData?.group?.name} | 📖 {sessionData?.subject?.name}
                        </Typography>
                        
                        {sessionData && (
                            <>
                                
                                <Typography level="body1" sx={{
                                    textAlign: 'center',
                                    opacity: 0.9,
                                    fontStyle: 'italic',
                                    fontSize: { xs: '0.9rem', sm: '1rem' }
                                }}>
                                
                                </Typography>
                            </>
                        )}
                    </Card>
                </Grid>

                {/* Invite section - only for host */}
                {sessionData && sessionData.host.username === user?.username && (
                    <Grid xs={12} md={6}>
                        <Card sx={{
                            background: 'linear-gradient(135deg, #4ECDC4 0%, #44A08D 100%)',
                            borderRadius: '20px',
                            boxShadow: '0 10px 30px rgba(78, 205, 196, 0.3)',
                            color: '#FFF',
                            p: { xs: 2, sm: 3 }
                        }}>
                            <Typography level="h3" sx={{
                                textAlign: 'center',
                                fontWeight: 'bold',
                                textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                                fontSize: { xs: '1.25rem', sm: '1.5rem' },
                                mb: 2
                            }}>📨 Spieler einladen</Typography>
                            {inviteError && (
                                <Alert color="danger" sx={{ mb: 2 }}>
                                    {inviteError}
                                </Alert>
                            )}
                            {inviteSuccess && (
                                <Alert color="success" sx={{ mb: 2 }}>
                                    {inviteSuccess}
                                </Alert>
                            )}
                            <Box sx={{ 
                                display: 'flex', 
                                gap: { xs: 1, sm: 2 }, 
                                alignItems: 'flex-end',
                                flexDirection: { xs: 'column', sm: 'row' }
                            }}>
                                <FormControl sx={{ flex: 1, width: { xs: '100%', sm: 'auto' } }}>
                                    <FormLabel sx={{ fontSize: { xs: '0.9rem', sm: '1rem' } }}>Benutzername</FormLabel>
                                    <Input
                                        placeholder="Benutzername eingeben"
                                        value={inviteeUsername}
                                        onChange={(e) => setInviteeUsername(e.target.value)}
                                        onKeyPress={(e) => {
                                            if (e.key === 'Enter') {
                                                sendInvitation();
                                            }
                                        }}
                                        sx={{ fontSize: { xs: '0.9rem', sm: '1rem' } }}
                                    />
                                </FormControl>
                                <Button
                                    onClick={sendInvitation}
                                    disabled={!inviteeUsername.trim()}
                                    sx={{
                                        background: 'linear-gradient(135deg, #FF6B6B 0%, #FF5252 100%)',
                                        color: '#FFF',
                                        fontWeight: 'bold',
                                        borderRadius: '10px',
                                        fontSize: { xs: '0.9rem', sm: '1rem' },
                                        px: { xs: 2, sm: 3 },
                                        width: { xs: '100%', sm: 'auto' },
                                        '&:hover': {
                                            background: 'linear-gradient(135deg, #FF5252 0%, #F44336 100%)'
                                        }
                                    }}
                                >
                                    ✉️ Einladen
                                </Button>
                            </Box>
                        </Card>
                    </Grid>
                )}

                {/* Participants Card */}
                <Grid xs={12} md={sessionData && sessionData.host.username === user?.username ? 6 : 12}>
                    <Card sx={{
                        background: 'linear-gradient(135deg, #96CEB4 0%, #FCEA2B 100%)',
                        borderRadius: '20px',
                        boxShadow: '0 10px 30px rgba(150, 206, 180, 0.3)',
                        color: '#2C3E50',
                        p: { xs: 2, sm: 3 },
                        height: '100%'
                    }}>
                        <Typography level="h2" sx={{
                            textAlign: 'center',
                            fontWeight: 'bold',
                            textShadow: '0 2px 4px rgba(0,0,0,0.1)',
                            fontSize: { xs: '1.5rem', sm: '1.75rem' },
                            mb: 2
                        }}>👥 Beigetreten ({participants.length})</Typography>
                        
                        <Card sx={{ 
                            backgroundColor: "rgba(255,255,255,0.9)", 
                            height: "100%",
                            borderRadius: '15px',
                            backdropFilter: 'blur(10px)'
                        }}>
                            <List>
                                {participants.length > 0 ? (
                                    participants.map(participant => (
                                        <ListItem key={participant.user_id} sx={{
                                            background: participant.is_host 
                                                ? 'linear-gradient(135deg, #FFD700 0%, #FFA500 100%)'
                                                : 'linear-gradient(135deg, #E8F5E8 0%, #F0F8FF 100%)',
                                            borderRadius: '12px',
                                            mb: 1,
                                            padding: { xs: '10px 12px', sm: '12px 16px' },
                                            boxShadow: '0 3px 10px rgba(0,0,0,0.1)',
                                            border: participant.is_host ? '2px solid #FF8C00' : '1px solid #E0E0E0'
                                        }}>
                                            <Box sx={{ 
                                                fontSize: { xs: '1rem', sm: '1.2rem' },
                                                marginRight: '12px'
                                            }}>
                                                {participant.is_host ? '👑' : '👤'}
                                            </Box>
                                            <ListItemDecorator sx={{
                                                fontSize: { xs: '1rem', sm: '1.1rem' },
                                                fontWeight: participant.is_host ? 'bold' : 'normal',
                                                color: participant.is_host ? '#B8860B' : '#2C3E50'
                                            }}>
                                                {participant.username}
                                                {participant.is_host && ' (Host)'}
                                            </ListItemDecorator>
                                        </ListItem>
                                    ))
                                ) : (
                                    <ListItem sx={{
                                        background: 'linear-gradient(135deg, #F0F0F0 0%, #E0E0E0 100%)',
                                        borderRadius: '12px',
                                        padding: '20px',
                                        textAlign: 'center',
                                        fontStyle: 'italic'
                                    }}>
                                        <ListItemDecorator sx={{
                                            fontSize: { xs: '1rem', sm: '1.1rem' },
                                            color: '#666'
                                        }}>
                                            ⏳ Warte auf Teilnehmer...
                                        </ListItemDecorator>
                                    </ListItem>
                                )}
                            </List>
                        </Card>

                        <Box sx={{ 
                            display: 'flex', 
                            gap: { xs: 1, sm: 2 }, 
                            marginTop: '16px',
                            flexDirection: { xs: 'column', sm: 'row' }
                        }}>
                            {sessionData && sessionData.host.username === user?.username ? (
                                <Button
                                    size="lg"
                                    onClick={startQuiz}
                                    fullWidth
                                    disabled={participants.length < 1}
                                    sx={{
                                        background: 'linear-gradient(135deg, #27AE60 0%, #2ECC71 100%)',
                                        color: '#FFF',
                                        fontWeight: 'bold',
                                        fontSize: { xs: '1rem', sm: '1.2rem' },
                                        borderRadius: '15px',
                                        boxShadow: '0 6px 20px rgba(39, 174, 96, 0.4)',
                                        '&:hover': {
                                            background: 'linear-gradient(135deg, #229954 0%, #27AE60 100%)',
                                            transform: 'translateY(-2px)',
                                            boxShadow: '0 8px 25px rgba(39, 174, 96, 0.5)'
                                        },
                                        '&:disabled': {
                                            background: 'rgba(150, 150, 150, 0.5)',
                                            color: 'rgba(255,255,255,0.7)'
                                        }
                                    }}
                                >
                                    🚀 Runde starten
                                </Button>
                            ) : (
                                <Typography level="h4" sx={{ 
                                    textAlign: 'center', 
                                    width: '100%', 
                                    mt: 2,
                                    color: '#2C3E50',
                                    fontWeight: 'bold',
                                    background: 'rgba(255,255,255,0.7)',
                                    borderRadius: '10px',
                                    p: 2,
                                    backdropFilter: 'blur(5px)',
                                    fontSize: { xs: '0.9rem', sm: '1rem' }
                                }}>
                                    ⏳ Warte auf den Host zum Starten...
                                </Typography>
                            )}
                            <Button
                                size="lg"
                                onClick={leaveSession}
                                sx={{
                                    background: 'linear-gradient(135deg, #E74C3C 0%, #C0392B 100%)',
                                    color: '#FFF',
                                    fontWeight: 'bold',
                                    fontSize: { xs: '1rem', sm: '1.1rem' },
                                    borderRadius: '15px',
                                    boxShadow: '0 6px 20px rgba(231, 76, 60, 0.4)',
                                    flex: { sm: sessionData && sessionData.host.username === user?.username ? 0.3 : 0 },
                                    '&:hover': {
                                        background: 'linear-gradient(135deg, #C0392B 0%, #A93226 100%)',
                                        transform: 'translateY(-2px)',
                                        boxShadow: '0 8px 25px rgba(231, 76, 60, 0.5)'
                                    }
                                }}
                            >
                                🚪 Verlassen
                            </Button>
                        </Box>
                    </Card>
                </Grid>
            </Grid>
        </Box>
    );
}

export default Lobby;