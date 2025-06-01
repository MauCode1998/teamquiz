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

function OnlineUsers({ groupName, showInviteButtons = false, sessionId = null }) {
    const [onlineUsers, setOnlineUsers] = useState([]);
    const [websocket, setWebsocket] = useState(null);
    const [inviteStatus, setInviteStatus] = useState({});
    const [error, setError] = useState('');
    const { getToken, user } = useAuth();

    useEffect(() => {
        const token = getToken();
        if (!token || !groupName) return;

        // Extract JWT token from cookie format if needed
        let wsToken = token;
        if (token.startsWith('Bearer ')) {
            wsToken = token.substring(7);
        }

        // Establish WebSocket connection
        const ws = new WebSocket(`ws://localhost:8000/ws/${wsToken}`);

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
    }, [getToken, groupName]);

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
                    "&:hover": { backgroundColor: '#DDD' },
                    borderRadius: '1rem',
                    display: "flex",
                    textDecoration: 'none'
                }}
            >
                <ListItemDecorator>
                    {userItem.username} {isCurrentUser && '(Du)'}
                </ListItemDecorator>
                {showInviteButtons && !isCurrentUser && (
                    <Button 
                        sx={{ marginLeft: "auto" }} 
                        color={status === 'sent' ? 'success' : 'primary'}
                        size="sm"
                        onClick={() => handleInvite(userItem.username)}
                        disabled={status === 'loading' || status === 'sent'}
                        loading={status === 'loading'}
                    >
                        {status === 'sent' ? 'Eingeladen ✓' : 'Einladen'}
                    </Button>
                )}
            </ListItem>
        );
    });

    return (
        <Card>
            <h3>🟢 Online ({onlineUsers.length})</h3>
            <Divider />
            {error && (
                <Alert color="danger" sx={{ mb: 2 }} onClose={() => setError('')}>
                    {error}
                </Alert>
            )}
            <Card sx={{ backgroundColor: "#FFF", height: "100%" }}>
                <List aria-labelledby="online-users-list">
                    {userItems.length > 0 ? userItems : (
                        <ListItem>
                            <ListItemDecorator>Keine Benutzer online</ListItemDecorator>
                        </ListItem>
                    )}
                </List>
            </Card>
        </Card>
    );
}

export default OnlineUsers;