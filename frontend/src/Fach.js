import React, { useState,useEffect } from "react";
import  Link from '@mui/joy/Link';
import { Link as RouterLink } from 'react-router-dom';
import List from '@mui/joy/List';
import ListItem from '@mui/joy/ListItem';
import ListItemDecorator from '@mui/joy/ListItemDecorator';
import Button from '@mui/joy/Button';
import Card from '@mui/joy/Card';
import Box from '@mui/joy/Box';
import Grid from '@mui/joy/Grid';
import Divider from '@mui/joy/Divider';
import CardCover from '@mui/joy/CardCover'
import Input from '@mui/joy/Input';
import { useParams, useNavigate } from "react-router-dom";
import Accordion from '@mui/joy/Accordion';
import AccordionDetails from '@mui/joy/AccordionDetails';
import AccordionGroup from '@mui/joy/AccordionGroup';
import AccordionSummary from '@mui/joy/AccordionSummary';
import Radio from '@mui/joy/Radio';
import RadioGroup from '@mui/joy/RadioGroup';
import Sheet from '@mui/joy/Sheet';
import FormControl from '@mui/joy/FormControl';
import FormLabel from '@mui/joy/FormLabel';
import Typography from '@mui/joy/Typography';
import Modal from '@mui/joy/Modal';
import ModalDialog from '@mui/joy/ModalDialog';
import DialogTitle from '@mui/joy/DialogTitle';
import DialogContent from '@mui/joy/DialogContent';
import DialogActions from '@mui/joy/DialogActions';
import Alert from '@mui/joy/Alert';
import api from './api/axios';
import OnlineUsers from './components/OnlineUsers';




