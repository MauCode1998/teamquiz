import React from "react";
import  Link from '@mui/joy/Link';
import { Link as RouterLink } from 'react-router-dom';
import List from '@mui/joy/List';
import ListItem from '@mui/joy/ListItem';
import Input from '@mui/joy/Input';
import Button from '@mui/joy/Button';
import ListItemDecorator from '@mui/joy/ListItemDecorator';
import Card from '@mui/joy/Card';
import {useState,useEffect} from 'react';
import api from './api/axios';
import { useAuth } from './AuthContext';

function Gruppen() {
    const { user } = useAuth();
    const [alleGruppen,gruppeAktualisieren] = useState([]);
    const [alleEinladungen,einladungenAktualisieren] = useState([]);
    const [neueGruppe,neueGruppeAktualisieren] = useState("");

    async function ladeGruppe() {
        try {
            const response = await api.get('/get-gruppeninfo');
            const gruppen = response.data.content.groups.map(gruppe => gruppe.name);
            console.log(gruppen)
            gruppeAktualisieren(gruppen)
        } catch (error) {
            console.error('Error loading groups:', error);
        }
    }
    
    useEffect(()=> {
        
        ladeGruppe();

    },[]);

    async function gruppeErstellen() {
        console.log(`Gruppe ${neueGruppe} wird gleich erstellt!`)
        
        try {
            const response = await api.post('/gruppe-erstellen', {
                "gruppen_name": neueGruppe
            });
            console.log(response.data)
            ladeGruppe();
        } catch (error) {
            console.error('Error creating group:', error);
        }
    }

    async function einladungAnnehmen(invitationId) {
        console.log(`Einladung ${invitationId} wird angenommen`)
        
        try {
            const response = await api.post('/accept-invitation', {
                "invitation_id": invitationId
            });
            console.log(response.data)
            ladeGruppe(); // Reload groups
            ladeEinladungen(); // Reload invitations
        } catch (error) {
            console.error('Error accepting invitation:', error);
        }
    }

    async function einladungAblehnen(invitationId) {
        console.log(`Einladung ${invitationId} wird abgelehnt`)
        
        try {
            const response = await api.post('/reject-invitation', {
                "invitation_id": invitationId
            });
            console.log(response.data)
            ladeEinladungen(); // Reload invitations
        } catch (error) {
            console.error('Error rejecting invitation:', error);
        }
    }

    async function ladeEinladungen() {
        try {
            const response = await api.get('/get-invitations');
            const einladungen = response.data.content
            console.log(einladungen)
            einladungenAktualisieren(einladungen);
        } catch (error) {
            console.error('Error loading invitations:', error);
        }
    }
    


        useEffect(()=> {
            ladeEinladungen();
        },[]);
    


    const listItems = alleGruppen.map(einzelGruppe => 
                
                <ListItem key = {einzelGruppe} sx={{"&:hover":{backgroundColor: '#DDD'}, height:"2rem", width:"50vw",cursor: 'pointer',borderRadius: '1rem',underline:'hidden',textDecoration:'none'}}>
                 <Link component={RouterLink} to={`/groups/${encodeURIComponent(einzelGruppe)}`}>{einzelGruppe}</Link>
                </ListItem>
            
    )


    const einladungen = alleEinladungen.map((Einladung,index)=> 
                
        <ListItem key = {index} sx={{"&:hover":{backgroundColor: '#DDD'}, height:"2rem", width:"50vw",cursor: 'pointer',borderRadius: '1rem',underline:'hidden',textDecoration:'none'}}>
         <ListItemDecorator>{Einladung.From} lädt dich in die Gruppe {Einladung.To} ein!  </ListItemDecorator> <div style={{marginLeft:"auto",display:"flex"}}><Button variant="outlined" color="primary" sx={{marginRight:"1rem"}} onClick={() => einladungAnnehmen(Einladung.id)}>Annehmen</Button><Button variant="outlined" color="danger" sx={{marginLeft:"auto"}} onClick={() => einladungAblehnen(Einladung.id)}>Ablehnen</Button></div>
        </ListItem>
    
)

    return (
        <div className='parent'>
        <h1>Willkommen, {user?.username || 'Benutzer'}.</h1>
        <div className='mittelPage'>

            <Card>
                <h2>Meine Gruppen</h2>
                <List aria-labelledby="decorated-list-demo">
                    {listItems}
                
                </List>

                
            </Card>

            <Card sx={{}}>

            <h3>Neue Gruppe erstellen</h3>
            <Input 
                placeholder='Gruppenname'
                value = {neueGruppe}
                onChange = {(e) => {
                    neueGruppeAktualisieren(e.target.value);
                }
}
            />
             <Button 
              variant="outlined" 
              color="success"
              sx = {{marginTop: "0.5rem;"}} 
              onClick={gruppeErstellen}>Erstellen!</Button>
                
            </Card>
           <Card>
           <h2>Einladungen</h2>
           <List aria-labelledby="decorated-list-demo">
                    {einladungen}
                
                </List>
           </Card>

            
            
        </div>
        </div>
    );
}



export default Gruppen