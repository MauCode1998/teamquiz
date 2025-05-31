import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from './AuthContext';
import Box from '@mui/joy/Box';
import Button from '@mui/joy/Button';
import FormControl from '@mui/joy/FormControl';
import FormLabel from '@mui/joy/FormLabel';
import Input from '@mui/joy/Input';
import Typography from '@mui/joy/Typography';
import Alert from '@mui/joy/Alert';
import LinearProgress from '@mui/joy/LinearProgress';
import Card from '@mui/joy/Card';

const Register = () => {
  const navigate = useNavigate();
  const { register } = useAuth();
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState(0);

  const calculatePasswordStrength = (password) => {
    let strength = 0;
    if (password.length >= 6) strength += 25;
    if (password.length >= 10) strength += 25;
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength += 25;
    if (/\d/.test(password)) strength += 12.5;
    if (/[^a-zA-Z\d]/.test(password)) strength += 12.5;
    return strength;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    if (name === 'password') {
      setPasswordStrength(calculatePasswordStrength(value));
    }
  };

  const getPasswordStrengthColor = () => {
    if (passwordStrength < 40) return 'danger';
    if (passwordStrength < 70) return 'warning';
    return 'success';
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Detailed validation with specific error messages
    if (!formData.username) {
      setError('Benutzername ist erforderlich');
      return;
    }

    if (!formData.email) {
      setError('E-Mail-Adresse ist erforderlich');
      return;
    }

    if (!formData.password) {
      setError('Passwort ist erforderlich');
      return;
    }

    if (!formData.confirmPassword) {
      setError('Passwort bestätigen ist erforderlich');
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      setError('Passwörter stimmen nicht überein');
      return;
    }

    if (formData.password.length < 6) {
      setError('Passwort muss mindestens 6 Zeichen lang sein');
      return;
    }

    setLoading(true);

    const result = await register(formData.username, formData.email, formData.password);

    if (result.success) {
      navigate('/groups');
    } else {
      // Translate common English error messages to German
      let germanError = result.error;
      if (result.error.includes('Username must contain only letters and numbers')) {
        germanError = 'Benutzername darf nur Buchstaben und Zahlen enthalten';
      } else if (result.error.includes('Username already registered')) {
        germanError = 'Benutzername ist bereits registriert';
      } else if (result.error.includes('Email already registered')) {
        germanError = 'E-Mail-Adresse ist bereits registriert';
      } else if (result.error.includes('valid email') || result.error.includes('email') && result.error.includes('invalid')) {
        germanError = 'Bitte geben Sie eine gültige E-Mail-Adresse ein';
      } else if (result.error.includes('Username must be at least 3 characters')) {
        germanError = 'Benutzername muss mindestens 3 Zeichen lang sein';
      }
      
      setError(germanError);
      setLoading(false);
    }
  };

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        backgroundImage: 'url(/background.jpeg)',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
      }}
    >
      <Card
        variant="outlined"
        sx={{
          width: 400,
          p: 4,
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
        }}
      >
        <Typography level="h3" sx={{ mb: 3, textAlign: 'center' }}>
          Registrierung
        </Typography>

        {error && (
          <Alert color="danger" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          <FormControl sx={{ mb: 2 }}>
            <FormLabel>Benutzername</FormLabel>
            <Input
              name="username"
              value={formData.username}
              onChange={handleChange}
              placeholder="Mindestens 3 Zeichen"
              disabled={loading}
            />
          </FormControl>

          <FormControl sx={{ mb: 2 }}>
            <FormLabel>E-Mail</FormLabel>
            <Input
              name="email"
              type="text"
              value={formData.email}
              onChange={handleChange}
              placeholder="name@example.com"
              disabled={loading}
            />
          </FormControl>

          <FormControl sx={{ mb: 1 }}>
            <FormLabel>Passwort</FormLabel>
            <Input
              name="password"
              type="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="Mindestens 6 Zeichen"
              disabled={loading}
            />
          </FormControl>

          {formData.password && (
            <Box sx={{ mb: 2 }}>
              <Typography level="body-xs" sx={{ mb: 0.5 }}>
                Passwortstärke
              </Typography>
              <LinearProgress
                determinate
                value={passwordStrength}
                color={getPasswordStrengthColor()}
                size="sm"
              />
            </Box>
          )}

          <FormControl sx={{ mb: 3 }}>
            <FormLabel>Passwort bestätigen</FormLabel>
            <Input
              name="confirmPassword"
              type="password"
              value={formData.confirmPassword}
              onChange={handleChange}
              placeholder="Passwort wiederholen"
              disabled={loading}
            />
          </FormControl>

          <Button
            type="submit"
            fullWidth
            loading={loading}
            sx={{ mb: 2 }}
          >
            Registrieren
          </Button>

          <Typography level="body-sm" sx={{ textAlign: 'center' }}>
            Bereits registriert?{' '}
            <Link to="/" style={{ textDecoration: 'none' }}>
              Zum Login
            </Link>
          </Typography>
        </form>
      </Card>
    </Box>
  );
};

export default Register;