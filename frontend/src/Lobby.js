import React, { useState, useEffect } from "react";
import List from '@mui/joy/List';
import ListItem from '@mui/joy/ListItem';
import ListItemDecorator from '@mui/joy/ListItemDecorator';
import Button from '@mui/joy/Button';
import Card from '@mui/joy/Card';
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
            <div className="parent">
                <div className='mittelPage'>
                    <Card>
                        <Typography>Lade Session...</Typography>
                    </Card>
                </div>
            </div>
        );
    }

    return (
        <div className="parent">
            <div className='mittelPage'>
                {error && (
                    <Alert color="danger" sx={{ mb: 2 }}>
                        {error}
                    </Alert>
                )}

                <Card sx={{
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    borderRadius: '25px',
                    boxShadow: '0 15px 35px rgba(102, 126, 234, 0.4)',
                    color: '#FFF'
                }}>
                    <h1 className='mainPageUeberschrift' style={{
                        textAlign: 'center',
                        fontSize: '2.5rem',
                        fontWeight: 'bold',
                        textShadow: '0 3px 6px rgba(0,0,0,0.3)',
                        margin: '0 0 1rem 0'
                    }}>
                        🎮 Lobby 🎮
                    </h1>
                    
                    <Typography level="h4" sx={{
                        textAlign: 'center',
                        fontWeight: 'bold',
                        textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                        background: 'rgba(255,255,255,0.15)',
                        borderRadius: '12px',
                        p: 2,
                        mb: 2
                    }}>
                        📚 {sessionData?.group?.name} | 📖 {sessionData?.subject?.name}
                    </Typography>
                    
                    {sessionData && (
                        <>
                            
                            <Typography level="body1" sx={{
                                textAlign: 'center',
                                opacity: 0.9,
                                fontStyle: 'italic'
                            }}>
                                📤 Teilen Sie diesen Code mit anderen Spielern
                            </Typography>
                        </>
                    )}
                </Card>

                {/* Invite section - only for host */}
                {sessionData && sessionData.host.username === user?.username && (
                    <Card sx={{
                        background: 'linear-gradient(135deg, #4ECDC4 0%, #44A08D 100%)',
                        borderRadius: '20px',
                        boxShadow: '0 10px 30px rgba(78, 205, 196, 0.3)',
                        color: '#FFF'
                    }}>
                        <br></br>
                        <h3 style={{
                            textAlign: 'center',
                            fontWeight: 'bold',
                            textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                            fontSize: '1.5rem',
                            margin: '0 0 1rem 0'
                        }}>📨 Spieler einladen</h3>
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
                        <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-end' }}>
                            <FormControl sx={{ flex: 1 }}>
                                <FormLabel>Benutzername</FormLabel>
                                <Input
                                    placeholder="Benutzername eingeben"
                                    value={inviteeUsername}
                                    onChange={(e) => setInviteeUsername(e.target.value)}
                                    onKeyPress={(e) => {
                                        if (e.key === 'Enter') {
                                            sendInvitation();
                                        }
                                    }}
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
                                    '&:hover': {
                                        background: 'linear-gradient(135deg, #FF5252 0%, #F44336 100%)'
                                    }
                                }}
                            >
                                ✉️ Einladen
                            </Button>
                        </div>
                    </Card>
                )}

                <Card sx={{
                    background: 'linear-gradient(135deg, #96CEB4 0%, #FCEA2B 100%)',
                    borderRadius: '20px',
                    boxShadow: '0 10px 30px rgba(150, 206, 180, 0.3)',
                    color: '#2C3E50'
                }}>
                    <h2 style={{
                        textAlign: 'center',
                        fontWeight: 'bold',
                        textShadow: '0 2px 4px rgba(0,0,0,0.1)',
                        fontSize: '1.8rem',
                        margin: '0 0 1rem 0'
                    }}>👥 Beigetreten ({participants.length})</h2>
                    
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
                                        padding: '12px 16px',
                                        boxShadow: '0 3px 10px rgba(0,0,0,0.1)',
                                        border: participant.is_host ? '2px solid #FF8C00' : '1px solid #E0E0E0'
                                    }}>
                                        <div style={{ 
                                            fontSize: '1.2rem',
                                            marginRight: '12px'
                                        }}>
                                            {participant.is_host ? '👑' : '👤'}
                                        </div>
                                        <ListItemDecorator sx={{
                                            fontSize: '1.1rem',
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
                                        fontSize: '1.1rem',
                                        color: '#666'
                                    }}>
                                        ⏳ Warte auf Teilnehmer...
                                    </ListItemDecorator>
                                </ListItem>
                            )}
                        </List>
                    </Card>

                    <div style={{ display: 'flex', gap: '8px', marginTop: '16px' }}>
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
                                    fontSize: '1.2rem',
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
                                backdropFilter: 'blur(5px)'
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
                                fontSize: '1.1rem',
                                borderRadius: '15px',
                                boxShadow: '0 6px 20px rgba(231, 76, 60, 0.4)',
                                '&:hover': {
                                    background: 'linear-gradient(135deg, #C0392B 0%, #A93226 100%)',
                                    transform: 'translateY(-2px)',
                                    boxShadow: '0 8px 25px rgba(231, 76, 60, 0.5)'
                                }
                            }}
                        >
                            🚪 Verlassen
                        </Button>
                    </div>
                </Card>
            </div>
        </div>
    );
}

export default Lobby;