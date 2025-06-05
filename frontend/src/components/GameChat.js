import React, { useState, useEffect, useRef } from 'react';
import { Box, Card, Typography, Input, Button, Stack } from '@mui/joy';
import axios from '../api/axios';

const GameChat = ({ sessionId, websocket }) => {
    const [messages, setMessages] = useState([]);
    const [newMessage, setNewMessage] = useState('');
    const [isExpanded, setIsExpanded] = useState(false);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        if (messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
        }
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Load existing messages on mount
    useEffect(() => {
        const loadMessages = async () => {
            try {
                const response = await axios.get(`/api/game/chat/${sessionId}`);
                setMessages(response.data.messages);
            } catch (error) {
                console.error('Error loading chat messages:', error);
            }
        };

        if (sessionId) {
            loadMessages();
        }
    }, [sessionId]);

    // Listen for WebSocket chat messages
    useEffect(() => {
        if (!websocket) return;

        const handleMessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'chat_message') {
                setMessages(prev => [...prev, data.message]);
            }
        };

        websocket.addEventListener('message', handleMessage);
        return () => websocket.removeEventListener('message', handleMessage);
    }, [websocket]);

    const sendMessage = async (e) => {
        e.preventDefault();
        if (!newMessage.trim()) return;

        try {
            await axios.post('/api/game/chat', {
                session_id: sessionId,
                message: newMessage.trim()
            });
            setNewMessage('');
        } catch (error) {
            console.error('Error sending message:', error);
        }
    };

    const formatTime = (timestamp) => {
        return new Date(timestamp).toLocaleTimeString('de-DE', {
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    if (!isExpanded) {
        return (
            <Card 
                variant="outlined" 
                sx={{ 
                    position: 'fixed', 
                    bottom: 20, 
                    right: 20, 
                    width: 250,
                    cursor: 'pointer'
                }}
                onClick={() => setIsExpanded(true)}
            >
                <Box sx={{ p: 1, textAlign: 'center' }}>
                    <Typography level="body-sm">
                        💬 Chat ({messages.length})
                    </Typography>
                </Box>
            </Card>
        );
    }

    return (
        <Card 
            variant="outlined" 
            sx={{ 
                position: 'fixed', 
                bottom: 20, 
                right: 20, 
                width: 350,
                height: 400,
                display: 'flex',
                flexDirection: 'column'
            }}
        >
            {/* Header */}
            <Box sx={{ 
                p: 1, 
                borderBottom: '1px solid', 
                borderColor: 'divider',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
            }}>
                <Typography level="title-sm">💬 Chat</Typography>
                <Button 
                    size="sm" 
                    variant="plain"
                    onClick={() => setIsExpanded(false)}
                >
                    ✕
                </Button>
            </Box>

            {/* Messages */}
            <Box sx={{ 
                flex: 1, 
                overflowY: 'auto', 
                p: 1,
                maxHeight: 280
            }}>
                <Stack spacing={1}>
                    {messages.map((msg) => (
                        <Box key={msg.id} sx={{ fontSize: '0.875rem' }}>
                            <Typography level="body-xs" sx={{ color: 'text.secondary' }}>
                                <strong>{msg.username}</strong> {formatTime(msg.sent_at)}
                            </Typography>
                            <Typography level="body-sm">{msg.message}</Typography>
                        </Box>
                    ))}
                    <div ref={messagesEndRef} />
                </Stack>
            </Box>

            {/* Input */}
            <Box sx={{ p: 1, borderTop: '1px solid', borderColor: 'divider' }}>
                <form onSubmit={sendMessage}>
                    <Stack direction="row" spacing={1}>
                        <Input
                            size="sm"
                            placeholder="Nachricht eingeben..."
                            value={newMessage}
                            onChange={(e) => setNewMessage(e.target.value)}
                            sx={{ flex: 1 }}
                        />
                        <Button 
                            type="submit" 
                            size="sm"
                            disabled={!newMessage.trim()}
                        >
                            Senden
                        </Button>
                    </Stack>
                </form>
            </Box>
        </Card>
    );
};

export default GameChat;