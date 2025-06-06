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
        sx={{
          width: 450,
          p: 4,
          background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
          borderRadius: '30px',
          boxShadow: '0 20px 60px rgba(240, 147, 251, 0.4)',
          color: '#FFF',
          border: 'none'
        }}
      >
        <Typography level="h2" sx={{ 
          mb: 3, 
          textAlign: 'center',
          fontWeight: 'bold',
          textShadow: '0 3px 6px rgba(0,0,0,0.3)',
          fontSize: '2.5rem'
        }}>
          📝 Registrierung
        </Typography>

        {error && (
          <Alert sx={{
            mb: 2,
            background: 'rgba(255,255,255,0.95)',
            color: '#C0392B',
            borderRadius: '12px',
            border: 'none'
          }}>
            {error}
          </Alert>
        )}

        <div style={{
          background: 'rgba(255,255,255,0.1)',
          borderRadius: '20px',
          padding: '2rem',
          backdropFilter: 'blur(10px)'
        }}>
          <form onSubmit={handleSubmit}>
            <FormControl sx={{ mb: 2 }}>
              <FormLabel sx={{
                color: '#FFF',
                fontWeight: 'bold',
                fontSize: '1.1rem',
                textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                mb: 1
              }}>👤 Benutzername</FormLabel>
              <Input
                name="username"
                value={formData.username}
                onChange={handleChange}
                placeholder="Mindestens 3 Zeichen"
                disabled={loading}
                sx={{
                  background: 'rgba(255,255,255,0.95)',
                  borderRadius: '12px',
                  border: 'none',
                  fontSize: '1rem'
                }}
              />
            </FormControl>

            <FormControl sx={{ mb: 2 }}>
              <FormLabel sx={{
                color: '#FFF',
                fontWeight: 'bold',
                fontSize: '1.1rem',
                textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                mb: 1
              }}>📧 E-Mail</FormLabel>
              <Input
                name="email"
                type="text"
                value={formData.email}
                onChange={handleChange}
                placeholder="name@example.com"
                disabled={loading}
                sx={{
                  background: 'rgba(255,255,255,0.95)',
                  borderRadius: '12px',
                  border: 'none',
                  fontSize: '1rem'
                }}
              />
            </FormControl>

            <FormControl sx={{ mb: 1 }}>
              <FormLabel sx={{
                color: '#FFF',
                fontWeight: 'bold',
                fontSize: '1.1rem',
                textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                mb: 1
              }}>🔒 Passwort</FormLabel>
              <Input
                name="password"
                type="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="Mindestens 6 Zeichen"
                disabled={loading}
                sx={{
                  background: 'rgba(255,255,255,0.95)',
                  borderRadius: '12px',
                  border: 'none',
                  fontSize: '1rem'
                }}
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
              <FormLabel sx={{
                color: '#FFF',
                fontWeight: 'bold',
                fontSize: '1.1rem',
                textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                mb: 1
              }}>🔁 Passwort bestätigen</FormLabel>
              <Input
                name="confirmPassword"
                type="password"
                value={formData.confirmPassword}
                onChange={handleChange}
                placeholder="Passwort wiederholen"
                disabled={loading}
                sx={{
                  background: 'rgba(255,255,255,0.95)',
                  borderRadius: '12px',
                  border: 'none',
                  fontSize: '1rem'
                }}
              />
            </FormControl>

            <Button
              type="submit"
              fullWidth
              loading={loading}
              sx={{ 
                mb: 3,
                background: 'linear-gradient(135deg, #4ECDC4 0%, #44A08D 100%)',
                color: '#FFF',
                fontWeight: 'bold',
                borderRadius: '15px',
                fontSize: '1.2rem',
                padding: '12px',
                boxShadow: '0 6px 20px rgba(78, 205, 196, 0.4)',
                '&:hover': {
                  background: 'linear-gradient(135deg, #44A08D 0%, #3d8f7a 100%)',
                  transform: 'translateY(-2px)',
                  boxShadow: '0 8px 25px rgba(78, 205, 196, 0.6)'
                }
              }}
            >
              🚀 Registrieren
            </Button>

            <Typography level="h4" sx={{ 
              textAlign: 'center',
              color: '#FFF',
              textShadow: '0 2px 4px rgba(0,0,0,0.3)'
            }}>
              Bereits registriert?{' '}
              <Link to="/" style={{ 
                color: '#4ECDC4',
                textDecoration: 'none',
                fontWeight: 'bold',
                textShadow: '0 2px 4px rgba(0,0,0,0.3)'
              }}>
                Zum Login 🔑
              </Link>
            </Typography>
          </form>
        </div>
      </Card>
    </Box>
  );
};

export default Register;