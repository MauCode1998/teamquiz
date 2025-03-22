import React, { useState,useEffect } from "react";
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
    const gruppenname = parameter.get("gruppenname")
    const gruppenId = parameter.get("gruppenid")
    const alleTeilnehmer = ["Mau","Hongfa"];
    const [alleKarteikarten,setAlleKarteikarten] = useState([]);
    const kartenId = "1"
    const gameid = "2"
    const gesamtAnzahlFragen = alleKarteikarten.length
   



    useEffect(() => {
        async function getCards() {
            console.log("get Cards Function wurde gecalled");
            const response = await fetch(`http://127.0.0.1:8000/get-subject-cards/?subjectname=${encodeURIComponent(fachname)}&gruppenname=${encodeURIComponent(gruppenname)}`, {
                "method":"GET",
                "headers": {
                    "token":"123456789",
                    "Content-Type":"application/json"
                }
            }
        )   
            const data = await response.json();
            console.log(data)
            try {
                const kartenContent = data.content;
                if (kartenContent.length != 0) {
                    const kartenList = kartenContent.flashcards;
                    console.log(kartenList);
                    setAlleKarteikarten(kartenList);
                }
                
            }
            catch {
                console.log("Keine Karten gefunden.")
            }
        }

        getCards();
    },[fachname,gruppenname])

    const teilnehmerItems = alleTeilnehmer.map(einzelTeilnehmer => 
        <ListItem sx={{"&:hover":{backgroundColor: '#DDD'},borderRadius: '1rem',display:"flex",underline:'hidden',textDecoration:'none'}}>
         <ListItemDecorator>{einzelTeilnehmer}</ListItemDecorator>
        </ListItem>)

    const kartenHTML = alleKarteikarten.map((karteikarte,index) =>
        <li key = {karteikarte.question}>
            <Accordion>
            <AccordionSummary>{karteikarte.question}</AccordionSummary>
                        <AccordionDetails>
                        <div className='buttonKombo'>
                        <Input value={karteikarte.answers[0].text} onChange={(e) => {
                            const neueKarten = [...alleKarteikarten];
                            neueKarten[index].answers[0].text = e.target.value;
                            
                            setAlleKarteikarten(neueKarten);
                        }}

                        />
                        <Input value={karteikarte.answers[1].text} onChange={(e) => {
                            const neueKarten = [...alleKarteikarten];
                            neueKarten[index].answers[1].text = e.target.value;
                            
                            setAlleKarteikarten(neueKarten);
                        }}

                        /><Input value={karteikarte.answers[2].text} onChange={(e) => {
                            const neueKarten = [...alleKarteikarten];
                            neueKarten[index].answers[2].text = e.target.value;
                            
                            setAlleKarteikarten(neueKarten);
                        }}

                        /><Input value={karteikarte.answers[3].text} color="success" onChange={(e) => {
                            const neueKarten = [...alleKarteikarten];
                            neueKarten[index].answers[3].text = e.target.value;
                            
                            setAlleKarteikarten(neueKarten);
                        }}

                        /> 
                        
                        
                      
                        <Button sx={{marginRight:"1rem"}} variant="outlined">Speichern</Button><Button color="danger" variant="outlined">Frage Löschen</Button>
                        </div>
                        
                        </AccordionDetails>
            </Accordion>
        </li>
    )

    return (
        <div className = 'parent'>
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
        </div>
    );
}



export default Fach