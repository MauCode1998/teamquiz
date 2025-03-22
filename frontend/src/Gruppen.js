import React from "react";
import  Link from '@mui/joy/Link';
import List from '@mui/joy/List';
import ListItem from '@mui/joy/ListItem';
import Input from '@mui/joy/Input';
import Button from '@mui/joy/Button';
import ListItemDecorator from '@mui/joy/ListItemDecorator';
import Card from '@mui/joy/Card';
import {useState,useEffect} from 'react';

function Gruppen() {
    const [alleGruppen,gruppeAktualisieren] = useState([]);
    const [alleEinladungen,einladungenAktualisieren] = useState([]);

    

    useEffect(()=> {
        async function ladeGruppe() {

            const gruppenDatenRequest = await fetch("http://127.0.0.1:8000/get-gruppeninfo", {

                "method":"GET",
                "headers":{
                    "token":"123456789",
                    "Content-Type":"application/json",
                },
                
                credentials: 'include',
          // Mode auf 'cors' setzen für explizite CORS-Behandlung
            mode: 'cors'})
            const daten = await gruppenDatenRequest.json()
            const gruppen = daten.content.groups.map(gruppe => gruppe.name);
            console.log(gruppen)
            gruppeAktualisieren(gruppen)
            
        
        }
        ladeGruppe();

        },[]);


        useEffect(()=> {
            async function ladeEinladungen() {
    
                const einladungsRequest = await fetch("http://127.0.0.1:8000/get-invitations", {
    
                    "method":"GET",
                    "headers":{
                        "token":"123456789",
                        "Content-Type":"application/json",
                    },
                    
                    credentials: 'include',
       
                mode: 'cors'})
                const daten = await einladungsRequest.json()
                const einladungen = daten.content
                console.log(einladungen)
                einladungenAktualisieren(einladungen);
                
            }
            ladeEinladungen();
    
            },[]);
    


    const listItems = alleGruppen.map(einzelGruppe => 
                
                <ListItem key = {einzelGruppe} sx={{"&:hover":{backgroundColor: '#DDD'}, height:"2rem", width:"50vw",cursor: 'pointer',borderRadius: '1rem',underline:'hidden',textDecoration:'none'}}>
                 <Link href={`/gruppe?name=${encodeURI(einzelGruppe)}`}>{einzelGruppe}</Link>
                </ListItem>
            
    )


    const einladungen = alleEinladungen.map((Einladung,index)=> 
                
        <ListItem key = {index} sx={{"&:hover":{backgroundColor: '#DDD'}, height:"2rem", width:"50vw",cursor: 'pointer',borderRadius: '1rem',underline:'hidden',textDecoration:'none'}}>
         <ListItemDecorator>{Einladung.From} lädt dich in die Gruppe {Einladung.To} ein!  </ListItemDecorator> <div style={{marginLeft:"auto",display:"flex"}}><Button variant="outlined" color="primary" sx={{marginRight:"1rem"}}>Annehmen</Button><Button variant="outlined" color="danger" sx={{marginLeft:"auto"}}>Ablehnen</Button></div>
        </ListItem>
    
)

    return (
        <div className='parent'>
        <h1>Willkommen, Maurice.</h1>
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
            />
             <Button 
              variant="outlined" 
              color="success"
              sx = {{marginTop: "0.5rem;"}} 
              >Erstellen</Button>
          
                
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