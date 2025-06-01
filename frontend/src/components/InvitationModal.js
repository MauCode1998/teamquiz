import React, { useState, useEffect } from 'react';
import Modal from '@mui/joy/Modal';
import ModalDialog from '@mui/joy/ModalDialog';
import DialogTitle from '@mui/joy/DialogTitle';
import DialogContent from '@mui/joy/DialogContent';
import List from '@mui/joy/List';
import ListItem from '@mui/joy/ListItem';
import ListItemContent from '@mui/joy/ListItemContent';
import Typography from '@mui/joy/Typography';
import Button from '@mui/joy/Button';
import IconButton from '@mui/joy/IconButton';
import Alert from '@mui/joy/Alert';
import api from '../api/axios';
import { useNavigate } from 'react-router-dom';

function InvitationModal({ open, onClose }) {
    const navigate = useNavigate();
    const [invitations, setInvitations] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        if (open) {
            fetchInvitations();
        }
    }, [open]);

    const fetchInvitations = async () => {
        setLoading(true);
        setError('');
        try {
            const response = await api.get('/api/invitations/pending');
            console.log('Fetched invitations:', response.data);
            setInvitations(response.data || []);
        } catch (error) {
            console.error('Error fetching invitations:', error);
            setError('Fehler beim Laden der Einladungen');
        } finally {
            setLoading(false);
        }
    };

    const handleAccept = async (invitationId) => {
        try {
            // Accept the invitation
            const acceptResponse = await api.post(`/api/invitation/accept/${invitationId}`);
            
            if (acceptResponse.data.session_id) {
                // Get the session to retrieve the join code
                const sessionResponse = await api.get(`/api/session/${acceptResponse.data.session_id}`);
                const sessionData = sessionResponse.data;
                
                onClose(); // Close the modal
                
                // Navigate to lobby with join code - this will trigger the join flow
                navigate(`/lobby?code=${sessionData.join_code}`);
            }
        } catch (error) {
            console.error('Error accepting invitation:', error);
            setError('Fehler beim Annehmen der Einladung');
        }
    };

    const handleReject = async (invitationId) => {
        try {
            await api.post(`/api/invitation/reject/${invitationId}`);
            // Remove rejected invitation from list
            setInvitations(invitations.filter(inv => inv.invitation_id !== invitationId));
        } catch (error) {
            console.error('Error rejecting invitation:', error);
            setError('Fehler beim Ablehnen der Einladung');
        }
    };

    return (
        <Modal open={open} onClose={onClose}>
            <ModalDialog sx={{ width: '90%', maxWidth: '500px' }}>
                <DialogTitle>
                    Einladungen
                    <IconButton
                        aria-label="close"
                        onClick={onClose}
                        sx={{ position: 'absolute', right: 8, top: 8 }}
                    >
                        ✕
                    </IconButton>
                </DialogTitle>
                <DialogContent>
                    {error && (
                        <Alert color="danger" sx={{ mb: 2 }}>
                            {error}
                        </Alert>
                    )}
                    
                    {loading ? (
                        <Typography>Lade Einladungen...</Typography>
                    ) : invitations.length === 0 ? (
                        <Typography>Keine Einladungen vorhanden</Typography>
                    ) : (
                        <List>
                            {invitations.map((invitation) => (
                                <ListItem key={invitation.invitation_id}>
                                    <ListItemContent>
                                        <Typography level="title-sm">
                                            Einladung von {invitation.inviter}
                                        </Typography>
                                        <Typography level="body-sm">
                                            Fach: {invitation.subject}
                                        </Typography>
                                        <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
                                            <Button
                                                size="sm"
                                                color="success"
                                                onClick={() => handleAccept(invitation.invitation_id)}
                                            >
                                                Annehmen
                                            </Button>
                                            <Button
                                                size="sm"
                                                variant="outlined"
                                                color="danger"
                                                onClick={() => handleReject(invitation.invitation_id)}
                                            >
                                                Ablehnen
                                            </Button>
                                        </div>
                                    </ListItemContent>
                                </ListItem>
                            ))}
                        </List>
                    )}
                </DialogContent>
            </ModalDialog>
        </Modal>
    );
}

export default InvitationModal;