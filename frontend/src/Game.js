import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from './AuthContext';
import axios from './api/axios';
import GameChat from './components/GameChat';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  LinearProgress,
  Alert,
  Stack,
  Grid
} from '@mui/joy';

const Game = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const { getToken } = useAuth();
  
  // Game state
  const [gameState, setGameState] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [votes, setVotes] = useState([]);
  const [voteCounts, setVoteCounts] = useState({});
  const [userVote, setUserVote] = useState(null);
  const [sessionData, setSessionData] = useState(null);
  const [isHost, setIsHost] = useState(false);
  const [websocket, setWebsocket] = useState(null);
  
  // UI state
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showResult, setShowResult] = useState(false);
  const [questionResult, setQuestionResult] = useState(null);
  const [gameResult, setGameResult] = useState(null);
  const [showFinalResult, setShowFinalResult] = useState(false);
  
  // Simple: Is this the last question?
  const isLastQuestion = () => {
    if (!currentQuestion) return false;
    return currentQuestion.question_index >= (currentQuestion.total_questions - 1);
  };
  
  useEffect(() => {
    loadSessionData();
    setupWebSocket();
    
    return () => {
      if (websocket) {
        websocket.close();
      }
    };
  }, [sessionId]);

  const loadGameState = async () => {
    try {
      const gameStateResponse = await axios.get(`/api/game/state/${sessionId}`);
      const gameData = gameStateResponse.data;
      
      // Update game state while preserving scores (WebSocket is authoritative)
      setGameState(prev => {
        if (!prev) {
          return gameData;
        }
        
        // CRITICAL: Never overwrite scores from WebSocket!
        return {
          ...prev,
          // Update from API but preserve WebSocket scores
          current_question_index: gameData.current_question_index,
          current_flashcard_id: gameData.current_flashcard_id,
          status: gameData.status,
          // NEVER update these from API:
          // total_score: KEEP from WebSocket
          // max_possible_score: KEEP original
        };
      });
      
      // Set current question if available
      if (gameData.current_question) {
        setCurrentQuestion(gameData.current_question);
        
        // Check if question is already ended (show result)
        if (gameData.status === 'question_ended' || gameData.show_result) {
          setShowResult(true);
          
          // Load question result if available
          if (gameData.question_result) {
            setQuestionResult(gameData.question_result);
          }
        } else {
          setShowResult(false);
        }
        
        // Load current votes for this question
        if (gameData.current_flashcard_id) {
          try {
            const votesResponse = await axios.get(`/api/game/votes/${sessionId}/${gameData.current_flashcard_id}`);
            setVotes(votesResponse.data.votes || []);
            setVoteCounts(votesResponse.data.vote_counts || {});
            
            // Check if current user already voted
            const userResponse = await axios.get('/me');
            const currentUser = userResponse.data;
            const currentUserVote = votesResponse.data.votes?.find(v => v.user_id === currentUser.id);
            if (currentUserVote) {
              setUserVote(currentUserVote.answer_id);
            }
          } catch (err) {
            console.log('Error loading votes:', err);
            setVotes([]);
            setVoteCounts({});
          }
        } else {
          setVotes([]);
          setVoteCounts({});
          setUserVote(null);
        }
      }
    } catch (err) {
      if (err.response?.status === 403) {
        console.log('403 in loadGameState - retrying in 200ms');
        setTimeout(() => {
          loadGameState();
        }, 200);
      } else {
        console.log('Error loading game state:', err);
      }
    }
  };

  const loadSessionData = async () => {
    try {
      setLoading(true);
      
      // Load session details from lobby endpoint
      const sessionResponse = await axios.get(`/api/lobby/${sessionId}`);
      const session = sessionResponse.data;
      setSessionData(session);
      
      // Check if current user is host
      const userResponse = await axios.get('/me');
      const currentUser = userResponse.data;
      setIsHost(session.host.id === currentUser.id);
      
      // Load game state if exists - preserve higher scores from WebSocket updates
      try {
        const gameStateResponse = await axios.get(`/api/game/state/${sessionId}`);
        const gameData = gameStateResponse.data;
        
        // Only update gameState if we don't have one, otherwise preserve WebSocket scores
        setGameState(prev => {
          if (!prev) {
            return gameData;
          }
          
          // CRITICAL: Never overwrite score from WebSocket updates!
          // Only update non-score related fields from API
          return { 
            ...prev,
            // Update from API but preserve WebSocket scores
            current_question_index: gameData.current_question_index,
            current_flashcard_id: gameData.current_flashcard_id,
            status: gameData.status,
            // NEVER update these from API:
            // total_score: KEEP from WebSocket
            // max_possible_score: KEEP original
          };
        });
        
        // Set current question if available
        if (gameData.current_question) {
          setCurrentQuestion(gameData.current_question);
        }
      } catch (err) {
        if (err.response?.status === 403) {
          console.log('Not a participant yet - waiting for auto-join to complete');
          // Retry with shorter delay
          setTimeout(() => {
            loadSessionData();
          }, 200);
          return; // Don't set loading to false yet
        } else {
          console.log('No game state yet - game not started');
        }
      }
      
    } catch (err) {
      console.error('Error loading session data:', err);
      setError('Fehler beim Laden der Session-Daten');
    } finally {
      setLoading(false);
    }
  };

  const setupWebSocket = () => {
    const token = getToken();
    if (!token) return;

    // Use the same host and port as the current page
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = window.location.host; // includes hostname:port
    const wsUrl = `${wsProtocol}//${wsHost}/ws/${token}`;
    
    console.log('Attempting WebSocket connection to:', wsUrl);
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      console.log('Game WebSocket connected successfully!');
      ws.send(JSON.stringify({
        type: 'join_game',
        session_id: sessionId
      }));
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      console.error('WebSocket URL was:', wsUrl);
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      handleWebSocketMessage(message);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
    };

    setWebsocket(ws);
  };

  const handleWebSocketMessage = (message) => {
    
    switch (message.type) {
      case 'game_joined':
        console.log('Successfully joined game');
        // Reload game state to get current question if game already started
        // Add small delay to ensure auto-join is complete
        setTimeout(() => {
          loadGameState();
        }, 100);
        break;
        
      case 'game_started':
        setGameState(message.game_state);
        setCurrentQuestion(message.question);
        setShowResult(false);
        setVotes([]);
        setVoteCounts({});
        setUserVote(null);
        break;
        
      case 'new_question':
      case 'next_question':
        setCurrentQuestion(message.question);
        setShowResult(false);
        setVotes([]);
        setVoteCounts({});
        setUserVote(null);
        break;
        
      case 'vote_update':
        console.log('🔥 VOTE UPDATE received:', message);
        console.log('🔥 Setting votes:', message.votes);
        console.log('🔥 Setting vote counts:', message.vote_counts);
        setVotes(message.votes || []);
        setVoteCounts(message.vote_counts || {});
        break;
        
      case 'question_ended':
        setQuestionResult(message.result);
        setShowResult(true);
        
        // CENTRAL SCORE UPDATE: Only from WebSocket question_ended
        setGameState(prev => {
          if (!prev) {
            // Initial game state from first question result
            const questionsCompleted = Math.floor(message.result.total_score / 100);
            return {
              total_score: message.result.total_score,
              max_possible_score: message.result.max_possible_score,
              status: 'playing',
              current_question_index: questionsCompleted,
              flashcard_count: (message.result.max_possible_score || 200) / 100,
              current_flashcard_id: message.result.flashcard_id
            };
          }
          
          // Update existing game state - ONLY score changes
          return {
            ...prev,
            total_score: message.result.total_score,
            // Keep everything else unchanged!
          };
        });
        break;
        
      case 'game_finished':
        setGameResult(message.result);
        setShowFinalResult(true);
        if (gameState) {
          setGameState(prev => ({
            ...prev,
            status: 'finished'
          }));
        }
        break;
        
      default:
        console.log('Unhandled WebSocket message type:', message.type);
    }
  };

  const startGame = async () => {
    try {
      setLoading(true);
      await axios.post(`/api/game/start/${sessionId}`);
    } catch (err) {
      console.error('Error starting game:', err);
      setError('Fehler beim Starten des Spiels');
    } finally {
      setLoading(false);
    }
  };

  const castVote = async (answerId) => {
    
    // Try to get flashcard_id from currentQuestion first, then from gameState as fallback
    const flashcardId = currentQuestion?.flashcard_id || gameState?.current_flashcard_id;
    
    if (!flashcardId) {
      console.error('❌ VOTE DEBUG - No flashcard_id available!', {
        currentQuestion,
        gameState,
        flashcardId
      });
      setError('Flashcard ID nicht verfügbar');
      return;
    }
    
    try {
      const voteData = {
        session_id: sessionId,
        flashcard_id: flashcardId,
        answer_id: answerId
      };
      
      const response = await axios.post('/api/game/vote', voteData);
      setUserVote(answerId);
    } catch (err) {
      console.error('❌ VOTE DEBUG - Error casting vote:', {
        error: err,
        response: err.response,
        data: err.response?.data,
        status: err.response?.status
      });
      setError('Fehler beim Abstimmen');
    }
  };

  const endQuestion = async () => {
    if (!isHost) return;
    
    try {
      await axios.post(`/api/game/end-question/${sessionId}`);
      // WebSocket will handle updates
    } catch (err) {
      console.error('Error ending question:', err);
      setError('Fehler beim Beenden der Frage');
    }
  };

  const nextQuestion = async () => {
    if (!isHost) return;
    try {
      await axios.post(`/api/game/next-question/${sessionId}`);
    } catch (err) {
      console.error('Error moving to next question:', err);
      setError('Fehler beim Wechsel zur nächsten Frage');
    }
  };

  const endGame = async () => {
    if (!isHost) return;
    
    try {
      await axios.post(`/api/game/end/${sessionId}`);
      // WebSocket will handle updates
    } catch (err) {
      console.error('Error ending game:', err);
      setError('Fehler beim Beenden des Spiels');
    }
  };

  const loadGameResult = async () => {
    try {
      const response = await axios.get(`/api/game/result/${sessionId}`);
      setGameResult(response.data);
      setShowFinalResult(true);
    } catch (err) {
      console.error('Error loading game result:', err);
      setError('Fehler beim Laden des Spielergebnisses');
    }
  };

  const calculateProgress = () => {
    if (!gameState || !currentQuestion) return 0;
    // Start at 0 for first question, then progress
    return (currentQuestion.question_index / currentQuestion.total_questions) * 100;
  };

  const calculateScorePercentage = () => {
    if (!gameState) return 0;
    return gameState.max_possible_score > 0 ? (gameState.total_score / gameState.max_possible_score) * 100 : 0;
  };

  // Auto-start game if session is playing but no game state exists
  useEffect(() => {
    console.log('Auto-start check:', {
      sessionData: sessionData?.status,
      hasGameState: !!gameState,
      isHost,
      shouldStart: sessionData && sessionData.status === 'playing' && !gameState && isHost
    });
    
    if (sessionData && sessionData.status === 'playing' && !gameState && isHost) {
      console.log('Auto-starting game...');
      startGame();
    }
  }, [sessionData, gameState, isHost, startGame]);

  if (loading) {
    return (
      <Box sx={{ p: { xs: 2, sm: 3, md: 4 }, textAlign: 'center' }}>
        <Typography level="h4">Lade Spiel...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
        <Alert color="danger">{error}</Alert>
        <Button onClick={() => navigate('/groups')} sx={{ mt: 2 }}>
          Zurück zu Gruppen
        </Button>
      </Box>
    );
  }

  // Game hasn't started yet - show loading until game starts
  if (!gameState || gameState.status === 'waiting') {
    return (
      <Box sx={{ p: { xs: 2, sm: 3, md: 4 }, maxWidth: 800, margin: '0 auto' }}>
        <Card>
          <CardContent>
            <Typography level="h2" textAlign="center" mb={2} sx={{ fontSize: { xs: '1.5rem', sm: '2rem' } }}>
              {sessionData?.subject?.name} Quiz
            </Typography>
            <Typography level="body1" textAlign="center" mb={4}>
              Spiel wird gestartet...
            </Typography>
            
            <Box textAlign="center">
              <Typography level="body2">
                Bitte warten Sie einen Moment.
              </Typography>
              {sessionData && sessionData.status === 'playing' && isHost && (
                <Typography level="body2" sx={{ mt: 1 }}>
                  Initialisiere Spiel...
                </Typography>
              )}
            </Box>
          </CardContent>
        </Card>
      </Box>
    );
  }

  // Game finished - but only show if we've already shown the last question result
  if (gameResult && showFinalResult) {
    const isWon = gameResult.status === 'won';
    return (
      <Box sx={{ p: { xs: 2, sm: 3, md: 4 }, maxWidth: 800, margin: '0 auto' }}>
        <Card sx={{
          background: isWon 
            ? 'linear-gradient(135deg, #FFD700 0%, #FFA500 50%, #FF6347 100%)'
            : 'linear-gradient(135deg, #FF7F7F 0%, #FF6B6B 50%, #FF5252 100%)',
          borderRadius: '30px',
          boxShadow: isWon 
            ? '0 15px 50px rgba(255, 215, 0, 0.5)'
            : '0 15px 50px rgba(255, 107, 107, 0.5)',
          position: 'relative',
          overflow: 'hidden'
        }}>
          {/* Celebration Confetti Effect */}
          {isWon && (
            <Box sx={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
              background: 'radial-gradient(circle at 20% 80%, #FFD700 0%, transparent 50%), radial-gradient(circle at 80% 20%, #FF6347 0%, transparent 50%), radial-gradient(circle at 40% 40%, #FFA500 0%, transparent 50%)',
              opacity: 0.3,
              zIndex: 0
            }} />
          )}
          
          <CardContent textAlign="center" sx={{ position: 'relative', zIndex: 1, p: { xs: 2, sm: 3 } }}>
            <Typography 
              level="h1" 
              mb={3}
              sx={{
                fontSize: { xs: '2rem', sm: '2.5rem', md: '3.5rem' },
                fontWeight: 'bold',
                color: '#FFF',
                textShadow: '0 4px 8px rgba(0,0,0,0.3)',
                animation: isWon ? 'bounce 2s infinite' : 'none'
              }}
            >
              {isWon ? '🎆🎉 GEWONNEN! 🎉🎆' : '😔📚 VERLOREN 📚😔'}
            </Typography>
            
            <Box sx={{
              background: 'rgba(255,255,255,0.2)',
              borderRadius: '20px',
              p: { xs: 2, sm: 3 },
              mb: 3,
              backdropFilter: 'blur(10px)'
            }}>
              <Typography 
                level="h2" 
                mb={2}
                sx={{
                  color: '#FFF',
                  fontWeight: 'bold',
                  textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                  fontSize: { xs: '1.5rem', sm: '2rem' }
                }}
              >
                🏆 {gameResult.total_score} / {gameResult.max_possible_score} Punkte
              </Typography>
              
              <Typography 
                level="h3" 
                mb={2}
                sx={{
                  color: '#FFF',
                  fontWeight: 'bold',
                  textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                  fontSize: { xs: '1.25rem', sm: '1.5rem' }
                }}
              >
                🎯 {gameResult.percentage?.toFixed(1)}% richtig
              </Typography>
            </Box>
            
            <Box sx={{
              background: 'rgba(255,255,255,0.15)',
              borderRadius: '16px',
              p: 2,
              mb: 4
            }}>
              {isWon ? (
                <Typography 
                  level="h4" 
                  sx={{
                    color: '#FFF',
                    fontWeight: 'bold',
                    textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                    fontSize: { xs: '1rem', sm: '1.25rem' }
                  }}
                >
                  ✨ Hervorragend! Ihr habt das Ziel von 90% erreicht! ✨
                </Typography>
              ) : (
                <Typography 
                  level="h4"
                  sx={{
                    color: '#FFF',
                    fontWeight: 'bold',
                    textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                    fontSize: { xs: '1rem', sm: '1.25rem' }
                  }}
                >
                  💪 Ihr habt verloren, da müsst ihr wohl noch was üben! 💪
                </Typography>
              )}
            </Box>
            
            <Button 
              onClick={() => navigate('/groups')} 
              size="lg"
              sx={{
                background: 'linear-gradient(135deg, #2C3E50 0%, #34495E 100%)',
                color: '#FFF',
                fontWeight: 'bold',
                borderRadius: '15px',
                padding: { xs: '10px 20px', sm: '12px 30px' },
                fontSize: { xs: '16px', sm: '18px' },
                boxShadow: '0 6px 20px rgba(44, 62, 80, 0.4)',
                '&:hover': {
                  background: 'linear-gradient(135deg, #34495E 0%, #2C3E50 100%)',
                  transform: 'translateY(-3px)',
                  boxShadow: '0 8px 25px rgba(44, 62, 80, 0.6)'
                }
              }}
            >
              🏠 Zurück zu Gruppen
            </Button>
          </CardContent>
        </Card>
        
        {/* Add bounce animation for winner */}
        <style>
          {`
            @keyframes bounce {
              0%, 20%, 50%, 80%, 100% {
                transform: translateY(0);
              }
              40% {
                transform: translateY(-10px);
              }
              60% {
                transform: translateY(-5px);
              }
            }
          `}
        </style>
      </Box>
    );
  }

  // Active game
  return (
    <Box sx={{ p: { xs: 2, sm: 3, md: 4 }, maxWidth: 1200, margin: '0 auto' }}>
      <Grid container spacing={{ xs: 2, sm: 3 }}>
        {/* Game Header */}
        <Grid xs={12}>
          <Card sx={{ 
            mb: 3, 
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            borderRadius: '20px',
            boxShadow: '0 8px 32px rgba(102, 126, 234, 0.4)'
          }}>
            <CardContent sx={{ color: '#FFF', textAlign: 'center', p: { xs: 2, sm: 3 } }}>
              <Typography 
                level="h3" 
                sx={{ 
                  fontWeight: 'bold',
                  textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                  mb: 1,
                  fontSize: { xs: '1.5rem', sm: '2rem' }
                }}
              >
                🎯 {sessionData?.subject?.name} Quiz
              </Typography>
              
              <Typography 
                level="body1" 
                sx={{ 
                  mb: 2,
                  opacity: 0.9,
                  fontSize: { xs: '14px', sm: '16px' }
                }}
              >
                📝 Frage {currentQuestion?.question_index + 1} von {currentQuestion?.total_questions}
              </Typography>
              
              {/* Progress Bar with Glow */}
              <Box sx={{ mb: 2, position: 'relative' }}>
                <LinearProgress 
                  determinate 
                  value={calculateProgress()} 
                  sx={{ 
                    height: { xs: 8, sm: 12 },
                    borderRadius: '6px',
                    background: 'rgba(255,255,255,0.2)',
                    '& .MuiLinearProgress-bar': {
                      background: 'linear-gradient(90deg, #FFD700, #FFA500)',
                      borderRadius: '6px',
                      boxShadow: '0 0 10px rgba(255, 215, 0, 0.6)'
                    }
                  }}
                />
              </Box>
              
              <Typography 
                level="h4" 
                sx={{ 
                  fontWeight: 'bold',
                  textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                  background: 'rgba(255,255,255,0.15)',
                  borderRadius: '12px',
                  p: { xs: 1.5, sm: 2 },
                  backdropFilter: 'blur(10px)',
                  fontSize: { xs: '1.1rem', sm: '1.25rem' }
                }}
              >
                🏆 {gameState?.total_score} / {gameState?.max_possible_score} Punkte ({calculateScorePercentage().toFixed(1)}%)
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Current Question */}
        {currentQuestion && !showResult && (
          <Grid xs={12}>
            <Card sx={{ 
              mb: 3,
              background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
              borderRadius: '20px',
              boxShadow: '0 8px 32px rgba(240, 147, 251, 0.4)'
            }}>
              <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
                <Typography 
                  level="h2" 
                  textAlign="center" 
                  mb={4}
                  sx={{
                    color: '#FFF',
                    fontWeight: 'bold',
                    textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                    background: 'rgba(255,255,255,0.1)',
                    borderRadius: '16px',
                    p: { xs: 2, sm: 3 },
                    backdropFilter: 'blur(10px)',
                    fontSize: { xs: '1.25rem', sm: '1.5rem', md: '2rem' }
                  }}
                >
                  🤔 {currentQuestion.question}
                </Typography>
                
                {/* 4 Quadrant Voting Layout */}
                <Grid container spacing={{ xs: 2, sm: 3 }}>
                  {currentQuestion.answers?.map((answer, index) => {
                    const voteCount = voteCounts[answer.id] || 0;
                    const totalVotes = Object.values(voteCounts).reduce((sum, count) => sum + count, 0);
                    const percentage = totalVotes > 0 ? (voteCount / totalVotes) * 100 : 0;
                    
                    // Vibrant colors for each quadrant
                    const quadrantColors = [
                      { bg: '#FF6B6B', hover: '#FF5252', border: '#FF1744' }, // Red
                      { bg: '#4ECDC4', hover: '#26C6DA', border: '#00BCD4' }, // Teal
                      { bg: '#45B7D1', hover: '#2196F3', border: '#1976D2' }, // Blue
                      { bg: '#96CEB4', hover: '#66BB6A', border: '#4CAF50' }  // Green
                    ];
                    
                    const colors = quadrantColors[index] || quadrantColors[0];
                    const isSelected = userVote === answer.id;
                    
                    return (
                      <Grid xs={6} sm={6} key={answer.id}>
                        <Card
                          sx={{
                            cursor: 'pointer',
                            background: isSelected 
                              ? `linear-gradient(135deg, ${colors.bg} 0%, ${colors.hover} 100%)`
                              : `linear-gradient(135deg, ${colors.bg}40 0%, ${colors.bg}20 100%)`,
                            border: `3px solid ${isSelected ? colors.border : colors.bg}`,
                            borderRadius: '20px',
                            transition: 'all 0.3s ease',
                            transform: isSelected ? 'scale(1.02)' : 'scale(1)',
                            boxShadow: isSelected 
                              ? `0 8px 25px ${colors.bg}60` 
                              : `0 4px 15px ${colors.bg}40`,
                            '&:hover': {
                              transform: 'scale(1.05)',
                              boxShadow: `0 12px 30px ${colors.bg}80`,
                              background: `linear-gradient(135deg, ${colors.hover}80 0%, ${colors.bg}60 100%)`
                            },
                            minHeight: { xs: '120px', sm: '180px' },
                            position: 'relative',
                            overflow: 'hidden'
                          }}
                          onClick={() => !showResult && castVote(answer.id)}
                        >
                          {/* Letter Badge */}
                          <Box sx={{
                            position: 'absolute',
                            top: { xs: 10, sm: 15 },
                            left: { xs: 10, sm: 15 },
                            width: { xs: 25, sm: 40 },
                            height: { xs: 25, sm: 40 },
                            borderRadius: '50%',
                            background: isSelected ? '#FFF' : colors.border,
                            color: isSelected ? colors.border : '#FFF',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontWeight: 'bold',
                            fontSize: { xs: '12px', sm: '18px' },
                            boxShadow: '0 2px 8px rgba(0,0,0,0.2)'
                          }}>
                            {String.fromCharCode(65 + index)}
                          </Box>
                          
                          <CardContent sx={{ textAlign: 'center', p: { xs: 1, sm: 3 } }}>
                            <Typography 
                              level="h4" 
                              sx={{ 
                                color: isSelected ? '#FFF' : colors.border,
                                fontWeight: 'bold',
                                mb: 2,
                                textShadow: isSelected ? '0 2px 4px rgba(0,0,0,0.3)' : 'none',
                                fontSize: { xs: '0.875rem', sm: '1.25rem' }
                              }}
                            >
                              {answer.text}
                            </Typography>
                            
                            {/* Vote Progress */}
                            <Box sx={{ 
                              mt: 2,
                              background: 'rgba(255,255,255,0.3)',
                              borderRadius: '10px',
                              p: 1,
                              backdropFilter: 'blur(10px)'
                            }}>
                              <Typography 
                                level="body2" 
                                sx={{ 
                                  color: '#FFF',
                                  fontWeight: 'bold',
                                  mb: 1,
                                  textShadow: '0 1px 2px rgba(0,0,0,0.5)',
                                  fontSize: { xs: '0.875rem', sm: '1rem' }
                                }}
                              >
                                {voteCount} Stimme{voteCount !== 1 ? 'n' : ''} ({percentage.toFixed(0)}%)
                              </Typography>
                              
                              <Box sx={{
                                height: { xs: 6, sm: 8 },
                                borderRadius: '4px',
                                background: 'rgba(255,255,255,0.3)',
                                overflow: 'hidden'
                              }}>
                                <Box sx={{
                                  width: `${percentage}%`,
                                  height: '100%',
                                  background: '#FFF',
                                  borderRadius: '4px',
                                  transition: 'width 0.5s ease'
                                }} />
                              </Box>
                            </Box>
                          </CardContent>
                        </Card>
                      </Grid>
                    );
                  })}
                </Grid>
                
                {userVote && (
                  <Alert 
                    sx={{ 
                      mt: 3,
                      background: 'rgba(255,255,255,0.9)',
                      borderRadius: '12px',
                      border: '2px solid #4CAF50',
                      boxShadow: '0 4px 15px rgba(76, 175, 80, 0.3)'
                    }}
                  >
                    <Typography sx={{ fontWeight: 'bold', color: '#2E7D32' }}>
                      ✅ Sie haben gestimmt. Sie können Ihre Stimme jederzeit ändern.
                    </Typography>
                  </Alert>
                )}
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Question Result */}
        {showResult && questionResult && !gameResult && (
          <Grid xs={12}>
            <Card sx={{ 
              mb: 3,
              background: questionResult.was_correct 
                ? 'linear-gradient(135deg, #4CAF50 0%, #8BC34A 100%)' 
                : 'linear-gradient(135deg, #FF5722 0%, #FF9800 100%)',
              borderRadius: '20px',
              boxShadow: questionResult.was_correct 
                ? '0 8px 32px rgba(76, 175, 80, 0.4)'
                : '0 8px 32px rgba(255, 87, 34, 0.4)'
            }}>
              <CardContent textAlign="center" sx={{ p: { xs: 2, sm: 3 } }}>
                <Typography 
                  level="h2" 
                  mb={3}
                  sx={{
                    color: '#FFF',
                    fontWeight: 'bold',
                    textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                    fontSize: { xs: '2rem', sm: '2.5rem' }
                  }}
                >
                  {questionResult.was_correct ? '🎉 Richtig!' : '😞 Falsch!'}
                </Typography>
                
                {/* Show correct answer and team choice */}
                <Box sx={{ mb: 3 }}>
                  <Typography level="h4" mb={2} sx={{ fontSize: { xs: '1.25rem', sm: '1.5rem' } }}>
                    Richtige Antwort:
                  </Typography>
                  {currentQuestion?.answers?.map((answer) => {
                    const isCorrect = answer.id === questionResult.correct_answer_id;
                    const isTeamChoice = answer.id === questionResult.winning_answer_id;
                    
                    if (isCorrect) {
                      return (
                        <Card key={answer.id} sx={{ 
                          mb: 1, 
                          background: 'linear-gradient(135deg, #66BB6A 0%, #4CAF50 100%)',
                          border: '3px solid #2E7D32',
                          borderRadius: '12px',
                          boxShadow: '0 4px 15px rgba(76, 175, 80, 0.3)'
                        }}>
                          <CardContent>
                            <Typography level="body1" sx={{ 
                              fontWeight: 'bold',
                              color: '#FFF',
                              textShadow: '0 1px 2px rgba(0,0,0,0.3)',
                              fontSize: { xs: '1rem', sm: '1.1rem' }
                            }}>
                              ✅ {answer.text}
                            </Typography>
                          </CardContent>
                        </Card>
                      );
                    }
                    return null;
                  })}
                  
                  <Typography level="h4" mb={2} mt={3} sx={{ fontSize: { xs: '1.25rem', sm: '1.5rem' } }}>
                    Eure Antwort:
                  </Typography>
                  {currentQuestion?.answers?.map((answer) => {
                    const isTeamChoice = answer.id === questionResult.winning_answer_id;
                    const isCorrect = answer.id === questionResult.correct_answer_id;
                    
                    if (isTeamChoice) {
                      return (
                        <Card key={answer.id} sx={{ 
                          mb: 1, 
                          background: isCorrect 
                            ? 'linear-gradient(135deg, #66BB6A 0%, #4CAF50 100%)'
                            : 'linear-gradient(135deg, #EF5350 0%, #F44336 100%)',
                          border: `3px solid ${isCorrect ? '#2E7D32' : '#C62828'}`,
                          borderRadius: '12px',
                          boxShadow: isCorrect 
                            ? '0 4px 15px rgba(76, 175, 80, 0.3)'
                            : '0 4px 15px rgba(244, 67, 54, 0.3)'
                        }}>
                          <CardContent>
                            <Typography level="body1" sx={{ 
                              fontWeight: 'bold',
                              color: '#FFF',
                              textShadow: '0 1px 2px rgba(0,0,0,0.3)',
                              fontSize: { xs: '1rem', sm: '1.1rem' }
                            }}>
                              {isCorrect ? '✅' : '❌'} {answer.text}
                            </Typography>
                          </CardContent>
                        </Card>
                      );
                    }
                    return null;
                  })}
                </Box>
                
                <Box sx={{
                  background: 'rgba(255,255,255,0.15)',
                  borderRadius: '16px',
                  p: { xs: 2, sm: 3 },
                  backdropFilter: 'blur(10px)',
                  mt: 3
                }}>
                  <Typography 
                    level="h4" 
                    mb={2}
                    sx={{
                      color: '#FFF',
                      fontWeight: 'bold',
                      textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                      fontSize: { xs: '1.25rem', sm: '1.5rem' }
                    }}
                  >
                    {questionResult.was_correct ? 
                      `🎆 +${questionResult.points_earned} Punkte!` : 
                      '🚫 Keine Punkte'
                    }
                  </Typography>
                  
                  <Typography 
                    level="body1"
                    sx={{
                      color: '#FFF',
                      fontWeight: 'bold',
                      textShadow: '0 1px 2px rgba(0,0,0,0.3)',
                      fontSize: { xs: '1rem', sm: '1.1rem' }
                    }}
                  >
                    🏆 Aktuelle Punktzahl: {questionResult.total_score} / {gameState?.max_possible_score}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Host Controls - ALWAYS VISIBLE */}
        {isHost && (
          <Grid xs={12}>
            <Card sx={{ 
              mb: 3,
              background: 'linear-gradient(135deg, #2C3E50 0%, #34495E 100%)',
              borderRadius: '20px',
              boxShadow: '0 8px 32px rgba(44, 62, 80, 0.4)'
            }}>
              <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
                <Typography 
                  level="h4" 
                  mb={2}
                  sx={{
                    color: '#FFF',
                    fontWeight: 'bold',
                    textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                    textAlign: 'center',
                    fontSize: { xs: '1.25rem', sm: '1.5rem' }
                  }}
                >
                  🎮 Host-Steuerung
                </Typography>
                
                <Stack 
                  direction={{ xs: 'column', sm: 'row' }} 
                  spacing={2} 
                  sx={{ flexWrap: 'wrap', justifyContent: 'center' }}
                >
                  {/* Always show all buttons */}
                  <Button 
                    onClick={endQuestion} 
                    size="lg" 
                    disabled={showResult}
                    sx={{
                      background: 'linear-gradient(135deg, #E74C3C 0%, #C0392B 100%)',
                      color: '#FFF',
                      fontWeight: 'bold',
                      borderRadius: '12px',
                      boxShadow: '0 4px 15px rgba(231, 76, 60, 0.3)',
                      fontSize: { xs: '0.9rem', sm: '1rem' },
                      px: { xs: 2, sm: 3 },
                      '&:hover': {
                        background: 'linear-gradient(135deg, #C0392B 0%, #A93226 100%)',
                        transform: 'translateY(-2px)',
                        boxShadow: '0 6px 20px rgba(231, 76, 60, 0.4)'
                      },
                      '&:disabled': {
                        background: 'rgba(255,255,255,0.2)',
                        color: 'rgba(255,255,255,0.5)'
                      }
                    }}
                  >
                    ⏹️ Voting beenden
                  </Button>
                  
                  <Button 
                    onClick={nextQuestion} 
                    size="lg" 
                    disabled={!showResult}
                    sx={{
                      background: 'linear-gradient(135deg, #27AE60 0%, #229954 100%)',
                      color: '#FFF',
                      fontWeight: 'bold',
                      borderRadius: '12px',
                      boxShadow: '0 4px 15px rgba(39, 174, 96, 0.3)',
                      fontSize: { xs: '0.9rem', sm: '1rem' },
                      px: { xs: 2, sm: 3 },
                      '&:hover': {
                        background: 'linear-gradient(135deg, #229954 0%, #1E8449 100%)',
                        transform: 'translateY(-2px)',
                        boxShadow: '0 6px 20px rgba(39, 174, 96, 0.4)'
                      },
                      '&:disabled': {
                        background: 'rgba(255,255,255,0.2)',
                        color: 'rgba(255,255,255,0.5)'
                      }
                    }}
                  >
                    ▶️ Nächste Frage
                  </Button>
                  
                  <Button 
                    onClick={endGame} 
                    size="lg" 
                    disabled={!showResult}
                    sx={{
                      background: 'linear-gradient(135deg, #F39C12 0%, #E67E22 100%)',
                      color: '#FFF',
                      fontWeight: 'bold',
                      borderRadius: '12px',
                      boxShadow: '0 4px 15px rgba(243, 156, 18, 0.3)',
                      fontSize: { xs: '0.9rem', sm: '1rem' },
                      px: { xs: 2, sm: 3 },
                      '&:hover': {
                        background: 'linear-gradient(135deg, #E67E22 0%, #D68910 100%)',
                        transform: 'translateY(-2px)',
                        boxShadow: '0 6px 20px rgba(243, 156, 18, 0.4)'
                      },
                      '&:disabled': {
                        background: 'rgba(255,255,255,0.2)',
                        color: 'rgba(255,255,255,0.5)'
                      }
                    }}
                  >
                    🏁 Spiel beenden
                  </Button>
                  
                  {gameResult && (
                    <Button 
                      onClick={() => setShowFinalResult(true)} 
                      size="lg"
                      sx={{
                        background: 'linear-gradient(135deg, #8E44AD 0%, #7D3C98 100%)',
                        color: '#FFF',
                        fontWeight: 'bold',
                        borderRadius: '12px',
                        boxShadow: '0 4px 15px rgba(142, 68, 173, 0.3)',
                        fontSize: { xs: '0.9rem', sm: '1rem' },
                        px: { xs: 2, sm: 3 },
                        '&:hover': {
                          background: 'linear-gradient(135deg, #7D3C98 0%, #6C3483 100%)',
                          transform: 'translateY(-2px)',
                          boxShadow: '0 6px 20px rgba(142, 68, 173, 0.4)'
                        }
                      }}
                    >
                      🏆 Endergebnis anzeigen
                    </Button>
                  )}
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        )}
        
        {/* Chat Component */}
        <Grid xs={12}>
          <GameChat sessionId={sessionId} websocket={websocket} />
        </Grid>
      </Grid>
    </Box>
  );
};

export default Game;