import React from 'react'
import deutschIcon from "./teamquizlogo.jpeg";
import Link from '@mui/joy/Link';
import List from '@mui/joy/List';
import Button from  '@mui/joy/Button';
import { useState,useEffect } from 'react';
import AccordionDetails from '@mui/joy/AccordionDetails';
import AccordionSummary from '@mui/joy/AccordionSummary';
import Accordion from '@mui/joy/Accordion';
import Logo from './logo.jpeg';
import AccordionGroup from '@mui/joy/AccordionGroup';
import { useAuth } from './AuthContext';
import { useNavigate, Link as RouterLink } from 'react-router-dom';
import Badge from '@mui/joy/Badge';
import IconButton from '@mui/joy/IconButton';
import InvitationModal from './components/InvitationModal';
import api from './api/axios';


function Header() {
    const { user, logout, isAuthenticated } = useAuth();
    const navigate = useNavigate();
    const [invitationCount, setInvitationCount] = useState(0);
    const [showInvitationModal, setShowInvitationModal] = useState(false);

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
            <header >
                <Link component={RouterLink} to="/groups" color="neutral" underline="none">
                    <img src={Logo} style={{width:"15rem",height:"12rem"}} ></img>
                </Link>
                
                <div id='headerlinks'>
                    {isAuthenticated && (
                        <Link component={RouterLink} to="/groups" sx={{marginLeft:"1rem",marginRight:"1rem"}} color="white" underline="none">
                            Startseite
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
                                    color="neutral"
                                    variant="outlined"
                                    size="sm"
                                    onClick={() => setShowInvitationModal(true)}
                                    sx={{marginLeft:"1rem"}}
                                >
                                    📧
                                </IconButton>
                            </Badge>
                            <span style={{color: 'white', marginLeft: '1rem', marginRight: '1rem'}}>
                                {user?.username}
                            </span>
                            <Button 
                                variant="outlined" 
                                color="neutral"
                                size="sm"
                                sx={{marginLeft:"1rem",marginRight:"1rem"}}
                                onClick={handleLogout}
                            >
                                Logout
                            </Button>
                        </>
                    ) : (
                        <Link component={RouterLink} to="/" sx={{marginLeft:"1rem",marginRight:"1rem"}} color="white" underline="none">
                            Login
                        </Link>
                    )}
                </div>
            </header>
            
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