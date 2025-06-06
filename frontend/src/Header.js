import React from 'react'
import deutschIcon from "./teamquizlogo.jpeg";
import Link from '@mui/joy/Link';
import List from '@mui/joy/List';
import Button from  '@mui/joy/Button';
import Box from '@mui/joy/Box';
import IconButton from '@mui/joy/IconButton';
import Drawer from '@mui/joy/Drawer';
import { useState,useEffect } from 'react';
import AccordionDetails from '@mui/joy/AccordionDetails';
import AccordionSummary from '@mui/joy/AccordionSummary';
import Accordion from '@mui/joy/Accordion';
import Logo from './logo.png';
import AccordionGroup from '@mui/joy/AccordionGroup';
import { useAuth } from './AuthContext';
import { useNavigate, Link as RouterLink } from 'react-router-dom';
import Badge from '@mui/joy/Badge';
import InvitationModal from './components/InvitationModal';
import api from './api/axios';



function Header() {
    const { user, logout, isAuthenticated } = useAuth();
    const navigate = useNavigate();
    const [invitationCount, setInvitationCount] = useState(0);
    const [showInvitationModal, setShowInvitationModal] = useState(false);
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

    useEffect(() => {
        if (isAuthenticated) {
            fetchInvitationCount();
            // Poll for new invitations every 10 seconds
            const interval = setInterval(fetchInvitationCount, 10000);
            return () => clearInterval(interval);
        }
    }, [isAuthenticated]);

    const fetchInvitationCount = async () => {
        try {
            const response = await api.get('/api/invitations/pending');
            const invitations = response.data || [];
            setInvitationCount(invitations.length);
        } catch (error) {
            console.error('Error fetching invitation count:', error);
        }
    };

    const handleLogout = async () => {
        await logout();
        navigate('/');
    };

    return(
        <>
            <Box component="header" sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: { xs: '0 1rem', sm: '0 1.5rem', md: '0 2rem' },
                position: 'relative'
            }}>
                <Link component={RouterLink} to="/groups" color="neutral" underline="none">
                    <Box 
                        component="img" 
                        src={Logo} 
                        sx={{
                            width: { xs: '10rem', sm: '12rem', md: '15rem' },
                            height: { xs: '8rem', sm: '10rem', md: '12rem' },
                            filter: 'drop-shadow(0 4px 8px rgba(0,0,0,0.3))',
                            transition: 'transform 0.3s ease',
                            '&:hover': {
                                transform: 'scale(1.05)'
                            }
                        }} 
                    />
                </Link>
                
                {/* Desktop Navigation */}
                <Box sx={{
                    display: { xs: 'none', md: 'flex' },
                    alignItems: 'center',
                    gap: '1rem'
                }}>
                    {isAuthenticated && (
                        <Link component={RouterLink} to="/groups" sx={{
                            color: '#FFF',
                            fontWeight: 'bold',
                            fontSize: '1.1rem',
                            textDecoration: 'none',
                            background: 'rgba(255,255,255,0.1)',
                            borderRadius: '10px',
                            padding: '8px 16px',
                            transition: 'all 0.3s ease',
                            '&:hover': {
                                background: 'rgba(255,255,255,0.2)',
                                transform: 'translateY(-2px)',
                                textDecoration: 'none'
                            }
                        }}>
                            🏠 Startseite
                        </Link>
                    )}
                    
                    {isAuthenticated ? (
                        <>
                            <Badge 
                                badgeContent={invitationCount} 
                                color="danger"
                                invisible={invitationCount === 0}
                            >
                                <IconButton
                                    onClick={() => setShowInvitationModal(true)}
                                    sx={{
                                        background: 'rgba(255,255,255,0.15)',
                                        color: '#FFF',
                                        borderRadius: '12px',
                                        fontSize: '1.2rem',
                                        border: '2px solid rgba(255,255,255,0.3)',
                                        transition: 'all 0.3s ease',
                                        '&:hover': {
                                            background: 'rgba(255,255,255,0.25)',
                                            transform: 'scale(1.1)',
                                            borderColor: 'rgba(255,255,255,0.5)'
                                        }
                                    }}
                                >
                                    📧
                                </IconButton>
                            </Badge>
                            <span style={{
                                color: '#FFF',
                                fontWeight: 'bold',
                                fontSize: '1.1rem',
                                background: 'rgba(255,255,255,0.15)',
                                borderRadius: '10px',
                                padding: '8px 12px',
                                backdropFilter: 'blur(10px)',
                                textShadow: '0 2px 4px rgba(0,0,0,0.3)'
                            }}>
                                👤 {user?.username}
                            </span>
                            <Button 
                                onClick={handleLogout}
                                sx={{
                                    background: 'linear-gradient(135deg, #E74C3C 0%, #C0392B 100%)',
                                    color: '#FFF',
                                    fontWeight: 'bold',
                                    borderRadius: '10px',
                                    border: 'none',
                                    fontSize: '1rem',
                                    boxShadow: '0 4px 15px rgba(231, 76, 60, 0.3)',
                                    transition: 'all 0.3s ease',
                                    '&:hover': {
                                        background: 'linear-gradient(135deg, #C0392B 0%, #A93226 100%)',
                                        transform: 'translateY(-2px)',
                                        boxShadow: '0 6px 20px rgba(231, 76, 60, 0.4)'
                                    }
                                }}
                            >
                                🚪 Logout
                            </Button>
                        </>
                    ) : (
                        <Link component={RouterLink} to="/" sx={{
                            color: '#FFF',
                            fontWeight: 'bold',
                            fontSize: '1.1rem',
                            textDecoration: 'none',
                            background: 'rgba(255,255,255,0.15)',
                            borderRadius: '10px',
                            padding: '8px 16px',
                            transition: 'all 0.3s ease',
                            '&:hover': {
                                background: 'rgba(255,255,255,0.25)',
                                transform: 'translateY(-2px)',
                                textDecoration: 'none'
                            }
                        }}>
                            🔑 Login
                        </Link>
                    )}
                </Box>

                {/* Mobile Menu Button */}
                <Box sx={{ display: { xs: 'flex', md: 'none' }, alignItems: 'center', gap: 1 }}>
                    {isAuthenticated && (
                        <Badge 
                            badgeContent={invitationCount} 
                            color="danger"
                            invisible={invitationCount === 0}
                        >
                            <IconButton
                                onClick={() => setShowInvitationModal(true)}
                                sx={{
                                    background: 'rgba(255,255,255,0.15)',
                                    color: '#FFF',
                                    borderRadius: '8px',
                                    fontSize: '1.1rem',
                                    p: 1
                                }}
                            >
                                📧
                            </IconButton>
                        </Badge>
                    )}
                    <IconButton
                        onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                        sx={{
                            background: 'rgba(255,255,255,0.15)',
                            color: '#FFF',
                            borderRadius: '8px',
                            fontSize: '1.5rem',
                            p: 1,
                            '&:hover': {
                                background: 'rgba(255,255,255,0.25)'
                            }
                        }}
                    >
                        ☰
                    </IconButton>
                </Box>
            </Box>

            {/* Mobile Drawer */}
            <Drawer
                anchor="right"
                open={mobileMenuOpen}
                onClose={() => setMobileMenuOpen(false)}
                sx={{
                    '& .MuiDrawer-paper': {
                        width: '250px',
                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        color: '#FFF'
                    }
                }}
            >
                <Box sx={{ p: 2 }}>
                    {isAuthenticated ? (
                        <>
                            <Box sx={{
                                background: 'rgba(255,255,255,0.15)',
                                borderRadius: '10px',
                                p: 2,
                                mb: 2,
                                textAlign: 'center'
                            }}>
                                <span style={{ fontSize: '1.2rem' }}>👤 {user?.username}</span>
                            </Box>
                            
                            <Button
                                component={RouterLink}
                                to="/groups"
                                onClick={() => setMobileMenuOpen(false)}
                                fullWidth
                                sx={{
                                    mb: 2,
                                    color: '#FFF',
                                    background: 'rgba(255,255,255,0.1)',
                                    justifyContent: 'flex-start',
                                    '&:hover': {
                                        background: 'rgba(255,255,255,0.2)'
                                    }
                                }}
                            >
                                🏠 Startseite
                            </Button>
                            
                            <Button 
                                onClick={() => {
                                    handleLogout();
                                    setMobileMenuOpen(false);
                                }}
                                fullWidth
                                sx={{
                                    background: 'linear-gradient(135deg, #E74C3C 0%, #C0392B 100%)',
                                    color: '#FFF',
                                    fontWeight: 'bold',
                                    '&:hover': {
                                        background: 'linear-gradient(135deg, #C0392B 0%, #A93226 100%)'
                                    }
                                }}
                            >
                                🚪 Logout
                            </Button>
                        </>
                    ) : (
                        <Button
                            component={RouterLink}
                            to="/"
                            onClick={() => setMobileMenuOpen(false)}
                            fullWidth
                            sx={{
                                color: '#FFF',
                                background: 'rgba(255,255,255,0.1)',
                                '&:hover': {
                                    background: 'rgba(255,255,255,0.2)'
                                }
                            }}
                        >
                            🔑 Login
                        </Button>
                    )}
                </Box>
            </Drawer>
            
            {isAuthenticated && (
                <InvitationModal 
                    open={showInvitationModal} 
                    onClose={() => {
                        setShowInvitationModal(false);
                        fetchInvitationCount(); // Refresh count when modal closes
                    }}
                />
            )}
        </>
    );
}


export default Header