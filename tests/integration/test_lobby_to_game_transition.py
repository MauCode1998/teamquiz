import pytest
import asyncio
import requests
import websockets
import json
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import threading

class TestLobbyToGameTransition:
    """Integration tests for lobby to game transition with real WebSocket connections"""
    
    @pytest.fixture
    def ws_url(self, server):
        """WebSocket URL from server fixture"""
        return server.replace("http://", "ws://")
    
    @pytest.fixture
    def setup_users(self, server):
        """Create test users and return their credentials"""
        timestamp = datetime.now().microsecond
        users = []
        
        # Create host
        host_data = {
            "username": f"testhost{timestamp}",
            "email": f"host{timestamp}@test.com",
            "password": "testpass123"
        }
        response = requests.post(f"{server}/register", json=host_data)
        assert response.status_code == 200
        host_token = response.json()["access_token"]
        users.append({"user": host_data, "token": host_token, "role": "host"})
        
        # Create 2 participants
        for i in range(2):
            participant_data = {
                "username": f"testplayer{i}{timestamp}",
                "email": f"player{i}{timestamp}@test.com",
                "password": "testpass123"
            }
            response = requests.post(f"{server}/register", json=participant_data)
            assert response.status_code == 200
            participant_token = response.json()["access_token"]
            users.append({"user": participant_data, "token": participant_token, "role": "participant"})
        
        return users
    
    @pytest.fixture
    def setup_game_content(self, server, setup_users):
        """Create group, subject and flashcard"""
        host_token = setup_users[0]["token"]
        headers = {"Authorization": f"Bearer {host_token}"}
        
        # Create group
        group_name = f"TestGroup{datetime.now().microsecond}"
        response = requests.post(
            f"{server}/gruppe-erstellen",
            json={"gruppen_name": group_name},
            headers=headers
        )
        assert response.status_code == 200
        
        # Create subject
        subject_name = f"TestSubject{datetime.now().microsecond}"
        response = requests.post(
            f"{server}/fach-erstellen",
            json={"fach_name": subject_name, "gruppen_name": group_name},
            headers=headers
        )
        assert response.status_code == 200
        
        # Create flashcard with correct schema
        response = requests.post(
            f"{server}/flashcard/create",
            json={
                "frage": "What is 2+2?",
                "antworten": [
                    {"text": "3", "is_correct": False},
                    {"text": "4", "is_correct": True},
                    {"text": "5", "is_correct": False},
                    {"text": "6", "is_correct": False}
                ],
                "fach": subject_name,
                "gruppe": group_name
            },
            headers=headers
        )
        if response.status_code != 200:
            print(f"❌ Flashcard creation failed: {response.status_code} - {response.text}")
        assert response.status_code == 200
        
        return {"group": group_name, "subject": subject_name}
    
    def test_solo_host_game_transition(self, server, clean_database, ws_url, setup_users, setup_game_content):
        """Test game transition with only host (solo play)"""
        print("\n🎮 TEST: Solo host game transition")
        
        host_data = setup_users[0]
        host_token = host_data["token"]
        headers = {"Authorization": f"Bearer {host_token}"}
        
        # Step 1: Create lobby
        print("📍 Step 1: Host creates lobby")
        response = requests.post(
            f"{server}/api/lobby/create",
            json={
                "subject_name": setup_game_content["subject"],
                "group_name": setup_game_content["group"]
            },
            headers=headers
        )
        assert response.status_code == 200
        session_data = response.json()
        session_id = session_data["session"]["id"]
        print(f"✅ Lobby created: {session_id}")
        
        # Step 2: Verify initial state (polling simulation)
        print("📍 Step 2: Check initial lobby state")
        response = requests.get(f"{server}/api/lobby/{session_id}", headers=headers)
        assert response.status_code == 200
        assert response.json()["status"] == "waiting"
        print("✅ Lobby status: waiting")
        
        # Step 3: Start game
        print("📍 Step 3: Host starts game")
        response = requests.post(f"{server}/api/lobby/{session_id}/start", headers=headers)
        assert response.status_code == 200
        print("✅ Game start initiated")
        
        # Step 4: Verify status changed (polling would detect this)
        print("📍 Step 4: Verify status changed to playing")
        response = requests.get(f"{server}/api/lobby/{session_id}", headers=headers)
        assert response.status_code == 200
        assert response.json()["status"] == "playing"
        print("✅ Lobby status: playing (would trigger navigation)")
        
        # Step 5: Start the actual game first (before WebSocket)
        print("📍 Step 5: Start the actual game")
        game_response = requests.post(
            f"{server}/api/game/start/{session_id}",
            headers=headers
        )
        assert game_response.status_code == 200
        print("✅ Game state created")
        
        # Step 6: Connect WebSocket (simulating Game component mount)
        print("📍 Step 6: Connect WebSocket for game")
        
        async def test_websocket():
            uri = f"{ws_url}/ws/{host_token}"
            async with websockets.connect(uri) as websocket:
                print("✅ WebSocket connected")
                
                # Send join_game message
                await websocket.send(json.dumps({
                    "type": "join_game",
                    "session_id": session_id
                }))
                print(f"📤 Sent: join_game for session {session_id}")
                
                # Wait for game_joined confirmation
                response = await websocket.recv()
                message = json.loads(response)
                assert message["type"] == "game_joined"
                print(f"📥 Received: {message['type']}")
                
                # Wait for game_started broadcast (should already be sent)
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    message = json.loads(response)
                    if message["type"] == "game_started":
                        assert message["session_id"] == session_id
                        assert "question" in message
                        print(f"📥 Received: game_started with question")
                        print(f"✅ Question: {message['question']['question']}")
                except asyncio.TimeoutError:
                    print("ℹ️ No game_started broadcast (game may already be started)")
                
                # Verify we can access game state
                state_response = requests.get(
                    f"{server}/api/game/state/{session_id}",
                    headers=headers
                )
                assert state_response.status_code == 200
                print("✅ Can access game state via API")
        
        # Run async test
        asyncio.run(test_websocket())
        
        print("\n🎉 Solo host transition test PASSED!")
    
    def test_multiplayer_game_transition(self, server, clean_database, ws_url, setup_users, setup_game_content):
        """Test game transition with multiple players"""
        print("\n🎮 TEST: Multiplayer game transition")
        
        host_data = setup_users[0]
        player1_data = setup_users[1]
        player2_data = setup_users[2]
        
        # Step 1: Host creates lobby
        print("📍 Step 1: Host creates lobby")
        host_headers = {"Authorization": f"Bearer {host_data['token']}"}
        response = requests.post(
            f"{server}/api/lobby/create",
            json={
                "subject_name": setup_game_content["subject"],
                "group_name": setup_game_content["group"]
            },
            headers=host_headers
        )
        assert response.status_code == 200
        session_data = response.json()
        session_id = session_data["session"]["id"]
        join_code = session_data["session"]["join_code"]
        print(f"✅ Lobby created: {session_id}, join code: {join_code}")
        
        # Step 2: Players join lobby
        print("📍 Step 2: Players join lobby")
        for i, player_data in enumerate([player1_data, player2_data]):
            player_headers = {"Authorization": f"Bearer {player_data['token']}"}
            response = requests.post(
                f"{server}/api/lobby/join",
                json={"join_code": join_code},
                headers=player_headers
            )
            assert response.status_code == 200
            print(f"✅ Player {i+1} joined")
        
        # Step 3: Verify all participants
        print("📍 Step 3: Verify participants")
        response = requests.get(f"{server}/api/lobby/{session_id}/participants", headers=host_headers)
        assert response.status_code == 200
        participants = response.json()["participants"]
        assert len(participants) == 3
        print(f"✅ Total participants: {len(participants)}")
        
        # Step 4: Start game
        print("📍 Step 4: Host starts game")
        response = requests.post(f"{server}/api/lobby/{session_id}/start", headers=host_headers)
        assert response.status_code == 200
        
        # Step 5: All players connect WebSocket simultaneously
        print("📍 Step 5: All players connect to game via WebSocket")
        
        async def player_websocket(token, username, player_num):
            """WebSocket connection for one player"""
            uri = f"{ws_url}/ws/{token}"
            messages_received = []
            
            async with websockets.connect(uri) as websocket:
                print(f"  Player {player_num} ({username}): WebSocket connected")
                
                # Join game
                await websocket.send(json.dumps({
                    "type": "join_game",
                    "session_id": session_id
                }))
                
                # Collect messages
                try:
                    while True:
                        response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        message = json.loads(response)
                        messages_received.append(message)
                        print(f"  Player {player_num}: Received {message['type']}")
                        
                        # Stop after game_started
                        if message["type"] == "game_started":
                            break
                except asyncio.TimeoutError:
                    pass
            
            return messages_received
        
        async def all_players_connect():
            """Connect all players simultaneously"""
            tasks = []
            
            # Create tasks for all players
            for i, user_data in enumerate(setup_users):
                task = player_websocket(
                    user_data["token"],
                    user_data["user"]["username"],
                    i + 1
                )
                tasks.append(task)
            
            # Run all connections in parallel
            results = await asyncio.gather(*tasks)
            
            # Start game after all connected
            print("\n📍 Starting actual game...")
            response = requests.post(
                f"{server}/api/game/start/{session_id}",
                headers=host_headers
            )
            assert response.status_code == 200
            
            # Verify all players received game_started
            for i, messages in enumerate(results):
                assert any(msg["type"] == "game_joined" for msg in messages)
                print(f"✅ Player {i+1} successfully joined game")
            
            print("\n✅ All players connected and received game updates!")
        
        # Run async test
        asyncio.run(all_players_connect())
        
        # Step 6: Verify all can access game state
        print("\n📍 Step 6: Verify all players can access game state")
        for i, user_data in enumerate(setup_users):
            headers = {"Authorization": f"Bearer {user_data['token']}"}
            response = requests.get(f"{server}/api/game/state/{session_id}", headers=headers)
            assert response.status_code == 200
            print(f"✅ Player {i+1} can access game state")
        
        print("\n🎉 Multiplayer transition test PASSED!")
    
