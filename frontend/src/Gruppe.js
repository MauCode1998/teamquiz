import React, { useState, useEffect} from "react";
import  Link from '@mui/joy/Link';
import List from '@mui/joy/List';
import ListItem from '@mui/joy/ListItem';
import ListItemDecorator from '@mui/joy/ListItemDecorator';
import Button from '@mui/joy/Button';
import Card from '@mui/joy/Card';
import Input from '@mui/joy/Input';
import { useSearchParams, useNavigate} from "react-router-dom";
import Accordion from '@mui/joy/Accordion';
import AccordionDetails from '@mui/joy/AccordionDetails';
import AccordionGroup from '@mui/joy/AccordionGroup';
import AccordionSummary from '@mui/joy/AccordionSummary';



function Gruppe() {
    
    const [alleFaecher,fächerAktualisieren] =  useState([]);
    const [alleTeilnehmer,teilnehmerAktualisieren] =  useState([]);
    const [neuesFach,neuesFachAktualisieren] = useState("");
    const gruppenId = "1";
    const [searchParams] = useSearchParams();
    const [params] = useSearchParams();
    const gruppenname = params.get("name")
    const navigate = useNavigate();


    async function gruppeLöschen() {
        console.log(`Gruppe wird gleich gelöscht!`)

        const gruppeErstellenRequest = await fetch("http://127.0.0.1:8000/delete-group", {
            "method":"DELETE",
            "headers": {
                "token":"123456789",
                "Content-Type":"application/json"
            },
            "body": JSON.stringify({"gruppen_name":searchParams.get("name")})
            ,
            credentials: 'include'
        })

        const data = await gruppeErstellenRequest.json();
        console.log(data)

        navigate("/gruppen")

      
    }

    async function fachErstellen() {
        console.log(`Fach ${neuesFach} wird gleich erstellt!`)

        const fachErstellenRequest = await fetch("http://127.0.0.1:8000/fach-erstellen", {
            "method":"POST",
            "headers": {
                "token":"123456789",
                "Content-Type":"application/json"
            },
            "body": JSON.stringify({"fach_name":neuesFach,"gruppen_name":gruppenname})
            ,
            credentials: 'include'
        })

        const data = await fachErstellenRequest.json();
        console.log(data)
        datenLaden();
        neuesFachAktualisieren("");

        
    }

    async function gruppeVerlassen() {
        console.log(`Gruppe wird verlassen.`)

        const gruppeVerlassenRequest = await fetch("http://127.0.0.1:8000/leave-group", {
            "method":"DELETE",
            "headers": {
                "token":"123456789",
                "Content-Type":"application/json"
            },
            "body": JSON.stringify({"gruppen_name":searchParams.get("name")})
            ,
            credentials: 'include'
        })

        const data = await gruppeVerlassenRequest.json();
        console.log(data)

        

      
    }

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


    useEffect(() => {
        

        datenLaden()
        },[gruppenname]);

    
    
    
    const listItems = alleFaecher.map((fach,index) => 
                
                <ListItem key={index} sx={{"&:hover":{backgroundColor: '#DDD'}, width:"50vw",cursor: 'pointer',borderRadius: '1rem',underline:'hidden',textDecoration:'none'}}>
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
                            value={neuesFach}
                            onChange={(e) => {
                                neuesFachAktualisieren(e.target.value)
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
            <Input 
                placeholder='Benutzername'
            />
             <Button 
              variant="solid" 
              color="primary"
              sx = {{marginTop: "0.5rem;"}} 
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