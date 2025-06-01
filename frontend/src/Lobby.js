import React, { useState, useEffect } from "react";
import  Link from '@mui/joy/Link';
import List from '@mui/joy/List';
import ListItem from '@mui/joy/ListItem';
import ListItemDecorator from '@mui/joy/ListItemDecorator';
import Button from '@mui/joy/Button';
import Card from '@mui/joy/Card';
import Divider from '@mui/joy/Divider';
import OnlineUsers from './components/OnlineUsers';
import { useSearchParams } from 'react-router-dom';
import api from './api/axios';
import Alert from '@mui/joy/Alert';
import Typography from '@mui/joy/Typography';
import { useAuth } from './AuthContext';




function Lobby() {
    const [searchParams] = useSearchParams();
    const groupName = searchParams.get('group');
    const subjectName = searchParams.get('subject');
    const joinCode = searchParams.get('code');
    const [sessionData, setSessionData] = useState(null);
    const [participants, setParticipants] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [websocket, setWebsocket] = useState(null);
    const { getToken, user } = useAuth();

    useEffect(() => {
        if (joinCode) {
            // Join with a code
            joinSessionWithCode();
        } else if (groupName && subjectName) {
            // Create or find session
            createOrJoinSession();
        } else {
            setError('Gruppe oder Fach fehlt in der URL');
            setLoading(false);
        }
    }, [groupName, subjectName, joinCode]);

    const joinSessionWithCode = async () => {
        try {
            // Join with code
            const joinResponse = await api.post('/api/session/join', {
                join_code: joinCode
            });
            
            // Get full session details
            const sessionId = joinResponse.data.session_id;
            const detailsResponse = await api.get(`/api/session/${sessionId}`);
            
            setSessionData(detailsResponse.data);
            setParticipants(detailsResponse.data.participants || []);
            console.log('Session data loaded:', detailsResponse.data);
            setupWebSocket(sessionId);
            setLoading(false);
        } catch (error) {
            console.error('Error joining session:', error);
            setError('Fehler beim Beitreten der Session');
            setLoading(false);
        }
    };

    const createOrJoinSession = async () => {
        try {
            // Try to create a new session
            const response = await api.post('/api/session/create', {
                subject_name: subjectName,
                group_name: groupName
            });
            
            // Get full session details
            const detailsResponse = await api.get(`/api/session/${response.data.session_id}`);
            
            setSessionData(detailsResponse.data);
            setParticipants(detailsResponse.data.participants || []);
            console.log('Session data loaded (create):', detailsResponse.data);
            setupWebSocket(response.data.session_id);
            setLoading(false);
        } catch (error) {
            console.error('Error with session:', error);
            if (error.response?.status === 400 && error.response?.data?.detail?.includes('already exists')) {
                setError('Eine Session für dieses Fach existiert bereits');
            } else {
                setError('Fehler beim Erstellen der Session');
            }
            setLoading(false);
        }
    };

    const setupWebSocket = (sessionId) => {
        const token = getToken();
        if (!token) return;

        let wsToken = token;
        if (token.startsWith('Bearer ')) {
            wsToken = token.substring(7);
        }

        const ws = new WebSocket(`ws://localhost:8000/ws/${wsToken}`);

        ws.onopen = () => {
            console.log('Lobby WebSocket connected');
            // Join the lobby room
            ws.send(JSON.stringify({
                type: 'join_lobby',
                session_id: sessionId
            }));
        };

        ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            console.log('Lobby WebSocket message:', message);
            
            if (message.type === 'participant_joined' || message.type === 'participant_left') {
                // Refresh participants list
                refreshParticipants(sessionId);
            } else if (message.type === 'session_started') {
                // TODO: Navigate to quiz
                console.log('Session started!');
            }
        };

        ws.onclose = () => {
            console.log('Lobby WebSocket disconnected');
        };

        ws.onerror = (error) => {
            console.error('Lobby WebSocket error:', error);
        };

        setWebsocket(ws);
    };

    const refreshParticipants = async (sessionId) => {
        try {
            const response = await api.get(`/api/session/${sessionId}`);
            setParticipants(response.data.participants || []);
            // Update host status if needed
            if (response.data.host.username !== sessionData?.host?.username) {
                setSessionData(response.data);
            }
        } catch (error) {
            console.error('Error refreshing participants:', error);
        }
    };

    const startQuiz = async () => {
        if (sessionData && sessionData.host.username === user?.username) {
            try {
                await api.post(`/api/session/start/${sessionData.id}`);
                // WebSocket will notify all participants
            } catch (error) {
                console.error('Error starting session:', error);
                setError('Fehler beim Starten der Runde');
            }
        }
    };

    const leaveSession = async () => {
        if (sessionData) {
            try {
                await api.post(`/api/session/leave/${sessionData.id}`);
                // Navigate back to subject page
                window.location.href = `/groups/${sessionData.group.name}/${sessionData.subject.name}`;
            } catch (error) {
                console.error('Error leaving session:', error);
            }
        }
    };

    // Cleanup WebSocket on unmount
    useEffect(() => {
        return () => {
            if (websocket && websocket.readyState === WebSocket.OPEN) {
                websocket.send(JSON.stringify({
                    type: 'leave_lobby',
                    session_id: sessionData?.id
                }));
                websocket.close();
            }
        };
    }, [websocket, sessionData]);
    

    return (
        <div className="parent">
            <div className='mittelPage'>
                {error && (
                    <Alert color="danger" sx={{ mb: 2 }}>
                        {error}
                    </Alert>
                )}

                {loading ? (
                    <Card>
                        <Typography>Lade Session...</Typography>
                    </Card>
                ) : (
                    <>
                        <Card>
                            <h1 className='mainPageUeberschrift'>Lobby</h1>
                            <Typography level="body-sm">
                                Gruppe: {sessionData?.group?.name || groupName} | Fach: {sessionData?.subject?.name || subjectName}
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

                        <Card>
                            <h2>Beigetreten</h2>
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
                                        disabled={participants.length < 2}
                                    >
                                        Runde starten {participants.length < 2 && '(min. 2 Spieler)'}
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

                        <OnlineUsers 
                            groupName={sessionData?.group?.name || groupName} 
                            showInviteButtons={true}
                            sessionId={sessionData?.id || sessionData?.session_id}
                        />
                    </>
                )}
            </div>
        </div>
    );
};



export default Lobby