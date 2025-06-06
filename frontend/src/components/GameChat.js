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
                sx={{ 
                    position: 'fixed', 
                    bottom: 20, 
                    right: 20, 
                    width: 250,
                    cursor: 'pointer',
                    zIndex: 9999,
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    borderRadius: '20px',
                    boxShadow: '0 8px 32px rgba(102, 126, 234, 0.4)',
                    border: 'none',
                    color: '#FFF'
                }}
                onClick={() => setIsExpanded(true)}
            >
                <Box sx={{ p: 2, textAlign: 'center' }}>
                    <Typography level="h4" sx={{
                        fontWeight: 'bold',
                        textShadow: '0 2px 4px rgba(0,0,0,0.3)'
                    }}>
                        💬 Chat ({messages.length})
                    </Typography>
                </Box>
            </Card>
        );
    }

    return (
        <Card 
            sx={{ 
                position: 'fixed', 
                bottom: 20, 
                right: 20, 
                width: 400,
                height: 500,
                display: 'flex',
                flexDirection: 'column',
                zIndex: 10000,
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                borderRadius: '25px',
                boxShadow: '0 15px 50px rgba(102, 126, 234, 0.5)',
                border: 'none',
                color: '#FFF'
            }}
        >
            {/* Header */}
            <Box sx={{ 
                p: 2, 
                borderBottom: '1px solid rgba(255,255,255,0.2)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                background: 'rgba(255,255,255,0.1)',
                backdropFilter: 'blur(10px)',
                borderRadius: '25px 25px 0 0'
            }}>
                <Typography level="h4" sx={{
                    fontWeight: 'bold',
                    textShadow: '0 2px 4px rgba(0,0,0,0.3)'
                }}>💬 Live Chat</Typography>
                <Button 
                    size="sm" 
                    onClick={() => setIsExpanded(false)}
                    sx={{
                        background: 'rgba(255,255,255,0.2)',
                        color: '#FFF',
                        borderRadius: '50%',
                        minWidth: '32px',
                        minHeight: '32px',
                        fontWeight: 'bold',
                        '&:hover': {
                            background: 'rgba(255,255,255,0.3)'
                        }
                    }}
                >
                    ✕
                </Button>
            </Box>

            {/* Messages */}
            <Box sx={{ 
                flex: 1, 
                overflowY: 'auto', 
                p: 2,
                maxHeight: 350,
                background: 'rgba(255,255,255,0.05)'
            }}>
                <Stack spacing={2}>
                    {messages.length === 0 ? (
                        <Typography level="body1" sx={{
                            textAlign: 'center',
                            color: 'rgba(255,255,255,0.7)',
                            fontStyle: 'italic',
                            mt: 4
                        }}>
                            Noch keine Nachrichten... 🤫
                        </Typography>
                    ) : (
                        messages.map((msg) => (
                            <Box key={msg.id} sx={{ 
                                background: 'rgba(255,255,255,0.1)',
                                borderRadius: '12px',
                                p: 1.5,
                                backdropFilter: 'blur(10px)'
                            }}>
                                <Typography level="body-xs" sx={{ 
                                    color: 'rgba(255,255,255,0.8)',
                                    fontWeight: 'bold',
                                    mb: 0.5
                                }}>
                                    👤 {msg.username} • {formatTime(msg.sent_at)}
                                </Typography>
                                <Typography level="body1" sx={{
                                    color: '#FFF',
                                    wordBreak: 'break-word'
                                }}>{msg.message}</Typography>
                            </Box>
                        ))
                    )}
                    <div ref={messagesEndRef} />
                </Stack>
            </Box>

            {/* Input */}
            <Box sx={{ 
                p: 2, 
                borderTop: '1px solid rgba(255,255,255,0.2)',
                background: 'rgba(255,255,255,0.1)',
                backdropFilter: 'blur(10px)',
                borderRadius: '0 0 25px 25px'
            }}>
                <form onSubmit={sendMessage}>
                    <Stack direction="row" spacing={1}>
                        <Input
                            placeholder="Nachricht eingeben..."
                            value={newMessage}
                            onChange={(e) => setNewMessage(e.target.value)}
                            sx={{ 
                                flex: 1,
                                background: 'rgba(255,255,255,0.9)',
                                borderRadius: '12px',
                                border: 'none',
                                '&:focus-within': {
                                    boxShadow: '0 0 0 2px rgba(255,255,255,0.5)'
                                }
                            }}
                        />
                        <Button 
                            type="submit" 
                            disabled={!newMessage.trim()}
                            sx={{
                                background: 'linear-gradient(135deg, #4ECDC4 0%, #44A08D 100%)',
                                color: '#FFF',
                                fontWeight: 'bold',
                                borderRadius: '12px',
                                px: 3,
                                '&:hover': {
                                    background: 'linear-gradient(135deg, #44A08D 0%, #3d8f7a 100%)',
                                    transform: 'translateY(-1px)'
                                },
                                '&:disabled': {
                                    background: 'rgba(255,255,255,0.3)',
                                    color: 'rgba(255,255,255,0.6)'
                                }
                            }}
                        >
                            📤 Senden
                        </Button>
                    </Stack>
                </form>
            </Box>
        </Card>
    );
};

export default GameChat;