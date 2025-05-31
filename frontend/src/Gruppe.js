import React, { useState, useEffect} from "react";
import  Link from '@mui/joy/Link';
import { Link as RouterLink } from 'react-router-dom';
import List from '@mui/joy/List';
import ListItem from '@mui/joy/ListItem';
import ListItemDecorator from '@mui/joy/ListItemDecorator';
import Button from '@mui/joy/Button';
import Card from '@mui/joy/Card';
import Input from '@mui/joy/Input';
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
                
                <ListItem key={index} sx={{"&:hover":{backgroundColor: '#DDD'}, width:"50vw",cursor: 'pointer',borderRadius: '1rem',underline:'hidden',textDecoration:'none'}}>
                 <Link component={RouterLink} to={`/groups/${encodeURIComponent(groupName)}/${encodeURIComponent(fach)}`}>{fach}</Link>
                </ListItem>
     
    )
    

    const teilnehmerItems = alleTeilnehmer.map((einzelTeilnehmer, index) => 
        <ListItem key={index} sx={{"&:hover":{backgroundColor: '#DDD'}, cursor:"point",width:"50vw",borderRadius: '1rem',underline:'hidden',textDecoration:'none'}}>
         <ListItemDecorator><span role="img" aria-label="fire">🔥</span></ListItemDecorator> {einzelTeilnehmer}
        </ListItem>
)

    return (
        <div className = 'parent'>
        <h1>{groupName}</h1>
        <div className='mittelPage'>
            
            <Card className='listenCard'sx={{height:"auto"}}>
                <div id='fachUeberschrift'>
                    <h2>Alle Fächer von {groupName}</h2>
                </div>
                
                <List aria-labelledby="decorated-list-demo">
                    {listItems}
                </List>
                
                <Accordion sx={{position:"absolute",right:0,minHeight:"50px"}}>
                        <AccordionSummary>Fach hinzufügen</AccordionSummary>
                        <AccordionDetails>
                        {fachError && (
                            <Alert color="danger" sx={{ mb: 2 }}>
                                {fachError}
                            </Alert>
                        )}
                        <Input 
                            placeholder='Neuer Fach Name'
                            value={neuesFach}
                            onChange={(e) => {
                                neuesFachAktualisieren(e.target.value);
                                if (fachError) setFachError(""); // Clear error when typing
                            }}
                           
                        />   
                        <Button
                        onClick={fachErstellen}>Speichern</Button>
                        </AccordionDetails>
                        
                </Accordion>
               
            </Card>


            
            <Card >
                
                <h3>Gruppenmitglieder</h3>
               
                <List aria-labelledby="decorated-list-demo">
                    {teilnehmerItems}
                </List>
                


                </Card>

            <Card sx={{}}>

            <h3>Person zur Gruppe einladen</h3>
            {einladungsError && (
                <Alert color="danger" sx={{ mb: 2 }}>
                    {einladungsError}
                </Alert>
            )}
            <Input 
                placeholder='Benutzername'
                value={einladungsName}
                onChange={(e) => {
                    setEinladungsName(e.target.value);
                    if (einladungsError) setEinladungsError(""); // Clear error when typing
                }}
            />
             <Button 
              variant="solid" 
              color="primary"
              sx = {{marginTop: "0.5rem;"}} 
              onClick={einladungSenden}
              >Einladen</Button>
          
                
            </Card>


            <Card>
            <Button 
              variant="outlined" 
              color="primary"
              sx = {{marginTop: "0.5rem;"}} 
              onClick= {gruppeVerlassen}
              >Austreten</Button>
          
    
            <Button 
              variant="outlined" 
              color="danger"
              sx = {{marginTop: "0.5rem;"}} 
              onClick= {gruppeLöschen}
              >Gruppe Löschen</Button>
          
                
            </Card>
     

            
            
        </div>
        </div>
    );
}



export default Gruppe