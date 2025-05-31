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


function Header() {
    const { user, logout, isAuthenticated } = useAuth();
    const navigate = useNavigate();

    const handleLogout = async () => {
        await logout();
        navigate('/');
    };

    return(
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
    );
}


export default Header