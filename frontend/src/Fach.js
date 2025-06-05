import React, { useState,useEffect } from "react";
import  Link from '@mui/joy/Link';
import { Link as RouterLink } from 'react-router-dom';
import List from '@mui/joy/List';
import ListItem from '@mui/joy/ListItem';
import ListItemDecorator from '@mui/joy/ListItemDecorator';
import Button from '@mui/joy/Button';
import Card from '@mui/joy/Card';
import Divider from '@mui/joy/Divider';
import CardCover from '@mui/joy/CardCover'
import Input from '@mui/joy/Input';
import { useParams, useNavigate } from "react-router-dom";
import Accordion from '@mui/joy/Accordion';
import AccordionDetails from '@mui/joy/AccordionDetails';
import Bild from './start.jpeg';
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
    const kartenId = "1"
    const gameid = "2"
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
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
                        <span>{karteikarte.question}</span>
                        <div style={{ display: 'flex', gap: '8px' }}>
                            <Button 
                                size="sm" 
                                variant="soft" 
                                color="primary"
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
                            >
                                Bearbeiten
                            </Button>
                            <Button 
                                size="sm" 
                                variant="soft" 
                                color="danger"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    setSelectedCard(karteikarte);
                                    setDeleteCardError("");
                                    setShowDeleteCardDialog(true);
                                }}
                            >
                                Löschen
                            </Button>
                        </div>
                    </div>
                </AccordionSummary>
                <AccordionDetails>
                    <List>
                        {karteikarte.answers.map((answer, answerIndex) => (
                            <ListItem key={answerIndex}>
                                <ListItemDecorator>
                                    {answer.is_correct ? '✅' : '❌'}
                                </ListItemDecorator>
                                {answer.text}
                            </ListItem>
                        ))}
                    </List>
                </AccordionDetails>
            </Accordion>
        </li>
    )

    return (
        <div className = 'parent'>
        <div className='mittelPage'>
            
            {/* Subject Title */}
            <Card sx={{ mb: 2 }}>
                <h1 className='mainPageUeberschrift'>Fach: {fachname}</h1>
                <Typography level="body-sm">Gruppe: {gruppenname}</Typography>
            </Card>
            
            <Card sx={{ display:"flex", cursor:"pointer",alignItems:"center",justifyContent:"center"}}>
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
                        '&:hover': { background: 'rgba(0,0,0,0.1)' }
                    }}
                >
                    <img
                        src={Bild}
                        loading="lazy"
                        alt="Lobby starten"
                        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                    />
                    {creatingLobby && (
                        <Typography 
                            sx={{ 
                                position: 'absolute', 
                                color: 'white', 
                                backgroundColor: 'rgba(0,0,0,0.7)', 
                                padding: '8px 16px', 
                                borderRadius: '4px' 
                            }}
                        >
                            Lobby wird erstellt...
                        </Typography>
                    )}
                </Button>
            </CardCover>
            </Card>

            <OnlineUsers groupName={gruppenname} showInviteButtons={false} />
           
            <Card>
            <h2 className = 'mainPageUeberschrift'>Alle Fragen ({gesamtAnzahlFragen})</h2>
                        
                <List>
                    {kartenHTML}
                    <Accordion variant="plain">
                        <AccordionSummary variant="plain" sx={{"&:hover":{backgroundColor:"transparent !important"},marginBottom:"1rem",border:"dotted 2px #004"}}>Frage hinzufügen</AccordionSummary>
                        <AccordionDetails>
                            <FormControl sx={{mb: 2}}>
                                <FormLabel>Frage</FormLabel>
                                <Input 
                                    placeholder='Geben Sie hier die Frage ein' 
                                    value={neueKarteikarte.frage} 
                                    onChange={(e) => {
                                        neueKarteikarteAktualisieren({
                                            ...neueKarteikarte,
                                            frage: e.target.value
                                        });
                                    }} 
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
                                                const updatedAntworten = [...neueKarteikarte.antworten];
                                                updatedAntworten[index].text = e.target.value;
                                                neueKarteikarteAktualisieren({
                                                    ...neueKarteikarte,
                                                    antworten: updatedAntworten
                                                });
                                            }}
                                            sx={{ flex: 1 }}
                                            variant={answer.is_correct ? "soft" : "outlined"}
                                            color={answer.is_correct ? "success" : "neutral"}
                                        />
                                    </Sheet>
                                ))}
                            </RadioGroup>
                            
                            <Button 
                                onClick={karteikarteErstellen} 
                                sx={{mt: 2}}
                                fullWidth
                            >
                                Karteikarte speichern
                            </Button>
                        </AccordionDetails>
                        
                    </Accordion>
                </List>
                
            </Card>

            <Card>
            <h3>Sonstiges</h3>
                <Divider></Divider>
                <Button variant="soft" color="primary" onClick={() => {
                    setNewSubjectName(fachname);
                    setRenameError("");
                    setShowRenameDialog(true);
                }}>Fach umbenennen</Button>
                <Button variant="soft" color="warning" onClick={() => {
                    setDeleteError("");
                    setShowDeleteDialog(true);
                }}>Fach löschen</Button>
            </Card>
        </div>

        {/* Rename Dialog */}
        <Modal open={showRenameDialog} onClose={() => setShowRenameDialog(false)}>
            <ModalDialog>
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
            <ModalDialog>
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
            <ModalDialog sx={{ width: '90%', maxWidth: '600px' }}>
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
            <ModalDialog>
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
        </div>
    );
}



export default Fach