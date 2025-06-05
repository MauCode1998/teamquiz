import pytest
import asyncio
import requests
import websockets
import json
from datetime import datetime

class TestCompleteGameFlow:
    """Test complete game flow from start to finish with score calculation"""
    
    @pytest.fixture
    def setup_game_with_flashcards(self, server, clean_database):
        """Setup a game session with multiple flashcards for complete testing"""
        timestamp = datetime.now().microsecond
        
        # Create users
        users = []
        for i in range(3):
            user_data = {
                "username": f"player{i}{timestamp}",
                "email": f"player{i}{timestamp}@test.com",
                "password": "testpass123"
            }
            response = requests.post(f"{server}/register", json=user_data)
            assert response.status_code == 200
            token = response.json()["access_token"]
            users.append({"user": user_data, "token": token, "id": i})
        
        # Host creates group and content
        host_token = users[0]["token"]
        headers = {"Authorization": f"Bearer {host_token}"}
        
        group_name = f"GameGroup{timestamp}"
        response = requests.post(
            f"{server}/gruppe-erstellen",
            json={"gruppen_name": group_name},
            headers=headers
        )
        assert response.status_code == 200
        
        subject_name = f"GameSubject{timestamp}"
        response = requests.post(
            f"{server}/fach-erstellen",
            json={"fach_name": subject_name, "gruppen_name": group_name},
            headers=headers
        )
        assert response.status_code == 200
        
        # Create 5 flashcards with known correct answers
        flashcards = [
            {
                "frage": "What is 2+2?",
                "antworten": [
                    {"text": "3", "is_correct": False},
                    {"text": "4", "is_correct": True},  # Correct
                    {"text": "5", "is_correct": False},
                    {"text": "6", "is_correct": False}
                ],
                "correct_index": 1
            },
            {
                "frage": "Capital of France?",
                "antworten": [
                    {"text": "London", "is_correct": False},
                    {"text": "Berlin", "is_correct": False}, 
                    {"text": "Paris", "is_correct": True},  # Correct
                    {"text": "Madrid", "is_correct": False}
                ],
                "correct_index": 2
            },
            {
                "frage": "Largest planet?",
                "antworten": [
                    {"text": "Earth", "is_correct": False},
                    {"text": "Jupiter", "is_correct": True},  # Correct
                    {"text": "Mars", "is_correct": False},
                    {"text": "Venus", "is_correct": False}
                ],
                "correct_index": 1
            },
            {
                "frage": "HTML stands for?",
                "antworten": [
                    {"text": "HyperText Markup Language", "is_correct": True},  # Correct
                    {"text": "Home Tool Markup Language", "is_correct": False},
                    {"text": "Hyperlinks Text Mark Language", "is_correct": False},
                    {"text": "Hyperlinking Text Marking Language", "is_correct": False}
                ],
                "correct_index": 0
            },
            {
                "frage": "Python creator?",
                "antworten": [
                    {"text": "James Gosling", "is_correct": False},
                    {"text": "Brendan Eich", "is_correct": False},
                    {"text": "Guido van Rossum", "is_correct": True},  # Correct
                    {"text": "Dennis Ritchie", "is_correct": False}
                ],
                "correct_index": 2
            }
        ]
        
        for flashcard in flashcards:
            response = requests.post(
                f"{server}/flashcard/create",
                json={
                    "frage": flashcard["frage"],
                    "antworten": flashcard["antworten"],
                    "fach": subject_name,
                    "gruppe": group_name
                },
                headers=headers
            )
            assert response.status_code == 200
        
        # Create lobby
        response = requests.post(
            f"{server}/api/lobby/create",
            json={"subject_name": subject_name, "group_name": group_name},
            headers=headers
        )
        assert response.status_code == 200
        session_id = response.json()["session"]["id"]
        join_code = response.json()["session"]["join_code"]
        
        # Other users join
        for user in users[1:]:
            user_headers = {"Authorization": f"Bearer {user['token']}"}
            response = requests.post(
                f"{server}/api/lobby/join",
                json={"join_code": join_code},
                headers=user_headers
            )
            assert response.status_code == 200
        
        # Start game
        response = requests.post(f"{server}/api/lobby/{session_id}/start", headers=headers)
        assert response.status_code == 200
        
        return {
            "session_id": session_id,
            "users": users,
            "server": server,
            "ws_url": server.replace("http://", "ws://"),
            "flashcards": flashcards,
            "expected_max_score": len(flashcards) * 100,  # 500 points
            "target_score": int(len(flashcards) * 100 * 0.9)  # 450 points (90%)
        }
    
    def test_complete_winning_game(self, setup_game_with_flashcards):
        """Test a complete game where team wins by achieving 90%+ score"""
        print("\n🏆 TEST: Complete winning game flow")
        
        session_id = setup_game_with_flashcards["session_id"]
        users = setup_game_with_flashcards["users"]
        server = setup_game_with_flashcards["server"]
        ws_url = setup_game_with_flashcards["ws_url"]
        flashcards = setup_game_with_flashcards["flashcards"]
        target_score = setup_game_with_flashcards["target_score"]
        
        print(f"📊 Target score: {target_score} points (90% of {setup_game_with_flashcards['expected_max_score']})")
        
        async def play_complete_game():
            # Connect all users
            websockets_list = []
            host_headers = {"Authorization": f"Bearer {users[0]['token']}"}
            
            # Connect players
            for i, user in enumerate(users):
                ws = await websockets.connect(f"{ws_url}/ws/{user['token']}")
                await ws.send(json.dumps({
                    "type": "join_game",
                    "session_id": session_id
                }))
                
                response = await ws.recv()
                message = json.loads(response)
                assert message["type"] == "game_joined"
                websockets_list.append(ws)
            
            # Start the actual game
            response = requests.post(f"{server}/api/game/start/{session_id}", headers=host_headers)
            assert response.status_code == 200
            print("✅ Game started")
            
            # Wait for first question
            game_started_message = None
            for ws in websockets_list:
                response = await ws.recv()
                message = json.loads(response)
                assert message["type"] == "game_started"
                if game_started_message is None:
                    game_started_message = message
                print(f"📝 First question: {message['question']['question']}")
            
            current_score = 0
            questions_answered = 0
            
            # Store current question data from WebSocket message
            current_question_data = game_started_message["question"]
            
            # Play through all questions
            for question_num in range(len(flashcards)):
                print(f"\n📍 Question {question_num + 1}/5")
                
                # Use question data from WebSocket message
                flashcard_id = current_question_data["flashcard_id"]
                
                # Team votes for correct answer (find by matching question and correct answer text)
                # Map questions to known correct answers
                question_text = current_question_data["question"]
                correct_answer_text = None
                
                if "2+2" in question_text:
                    correct_answer_text = "4"
                elif "France" in question_text:
                    correct_answer_text = "Paris"
                elif "planet" in question_text:
                    correct_answer_text = "Jupiter"
                elif "HTML" in question_text:
                    correct_answer_text = "HyperText Markup Language"
                elif "Python" in question_text:
                    correct_answer_text = "Guido van Rossum"
                
                assert correct_answer_text is not None, f"Unknown question: {question_text}"
                
                correct_answer_id = None
                for answer in current_question_data["answers"]:
                    if answer["text"] == correct_answer_text:
                        correct_answer_id = answer["id"]
                        break
                
                assert correct_answer_id is not None, f"Could not find correct answer '{correct_answer_text}'"
                print(f"  Team voting for correct answer: {correct_answer_text}")
                
                # All players vote for correct answer
                for user in users:
                    headers = {"Authorization": f"Bearer {user['token']}"}
                    response = requests.post(
                        f"{server}/api/game/vote",
                        json={
                            "session_id": session_id,
                            "flashcard_id": flashcard_id,
                            "answer_id": correct_answer_id
                        },
                        headers=headers
                    )
                    assert response.status_code == 200
                
                # Move to next question or end if last question
                if question_num < len(flashcards) - 1:
                    # Not the last question - use next-question which ends current and moves to next
                    response = requests.post(f"{server}/api/game/next-question/{session_id}", headers=host_headers)
                    assert response.status_code == 200
                else:
                    # Last question - just end it
                    response = requests.post(f"{server}/api/game/end-question/{session_id}", headers=host_headers)
                    assert response.status_code == 200
                
                # Wait for question result (might get vote_update first)
                question_ended = None
                for ws in websockets_list:
                    while True:
                        response = await ws.recv()
                        message = json.loads(response)
                        if message["type"] == "question_ended":
                            question_ended = message
                            break
                        elif message["type"] == "vote_update":
                            continue  # Skip vote updates
                        else:
                            print(f"  Unexpected message: {message['type']}")
                    
                    result = question_ended["result"]
                    
                    # Should be correct since we voted for correct answer
                    assert result["was_correct"] == True
                    current_score += 100
                    questions_answered += 1
                    
                    print(f"  ✅ Correct! Score: {current_score}/{questions_answered * 100}")
                    break  # Only need to process one WebSocket message
                
                # If not last question, wait for next_question message
                if question_num < len(flashcards) - 1:
                    
                    # Wait for next question broadcast (might get other messages first)
                    for ws in websockets_list:
                        while True:
                            response = await ws.recv()
                            message = json.loads(response)
                            if message["type"] in ["next_question", "new_question"]:
                                current_question_data = message["question"]  # Update question data
                                print(f"📝 Next question: {message['question']['question']}")
                                break
                            else:
                                print(f"  Received {message['type']}, waiting for next_question...")
                                continue
                        break  # Only need to process one WebSocket message
            
            # Game should end with victory
            print("\n📍 Checking final game result...")
            response = requests.get(f"{server}/api/game/result/{session_id}", headers=host_headers)
            assert response.status_code == 200
            final_result = response.json()
            
            print(f"🎉 Final Score: {final_result['final_score']}/{final_result['max_possible_score']}")
            print(f"🎯 Target Score: {final_result['target_score']}")
            print(f"🏆 Victory: {final_result['victory']}")
            
            # Verify win condition
            assert final_result["final_score"] == 500  # All correct = 500 points
            assert final_result["target_score"] == target_score  # 450 points
            assert final_result["victory"] == True  # Should win with 500 >= 450
            assert final_result["questions_total"] == 5
            assert final_result["questions_correct"] == 5
            
            # Close connections
            for ws in websockets_list:
                await ws.close()
            
            return final_result
        
        # Run the complete game
        result = asyncio.run(play_complete_game())
        print(f"\n🎉 Complete winning game test PASSED! Final score: {result['final_score']}")
    
    def test_losing_game_insufficient_score(self, setup_game_with_flashcards):
        """Test a complete game where team loses by not achieving 90% score"""
        print("\n💔 TEST: Losing game - insufficient score")
        
        session_id = setup_game_with_flashcards["session_id"]
        users = setup_game_with_flashcards["users"]
        server = setup_game_with_flashcards["server"]
        ws_url = setup_game_with_flashcards["ws_url"]
        target_score = setup_game_with_flashcards["target_score"]
        
        print(f"📊 Target score: {target_score} points - Testing early termination when 90% becomes impossible")
        
        async def play_losing_game():
            # Connect all users
            websockets_list = []
            host_headers = {"Authorization": f"Bearer {users[0]['token']}"}
            
            # Connect players
            for i, user in enumerate(users):
                ws = await websockets.connect(f"{ws_url}/ws/{user['token']}")
                await ws.send(json.dumps({
                    "type": "join_game",
                    "session_id": session_id
                }))
                
                response = await ws.recv()
                message = json.loads(response)
                assert message["type"] == "game_joined"
                websockets_list.append(ws)
            
            # Start the actual game
            response = requests.post(f"{server}/api/game/start/{session_id}", headers=host_headers)
            assert response.status_code == 200
            
            # Wait for first question
            game_started_message = None
            for ws in websockets_list:
                response = await ws.recv()
                message = json.loads(response)
                assert message["type"] == "game_started"
                if game_started_message is None:
                    game_started_message = message
            
            current_score = 0
            
            # Store current question data from WebSocket message
            current_question_data = game_started_message["question"]
            
            # Play through 5 questions - get first 3 correct, last 2 wrong
            for question_num in range(5):
                print(f"\n📍 Question {question_num + 1}/5")
                
                # Use question data from WebSocket message
                flashcard_id = current_question_data["flashcard_id"]
                
                # Choose answer based on strategy (correct for first 3, wrong for last 2)
                question_text = current_question_data["question"]
                print(f"  📝 Question: '{question_text}'")
                print(f"  📋 Available answers: {[a['text'] for a in current_question_data['answers']]}")
                
                target_answer_id = None
                
                # Strategy: Answer first few questions wrong to trigger early termination
                # Target: Get 0 points so that after 2-3 questions, 90% becomes impossible
                
                if question_num < 2:  # First 2 questions - vote incorrectly to get 0 points
                    # Just pick the first answer (likely wrong)
                    target_answer_id = current_question_data["answers"][0]["id"]
                    print(f"  Team voting INCORRECTLY for: {current_question_data['answers'][0]['text']}")
                else:  # If game continues, vote correctly  
                    # Try each answer until we find one that works
                    target_answer_id = current_question_data["answers"][1]["id"]  # Pick second answer
                    print(f"  Team voting for: {current_question_data['answers'][1]['text']}")
                
                assert target_answer_id is not None
                
                # All players vote for chosen answer
                for user in users:
                    headers = {"Authorization": f"Bearer {user['token']}"}
                    response = requests.post(
                        f"{server}/api/game/vote",
                        json={
                            "session_id": session_id,
                            "flashcard_id": flashcard_id,
                            "answer_id": target_answer_id
                        },
                        headers=headers
                    )
                    assert response.status_code == 200
                
                # Move to next question or end if last question
                if question_num < 4:
                    # Not the last question - use next-question which ends current and moves to next
                    response = requests.post(f"{server}/api/game/next-question/{session_id}", headers=host_headers)
                    assert response.status_code == 200
                else:
                    # Last question - just end it
                    response = requests.post(f"{server}/api/game/end-question/{session_id}", headers=host_headers)
                    assert response.status_code == 200
                
                # Wait for question result (might get vote_update first)
                question_ended = None
                for ws in websockets_list:
                    while True:
                        response = await ws.recv()
                        message = json.loads(response)
                        if message["type"] == "question_ended":
                            question_ended = message
                            break
                        elif message["type"] == "vote_update":
                            continue  # Skip vote updates
                        else:
                            print(f"  Unexpected message: {message['type']}")
                    
                    result = question_ended["result"]
                    
                    if question_num < 2:
                        # Expecting wrong answers for first 2 questions
                        if result["was_correct"]:
                            current_score += 100
                            print(f"  ✅ Unexpected correct! Score: {current_score}")
                        else:
                            print(f"  ❌ Wrong as expected! Score stays: {current_score}")
                    else:
                        # For later questions, just track the result  
                        if result["was_correct"]:
                            current_score += 100
                            print(f"  ✅ Correct! Score: {current_score}")
                        else:
                            print(f"  ❌ Wrong! Score stays: {current_score}")
                    break  # Only need to process one WebSocket message
                
                # Try to continue to next question (might trigger early termination)
                if question_num < 4:
                    response = requests.post(f"{server}/api/game/next-question/{session_id}", headers=host_headers)
                    
                    if response.status_code == 200:
                        # Game continues - wait for next question
                        for ws in websockets_list:
                            while True:
                                response = await ws.recv()
                                message = json.loads(response)
                                if message["type"] in ["next_question", "new_question"]:
                                    current_question_data = message["question"]  # Update question data
                                    print(f"  📝 Next Question: '{message['question']['question']}'")
                                    break
                                elif message["type"] == "game_finished":
                                    print(f"  🛑 Game terminated early after question {question_num + 1}")
                                    # Game ended early due to 90% impossible - check result and return it
                                    final_result = message["result"]
                                    print(f"💔 Early termination result: {final_result['total_score']}/{final_result['max_possible_score']} - Status: {final_result['status']}")
                                    
                                    # Verify early termination conditions
                                    assert final_result["status"] == "lost", f"Should lose when 90% impossible, got {final_result['status']}"
                                    assert final_result["total_score"] < target_score, f"Should have low score, got {final_result['total_score']}"
                                    
                                    # Close connections and return result
                                    for ws_close in websockets_list:
                                        await ws_close.close()
                                    return final_result
                                else:
                                    print(f"  Received {message['type']}, waiting for next_question...")
                                    continue
                            break  # Only need to process one WebSocket message
                    else:
                        # Early termination - game ended via API
                        print(f"  🛑 Game terminated early after question {question_num + 1} (API returned {response.status_code})")
                        # Get final result from API
                        result_response = requests.get(f"{server}/api/game/result/{session_id}", headers=host_headers)
                        if result_response.status_code == 200:
                            final_result = result_response.json()
                            print(f"💔 Early termination result: {final_result['final_score']}/{final_result['max_possible_score']} - Status: {final_result['victory']}")
                            
                            # Verify early termination conditions
                            assert final_result["victory"] == False, f"Should lose when 90% impossible, got {final_result['victory']}"
                            assert final_result["final_score"] < target_score, f"Should have low score, got {final_result['final_score']}"
                            
                            # Close connections and return result
                            for ws_close in websockets_list:
                                await ws_close.close()
                            return final_result
                        break
            
            # Game should end with loss
            print("\n📍 Checking final game result...")
            response = requests.get(f"{server}/api/game/result/{session_id}", headers=host_headers)
            assert response.status_code == 200
            final_result = response.json()
            
            print(f"💔 Final Score: {final_result['final_score']}/{final_result['max_possible_score']}")
            print(f"🎯 Target Score: {final_result['target_score']}")
            print(f"😢 Victory: {final_result['victory']}")
            
            # Verify loss condition (if game didn't terminate early)
            assert final_result["victory"] == False, f"Should lose, got victory = {final_result['victory']}"
            assert final_result["final_score"] < target_score, f"Should lose with {final_result['final_score']} < {target_score}"
            print(f"💔 Game completed with loss: {final_result['final_score']}/{final_result['max_possible_score']}")
            
            # Close connections
            for ws in websockets_list:
                await ws.close()
            
            return final_result
        
        # Run the losing game
        result = asyncio.run(play_losing_game())
        final_score = result.get('final_score', result.get('total_score', 0))
        print(f"\n😢 Losing game test PASSED! Final score: {final_score} < {target_score}")