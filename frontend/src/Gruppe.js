import React, { useState, useEffect} from "react";
import  Link from '@mui/joy/Link';
import List from '@mui/joy/List';
import ListItem from '@mui/joy/ListItem';
import ListItemDecorator from '@mui/joy/ListItemDecorator';
import Button from '@mui/joy/Button';
import Card from '@mui/joy/Card';
import Input from '@mui/joy/Input';
import { useSearchParams } from "react-router-dom";
import Accordion from '@mui/joy/Accordion';
import AccordionDetails from '@mui/joy/AccordionDetails';
import AccordionGroup from '@mui/joy/AccordionGroup';
import AccordionSummary from '@mui/joy/AccordionSummary';



function Gruppe() {
    
    const [alleFaecher,fächerAktualisieren] =  useState([]);
    const [alleTeilnehmer,teilnehmerAktualisieren] =  useState([]);
    const gruppenId = "1";
    const [searchParams] = useSearchParams();
    


    useEffect(() => {
        async function datenLaden(){
            const response = await fetch(`http://127.0.0.1:8000/get-specific-group/?name=${encodeURIComponent(gruppenname)}`,
            {"method":"GET",
             "headers": {
                "token":"123456789",
                "Content-Type":"application/json"
             }
             
            })

            const data = await response.json();
            const mitglieder = data.content.users;
            const faecher = data.content.subjects;

            fächerAktualisieren(faecher);
            teilnehmerAktualisieren(mitglieder);
        }

        datenLaden()
        },[]);

    
    const [params] = useSearchParams();
    const gruppenname = params.get("name")
    
    const listItems = alleFaecher.map(fach => 
                
                <ListItem sx={{"&:hover":{backgroundColor: '#DDD'}, width:"50vw",cursor: 'pointer',borderRadius: '1rem',underline:'hidden',textDecoration:'none'}}>
                 <Link href={`/fach?name=${encodeURI(fach)}&gruppenname=${encodeURIComponent(gruppenname)}`}>{fach}</Link>
                </ListItem>
     
    )
    

    const teilnehmerItems = alleTeilnehmer.map(einzelTeilnehmer => 
        <ListItem sx={{"&:hover":{backgroundColor: '#DDD'}, cursor:"point",width:"50vw",borderRadius: '1rem',underline:'hidden',textDecoration:'none'}}>
         <ListItemDecorator>🔥</ListItemDecorator> {einzelTeilnehmer}
        </ListItem>
)

    return (
        <div className = 'parent'>
        <h1>{gruppenname}</h1>
        <div className='mittelPage'>
            
            <Card className='listenCard'sx={{height:"auto"}}>
                <div id='fachUeberschrift'>
                    <h2>Alle Fächer von {gruppenname}</h2>
                </div>
                
                <List aria-labelledby="decorated-list-demo">
                    {listItems}
                </List>
                
                <Accordion sx={{position:"absolute",right:0,minHeight:"50px"}}>
                        <AccordionSummary>Fach hinzufügen</AccordionSummary>
                        <AccordionDetails>
                        <Input 
                            placeholder='Neuer Fach Name'
                           
                        />   
                        <Button>Speichern</Button>
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
            <Input 
                placeholder='Benutzername'
            />
             <Button 
              variant="solid" 
              color="primary"
              sx = {{marginTop: "0.5rem;"}} 
              >Einladen</Button>
          
                
            </Card>

            
            
        </div>
        </div>
    );
}



export default Gruppe