function Fach() {
    const { groupName, subject } = useParams();
    const navigate = useNavigate();
    
    const fachname = subject;
    const gruppenname = groupName;
    // Remove hardcoded users - now handled by OnlineUsers component
    const [alleKarteikarten,setAlleKarteikarten] = useState([]);
    const gesamtAnzahlFragen = alleKarteikarten.length

    const [neueKarteikarte,neueKarteikarteAktualisieren] = useState({
        frage: "",
        antworten: [
            { text: "", is_correct: false },
            { text: "", is_correct: false },
            { text: "", is_correct: false },
            { text: "", is_correct: true }
        ]
    });

    // States for subject management
    const [showRenameDialog, setShowRenameDialog] = useState(false);
    const [showDeleteDialog, setShowDeleteDialog] = useState(false);
    const [newSubjectName, setNewSubjectName] = useState("");
    const [renameError, setRenameError] = useState("");
    const [deleteError, setDeleteError] = useState("");
    
    // States for flashcard management
    const [showEditDialog, setShowEditDialog] = useState(false);
    const [showDeleteCardDialog, setShowDeleteCardDialog] = useState(false);
    const [selectedCard, setSelectedCard] = useState(null);
    const [editCardData, setEditCardData] = useState({
        frage: "",
        antworten: [
            { text: "", is_correct: false },
            { text: "", is_correct: false },
            { text: "", is_correct: false },
            { text: "", is_correct: true }
        ]
    });
    const [editError, setEditError] = useState("");
    const [deleteCardError, setDeleteCardError] = useState("");
    
    // State for lobby creation
    const [creatingLobby, setCreatingLobby] = useState(false);
   
    async function karteikarteErstellen() {
        console.log(`Karte wird gleich erstellt!`)
        
        // Validate inputs
        if (!neueKarteikarte.frage.trim()) {
            alert("Bitte geben Sie eine Frage ein");
            return;
        }
        
        const filledAnswers = neueKarteikarte.antworten.filter(a => a.text.trim());
        if (filledAnswers.length !== 4) {
            alert("Bitte füllen Sie alle 4 Antwortfelder aus");
            return;
        }

        try {
            const response = await api.post('/flashcard/create', {
                fach: subject,
                gruppe: groupName,
                frage: neueKarteikarte.frage,
                antworten: neueKarteikarte.antworten
            });
            console.log(response.data)
            
            // Reset form
            neueKarteikarteAktualisieren({
                frage: "",
                antworten: [
                    { text: "", is_correct: false },
                    { text: "", is_correct: false },
                    { text: "", is_correct: false },
                    { text: "", is_correct: true }
                ]
            });
            
            // Reload cards
            getCards();
        } catch (error) {
            console.error('Error creating flashcard:', error);
            alert(error.response?.data?.detail || "Fehler beim Erstellen der Karteikarte");
        }
    }
    
    async function getCards() {
        console.log("get Cards Function wurde gecalled");
        console.log("Loading cards for:", fachname, "in group:", gruppenname);
        try {
            const response = await api.get('/get-subject-cards/', {
                params: {
                    subjectname: fachname,
                    gruppenname: gruppenname
                }
            });
            console.log("API Response:", response.data);
            
            if (response.data && response.data.content) {
                const kartenContent = response.data.content;
                
                // Check if content is empty array (no subject cards)
                if (Array.isArray(kartenContent) && kartenContent.length === 0) {
                    console.log("No subject found, setting empty array");
                    setAlleKarteikarten([]);
                }
                // Check if content has flashcards
                else if (kartenContent.flashcards && kartenContent.flashcards.length > 0) {
                    const kartenList = kartenContent.flashcards;
                    console.log("Setting cards:", kartenList);
                    setAlleKarteikarten(kartenList);
                } else {
                    console.log("No flashcards found, setting empty array");
                    setAlleKarteikarten([]);
                }
            } else {
                console.log("No content in response");
                setAlleKarteikarten([]);
            }
        } catch (error) {
            console.error('Error loading cards:', error);
            
            // If subject doesn't exist (404), redirect to group page
            if (error.response && error.response.status === 404) {
                console.log("Subject not found, redirecting to group page");
                navigate(`/groups/${gruppenname}`);
                return;
            }
            
            setAlleKarteikarten([]);
        }
    }

    async function fachUmbenennen() {
        console.log(`Fach umbenennen: ${fachname} -> ${newSubjectName}`);
        setRenameError("");
        
        if (!newSubjectName.trim()) {
            setRenameError("Bitte geben Sie einen neuen Fachnamen ein");
            return;
        }
        
        if (newSubjectName.trim() === fachname) {
            setRenameError("Der neue Name muss sich vom aktuellen Namen unterscheiden");
            return;
        }
        
        try {
            const response = await api.put('/fach-umbenennen', {
                old_fach_name: fachname,
                new_fach_name: newSubjectName.trim(),
                gruppen_name: gruppenname
            });
            console.log("Rename response:", response.data);
            
            // Close dialog and redirect to the renamed subject
            setShowRenameDialog(false);
            navigate(`/groups/${gruppenname}/${newSubjectName.trim()}`);
            
        } catch (error) {
            console.error('Error renaming subject:', error);
            const errorMessage = error.response?.data?.detail || 'Fehler beim Umbenennen des Fachs';
            setRenameError(errorMessage);
        }
    }
    
    async function fachLoeschen() {
        console.log(`Fach löschen: ${fachname}`);
        setDeleteError("");
        
        try {
            const response = await api.delete('/fach-loeschen', {
                data: {
                    fach_name: fachname,
                    gruppen_name: gruppenname
                }
            });
            console.log("Delete response:", response.data);
            
            // Close dialog and redirect back to group page
            setShowDeleteDialog(false);
            navigate(`/groups/${gruppenname}`);
            
        } catch (error) {
            console.error('Error deleting subject:', error);
            const errorMessage = error.response?.data?.detail || 'Fehler beim Löschen des Fachs';
            setDeleteError(errorMessage);
        }
    }

    async function karteikarteBearbeiten() {
        console.log('Karteikarte bearbeiten:', selectedCard);
        setEditError("");
        
        // Validate inputs
        if (!editCardData.frage.trim()) {
            setEditError("Bitte geben Sie eine Frage ein");
            return;
        }
        
        const filledAnswers = editCardData.antworten.filter(a => a.text.trim());
        if (filledAnswers.length !== 4) {
            setEditError("Bitte füllen Sie alle 4 Antwortfelder aus");
            return;
        }

        try {
            const response = await api.put('/flashcard/update', {
                flashcard_id: selectedCard.flashcard_id,
                frage: editCardData.frage,
                antworten: editCardData.antworten
            });
            console.log("Update response:", response.data);
            
            // Close dialog and reload cards
            setShowEditDialog(false);
            getCards();
            
        } catch (error) {
            console.error('Error updating flashcard:', error);
            const errorMessage = error.response?.data?.detail || 'Fehler beim Bearbeiten der Karteikarte';
            setEditError(errorMessage);
        }
    }
    
    async function karteikarteLoeschen() {
        console.log('Karteikarte löschen:', selectedCard);
        setDeleteCardError("");
        
        try {
            const response = await api.delete('/flashcard/delete', {
                data: {
                    flashcard_id: selectedCard.flashcard_id
                }
            });
            console.log("Delete flashcard response:", response.data);
            
            // Close dialog and reload cards
            setShowDeleteCardDialog(false);
            getCards();
            
        } catch (error) {
            console.error('Error deleting flashcard:', error);
            const errorMessage = error.response?.data?.detail || 'Fehler beim Löschen der Karteikarte';
            setDeleteCardError(errorMessage);
        }
    }

    async function startLobby() {
        setCreatingLobby(true);
        
        try {
            const response = await api.post('/api/lobby/create', {
                subject_name: fachname,
                group_name: gruppenname
            });
            
            const sessionId = response.data.session.id;
            navigate(`/lobby/${sessionId}`);
            
        } catch (error) {
            console.error('Error creating lobby:', error);
            alert('Fehler beim Erstellen der Lobby: ' + (error.response?.data?.detail || 'Unbekannter Fehler'));
        } finally {
            setCreatingLobby(false);
        }
    }

    useEffect(() => {
        if (fachname && gruppenname) {
            getCards();
        }
    },[fachname,gruppenname])

    // Remove hardcoded teilnehmerItems - now handled by OnlineUsers component

    const kartenHTML = alleKarteikarten.map((karteikarte,index) =>
        <li key = {karteikarte.question}>
            <Accordion>
                <AccordionSummary>
                    <Box sx={{ 
                        display: 'flex', 
                        justifyContent: 'space-between', 
                        alignItems: 'center', 
                        width: '100%',
                        flexWrap: { xs: 'wrap', sm: 'nowrap' },
                        gap: 1
                    }}>
                        <Typography sx={{ 
                            fontSize: { xs: '0.9rem', sm: '1rem' },
                            flex: 1,
                            pr: 1
                        }}>
                            {karteikarte.question}
                        </Typography>
                        <Box sx={{ 
                            display: 'flex', 
                            gap: { xs: 0.5, sm: 1 },
                            flexShrink: 0
                        }}>
                            <Button 
                                size="sm" 
                                onClick={(e) => {
                                    e.stopPropagation();
                                    setSelectedCard(karteikarte);
                                    setEditCardData({
                                        frage: karteikarte.question,
                                        antworten: karteikarte.answers.map(a => ({
                                            text: a.text,
                                            is_correct: a.is_correct
                                        }))
                                    });
                                    setEditError("");
                                    setShowEditDialog(true);
                                }}
                                sx={{
                                    background: 'linear-gradient(135deg, #4ECDC4 0%, #44A08D 100%)',
                                    color: '#FFF',
                                    fontWeight: 'bold',
                                    borderRadius: '8px',
                                    fontSize: { xs: '0.75rem', sm: '0.875rem' },
                                    px: { xs: 1, sm: 2 },
                                    '&:hover': {
                                        background: 'linear-gradient(135deg, #44A08D 0%, #3d8f7a 100%)'
                                    }
                                }}
                            >
                                ✏️ <Box component="span" sx={{ display: { xs: 'none', sm: 'inline' } }}>Bearbeiten</Box>
                            </Button>
                            <Button 
                                size="sm" 
                                onClick={(e) => {
                                    e.stopPropagation();
                                    setSelectedCard(karteikarte);
                                    setDeleteCardError("");
                                    setShowDeleteCardDialog(true);
                                }}
                                sx={{
                                    background: 'linear-gradient(135deg, #E74C3C 0%, #C0392B 100%)',
                                    color: '#FFF',
                                    fontWeight: 'bold',
                                    borderRadius: '8px',
                                    fontSize: { xs: '0.75rem', sm: '0.875rem' },
                                    px: { xs: 1, sm: 2 },
                                    '&:hover': {
                                        background: 'linear-gradient(135deg, #C0392B 0%, #A93226 100())'
                                    }
                                }}
                            >
                                🗑️ <Box component="span" sx={{ display: { xs: 'none', sm: 'inline' } }}>Löschen</Box>
                            </Button>
                        </Box>
                    </Box>
                </AccordionSummary>
                <AccordionDetails>
                    <List>
                        {karteikarte.answers.map((answer, answerIndex) => (
                            <ListItem key={answerIndex}>
                                <ListItemDecorator>
                                    {answer.is_correct ? '✅' : '❌'}
                                </ListItemDecorator>
                                <Typography sx={{ fontSize: { xs: '0.9rem', sm: '1rem' } }}>
                                    {answer.text}
                                </Typography>
                            </ListItem>
                        ))}
                    </List>
                </AccordionDetails>
            </Accordion>
        </li>
    )

    return (
        <Box className='parent' sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
        <Grid 
            container 
            spacing={{ xs: 2, sm: 3 }}
            sx={{ 
                maxWidth: { lg: '1200px' },
                mx: 'auto'
            }}
        >
            {/* Subject Title */}
            <Grid xs={12}>
                <Card sx={{ 
                    mb: 2,
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    borderRadius: '25px',
                    boxShadow: '0 15px 35px rgba(102, 126, 234, 0.4)',
                    color: '#FFF',
                    textAlign: 'center',
                    p: { xs: 2, sm: 3 }
                }}>
                    <Typography level="h1" sx={{
                        fontSize: { xs: '1.75rem', sm: '2rem', md: '2.5rem' },
                        fontWeight: 'bold',
                        textShadow: '0 3px 6px rgba(0,0,0,0.3)',
                        mb: 1
                    }}>📖 Fach: {fachname}</Typography>
                    <Typography level="h4" sx={{
                        fontWeight: 'bold',
                        textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                        background: 'rgba(255,255,255,0.15)',
                        borderRadius: '12px',
                        p: 1,
                        display: 'inline-block',
                        fontSize: { xs: '1rem', sm: '1.25rem' }
                    }}>🏆 Gruppe: {gruppenname}</Typography>
                </Card>
            </Grid>
            
            {/* Start Quiz Card */}
            <Grid xs={12} md={6}>
                <Card sx={{ 
                    display:"flex", 
                    cursor:"pointer",
                    alignItems:"center",
                    justifyContent:"center",
                    background: 'linear-gradient(135deg, #4ECDC4 0%, #44A08D 100%)',
                    borderRadius: '25px',
                    boxShadow: '0 15px 35px rgba(78, 205, 196, 0.4)',
                    minHeight: { xs: '150px', sm: '200px' },
                    position: 'relative',
                    overflow: 'hidden',
                    transition: 'all 0.3s ease',
                    '&:hover': {
                        transform: 'translateY(-5px)',
                        boxShadow: '0 20px 40px rgba(78, 205, 196, 0.6)'
                    }
                }}>
                <CardCover sx={{overflow:"hidden"}}>
                    <Button
                        onClick={startLobby}
                        disabled={creatingLobby}
                        sx={{
                            width: '100%',
                            height: '100%',
                            p: 0,
                            border: 'none',
                            borderRadius: 0,
                            background: 'transparent',
                            '&:hover': { background: 'rgba(78, 205, 196, 0.3)' },
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            justifyContent: 'center'
                        }}
                    >
                        <Box sx={{
                            position: 'absolute',
                            top: 0,
                            left: 0,
                            width: '100%',
                            height: '100%',
                            background: 'linear-gradient(135deg, rgba(78, 205, 196, 0.8) 0%, rgba(68, 160, 141, 0.8) 100%)',
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: '#FFF'
                        }}>
                            <Typography level="h1" sx={{
                                fontSize: { xs: '3rem', sm: '4rem' },
                                fontWeight: 'bold',
                                textShadow: '0 4px 8px rgba(0,0,0,0.3)',
                                mb: 2
                            }}>🚀</Typography>
                            
                            <Typography level="h2" sx={{
                                fontWeight: 'bold',
                                textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                                textAlign: 'center',
                                fontSize: { xs: '1.25rem', sm: '1.5rem', md: '1.75rem' }
                            }}>
                                {creatingLobby ? 'Lobby wird erstellt...' : 'Quiz-Lobby starten'}
                            </Typography>
                            
                            <Typography level="body1" sx={{
                                mt: 1,
                                textAlign: 'center',
                                opacity: 0.9,
                                fontSize: { xs: '0.875rem', sm: '1rem' },
                                px: 2
                            }}>
                                Klicken Sie hier, um eine neue Spielrunde zu beginnen!
                            </Typography>
                        </Box>
                    </Button>
                </CardCover>
                </Card>
            </Grid>

            {/* Online Users */}
            <Grid xs={12} md={6}>
                <OnlineUsers groupName={gruppenname} showInviteButtons={false} />
            </Grid>
           
            {/* Questions Card */}
            <Grid xs={12}>
                <Card sx={{
                    background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                    borderRadius: '25px',
                    boxShadow: '0 15px 35px rgba(240, 147, 251, 0.4)',
                    color: '#FFF',
                    p: { xs: 2, sm: 3 }
                }}>
                <Typography level="h2" sx={{
                    textAlign: 'center',
                    fontWeight: 'bold',
                    textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                    fontSize: { xs: '1.5rem', sm: '1.75rem', md: '2rem' },
                    mb: 2
                }}>📝 Alle Fragen ({gesamtAnzahlFragen})</Typography>
                            
                    <List sx={{
                        background: 'rgba(255,255,255,0.1)',
                        borderRadius: '15px',
                        p: { xs: 1, sm: 2 },
                        backdropFilter: 'blur(10px)'
                    }}>
                        {alleKarteikarten.length === 0 ? (
                            <ListItem sx={{
                                textAlign: 'center',
                                fontStyle: 'italic',
                                color: 'rgba(255,255,255,0.8)',
                                py: 3
                            }}>
                                Noch keine Fragen vorhanden 🤔
                            </ListItem>
                        ) : kartenHTML}
                        <Accordion sx={{
                            background: 'rgba(255,255,255,0.15)',
                            borderRadius: '15px',
                            border: 'none',
                            backdropFilter: 'blur(10px)',
                            mt: 2
                        }}>
                            <AccordionSummary sx={{
                                color: '#FFF',
                                fontWeight: 'bold',
                                fontSize: { xs: '1rem', sm: '1.1rem' },
                                '&:hover': {
                                    background: 'rgba(255,255,255,0.1)'
                                }
                            }}>➕ Frage hinzufügen</AccordionSummary>
                            <AccordionDetails sx={{
                                background: 'rgba(255,255,255,0.05)',
                                borderRadius: '0 0 15px 15px'
                            }}>
                                <FormControl sx={{mb: 2}}>
                                    <FormLabel sx={{ fontSize: { xs: '0.9rem', sm: '1rem' } }}>Frage</FormLabel>
                                    <Input 
                                        placeholder='Geben Sie hier die Frage ein' 
                                        value={neueKarteikarte.frage} 
                                        onChange={(e) => {
                                            neueKarteikarteAktualisieren({
                                                ...neueKarteikarte,
                                                frage: e.target.value
                                            });
                                        }} 
                                        sx={{ fontSize: { xs: '0.9rem', sm: '1rem' } }}
                                    />
                                </FormControl>
                                
                                <Typography level="body-sm" sx={{mb: 1}}>
                                    Geben Sie 4 Antworten ein und markieren Sie die richtige:
                                </Typography>
                                
                                <RadioGroup 
                                    value={neueKarteikarte.antworten.findIndex(a => a.is_correct).toString()}
                                    onChange={(e) => {
                                        const correctIndex = parseInt(e.target.value);
                                        const updatedAntworten = neueKarteikarte.antworten.map((answer, index) => ({
                                            ...answer,
                                            is_correct: index === correctIndex
                                        }));
                                        neueKarteikarteAktualisieren({
                                            ...neueKarteikarte,
                                            antworten: updatedAntworten
                                        });
                                    }}
                                >
                                    {neueKarteikarte.antworten.map((answer, index) => (
                                        <Sheet 
                                            key={index} 
                                            sx={{ 
                                                p: { xs: 0.75, sm: 1 }, 
                                                mb: 1, 
                                                borderRadius: 'sm', 
                                                border: '1px solid', 
                                                borderColor: answer.is_correct ? 'success.outlinedBorder' : 'neutral.outlinedBorder',
                                                display: 'flex',
                                                alignItems: 'center',
                                                gap: 1
                                            }}
                                        >
                                            <Radio 
                                                value={index.toString()}
                                                size="sm"
                                            />
                                            <Input 
                                                placeholder={`Antwort ${index + 1}`}
                                                value={answer.text}
                                                onChange={(e) => {
                                                    const updatedAntworten = [...neueKarteikarte.antworten];
                                                    updatedAntworten[index].text = e.target.value;
                                                    neueKarteikarteAktualisieren({
                                                        ...neueKarteikarte,
                                                        antworten: updatedAntworten
                                                    });
                                                }}
                                                sx={{ 
                                                    flex: 1,
                                                    fontSize: { xs: '0.875rem', sm: '1rem' }
                                                }}
                                                variant={answer.is_correct ? "soft" : "outlined"}
                                                color={answer.is_correct ? "success" : "neutral"}
                                            />
                                        </Sheet>
                                    ))}
                                </RadioGroup>
                                
                                <Button 
                                    onClick={karteikarteErstellen} 
                                    fullWidth
                                    sx={{
                                        mt: 2,
                                        background: 'linear-gradient(135deg, #27AE60 0%, #2ECC71 100%)',
                                        color: '#FFF',
                                        fontWeight: 'bold',
                                        borderRadius: '12px',
                                        fontSize: { xs: '1rem', sm: '1.1rem' },
                                        '&:hover': {
                                            background: 'linear-gradient(135deg, #229954 0%, #27AE60 100%)'
                                        }
                                    }}
                                >
                                    💾 Karteikarte speichern
                                </Button>
                            </AccordionDetails>
                            
                        </Accordion>
                    </List>
                    
                </Card>
            </Grid>

            {/* Subject Management Card */}
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
                }}>⚙️ Fach-Verwaltung</Typography>
                    
                    <Box sx={{ 
                        display: 'flex', 
                        flexDirection: { xs: 'column', sm: 'row' }, 
                        gap: { xs: '10px', sm: '12px' },
                        justifyContent: 'center'
                    }}>
                        <Button onClick={() => {
                            setNewSubjectName(fachname);
                            setRenameError("");
                            setShowRenameDialog(true);
                        }} sx={{
                            background: 'linear-gradient(135deg, #F39C12 0%, #E67E22 100%)',
                            color: '#FFF',
                            fontWeight: 'bold',
                            borderRadius: '12px',
                            fontSize: { xs: '0.9rem', sm: '1rem' },
                            px: { xs: 2, sm: 3 },
                            '&:hover': {
                                background: 'linear-gradient(135deg, #E67E22 0%, #D68910 100%)'
                            }
                        }}>✏️ Fach umbenennen</Button>
                        
                        <Button onClick={() => {
                            setDeleteError("");
                            setShowDeleteDialog(true);
                        }} sx={{
                            background: 'linear-gradient(135deg, #E74C3C 0%, #C0392B 100%)',
                            color: '#FFF',
                            fontWeight: 'bold',
                            borderRadius: '12px',
                            fontSize: { xs: '0.9rem', sm: '1rem' },
                            px: { xs: 2, sm: 3 },
                            '&:hover': {
                                background: 'linear-gradient(135deg, #C0392B 0%, #A93226 100())'
                            }
                        }}>🗑️ Fach löschen</Button>
                    </Box>
                </Card>
            </Grid>
        </Grid>

        {/* Rename Dialog */}
        <Modal open={showRenameDialog} onClose={() => setShowRenameDialog(false)}>
            <ModalDialog sx={{ width: { xs: '90%', sm: '400px' }, maxWidth: '400px' }}>
                <DialogTitle>Fach umbenennen</DialogTitle>
                <DialogContent>
                    {renameError && (
                        <Alert color="danger" sx={{ mb: 2 }}>
                            {renameError}
                        </Alert>
                    )}
                    <FormControl>
                        <FormLabel>Neuer Fachname</FormLabel>
                        <Input
                            placeholder="Neuen Namen eingeben"
                            value={newSubjectName}
                            onChange={(e) => {
                                setNewSubjectName(e.target.value);
                                if (renameError) setRenameError("");
                            }}
                        />
                    </FormControl>
                </DialogContent>
                <DialogActions>
                    <Button variant="outlined" onClick={() => setShowRenameDialog(false)}>
                        Abbrechen
                    </Button>
                    <Button color="primary" onClick={fachUmbenennen}>
                        Umbenennen
                    </Button>
                </DialogActions>
            </ModalDialog>
        </Modal>

        {/* Delete Dialog */}
        <Modal open={showDeleteDialog} onClose={() => setShowDeleteDialog(false)}>
            <ModalDialog sx={{ width: { xs: '90%', sm: '400px' }, maxWidth: '400px' }}>
                <DialogTitle>Fach löschen</DialogTitle>
                <DialogContent>
                    {deleteError && (
                        <Alert color="danger" sx={{ mb: 2 }}>
                            {deleteError}
                        </Alert>
                    )}
                    <Typography>
                        Sind Sie sicher, dass Sie das Fach "<strong>{fachname}</strong>" löschen möchten?
                    </Typography>
                    <Typography level="body-sm" sx={{ mt: 1 }}>
                        Alle Karteikarten in diesem Fach werden ebenfalls gelöscht. 
                        Diese Aktion kann nicht rückgängig gemacht werden.
                    </Typography>
                </DialogContent>
                <DialogActions>
                    <Button variant="outlined" onClick={() => setShowDeleteDialog(false)}>
                        Abbrechen
                    </Button>
                    <Button id='fachLoeschenButton' color="danger" onClick={fachLoeschen}>
                        Löschen
                    </Button>
                </DialogActions>
            </ModalDialog>
        </Modal>

        {/* Edit Flashcard Dialog */}
        <Modal open={showEditDialog} onClose={() => setShowEditDialog(false)}>
            <ModalDialog sx={{ width: { xs: '95%', sm: '90%', md: '600px' }, maxWidth: '600px' }}>
                <DialogTitle>Karteikarte bearbeiten</DialogTitle>
                <DialogContent>
                    {editError && (
                        <Alert color="danger" sx={{ mb: 2 }}>
                            {editError}
                        </Alert>
                    )}
                    <FormControl sx={{ mb: 2 }}>
                        <FormLabel>Frage</FormLabel>
                        <Input
                            placeholder="Geben Sie hier die Frage ein"
                            value={editCardData.frage}
                            onChange={(e) => {
                                setEditCardData({
                                    ...editCardData,
                                    frage: e.target.value
                                });
                                if (editError) setEditError("");
                            }}
                        />
                    </FormControl>
                    
                    <Typography level="body-sm" sx={{ mb: 1 }}>
                        Bearbeiten Sie die Antworten und markieren Sie die richtige:
                    </Typography>
                    
                    <RadioGroup
                        value={editCardData.antworten.findIndex(a => a.is_correct).toString()}
                        onChange={(e) => {
                            const correctIndex = parseInt(e.target.value);
                            const updatedAntworten = editCardData.antworten.map((answer, index) => ({
                                ...answer,
                                is_correct: index === correctIndex
                            }));
                            setEditCardData({
                                ...editCardData,
                                antworten: updatedAntworten
                            });
                        }}
                    >
                        {editCardData.antworten.map((answer, index) => (
                            <Sheet
                                key={index}
                                sx={{
                                    p: 1,
                                    mb: 1,
                                    borderRadius: 'sm',
                                    border: '1px solid',
                                    borderColor: answer.is_correct ? 'success.outlinedBorder' : 'neutral.outlinedBorder',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: 1
                                }}
                            >
                                <Radio
                                    value={index.toString()}
                                    size="sm"
                                />
                                <Input
                                    placeholder={`Antwort ${index + 1}`}
                                    value={answer.text}
                                    onChange={(e) => {
                                        const updatedAntworten = [...editCardData.antworten];
                                        updatedAntworten[index].text = e.target.value;
                                        setEditCardData({
                                            ...editCardData,
                                            antworten: updatedAntworten
                                        });
                                        if (editError) setEditError("");
                                    }}
                                    sx={{ flex: 1 }}
                                    variant={answer.is_correct ? "soft" : "outlined"}
                                    color={answer.is_correct ? "success" : "neutral"}
                                />
                            </Sheet>
                        ))}
                    </RadioGroup>
                </DialogContent>
                <DialogActions>
                    <Button variant="outlined" onClick={() => setShowEditDialog(false)}>
                        Abbrechen
                    </Button>
                    <Button color="primary" onClick={karteikarteBearbeiten}>
                        Speichern
                    </Button>
                </DialogActions>
            </ModalDialog>
        </Modal>

        {/* Delete Flashcard Dialog */}
        <Modal open={showDeleteCardDialog} onClose={() => setShowDeleteCardDialog(false)}>
            <ModalDialog sx={{ width: { xs: '90%', sm: '400px' }, maxWidth: '400px' }}>
                <DialogTitle>Karteikarte löschen</DialogTitle>
                <DialogContent>
                    {deleteCardError && (
                        <Alert color="danger" sx={{ mb: 2 }}>
                            {deleteCardError}
                        </Alert>
                    )}
                    <Typography>
                        Sind Sie sicher, dass Sie diese Karteikarte löschen möchten?
                    </Typography>
                    {selectedCard && (
                        <Typography level="body-sm" sx={{ mt: 1, fontStyle: 'italic' }}>
                            Frage: "{selectedCard.question}"
                        </Typography>
                    )}
                    <Typography level="body-sm" sx={{ mt: 1 }}>
                        Diese Aktion kann nicht rückgängig gemacht werden.
                    </Typography>
                </DialogContent>
                <DialogActions>
                    <Button variant="outlined" onClick={() => setShowDeleteCardDialog(false)}>
                        Abbrechen
                    </Button>
                    <Button color="danger" onClick={karteikarteLoeschen}>
                        Löschen
                    </Button>
                </DialogActions>
            </ModalDialog>
        </Modal>
        </Box>
    );
}



export default Fach