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


function Header() {


    const loginkomponente = <Link sx={{marginLeft:"1rem",marginRight:"1rem"}} color="white" underline="none" href="/login">
                                Login
                            </Link>
                           

   
    


    const eingeloggt = <p>Mau</p>

    const [loggedIn,setLogin] = useState(loginkomponente);
    
    const toggle = true;

    useEffect(() => {
        if (toggle) {
            setLogin(eingeloggt)
        } else {
            setLogin(loginkomponente)
        }
       
},[])
   

    return(
        <header >
            <Link color="neutral" underline="none" href="/gruppen">
                <img src={Logo} style={{width:"15rem",height:"12rem"}} ></img>
            </Link>
            
            <div id='headerlinks'>
                <Link sx={{marginLeft:"1rem",marginRight:"1rem"}} color="white" underline="none" href="/gruppen">
                Startseite
                </Link>
                
                {loggedIn}

               
            </div>
            
            
        </header>
    );
}


export default Header