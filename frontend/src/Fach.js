import React, { use } from "react";
import  Link from '@mui/joy/Link';
import List from '@mui/joy/List';
import ListItem from '@mui/joy/ListItem';
import ListItemDecorator from '@mui/joy/ListItemDecorator';
import Button from '@mui/joy/Button';
import Card from '@mui/joy/Card';
import Divider from '@mui/joy/Divider';
import CardCover from '@mui/joy/CardCover'
import Input from '@mui/joy/Input';
import { useSearchParams } from "react-router-dom";
import Accordion from '@mui/joy/Accordion';
import AccordionDetails from '@mui/joy/AccordionDetails';
import Bild from './start.jpeg';
import AccordionGroup from '@mui/joy/AccordionGroup';
import AccordionSummary from '@mui/joy/AccordionSummary';




function Fach() {
    const [parameter] = useSearchParams();
    const fachname = parameter.get("name");
    const gruppenId = parameter.get("gruppenid")
    const alleTeilnehmer = ["Mau","Hongfa"];
    const alleKarteikarten = ["Wie groß war Napoleon?","Ist Steak groß?","Wie nice ist Ida bitte"]
    const kartenId = "1"
    const gameid = "2"
    const gesamtAnzahlFragen = alleKarteikarten.length

    const teilnehmerItems = alleTeilnehmer.map(einzelTeilnehmer => 
        <ListItem sx={{"&:hover":{backgroundColor: '#DDD'},borderRadius: '1rem',display:"flex",underline:'hidden',textDecoration:'none'}}>
         <ListItemDecorator>{einzelTeilnehmer}</ListItemDecorator>
        </ListItem>)

    const kartenHTML = alleKarteikarten.map(karteikarte =>
        <li key = {karteikarte}>
            <Accordion>
            <AccordionSummary>{karteikarte}</AccordionSummary>
                        <AccordionDetails>
                        <div className='buttonKombo'>
                        <Input  placeholder='Falsche Antwort 1' value="Dwaine the Rock Johnson" />
                        <Input sx={{marginTop:"1rem"}}  placeholder='Falsche Antwort 2' value="Ketemenräng" wda/>
                        <Input sx={{marginTop:"1rem"}}  placeholder='Falsche Antwort 3' value="Met" />
                        <Input sx={{marginTop:"1rem",marginBottom:"1rem"}} color="success" placeholder='Richtige Antwort' value="Garler" />
                        <Button sx={{marginRight:"1rem"}} variant="outlined">Speichern</Button><Button color="danger" variant="outlined">Frage Löschen</Button>
                        </div>
                        
                        </AccordionDetails>
            </Accordion>
        </li>
    )

    return (
        
        <div className='mittelPage'>
            
            <Card sx={{ display:"flex", cursor:"pointer",alignItems:"center",justifyContent:"center"}}>
            <CardCover sx={{overflow:"hidden"}}>
            <Link href={`/lobby?gameid=${gameid}`}>
                    <img
                        src={Bild}
                        
                        loading="lazy"
                        alt=""
                    />
            </Link>
            </CardCover>
                
            </Card>

            <Card>
                
                <h3>🟢 Online</h3>
                <Divider></Divider>
                <Card  sx = {{backgroundColor:"#FFF", height:"100%"}}>
                    <List aria-labelledby="decorated-list-demo">
                        {teilnehmerItems}
                    </List>
                </Card>

                

            </Card>
           
            <Card>
            <h2 className = 'mainPageUeberschrift'>Alle Fragen ({gesamtAnzahlFragen})</h2>
                        
            
                <List>
                    {kartenHTML}
                    <Accordion variant="plain">
                        <AccordionSummary variant="plain" sx={{"&:hover":{backgroundColor:"transparent !important"},marginBottom:"1rem",border:"dotted 2px #004"}}>Frage hinzufügen</AccordionSummary>
                        <AccordionDetails>
                        <Input sx={{marginBottom:"1rem"}} placeholder='Frage' />
                        <Input color="danger" placeholder='Falsche Antwort 1' />
                        <Input sx={{marginTop:"1rem"}} color="danger" placeholder='Falsche Antwort 2' />
                        <Input sx={{marginTop:"1rem"}} color="danger" placeholder='Falsche Antwort 3' />
                        <Input sx={{marginTop:"1rem",marginBottom:"1rem"}} color="success" placeholder='Richtige Antwort'/>  
                        <Button>Speichern</Button>
                        
                        </AccordionDetails>
                        
                    </Accordion>
                </List>
                
            </Card>

            <Card>
            <h3>Sonstiges</h3>
                <Divider></Divider>
                <Button variant="soft" color="primary">Fach umbenennen</Button>
                <Button variant="soft" color="warning">Fach löschen</Button>
            </Card>
        </div>
    );
}



export default Fach