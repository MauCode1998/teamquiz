"""
Integration tests for multi-question scoring system.
Tests the complete flow of answering multiple questions and verifying correct point calculation.
"""
import pytest
import requests
import json
import asyncio
import websockets
from datetime import datetime


class TestMultiQuestionScoring:
    """Test multi-question scenarios with correct scoring"""
    
    @pytest.fixture
    def setup_two_question_game(self, server, clean_database):
        """Setup a game with exactly 2 flashcards for scoring tests"""
        timestamp = datetime.now().microsecond
        
        # Create user
        user_data = {
            "username": f"scorer{timestamp}",
            "email": f"scorer{timestamp}@test.com", 
            "password": "testpass123"
        }
        response = requests.post(f"{server}/register", json=user_data)
        assert response.status_code == 200
        token = response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create group and subject
        group_name = f"ScoreTestGroup{timestamp}"
        response = requests.post(
            f"{server}/gruppe-erstellen",
            json={"gruppen_name": group_name},
            headers=headers
        )
        assert response.status_code == 200
        
        subject_name = f"ScoreTestSubject{timestamp}"
        response = requests.post(
            f"{server}/fach-erstellen", 
            json={"fach_name": subject_name, "gruppen_name": group_name},
            headers=headers
        )
        assert response.status_code == 200
        
        # Create 2 flashcards 
        flashcard1_data = {
            "frage": "What is 2+2?",
            "antworten": [
                {"text": "4", "is_correct": True},   # Correct
                {"text": "5", "is_correct": False},  # Wrong
                {"text": "6", "is_correct": False},  # Wrong
                {"text": "7", "is_correct": False}   # Wrong
            ],
            "fach": subject_name,
            "gruppe": group_name
        }
        response = requests.post(f"{server}/flashcard/create", json=flashcard1_data, headers=headers)
        assert response.status_code == 200
        
        flashcard2_data = {
            "frage": "What is 3+3?",
            "antworten": [
                {"text": "5", "is_correct": False},  # Wrong
                {"text": "6", "is_correct": True},   # Correct
                {"text": "7", "is_correct": False},  # Wrong
                {"text": "8", "is_correct": False}   # Wrong
            ],
            "fach": subject_name,
            "gruppe": group_name
        }
        response = requests.post(f"{server}/flashcard/create", json=flashcard2_data, headers=headers)
        assert response.status_code == 200
        
        return {
            "user": user_data,
            "token": token,
            "headers": headers,
            "group_name": group_name,
            "subject_name": subject_name
        }

    def test_two_questions_correct_scoring(self, server, setup_two_question_game):
        """Test that answering 2 questions correctly results in correct score calculation"""
        setup = setup_two_question_game
        headers = setup["headers"]
        token = setup["token"]
        group_name = setup["group_name"]
        subject_name = setup["subject_name"]
        
        # Create lobby session
        response = requests.post(f"{server}/api/lobby/create", json={
            "subject_name": subject_name,
            "group_name": group_name
        }, headers=headers)
        assert response.status_code == 200
        session_data = response.json()
        session_id = session_data["session"]["id"]
        
        print(f"\n🎯 Testing multi-question scoring with session {session_id}")
        
        async def run_multi_question_test():
            # Connect WebSocket
            ws_url = server.replace("http://", "ws://")
            ws = await websockets.connect(f"{ws_url}/ws/{token}")
            
            # Join game
            await ws.send(json.dumps({
                "type": "join_game",
                "session_id": session_id
            }))
            await ws.recv()  # game_joined
            
            # Start game
            print("🎮 Starting game...")
            response = requests.post(f"{server}/api/game/start/{session_id}", headers=headers)
            assert response.status_code == 200
            
            # Receive game_started message
            msg = await ws.recv()
            game_started = json.loads(msg)
            assert game_started["type"] == "game_started"
            
            question1 = game_started["question"]
            game_state = game_started["game_state"]
            
            print(f"📊 Initial game state: {game_state['total_score']}/{game_state['max_possible_score']} points")
            print(f"❓ Question 1: {question1['question']}")
            
            # Expected: max_possible_score should be 200 (2 questions * 100 points each)
            assert game_state["max_possible_score"] == 200, f"Max possible score should be 200, got {game_state['max_possible_score']}"
            assert game_state["total_score"] == 0, f"Initial score should be 0, got {game_state['total_score']}"
            
            # QUESTION 1: Answer correctly (2+2=4, which is answer 1)
            answers1 = question1["answers"]
            flashcard1_id = question1["flashcard_id"]
            
            correct_answer1_id = None
            for answer in answers1:
                if answer["text"] == "4":
                    correct_answer1_id = answer["id"]
                    break
            
            assert correct_answer1_id is not None, "Could not find correct answer '4'"
            
            # Vote for correct answer
            print(f"✅ Voting for correct answer: 4 (ID: {correct_answer1_id})")
            response = requests.post(f"{server}/api/game/vote", json={
                "session_id": session_id,
                "flashcard_id": flashcard1_id,
                "answer_id": correct_answer1_id
            }, headers=headers)
            assert response.status_code == 200
            
            # Move to question 2 (this ends Q1 and moves to Q2)
            print("➡️ Moving to question 2...")
            response = requests.post(f"{server}/api/game/next-question/{session_id}", headers=headers)
            assert response.status_code == 200
            
            # Receive question_ended message first (from ending Q1)
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data["type"] == "question_ended":
                    question_ended = data
                    break
                elif data["type"] == "vote_update":
                    print(f"  Received vote_update, waiting for question_ended...")
                    continue
                else:
                    print(f"  Unexpected message: {data['type']}")
            
            result1 = question_ended["result"]
            print(f"📊 After Q1: {result1['total_score']} points, was_correct: {result1['was_correct']}")
            
            # Verify question 1 results
            assert result1["was_correct"] == True, "Question 1 should be correct"
            assert result1["points_earned"] == 100, f"Should earn 100 points, got {result1['points_earned']}"
            assert result1["total_score"] == 100, f"Total score should be 100 after Q1, got {result1['total_score']}"
            
            # Receive next_question message (might get other messages first)
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data["type"] in ["next_question", "new_question"]:
                    question2 = data["question"]
                    break
                else:
                    print(f"  Received {data['type']}, waiting for next_question...")
                    continue
            
            print(f"❓ Question 2: {question2['question']}")
            
            # QUESTION 2: Answer correctly (3+3=6, which is answer 2)
            answers2 = question2["answers"]
            flashcard2_id = question2["flashcard_id"]
            
            correct_answer2_id = None
            for answer in answers2:
                if answer["text"] == "6":
                    correct_answer2_id = answer["id"]
                    break
            
            assert correct_answer2_id is not None, "Could not find correct answer '6'"
            
            # Vote for correct answer
            print(f"✅ Voting for correct answer: 6 (ID: {correct_answer2_id})")
            response = requests.post(f"{server}/api/game/vote", json={
                "session_id": session_id,
                "flashcard_id": flashcard2_id,
                "answer_id": correct_answer2_id
            }, headers=headers)
            assert response.status_code == 200
            
            # End question 2 (since this is the last question, just end it)
            print("🏁 Ending question 2...")
            response = requests.post(f"{server}/api/game/end-question/{session_id}", headers=headers)
            assert response.status_code == 200
            
            # Receive question_ended message (might get vote_update first)
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data["type"] == "question_ended":
                    question_ended = data
                    break
                elif data["type"] == "vote_update":
                    print(f"  Received vote_update, waiting for question_ended...")
                    continue
                else:
                    print(f"  Unexpected message: {data['type']}")
            
            result2 = question_ended["result"]
            print(f"📊 After Q2: {result2['total_score']} points, was_correct: {result2['was_correct']}")
            
            # Verify question 2 results
            assert result2["was_correct"] == True, "Question 2 should be correct"
            assert result2["points_earned"] == 100, f"Should earn 100 points, got {result2['points_earned']}"
            assert result2["total_score"] == 200, f"Total score should be 200 after Q2, got {result2['total_score']}"
            
            # Try to move to next question - should automatically end game since no more questions
            print("🎯 Trying to move to next question - should auto-end game (200/200 = 100% > 90%)...")
            response = requests.post(f"{server}/api/game/next-question/{session_id}", headers=headers)
            assert response.status_code == 200
            
            msg = await ws.recv()
            game_finished = json.loads(msg)
            assert game_finished["type"] == "game_finished"
            
            final_result = game_finished["result"]
            
            # Verify final results - THIS IS WHERE THE BUG SHOULD SHOW UP
            print(f"🔍 FINAL RESULT CHECK:")
            print(f"  - Total score: {final_result['total_score']}")
            print(f"  - Max possible: {final_result['max_possible_score']}")
            print(f"  - Percentage: {final_result.get('percentage', 'Not provided')}%")
            print(f"  - Status: {final_result['status']}")
            
            # Status should be "won" since 200/200 = 100% > 90%
            assert final_result["status"] == "won", f"Should win with 100%, got {final_result['status']}"
            assert final_result["total_score"] == 200, f"Final score should be 200, got {final_result['total_score']}"
            assert final_result["max_possible_score"] == 200, f"Max score should be 200, got {final_result['max_possible_score']}"
            
            # This is the critical test - percentage calculation should be correct
            if "percentage" in final_result:
                percentage = final_result["percentage"]
                assert abs(percentage - 100.0) < 0.1, f"Percentage should be 100%, got {percentage}% - THIS IS THE BUG!"
            
            await ws.close()
            print("✅ Multi-question scoring test completed!")
        
        # Run the async test
        asyncio.run(run_multi_question_test())