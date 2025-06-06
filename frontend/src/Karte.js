import React from 'react';
import { useSearchParams } from 'react-router-dom';
import Card from '@mui/joy/Card';
import Typography from '@mui/joy/Typography';
import Box from '@mui/joy/Box';
import List from '@mui/joy/List';
import ListItem from '@mui/joy/ListItem';
import ListItemDecorator from '@mui/joy/ListItemDecorator';

function Karte() {
    const [paramater] = useSearchParams();
    const kartenid = paramater.get("kartenid")
    const kartendata = [{"Frage":"Was ist der Sinn des Lebens?","FalscheAntwort1":"Essen","FalscheAntwort2":"sdsdd","FalscheAntwort3":"sdsd","RichtigeAntwort":"Chillen"}]
    
    return (
        <div className='parent'>
            <h1 style={{
                textAlign: 'center',
                fontSize: '2.5rem',
                fontWeight: 'bold',
                color: '#FFF',
                textShadow: '0 3px 6px rgba(0,0,0,0.5)',
                margin: '2rem 0'
            }}>🃏 Kartendetails 🃏</h1>
            
            <div className='mittelPage'>
                <Card sx={{
                    background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                    borderRadius: '25px',
                    boxShadow: '0 15px 35px rgba(240, 147, 251, 0.4)',
                    color: '#FFF',
                    p: 3
                }}>
                    <Typography level="h3" sx={{
                        textAlign: 'center',
                        fontWeight: 'bold',
                        textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                        fontSize: '1.8rem',
                        mb: 3
                    }}>🤔 Frage:</Typography>
                    
                    <Box sx={{
                        background: 'rgba(255,255,255,0.15)',
                        borderRadius: '15px',
                        p: 3,
                        backdropFilter: 'blur(10px)',
                        mb: 3,
                        textAlign: 'center'
                    }}>
                        <Typography level="h2" sx={{
                            fontWeight: 'bold',
                            textShadow: '0 2px 4px rgba(0,0,0,0.3)'
                        }}>
                            {kartendata[0]["Frage"]}
                        </Typography>
                    </Box>
                    
                    <Typography level="h4" sx={{
                        textAlign: 'center',
                        fontWeight: 'bold',
                        textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                        mb: 2
                    }}>📝 Antwortmöglichkeiten:</Typography>
                    
                    <List sx={{
                        background: 'rgba(255,255,255,0.1)',
                        borderRadius: '15px',
                        p: 2,
                        backdropFilter: 'blur(10px)'
                    }}>
                        <ListItem sx={{
                            background: 'linear-gradient(135deg, rgba(231, 76, 60, 0.8) 0%, rgba(192, 57, 43, 0.8) 100%)',
                            borderRadius: '10px',
                            mb: 1
                        }}>
                            <ListItemDecorator sx={{ color: '#FFF', fontSize: '1.2rem' }}>❌</ListItemDecorator>
                            <Typography level="body1" sx={{ color: '#FFF', fontWeight: 'bold' }}>
                                {kartendata[0]["FalscheAntwort1"]}
                            </Typography>
                        </ListItem>
                        
                        <ListItem sx={{
                            background: 'linear-gradient(135deg, rgba(231, 76, 60, 0.8) 0%, rgba(192, 57, 43, 0.8) 100%)',
                            borderRadius: '10px',
                            mb: 1
                        }}>
                            <ListItemDecorator sx={{ color: '#FFF', fontSize: '1.2rem' }}>❌</ListItemDecorator>
                            <Typography level="body1" sx={{ color: '#FFF', fontWeight: 'bold' }}>
                                {kartendata[0]["FalscheAntwort2"]}
                            </Typography>
                        </ListItem>
                        
                        <ListItem sx={{
                            background: 'linear-gradient(135deg, rgba(231, 76, 60, 0.8) 0%, rgba(192, 57, 43, 0.8) 100%)',
                            borderRadius: '10px',
                            mb: 1
                        }}>
                            <ListItemDecorator sx={{ color: '#FFF', fontSize: '1.2rem' }}>❌</ListItemDecorator>
                            <Typography level="body1" sx={{ color: '#FFF', fontWeight: 'bold' }}>
                                {kartendata[0]["FalscheAntwort3"]}
                            </Typography>
                        </ListItem>
                        
                        <ListItem sx={{
                            background: 'linear-gradient(135deg, rgba(39, 174, 96, 0.9) 0%, rgba(46, 204, 113, 0.9) 100%)',
                            borderRadius: '10px',
                            border: '2px solid #27AE60'
                        }}>
                            <ListItemDecorator sx={{ color: '#FFF', fontSize: '1.2rem' }}>✅</ListItemDecorator>
                            <Typography level="body1" sx={{ color: '#FFF', fontWeight: 'bold' }}>
                                {kartendata[0]["RichtigeAntwort"]} (Richtige Antwort)
                            </Typography>
                        </ListItem>
                    </List>
                </Card>
            </div>
        </div>
    );
}

export default Karte