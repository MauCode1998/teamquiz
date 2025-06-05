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

                <Card>
                    <h1 className='mainPageUeberschrift'>Lobby</h1>
                    <Typography level="body-sm">
                        Gruppe: {sessionData?.group?.name} | Fach: {sessionData?.subject?.name}
                    </Typography>
                    {sessionData && (
                        <>
                            <Typography level="title-lg" sx={{ mt: 2, mb: 1 }}>
                                Join Code: <strong>{sessionData.join_code}</strong>
                            </Typography>
                            <Typography level="body-xs">
                                Teilen Sie diesen Code mit anderen Spielern
                            </Typography>
                        </>
                    )}
                </Card>

                {/* Invite section - only for host */}
                {sessionData && sessionData.host.username === user?.username && (
                    <Card>
                        <h3>Spieler einladen</h3>
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
                            >
                                Einladen
                            </Button>
                        </div>
                    </Card>
                )}

                <Card>
                    <h2>Beigetreten ({participants.length})</h2>
                    <Card sx={{ backgroundColor: "#FFF", height: "100%" }}>
                        <List>
                            {participants.length > 0 ? (
                                participants.map(participant => (
                                    <ListItem key={participant.user_id}>
                                        <div>✅</div>
                                        <ListItemDecorator>
                                            {participant.username}
                                            {participant.is_host && ' (Host)'}
                                        </ListItemDecorator>
                                    </ListItem>
                                ))
                            ) : (
                                <ListItem>
                                    <ListItemDecorator>
                                        Warte auf Teilnehmer...
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
                            >
                                Runde starten
                            </Button>
                        ) : (
                            <Typography level="body-sm" sx={{ textAlign: 'center', width: '100%', mt: 2 }}>
                                Warte auf den Host zum Starten...
                            </Typography>
                        )}
                        <Button
                            size="lg"
                            variant="outlined"
                            color="danger"
                            onClick={leaveSession}
                        >
                            Verlassen
                        </Button>
                    </div>
                </Card>
            </div>
        </div>
    );
}

export default Lobby;