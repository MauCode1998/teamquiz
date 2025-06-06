import React from "react";
import  Link from '@mui/joy/Link';
import { Link as RouterLink } from 'react-router-dom';
import List from '@mui/joy/List';
import ListItem from '@mui/joy/ListItem';
import Input from '@mui/joy/Input';
import Button from '@mui/joy/Button';
import ListItemDecorator from '@mui/joy/ListItemDecorator';
import Card from '@mui/joy/Card';
import Box from '@mui/joy/Box';
import Typography from '@mui/joy/Typography';
import Grid from '@mui/joy/Grid';
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
                
                <ListItem key = {einzelGruppe} sx={{
                    background: 'linear-gradient(135deg, rgba(255,255,255,0.15) 0%, rgba(255,255,255,0.05) 100%)',
                    borderRadius: '12px',
                    mb: 1,
                    cursor: 'pointer',
                    transition: 'all 0.3s ease',
                    '&:hover': {
                        background: 'linear-gradient(135deg, rgba(255,255,255,0.25) 0%, rgba(255,255,255,0.15) 100%)',
                        transform: 'translateX(5px)',
                        boxShadow: '0 4px 15px rgba(0,0,0,0.2)'
                    }
                }}>
                 <Link component={RouterLink} to={`/groups/${encodeURIComponent(einzelGruppe)}`} sx={{
                    color: '#FFF',
                    fontWeight: 'bold',
                    fontSize: { xs: '1rem', sm: '1.1rem' },
                    textDecoration: 'none',
                    '&:hover': { textDecoration: 'none' }
                 }}>🎯 {einzelGruppe}</Link>
                </ListItem>
            
    )


    const einladungen = alleEinladungen.map((Einladung,index)=> 
                
        <ListItem key = {index} sx={{
            background: 'linear-gradient(135deg, rgba(255,255,255,0.15) 0%, rgba(255,255,255,0.05) 100%)',
            borderRadius: '12px',
            mb: 1,
            p: { xs: 1.5, sm: 2 },
            transition: 'all 0.3s ease',
            '&:hover': {
                background: 'linear-gradient(135deg, rgba(255,255,255,0.25) 0%, rgba(255,255,255,0.15) 100%)',
                transform: 'translateY(-2px)',
                boxShadow: '0 4px 15px rgba(0,0,0,0.2)'
            }
        }}>
         <ListItemDecorator sx={{ 
            color: '#FFF', 
            fontWeight: 'bold', 
            fontSize: { xs: '0.9rem', sm: '1rem' },
            flexWrap: 'wrap'
         }}>
            🎉 {Einladung.From} lädt dich in die Gruppe {Einladung.To} ein!
         </ListItemDecorator> 
         <Box sx={{
            marginLeft:"auto",
            display:"flex", 
            gap: { xs: '8px', sm: '10px' },
            flexWrap: { xs: 'wrap', sm: 'nowrap' },
            justifyContent: { xs: 'center', sm: 'flex-end' },
            width: { xs: '100%', sm: 'auto' },
            mt: { xs: 1, sm: 0 }
         }}>
            <Button 
                onClick={() => einladungAnnehmen(Einladung.id)}
                size="sm"
                sx={{
                    background: 'linear-gradient(135deg, #27AE60 0%, #2ECC71 100%)',
                    color: '#FFF',
                    fontWeight: 'bold',
                    borderRadius: '10px',
                    fontSize: { xs: '0.875rem', sm: '1rem' },
                    px: { xs: 2, sm: 3 },
                    '&:hover': {
                        background: 'linear-gradient(135deg, #229954 0%, #27AE60 100%)'
                    }
                }}
            >✅ Annehmen</Button>
            <Button 
                onClick={() => einladungAblehnen(Einladung.id)}
                size="sm"
                sx={{
                    background: 'linear-gradient(135deg, #E74C3C 0%, #C0392B 100%)',
                    color: '#FFF',
                    fontWeight: 'bold',
                    borderRadius: '10px',
                    fontSize: { xs: '0.875rem', sm: '1rem' },
                    px: { xs: 2, sm: 3 },
                    '&:hover': {
                        background: 'linear-gradient(135deg, #C0392B 0%, #A93226 100%)'
                    }
                }}
            >❌ Ablehnen</Button>
         </Box>
        </ListItem>
    
)

    return (
        <Box className='parent' sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
        <Typography level="h1" sx={{
            textAlign: 'center',
            fontSize: { xs: '1.75rem', sm: '2rem', md: '2.5rem' },
            fontWeight: 'bold',
            color: '#FFF',
            textShadow: '0 3px 6px rgba(0,0,0,0.5)',
            mb: { xs: 2, sm: 3, md: 4 }
        }}>🏠 Willkommen, {user?.username || 'Benutzer'}! 🏠</Typography>
        
        <Grid 
            container 
            spacing={{ xs: 2, sm: 3 }}
            sx={{ 
                maxWidth: { lg: '1200px' },
                mx: 'auto'
            }}
        >
            <Grid xs={12} md={6}>
                <Card sx={{
                    background: 'linear-gradient(135deg, #4ECDC4 0%, #44A08D 100%)',
                    borderRadius: '25px',
                    boxShadow: '0 15px 35px rgba(78, 205, 196, 0.4)',
                    color: '#FFF',
                    height: '100%'
                }}>
                    <Typography level="h2" sx={{
                        textAlign: 'center',
                        fontWeight: 'bold',
                        textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                        fontSize: { xs: '1.5rem', sm: '1.75rem', md: '2rem' },
                        margin: '1rem 0'
                    }}>📚 Meine Gruppen</Typography>
                    
                    <List aria-labelledby="decorated-list-demo" sx={{
                        background: 'rgba(255,255,255,0.1)',
                        borderRadius: '15px',
                        p: 1,
                        backdropFilter: 'blur(10px)'
                    }}>
                        {listItems}
                    </List>
                </Card>
            </Grid>

            <Grid xs={12} md={6}>
                <Card sx={{
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    borderRadius: '25px',
                    boxShadow: '0 15px 35px rgba(102, 126, 234, 0.4)',
                    color: '#FFF',
                    height: '100%'
                }}>

                <Typography level="h3" sx={{
                    textAlign: 'center',
                    fontWeight: 'bold',
                    textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                    fontSize: { xs: '1.25rem', sm: '1.5rem' },
                    margin: '1rem 0'
                }}>➕ Neue Gruppe erstellen</Typography>
                
                <Box sx={{
                    background: 'rgba(255,255,255,0.1)',
                    borderRadius: '15px',
                    p: 2,
                    backdropFilter: 'blur(10px)'
                }}>
                    <Input 
                        placeholder='Gruppenname eingeben...'
                        value = {neueGruppe}
                        onChange = {(e) => {
                            neueGruppeAktualisieren(e.target.value);
                        }}
                        sx={{
                            background: 'rgba(255,255,255,0.9)',
                            borderRadius: '12px',
                            border: 'none',
                            mb: 2,
                            fontSize: { xs: '0.9rem', sm: '1rem' }
                        }}
                    />
                     <Button 
                      onClick={gruppeErstellen}
                      fullWidth
                      sx={{
                        background: 'linear-gradient(135deg, #27AE60 0%, #2ECC71 100%)',
                        color: '#FFF',
                        fontWeight: 'bold',
                        borderRadius: '12px',
                        fontSize: { xs: '1rem', sm: '1.1rem' },
                        boxShadow: '0 6px 20px rgba(39, 174, 96, 0.4)',
                        '&:hover': {
                            background: 'linear-gradient(135deg, #229954 0%, #27AE60 100%)',
                            transform: 'translateY(-2px)',
                            boxShadow: '0 8px 25px rgba(39, 174, 96, 0.5)'
                        }
                      }}>🚀 Erstellen!</Button>
                </Box>
                    
                </Card>
            </Grid>
            
            <Grid xs={12}>
                <Card sx={{
                    background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                    borderRadius: '25px',
                    boxShadow: '0 15px 35px rgba(240, 147, 251, 0.4)',
                    color: '#FFF'
                }}>
                <Typography level="h2" sx={{
                    textAlign: 'center',
                    fontWeight: 'bold',
                    textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                    fontSize: { xs: '1.5rem', sm: '1.75rem', md: '2rem' },
                    margin: '1rem 0'
                }}>📨 Einladungen</Typography>
               
               <List aria-labelledby="decorated-list-demo" sx={{
                    background: 'rgba(255,255,255,0.1)',
                    borderRadius: '15px',
                    p: 1,
                    backdropFilter: 'blur(10px)'
                }}>
                        {einladungen.length === 0 ? (
                            <ListItem sx={{
                                textAlign: 'center',
                                fontStyle: 'italic',
                                color: 'rgba(255,255,255,0.8)',
                                py: 3
                            }}>
                                Keine Einladungen vorhanden 📭
                            </ListItem>
                        ) : einladungen}
                    </List>
               </Card>
            </Grid>
        </Grid>
        </Box>
    );
}



export default Gruppen