import { useState,React } from "react";
import  Link from '@mui/joy/Link';
import List from '@mui/joy/List';
import ListItem from '@mui/joy/ListItem';
import ListItemDecorator from '@mui/joy/ListItemDecorator';
import Button from '@mui/joy/Button';
import Card from '@mui/joy/Card';
import Divider from '@mui/joy/Divider';
import Input from '@mui/joy/Input';
import { useSearchParams } from "react-router-dom";
import Accordion from '@mui/joy/Accordion';
import AccordionDetails from '@mui/joy/AccordionDetails';
import AccordionGroup from '@mui/joy/AccordionGroup';
import AccordionSummary from '@mui/joy/AccordionSummary';




function Lobby() {
    const alleTeilnehmer = ["Mau","Hongfa"];
    const alleBeigetretenen = ["Bea","Florian"];
    const gameid = "2";

    const teilnehmerItems = alleTeilnehmer.map(einzelTeilnehmer => 
        <ListItem sx={{"&:hover":{backgroundColor: '#DDD'},borderRadius: '1rem',display:"flex",underline:'hidden',textDecoration:'none'}}>
         <ListItemDecorator>{einzelTeilnehmer}</ListItemDecorator><Button sx = {{marginLeft:"auto"}}color="primary">Einladen</Button>
        </ListItem>)

    const beigetretene = alleBeigetretenen.map(einzelTeilnehmer => 
    <ListItem sx={{"&:hover":{backgroundColor: '#DDD'},borderRadius: '1rem',display:"flex",underline:'hidden',textDecoration:'none'}}>
     <div>✅</div><ListItemDecorator>{einzelTeilnehmer}</ListItemDecorator> 
    </ListItem>)
    

    return (


        <div className="parent">
            <div className='mittelPage'>

                <Card >
                <h2>Beigetreten</h2>
                <Card sx = {{backgroundColor:"#FFF", height:"100%"}}>
                    <List>
                        {beigetretene}
                    </List>
                </Card>

                <Card sx={{ display:"flex", cursor:"pointer",alignItems:"center",justifyContent:"center"}}>
                    <Link href={`/lobby?gameid=${gameid}`}><h1>Runde starten</h1></Link>
                    </Card>
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
            
            </div>
        </div>
    );
};



export default Lobby