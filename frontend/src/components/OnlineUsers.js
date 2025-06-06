import React, { useState, useEffect, useContext } from 'react';
import List from '@mui/joy/List';
import ListItem from '@mui/joy/ListItem';
import ListItemDecorator from '@mui/joy/ListItemDecorator';
import Card from '@mui/joy/Card';
import Divider from '@mui/joy/Divider';
import Button from '@mui/joy/Button';
import { useAuth } from '../AuthContext';
import api from '../api/axios';
import Alert from '@mui/joy/Alert';

function OnlineUsers({ groupName, showInviteButtons = false, sessionId = null, disableWebSocket = false }) {
    const [onlineUsers, setOnlineUsers] = useState([]);
    const [websocket, setWebsocket] = useState(null);
    const [inviteStatus, setInviteStatus] = useState({});
    const [error, setError] = useState('');
    const { getToken, user } = useAuth();

    useEffect(() => {
        const token = getToken();
        if (!token || !groupName || disableWebSocket) return;

        // Extract JWT token from cookie format if needed
        let wsToken = token;
        if (token.startsWith('Bearer ')) {
            wsToken = token.substring(7);
        }

        // Establish WebSocket connection - use same host and port as current page
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsHost = window.location.host; // includes hostname:port
        const wsUrl = `${wsProtocol}//${wsHost}/ws/${wsToken}`;
        
        console.log('OnlineUsers WebSocket connecting to:', wsUrl);
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            console.log('WebSocket connected for group:', groupName);
            // Join the group
            ws.send(JSON.stringify({
                type: 'join_group',
                group_name: groupName
            }));
        };

        ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            console.log('WebSocket message received:', message);
            
            if (message.type === 'online_users_update' && message.group_name === groupName) {
                setOnlineUsers(message.online_users);
            }
        };

        ws.onclose = () => {
            console.log('WebSocket disconnected');
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        setWebsocket(ws);

        // Cleanup on unmount
        return () => {
            if (ws.readyState === WebSocket.OPEN) {
                // Leave the group before disconnecting
                ws.send(JSON.stringify({
                    type: 'leave_group',
                    group_name: groupName
                }));
            }
            ws.close();
        };
    }, [getToken, groupName, disableWebSocket]);

    // Fallback: Load online users via API if WebSocket is disabled
    useEffect(() => {
        if (disableWebSocket && groupName) {
            const loadOnlineUsers = async () => {
                try {
                    const response = await api.get(`/api/online-users/${groupName}`);
                    setOnlineUsers(response.data.online_users || []);
                } catch (error) {
                    console.error('Error loading online users:', error);
                }
            };

            loadOnlineUsers();
            // Refresh every 5 seconds when WebSocket is disabled
            const interval = setInterval(loadOnlineUsers, 5000);
            
            return () => clearInterval(interval);
        }
    }, [groupName, disableWebSocket]);

    const handleInvite = async (username) => {
        if (!sessionId) {
            setError('Keine aktive Session. Bitte erstellen Sie zuerst eine Lobby.');
            return;
        }

        console.log(`Inviting user: ${username} to session: ${sessionId}`);
        setInviteStatus({ ...inviteStatus, [username]: 'loading' });
        
        try {
            await api.post('/api/invitation/send', {
                session_id: sessionId,
                invitee_username: username
            });
            setInviteStatus({ ...inviteStatus, [username]: 'sent' });
            setTimeout(() => {
                setInviteStatus(prev => {
                    const updated = { ...prev };
                    delete updated[username];
                    return updated;
                });
            }, 3000);
        } catch (error) {
            console.error('Error sending invitation:', error);
            setError(error.response?.data?.detail || 'Fehler beim Senden der Einladung');
            setInviteStatus({ ...inviteStatus, [username]: 'error' });
        }
    };

    const userItems = onlineUsers.map((userItem, index) => {
        const isCurrentUser = userItem.username === user?.username;
        const status = inviteStatus[userItem.username];
        
        return (
            <ListItem 
                key={userItem.user_id} 
                sx={{
                    background: isCurrentUser 
                        ? 'linear-gradient(135deg, rgba(39, 174, 96, 0.2) 0%, rgba(46, 204, 113, 0.2) 100%)'
                        : 'linear-gradient(135deg, rgba(44, 62, 80, 0.1) 0%, rgba(44, 62, 80, 0.05) 100%)',
                    borderRadius: '10px',
                    mb: 1,
                    display: "flex",
                    alignItems: 'center',
                    transition: 'all 0.3s ease',
                    border: isCurrentUser ? '2px solid #27AE60' : '1px solid rgba(44, 62, 80, 0.1)',
                    '&:hover': {
                        background: isCurrentUser
                            ? 'linear-gradient(135deg, rgba(39, 174, 96, 0.3) 0%, rgba(46, 204, 113, 0.3) 100%)'
                            : 'linear-gradient(135deg, rgba(44, 62, 80, 0.2) 0%, rgba(44, 62, 80, 0.1) 100%)',
                        transform: 'translateX(3px)'
                    }
                }}
            >
                <ListItemDecorator sx={{ 
                    color: '#2C3E50', 
                    fontWeight: isCurrentUser ? 'bold' : 'normal',
                    fontSize: '1rem'
                }}>
                    {isCurrentUser ? '👤' : '🟢'} {userItem.username} {isCurrentUser && '(Du)'}
                </ListItemDecorator>
                {showInviteButtons && !isCurrentUser && (
                    <Button 
                        sx={{ 
                            marginLeft: "auto",
                            background: status === 'sent' 
                                ? 'linear-gradient(135deg, #27AE60 0%, #2ECC71 100%)'
                                : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                            color: '#FFF',
                            fontWeight: 'bold',
                            borderRadius: '8px',
                            fontSize: '0.8rem',
                            '&:hover': {
                                transform: 'scale(1.05)'
                            }
                        }} 
                        size="sm"
                        onClick={() => handleInvite(userItem.username)}
                        disabled={status === 'loading' || status === 'sent'}
                        loading={status === 'loading'}
                    >
                        {status === 'sent' ? '✅ Eingeladen' : '📨 Einladen'}
                    </Button>
                )}
            </ListItem>
        );
    });

    return (
        <Card sx={{
            background: 'linear-gradient(135deg, #96CEB4 0%, #FCEA2B 100%)',
            borderRadius: '25px',
            boxShadow: '0 15px 35px rgba(150, 206, 180, 0.4)',
            color: '#2C3E50'
        }}>
            <h3 style={{
                textAlign: 'center',
                fontWeight: 'bold',
                textShadow: '0 2px 4px rgba(0,0,0,0.1)',
                fontSize: '1.5rem',
                margin: '1rem 0'
            }}>🟢 Online ({onlineUsers.length})</h3>
            
            {error && (
                <Alert sx={{
                    mb: 2,
                    background: 'rgba(255,255,255,0.9)',
                    color: '#C0392B',
                    borderRadius: '10px'
                }} onClose={() => setError('')}>
                    {error}
                </Alert>
            )}
            
            <Card sx={{ 
                backgroundColor: "rgba(255,255,255,0.7)", 
                height: "100%",
                borderRadius: '15px',
                backdropFilter: 'blur(10px)'
            }}>
                <List aria-labelledby="online-users-list">
                    {userItems.length > 0 ? userItems : (
                        <ListItem sx={{
                            textAlign: 'center',
                            fontStyle: 'italic',
                            color: '#666',
                            py: 2
                        }}>
                            <ListItemDecorator>Keine Benutzer online 📭</ListItemDecorator>
                        </ListItem>
                    )}
                </List>
            </Card>
        </Card>
    );
}

export default OnlineUsers;