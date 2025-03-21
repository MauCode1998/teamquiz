import React from "react";
import  Link from '@mui/joy/Link';
import List from '@mui/joy/List';
import ListItem from '@mui/joy/ListItem';
import ListItemDecorator from '@mui/joy/ListItemDecorator';
import Button from '@mui/joy/Button';
import Card from '@mui/joy/Card';
import Divider from '@mui/joy/Divider';




function Gruppen() {
    
    const alleGruppen = ["Quizzers","Rizzers"];
    const listItems = alleGruppen.map(einzelGruppe => 
                
                <ListItem sx={{"&:hover":{backgroundColor: '#DDD'}, height:"2rem", width:"50vw",cursor: 'pointer',borderRadius: '1rem',underline:'hidden',textDecoration:'none'}}>
                 <Link href={`/gruppe?name=${encodeURI(einzelGruppe)}`}>{einzelGruppe}</Link>
                </ListItem>
            
             
               
     
    )

    return (
        <div className='mittelPage'>

            <Card>
                <h2>Meine Gruppen</h2>
                <List aria-labelledby="decorated-list-demo">
                    {listItems}
                
                </List>
            </Card>

            
            
        </div>
    );
}



export default Gruppen