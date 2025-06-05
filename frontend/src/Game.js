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
  Stack
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
      
      // Update game state
      setGameState(gameData);
      
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
        
        // Only update gameState if we don't have one, or if the API has a higher score
        setGameState(prev => {
          if (!prev) {
            return gameData;
          }
          
          // Preserve higher score (WebSocket updates are more current)
          if ((gameData.total_score || 0) > (prev.total_score || 0)) {
            return { ...prev, ...gameData };
          } else {
            return { ...prev, ...gameData, total_score: prev.total_score };
          }
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

    const ws = new WebSocket(`ws://localhost:8000/ws/${token}`);
    
    ws.onopen = () => {
      console.log('Game WebSocket connected');
      ws.send(JSON.stringify({
        type: 'join_game',
        session_id: sessionId
      }));
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
        
        if (gameState) {
          setGameState(prev => ({
            ...prev,
            total_score: message.result.total_score
          }));
        } else {
          const questionsCompleted = Math.floor(message.result.total_score / 100);
          setGameState({
            total_score: message.result.total_score,
            max_possible_score: message.result.max_possible_score || 200,
            status: 'playing',
            current_question_index: questionsCompleted,
            flashcard_count: (message.result.max_possible_score || 200) / 100,
            current_flashcard_id: message.result.flashcard_id
          });
        }
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
    return ((currentQuestion.question_index + 1) / currentQuestion.total_questions) * 100;
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
      <Box sx={{ p: 4, textAlign: 'center' }}>
        <Typography level="h4">Lade Spiel...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 4 }}>
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
      <Box sx={{ p: 4, maxWidth: 800, margin: '0 auto' }}>
        <Card>
          <CardContent>
            <Typography level="h2" textAlign="center" mb={2}>
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
    return (
      <Box sx={{ p: 4, maxWidth: 800, margin: '0 auto' }}>
        <Card>
          <CardContent textAlign="center">
            <Typography level="h2" mb={2}>
              {gameResult.status === 'won' ? '🎉 Gewonnen!' : '😔 Verloren'}
            </Typography>
            
            <Typography level="h4" mb={2}>
              {gameResult.total_score} / {gameResult.max_possible_score} Punkte
            </Typography>
            
            <Typography level="body1" mb={2}>
              {gameResult.percentage?.toFixed(1)}% richtig
            </Typography>
            
            {gameResult.status === 'won' ? (
              <Typography level="body1" color="success">
                Hervorragend! Ihr habt das Ziel von 90% erreicht! 🎊
              </Typography>
            ) : (
              <Typography level="body1" color="warning">
                Ihr habt verloren, da müsst ihr wohl noch was üben 📚
              </Typography>
            )}
            
            <Button 
              onClick={() => navigate('/groups')} 
              sx={{ mt: 4 }}
              size="lg"
            >
              Zurück zu Gruppen
            </Button>
          </CardContent>
        </Card>
      </Box>
    );
  }

  // Active game
  return (
    <Box sx={{ p: 4, maxWidth: 1000, margin: '0 auto' }}>
      {/* Game Header */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography level="h3">{sessionData?.subject?.name} Quiz</Typography>
          <Typography level="body2">
            Frage {currentQuestion?.question_index + 1} von {currentQuestion?.total_questions}
          </Typography>
          <LinearProgress 
            determinate 
            value={calculateProgress()} 
            sx={{ mt: 1 }}
          />
          <Typography level="h4" sx={{ mt: 2 }}>
            {gameState?.total_score} / {gameState?.max_possible_score} Punkte ({calculateScorePercentage().toFixed(1)}%)
          </Typography>
        </CardContent>
      </Card>

      {/* Current Question */}
      {currentQuestion && !showResult && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography level="h2" textAlign="center" mb={4}>
              {currentQuestion.question}
            </Typography>
            
            <Stack spacing={2}>
              {currentQuestion.answers?.map((answer, index) => {
                const voteCount = voteCounts[answer.id] || 0;
                const totalVotes = Object.values(voteCounts).reduce((sum, count) => sum + count, 0);
                const percentage = totalVotes > 0 ? (voteCount / totalVotes) * 100 : 0;
                
                return (
                  <Card
                    key={answer.id}
                    variant="outlined"
                    sx={{
                      cursor: 'pointer',
                      border: userVote === answer.id ? 2 : 1,
                      borderColor: userVote === answer.id ? 'primary.500' : 'neutral.300'
                    }}
                    onClick={() => !showResult && castVote(answer.id)}
                  >
                    <CardContent>
                      <Typography level="h4" mb={1}>
                        {String.fromCharCode(65 + index)}: {answer.text}
                      </Typography>
                      
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <Typography level="body2">
                          {voteCount} Stimme{voteCount !== 1 ? 'n' : ''}
                        </Typography>
                        <LinearProgress
                          determinate
                          value={percentage}
                          sx={{ flexGrow: 1 }}
                        />
                        <Typography level="body2">
                          {percentage.toFixed(0)}%
                        </Typography>
                      </Box>
                    </CardContent>
                  </Card>
                );
              })}
            </Stack>
            
            {userVote && (
              <Alert color="primary" sx={{ mt: 2 }}>
                Sie haben gestimmt. Sie können Ihre Stimme jederzeit ändern.
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {/* Question Result */}
      {showResult && questionResult && !gameResult && (
        <Card sx={{ mb: 3 }}>
          <CardContent textAlign="center">
            <Typography level="h2" mb={3}>
              {questionResult.was_correct ? '🎉 Richtig!' : '😞 Falsch!'}
            </Typography>
            
            {/* Show correct answer and team choice */}
            <Box sx={{ mb: 3 }}>
              <Typography level="h4" mb={2}>Richtige Antwort:</Typography>
              {currentQuestion?.answers?.map((answer) => {
                const isCorrect = answer.id === questionResult.correct_answer_id;
                const isTeamChoice = answer.id === questionResult.winning_answer_id;
                
                if (isCorrect) {
                  return (
                    <Card key={answer.id} sx={{ 
                      mb: 1, 
                      bgcolor: 'success.50', 
                      border: '2px solid', 
                      borderColor: 'success.500' 
                    }}>
                      <CardContent>
                        <Typography level="body1" sx={{ fontWeight: 'bold' }}>
                          ✅ {answer.text}
                        </Typography>
                      </CardContent>
                    </Card>
                  );
                }
                return null;
              })}
              
              <Typography level="h4" mb={2} mt={3}>Eure Antwort:</Typography>
              {currentQuestion?.answers?.map((answer) => {
                const isTeamChoice = answer.id === questionResult.winning_answer_id;
                const isCorrect = answer.id === questionResult.correct_answer_id;
                
                if (isTeamChoice) {
                  return (
                    <Card key={answer.id} sx={{ 
                      mb: 1, 
                      bgcolor: isCorrect ? 'success.50' : 'danger.50',
                      border: '2px solid', 
                      borderColor: isCorrect ? 'success.500' : 'danger.500'
                    }}>
                      <CardContent>
                        <Typography level="body1" sx={{ fontWeight: 'bold' }}>
                          {isCorrect ? '✅' : '❌'} {answer.text}
                        </Typography>
                      </CardContent>
                    </Card>
                  );
                }
                return null;
              })}
            </Box>
            
            <Typography level="h4" mb={2}>
              {questionResult.was_correct ? 
                `+${questionResult.points_earned} Punkte!` : 
                'Keine Punkte'
              }
            </Typography>
            
            <Typography level="body2">
              Aktuelle Punktzahl: {questionResult.total_score} / {gameState?.max_possible_score}
            </Typography>
          </CardContent>
        </Card>
      )}

      {/* Host Controls - ALWAYS VISIBLE */}
      {isHost && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography level="h4" mb={2}>Host-Steuerung</Typography>
            <Stack direction="row" spacing={2}>
              {/* Always show all buttons */}
              <Button onClick={endQuestion} color="primary" size="lg">
                Voting beenden
              </Button>
              
              <Button onClick={nextQuestion} color="success" size="lg" disabled={!showResult}>
                Nächste Frage
              </Button>
              
              <Button onClick={endGame} color="warning" size="lg" disabled={!showResult}>
                Spiel beenden
              </Button>
              
              {gameResult && (
                <Button onClick={() => setShowFinalResult(true)} color="warning" size="lg">
                  Endergebnis anzeigen
                </Button>
              )}
            </Stack>
          </CardContent>
        </Card>
      )}
      
      {/* Chat Component */}
      <GameChat sessionId={sessionId} websocket={websocket} />
    </Box>
  );
};

export default Game;