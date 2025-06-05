import pytest
import asyncio
import requests
import websockets
import json
from datetime import datetime

class TestWebSocketVoting:
    """Test real-time voting functionality with multiple WebSocket connections"""
    
    @pytest.fixture
    def setup_game_session(self, server, clean_database):
        """Setup a game session ready for voting"""
        timestamp = datetime.now().microsecond
        
        # Create users
        users = []
        for i in range(3):
            user_data = {
                "username": f"voter{i}{timestamp}",
                "email": f"voter{i}{timestamp}@test.com",
                "password": "testpass123"
            }
            response = requests.post(f"{server}/register", json=user_data)
            assert response.status_code == 200
            token = response.json()["access_token"]
            users.append({"user": user_data, "token": token, "id": i})
        
        # Host creates group and content
        host_token = users[0]["token"]
        headers = {"Authorization": f"Bearer {host_token}"}
        
        group_name = f"VoteGroup{timestamp}"
        response = requests.post(
            f"{server}/gruppe-erstellen",
            json={"gruppen_name": group_name},
            headers=headers
        )
        
        subject_name = f"VoteSubject{timestamp}"
        response = requests.post(
            f"{server}/fach-erstellen",
            json={"fach_name": subject_name, "gruppen_name": group_name},
            headers=headers
        )
        
        # Create flashcard with correct schema
        response = requests.post(
            f"{server}/flashcard/create",
            json={
                "frage": "What is the capital of France?",
                "antworten": [
                    {"text": "London", "is_correct": False},
                    {"text": "Paris", "is_correct": True},
                    {"text": "Berlin", "is_correct": False},
                    {"text": "Madrid", "is_correct": False}
                ],
                "fach": subject_name,
                "gruppe": group_name
            },
            headers=headers
        )
        
        # Create lobby
        response = requests.post(
            f"{server}/api/lobby/create",
            json={"subject_name": subject_name, "group_name": group_name},
            headers=headers
        )
        assert response.status_code == 200, f"Lobby creation failed: {response.text}"
        session_id = response.json()["session"]["id"]
        join_code = response.json()["session"]["join_code"]
        
        # Other users join
        for user in users[1:]:
            user_headers = {"Authorization": f"Bearer {user['token']}"}
            requests.post(
                f"{server}/api/lobby/join",
                json={"join_code": join_code},
                headers=user_headers
            )
        
        # Start game
        requests.post(f"{server}/api/lobby/{session_id}/start", headers=headers)
        
        return {
            "session_id": session_id,
            "users": users,
            "server": server,
            "ws_url": server.replace("http://", "ws://")
        }
    
    def test_realtime_voting_updates(self, setup_game_session):
        """Test that votes are broadcast to all players in real-time"""
        print("\n🗳️ TEST: Real-time voting updates")
        
        session_id = setup_game_session["session_id"]
        users = setup_game_session["users"]
        server = setup_game_session["server"]
        ws_url = setup_game_session["ws_url"]
        
        async def voting_scenario():
            # Connect all users
            websockets_list = []
            
            print("📍 Connecting all players...")
            for i, user in enumerate(users):
                ws = await websockets.connect(f"{ws_url}/ws/{user['token']}")
                await ws.send(json.dumps({
                    "type": "join_game",
                    "session_id": session_id
                }))
                # Wait for game_joined
                await ws.recv()
                websockets_list.append(ws)
                print(f"✅ Player {i+1} connected")
            
            # Start the game
            print("\n📍 Starting game...")
            host_headers = {"Authorization": f"Bearer {users[0]['token']}"}
            response = requests.post(
                f"{server}/api/game/start/{session_id}",
                headers=host_headers
            )
            
            # All should receive game_started
            print("\n📍 Waiting for game_started broadcast...")
            for i, ws in enumerate(websockets_list):
                msg = await ws.recv()
                data = json.loads(msg)
                assert data["type"] == "game_started"
                print(f"✅ Player {i+1} received game_started")
            
            # Get question details from game_started message
            question_data = json.loads(msg)["question"]
            flashcard_id = question_data["flashcard_id"]
            answers = question_data["answers"]
            
            print(f"\n📍 Question: {question_data['question']}")
            print(f"   Answers: {[a['text'] for a in answers]}")
            
            # Simulate voting
            print("\n📍 Players voting...")
            vote_tasks = []
            
            async def cast_vote(user_index, answer_index):
                """Cast a vote and listen for updates"""
                headers = {"Authorization": f"Bearer {users[user_index]['token']}"}
                answer_id = answers[answer_index]["id"]
                
                # Cast vote via API
                response = requests.post(
                    f"{server}/api/game/vote",
                    json={
                        "session_id": session_id,
                        "flashcard_id": flashcard_id,
                        "answer_id": answer_id
                    },
                    headers=headers
                )
                assert response.status_code == 200
                print(f"✅ Player {user_index+1} voted for: {answers[answer_index]['text']}")
                return response
            
            # Players vote simultaneously
            await asyncio.gather(
                cast_vote(0, 1),  # Host votes for Paris (correct)
                cast_vote(1, 1),  # Player 2 votes for Paris
                cast_vote(2, 0),  # Player 3 votes for London (wrong)
            )
            
            # Small delay to ensure all broadcasts are sent
            await asyncio.sleep(0.5)
            
            # Get final vote counts via API to verify
            headers = {"Authorization": f"Bearer {users[0]['token']}"}
            response = requests.get(
                f"{server}/api/game/votes/{session_id}/{flashcard_id}",
                headers=headers
            )
            assert response.status_code == 200
            vote_counts = response.json()["vote_counts"]
            
            print("\n📊 Final vote counts:")
            for answer in answers:
                count = vote_counts.get(str(answer["id"]), 0)
                print(f"   {answer['text']}: {count} votes")
            
            # Verify Paris got 2 votes, London got 1
            paris_id = str(answers[1]["id"])
            london_id = str(answers[0]["id"])
            assert vote_counts[paris_id] == 2
            assert vote_counts[london_id] == 1
            
            print("\n✅ All players received real-time vote updates!")
            
            # Cleanup
            for ws in websockets_list:
                await ws.close()
        
        asyncio.run(voting_scenario())
        print("\n🎉 Real-time voting test PASSED!")
    
    def test_vote_changing(self, setup_game_session):
        """Test that players can change their vote"""
        print("\n🔄 TEST: Vote changing")
        
        session_id = setup_game_session["session_id"]
        user = setup_game_session["users"][0]
        server = setup_game_session["server"]
        ws_url = setup_game_session["ws_url"]
        
        async def vote_change_scenario():
            # Connect user
            ws = await websockets.connect(f"{ws_url}/ws/{user['token']}")
            await ws.send(json.dumps({
                "type": "join_game", 
                "session_id": session_id
            }))
            await ws.recv()  # game_joined
            
            # Start game
            headers = {"Authorization": f"Bearer {user['token']}"}
            requests.post(f"{server}/api/game/start/{session_id}", headers=headers)
            
            # Get game_started
            msg = await ws.recv()
            data = json.loads(msg)
            flashcard_id = data["question"]["flashcard_id"]
            answers = data["question"]["answers"]
            
            print(f"📍 Initial vote for: {answers[0]['text']}")
            
            # Vote for first answer
            response = requests.post(
                f"{server}/api/game/vote",
                json={
                    "session_id": session_id,
                    "flashcard_id": flashcard_id,
                    "answer_id": answers[0]["id"]
                },
                headers=headers
            )
            
            # Get vote update
            vote_update = await ws.recv()
            data = json.loads(vote_update)
            assert data["vote_counts"][str(answers[0]["id"])] == 1
            print("✅ First vote registered")
            
            # Change vote to second answer
            print(f"📍 Changing vote to: {answers[1]['text']}")
            response = requests.post(
                f"{server}/api/game/vote",
                json={
                    "session_id": session_id,
                    "flashcard_id": flashcard_id,
                    "answer_id": answers[1]["id"]
                },
                headers=headers
            )
            
            # Get updated vote counts
            vote_update = await ws.recv()
            data = json.loads(vote_update)
            
            # First answer should have 0 votes, second should have 1
            assert data["vote_counts"].get(str(answers[0]["id"]), 0) == 0
            assert data["vote_counts"][str(answers[1]["id"])] == 1
            print("✅ Vote successfully changed!")
            
            await ws.close()
        
        asyncio.run(vote_change_scenario())
        print("\n🎉 Vote changing test PASSED!")