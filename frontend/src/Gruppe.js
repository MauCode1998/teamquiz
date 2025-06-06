import React, { useState, useEffect} from "react";
import  Link from '@mui/joy/Link';
import { Link as RouterLink } from 'react-router-dom';
import List from '@mui/joy/List';
import ListItem from '@mui/joy/ListItem';
import ListItemDecorator from '@mui/joy/ListItemDecorator';
import Button from '@mui/joy/Button';
import Card from '@mui/joy/Card';
import Input from '@mui/joy/Input';
import Box from '@mui/joy/Box';
import Typography from '@mui/joy/Typography';
import Grid from '@mui/joy/Grid';
import { useParams, useNavigate} from "react-router-dom";
import Accordion from '@mui/joy/Accordion';
import AccordionDetails from '@mui/joy/AccordionDetails';
import AccordionSummary from '@mui/joy/AccordionSummary';
import Alert from '@mui/joy/Alert';
import api from './api/axios';



function Gruppe() {
    
    const [alleFaecher,fächerAktualisieren] =  useState([]);
    const [alleTeilnehmer,teilnehmerAktualisieren] =  useState([]);
    const [neuesFach,neuesFachAktualisieren] = useState("");
    const [fachError, setFachError] = useState("");
    const [einladungsName, setEinladungsName] = useState("");
    const [einladungsError, setEinladungsError] = useState("");
    const { groupName } = useParams();
    const navigate = useNavigate();


    async function gruppeLöschen() {
        console.log(`Gruppe wird gleich gelöscht!`)

        try {
            const response = await api.delete('/delete-group', {
                data: {"gruppen_name": groupName}
            });
            console.log(response.data)
            navigate("/groups")
        } catch (error) {
            console.error('Error deleting group:', error);
        }
    }

    async function fachErstellen() {
        console.log(`Fach ${neuesFach} wird gleich erstellt!`)
        setFachError(""); // Clear previous errors

        if (!neuesFach.trim()) {
            setFachError("Bitte geben Sie einen Fachnamen ein");
            return;
        }

        try {
            const response = await api.post('/fach-erstellen', {
                "fach_name": neuesFach.trim(),
                "gruppen_name": groupName
            });
            console.log(response.data)
            datenLaden();
            neuesFachAktualisieren("");
            setFachError(""); // Clear error on success
        } catch (error) {
            console.error('Error creating subject:', error);
            const errorMessage = error.response?.data?.detail || 'Fehler beim Erstellen des Fachs';
            setFachError(errorMessage);
        }
    }

    async function gruppeVerlassen() {
        console.log(`Gruppe wird verlassen.`)

        try {
            const response = await api.delete('/leave-group', {
                data: {"gruppen_name": groupName}
            });
            console.log(response.data)
            navigate("/groups")
        } catch (error) {
            console.error('Error leaving group:', error);
        }
    }

    async function einladungSenden() {
        console.log(`Einladung wird an ${einladungsName} gesendet`)
        setEinladungsError(""); // Clear previous errors

        if (!einladungsName.trim()) {
            setEinladungsError("Bitte geben Sie einen Benutzernamen ein");
            return;
        }

        try {
            const response = await api.post('/send-invitation', {
                "gruppen_name": groupName,
                "username": einladungsName.trim()
            });
            console.log(response.data)
            setEinladungsName("");
            setEinladungsError(""); // Clear error on success
            // Show success message could be added here
        } catch (error) {
            console.error('Error sending invitation:', error);
            const errorMessage = error.response?.data?.detail || 'Fehler beim Senden der Einladung';
            setEinladungsError(errorMessage);
        }
    }

    async function datenLaden(){
        try {
            console.log(`Loading data for group: ${groupName}`);
            const response = await api.get('/get-specific-group/', {
                params: { name: groupName }
            });
            console.log('Group data response:', response.data);
            
            const mitglieder = response.data.content.users;
            const faecher = response.data.content.subjects;
            
            console.log(`Found ${mitglieder.length} members:`, mitglieder);
            console.log(`Found ${faecher.length} subjects:`, faecher);

            fächerAktualisieren(faecher);
            teilnehmerAktualisieren(mitglieder);
        } catch (error) {
            console.error('Error loading group data:', error);
        }
    }

    useEffect(() => {
        if (groupName) {
            datenLaden();
        }
    },[groupName]);

    
    
    
    const listItems = alleFaecher.map((fach,index) => 
                
                <ListItem key={index} sx={{
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
                 <Link component={RouterLink} to={`/groups/${encodeURIComponent(groupName)}/${encodeURIComponent(fach)}`} sx={{
                    color: '#FFF',
                    fontWeight: 'bold',
                    fontSize: { xs: '1rem', sm: '1.1rem' },
                    textDecoration: 'none',
                    width: '100%',
                    '&:hover': { textDecoration: 'none' }
                 }}>📖 {fach}</Link>
                </ListItem>
     
    )
    

    const teilnehmerItems = alleTeilnehmer.map((einzelTeilnehmer, index) => 
        <ListItem key={index} sx={{
            background: 'rgba(255,255,255,0.1)',
            borderRadius: '10px',
            mb: 0.5,
            padding: { xs: '8px', sm: '12px' }
        }}>
         <ListItemDecorator><span role="img" aria-label="fire">🔥</span></ListItemDecorator> 
         <Typography sx={{ color: '#2C3E50', fontSize: { xs: '0.9rem', sm: '1rem' } }}>
            {einzelTeilnehmer}
         </Typography>
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
            mb: { xs: 2, sm: 3 }
        }}>🏆 {groupName} 🏆</Typography>
        
        <Grid 
            container 
            spacing={{ xs: 2, sm: 3 }}
            sx={{ 
                maxWidth: { lg: '1200px' },
                mx: 'auto'
            }}
        >
            {/* Subjects Card */}
            <Grid xs={12} lg={8}>
                <Card sx={{
                    height:"auto",
                    background: 'linear-gradient(135deg, #4ECDC4 0%, #44A08D 100%)',
                    borderRadius: '25px',
                    boxShadow: '0 15px 35px rgba(78, 205, 196, 0.4)',
                    color: '#FFF',
                    position: 'relative',
                    p: { xs: 2, sm: 3 }
                }}>
                    <Box sx={{ 
                        display: 'flex', 
                        justifyContent: 'space-between', 
                        alignItems: 'flex-start',
                        flexDirection: { xs: 'column', md: 'row' },
                        gap: 2
                    }}>
                        <Box sx={{ flex: 1, width: '100%' }}>
                            <Typography level="h2" sx={{
                                textAlign: 'center',
                                fontWeight: 'bold',
                                textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                                fontSize: { xs: '1.5rem', sm: '1.75rem', md: '2rem' },
                                mb: 2
                            }}>📚 Alle Fächer von {groupName}</Typography>
                            
                            <List aria-labelledby="decorated-list-demo" sx={{
                                background: 'rgba(255,255,255,0.1)',
                                borderRadius: '15px',
                                p: 2,
                                backdropFilter: 'blur(10px)'
                            }}>
                                {listItems.length === 0 ? (
                                    <ListItem sx={{
                                        textAlign: 'center',
                                        fontStyle: 'italic',
                                        color: 'rgba(255,255,255,0.8)',
                                        py: 3,
                                        background: 'rgba(255,255,255,0.05)',
                                        borderRadius: '10px'
                                    }}>
                                        📭 Noch keine Fächer vorhanden - fügen Sie das erste hinzu!
                                    </ListItem>
                                ) : listItems}
                            </List>
                        </Box>
                        
                        <Box sx={{ 
                            width: { xs: '100%', md: '250px' },
                            flexShrink: 0
                        }}>
                            <Accordion sx={{
                                background: 'rgba(255,255,255,0.15)',
                                borderRadius: '20px',
                                border: 'none',
                                backdropFilter: 'blur(15px)',
                                boxShadow: '0 8px 25px rgba(0,0,0,0.1)'
                            }}>
                                <AccordionSummary sx={{
                                    color: '#FFF',
                                    fontWeight: 'bold',
                                    fontSize: { xs: '1rem', sm: '1.1rem' },
                                    textAlign: 'center',
                                    '&:hover': {
                                        background: 'rgba(255,255,255,0.1)'
                                    }
                                }}>➕ Fach hinzufügen</AccordionSummary>
                                <AccordionDetails sx={{
                                    background: 'rgba(255,255,255,0.1)',
                                    borderRadius: '0 0 20px 20px',
                                    p: 2
                                }}>
                                {fachError && (
                                    <Alert sx={{ 
                                        mb: 2,
                                        background: 'rgba(255,255,255,0.95)',
                                        color: '#C0392B',
                                        borderRadius: '12px',
                                        border: 'none'
                                    }}>
                                        {fachError}
                                    </Alert>
                                )}
                                <Input 
                                    placeholder='Neuen Fach-Namen eingeben...'
                                    value={neuesFach}
                                    onChange={(e) => {
                                        neuesFachAktualisieren(e.target.value);
                                        if (fachError) setFachError(""); // Clear error when typing
                                    }}
                                    sx={{
                                        background: 'rgba(255,255,255,0.95)',
                                        borderRadius: '12px',
                                        border: 'none',
                                        mb: 2,
                                        fontSize: { xs: '0.9rem', sm: '1rem' }
                                    }}
                                />   
                                <Button
                                onClick={fachErstellen}
                                fullWidth
                                sx={{
                                    background: 'linear-gradient(135deg, #27AE60 0%, #2ECC71 100%)',
                                    color: '#FFF',
                                    fontWeight: 'bold',
                                    borderRadius: '12px',
                                    fontSize: { xs: '0.9rem', sm: '1rem' },
                                    boxShadow: '0 4px 15px rgba(39, 174, 96, 0.3)',
                                    '&:hover': {
                                        background: 'linear-gradient(135deg, #229954 0%, #27AE60 100%)',
                                        transform: 'translateY(-2px)',
                                        boxShadow: '0 6px 20px rgba(39, 174, 96, 0.4)'
                                    }
                                }}>💾 Speichern</Button>
                                </AccordionDetails>
                            </Accordion>
                        </Box>
                    </Box>
                </Card>
            </Grid>

            {/* Right Column - Members and Invite */}
            <Grid xs={12} lg={4}>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: { xs: 2, sm: 3 } }}>
                    {/* Members Card */}
                    <Card sx={{
                        background: 'linear-gradient(135deg, #96CEB4 0%, #FCEA2B 100%)',
                        borderRadius: '25px',
                        boxShadow: '0 15px 35px rgba(150, 206, 180, 0.4)',
                        color: '#2C3E50',
                        p: { xs: 2, sm: 3 }
                    }}>
                        
                        <Typography level="h3" sx={{
                            textAlign: 'center',
                            fontWeight: 'bold',
                            textShadow: '0 2px 4px rgba(0,0,0,0.1)',
                            fontSize: { xs: '1.25rem', sm: '1.5rem' },
                            mb: 2
                        }}>👥 Gruppenmitglieder</Typography>
                       
                        <List aria-labelledby="decorated-list-demo" sx={{
                            background: 'rgba(255,255,255,0.7)',
                            borderRadius: '15px',
                            p: 1,
                            backdropFilter: 'blur(10px)'
                        }}>
                            {teilnehmerItems}
                        </List>

                    </Card>

                    {/* Invite Card */}
                    <Card sx={{
                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        borderRadius: '25px',
                        boxShadow: '0 15px 35px rgba(102, 126, 234, 0.4)',
                        color: '#FFF',
                        p: { xs: 2, sm: 3 }
                    }}>

                    <Typography level="h3" sx={{
                        textAlign: 'center',
                        fontWeight: 'bold',
                        textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                        fontSize: { xs: '1.25rem', sm: '1.5rem' },
                        mb: 2
                    }}>📨 Person zur Gruppe einladen</Typography>
                    
                    <Box sx={{
                        background: 'rgba(255,255,255,0.1)',
                        borderRadius: '15px',
                        padding: '1rem',
                        backdropFilter: 'blur(10px)'
                    }}>
                        {einladungsError && (
                            <Alert sx={{ 
                                mb: 2,
                                background: 'rgba(255,255,255,0.9)',
                                color: '#C0392B',
                                borderRadius: '10px'
                            }}>
                                {einladungsError}
                            </Alert>
                        )}
                        <Input 
                            placeholder='Benutzername eingeben...'
                            value={einladungsName}
                            onChange={(e) => {
                                setEinladungsName(e.target.value);
                                if (einladungsError) setEinladungsError(""); // Clear error when typing
                            }}
                            sx={{
                                background: 'rgba(255,255,255,0.9)',
                                borderRadius: '10px',
                                border: 'none',
                                mb: 2,
                                fontSize: { xs: '0.9rem', sm: '1rem' }
                            }}
                        />
                         <Button 
                          onClick={einladungSenden}
                          fullWidth
                          sx={{
                            background: 'linear-gradient(135deg, #4ECDC4 0%, #44A08D 100%)',
                            color: '#FFF',
                            fontWeight: 'bold',
                            borderRadius: '10px',
                            fontSize: { xs: '1rem', sm: '1.1rem' },
                            '&:hover': {
                                background: 'linear-gradient(135deg, #44A08D 0%, #3d8f7a 100())'
                            }
                          }}>✉️ Einladen</Button>
                    </Box>
                        
                    </Card>
                </Box>
            </Grid>

            {/* Group Actions Card - Full Width */}
            <Grid xs={12}>
                <Card sx={{
                    background: 'linear-gradient(135deg, #2C3E50 0%, #34495E 100%)',
                    borderRadius: '25px',
                    boxShadow: '0 15px 35px rgba(44, 62, 80, 0.4)',
                    color: '#FFF',
                    p: { xs: 2, sm: 3 }
                }}>
                <Typography level="h3" sx={{
                    textAlign: 'center',
                    fontWeight: 'bold',
                    textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                    fontSize: { xs: '1.25rem', sm: '1.5rem' },
                    mb: 2
                }}>⚙️ Gruppenaktionen</Typography>
                
                <Box sx={{ 
                    display: 'flex', 
                    flexDirection: { xs: 'column', sm: 'row' }, 
                    gap: { xs: '10px', sm: '12px' },
                    justifyContent: 'center'
                }}>
                    <Button 
                      onClick= {gruppeVerlassen}
                      sx={{
                        background: 'linear-gradient(135deg, #F39C12 0%, #E67E22 100%)',
                        color: '#FFF',
                        fontWeight: 'bold',
                        borderRadius: '10px',
                        fontSize: { xs: '0.9rem', sm: '1rem' },
                        padding: { xs: '10px 20px', sm: '12px 30px' },
                        '&:hover': {
                            background: 'linear-gradient(135deg, #E67E22 0%, #D68910 100())'
                        }
                      }}
                      >🚪 Austreten</Button>
                  
                    <Button 
                      onClick= {gruppeLöschen}
                      sx={{
                        background: 'linear-gradient(135deg, #E74C3C 0%, #C0392B 100%)',
                        color: '#FFF',
                        fontWeight: 'bold',
                        borderRadius: '10px',
                        fontSize: { xs: '0.9rem', sm: '1rem' },
                        padding: { xs: '10px 20px', sm: '12px 30px' },
                        '&:hover': {
                            background: 'linear-gradient(135deg, #C0392B 0%, #A93226 100())'
                        }
                      }}
                      >🗑️ Gruppe Löschen</Button>
                </Box>
                    
                </Card>
            </Grid>
        </Grid>
        </Box>
    );
}



export default Gruppe