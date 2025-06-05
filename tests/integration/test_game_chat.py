import pytest
import asyncio
import requests
import websockets
import json
from datetime import datetime

class TestGameChat:
    """Test real-time chat functionality during game sessions"""
    
    @pytest.fixture
    def setup_game_session(self, server, clean_database):
        """Setup a game session ready for chat testing"""
        timestamp = datetime.now().microsecond
        
        # Create users
        users = []
        for i in range(3):
            user_data = {
                "username": f"chatter{i}{timestamp}",
                "email": f"chatter{i}{timestamp}@test.com",
                "password": "testpass123"
            }
            response = requests.post(f"{server}/register", json=user_data)
            assert response.status_code == 200
            token = response.json()["access_token"]
            users.append({"user": user_data, "token": token, "id": i})
        
        # Host creates group and content
        host_token = users[0]["token"]
        headers = {"Authorization": f"Bearer {host_token}"}
        
        group_name = f"ChatGroup{timestamp}"
        response = requests.post(
            f"{server}/gruppe-erstellen",
            json={"gruppen_name": group_name},
            headers=headers
        )
        assert response.status_code == 200
        
        subject_name = f"ChatSubject{timestamp}"
        response = requests.post(
            f"{server}/fach-erstellen",
            json={"fach_name": subject_name, "gruppen_name": group_name},
            headers=headers
        )
        assert response.status_code == 200
        
        # Create flashcard
        response = requests.post(
            f"{server}/flashcard/create",
            json={
                "frage": "Chat test question?",
                "antworten": [
                    {"text": "Answer A", "is_correct": False},
                    {"text": "Answer B", "is_correct": True},
                    {"text": "Answer C", "is_correct": False},
                    {"text": "Answer D", "is_correct": False}
                ],
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
            "ws_url": server.replace("http://", "ws://")
        }
    
    def test_send_and_receive_chat_messages(self, setup_game_session):
        """Test that chat messages are sent and received correctly"""
        print("\n💬 TEST: Send and receive chat messages")
        
        session_id = setup_game_session["session_id"]
        users = setup_game_session["users"]
        server = setup_game_session["server"]
        ws_url = setup_game_session["ws_url"]
        
        async def chat_scenario():
            # Connect all users to game
            websockets_list = []
            received_messages = {i: [] for i in range(len(users))}
            
            print("📍 Connecting all players to game...")
            for i, user in enumerate(users):
                ws = await websockets.connect(f"{ws_url}/ws/{user['token']}")
                await ws.send(json.dumps({
                    "type": "join_game",
                    "session_id": session_id
                }))
                
                # Wait for join confirmation
                response = await ws.recv()
                message = json.loads(response)
                assert message["type"] == "game_joined"
                print(f"✅ Player {i+1} ({user['user']['username']}) connected")
                
                websockets_list.append(ws)
            
            # Function to listen for messages
            async def listen_for_messages(ws_index, websocket):
                try:
                    while True:
                        response = await asyncio.wait_for(websocket.recv(), timeout=0.5)
                        message = json.loads(response)
                        if message["type"] == "chat_message":
                            received_messages[ws_index].append(message)
                            print(f"📨 Player {ws_index+1} received chat: {message['message']['message']}")
                except asyncio.TimeoutError:
                    pass
            
            # Start listening tasks
            listen_tasks = []
            for i, ws in enumerate(websockets_list):
                task = asyncio.create_task(listen_for_messages(i, ws))
                listen_tasks.append(task)
            
            # Send chat messages via API
            print("\n📍 Sending chat messages...")
            
            # User 0 sends message
            headers = {"Authorization": f"Bearer {users[0]['token']}"}
            response = requests.post(
                f"{server}/api/game/chat",
                json={
                    "session_id": session_id,
                    "message": "Hello everyone! 👋"
                },
                headers=headers
            )
            assert response.status_code == 200
            print(f"✅ {users[0]['user']['username']} sent: 'Hello everyone! 👋'")
            
            await asyncio.sleep(0.3)  # Allow message propagation
            
            # User 1 sends message
            headers = {"Authorization": f"Bearer {users[1]['token']}"}
            response = requests.post(
                f"{server}/api/game/chat",
                json={
                    "session_id": session_id,
                    "message": "Hi there! Ready to play? 🎮"
                },
                headers=headers
            )
            assert response.status_code == 200
            print(f"✅ {users[1]['user']['username']} sent: 'Hi there! Ready to play? 🎮'")
            
            await asyncio.sleep(0.3)  # Allow message propagation
            
            # User 2 sends message
            headers = {"Authorization": f"Bearer {users[2]['token']}"}
            response = requests.post(
                f"{server}/api/game/chat",
                json={
                    "session_id": session_id,
                    "message": "Let's go! 🚀"
                },
                headers=headers
            )
            assert response.status_code == 200
            print(f"✅ {users[2]['user']['username']} sent: 'Let's go! 🚀'")
            
            await asyncio.sleep(0.5)  # Final wait for all messages
            
            # Stop listening
            for task in listen_tasks:
                task.cancel()
            
            # Close connections
            for ws in websockets_list:
                await ws.close()
            
            return received_messages
        
        # Run the chat scenario
        messages = asyncio.run(chat_scenario())
        
        # Verify that all users received all messages
        print("\n📊 Verifying message reception...")
        expected_messages = [
            "Hello everyone! 👋",
            "Hi there! Ready to play? 🎮", 
            "Let's go! 🚀"
        ]
        
        for user_index in range(len(users)):
            user_messages = messages[user_index]
            print(f"Player {user_index+1} received {len(user_messages)} messages")
            
            # Should have received all 3 messages
            assert len(user_messages) == 3, f"Player {user_index+1} should receive 3 messages, got {len(user_messages)}"
            
            # Verify message content and senders
            for i, expected_msg in enumerate(expected_messages):
                received_msg = user_messages[i]["message"]
                assert received_msg["message"] == expected_msg
                assert received_msg["username"] == users[i]["user"]["username"]
                print(f"  ✅ Received: '{received_msg['message']}' from {received_msg['username']}")
        
        print("\n🎉 All chat messages sent and received correctly!")
    
    def test_chat_message_persistence(self, setup_game_session):
        """Test that chat messages are persisted and can be retrieved"""
        print("\n💾 TEST: Chat message persistence")
        
        session_id = setup_game_session["session_id"]
        users = setup_game_session["users"]
        server = setup_game_session["server"]
        
        # Send a few messages
        test_messages = [
            "First message",
            "Second message", 
            "Third message"
        ]
        
        print("📍 Sending messages to persist...")
        for i, message in enumerate(test_messages):
            headers = {"Authorization": f"Bearer {users[i]['token']}"}
            response = requests.post(
                f"{server}/api/game/chat",
                json={
                    "session_id": session_id,
                    "message": message
                },
                headers=headers
            )
            assert response.status_code == 200
            print(f"✅ Sent: '{message}'")
        
        # Retrieve messages via API
        print("\n📍 Retrieving persisted messages...")
        headers = {"Authorization": f"Bearer {users[0]['token']}"}
        response = requests.get(f"{server}/api/game/chat/{session_id}", headers=headers)
        assert response.status_code == 200
        
        messages = response.json()["messages"]
        print(f"✅ Retrieved {len(messages)} messages")
        
        # Verify all messages are there
        assert len(messages) == 3
        for i, message in enumerate(messages):
            assert message["message"] == test_messages[i]
            assert message["username"] == users[i]["user"]["username"]
            assert "sent_at" in message
            print(f"  ✅ Message {i+1}: '{message['message']}' by {message['username']}")
        
        print("\n🎉 Chat persistence test passed!")
    
    def test_chat_access_control(self, setup_game_session):
        """Test that only session participants can send/receive chat messages"""
        print("\n🔒 TEST: Chat access control")
        
        session_id = setup_game_session["session_id"]
        users = setup_game_session["users"]
        server = setup_game_session["server"]
        timestamp = datetime.now().microsecond
        
        # Create a user who is NOT part of the session
        outsider_data = {
            "username": f"outsider{timestamp}",
            "email": f"outsider{timestamp}@test.com",
            "password": "testpass123"
        }
        response = requests.post(f"{server}/register", json=outsider_data)
        assert response.status_code == 200
        outsider_token = response.json()["access_token"]
        
        print("📍 Testing unauthorized chat access...")
        
        # Try to send message as outsider
        headers = {"Authorization": f"Bearer {outsider_token}"}
        response = requests.post(
            f"{server}/api/game/chat",
            json={
                "session_id": session_id,
                "message": "I shouldn't be able to send this!"
            },
            headers=headers
        )
        assert response.status_code == 403
        print("✅ Outsider correctly blocked from sending messages")
        
        # Try to read messages as outsider
        response = requests.get(f"{server}/api/game/chat/{session_id}", headers=headers)
        assert response.status_code == 403
        print("✅ Outsider correctly blocked from reading messages")
        
        # Verify legitimate user can still send messages
        participant_headers = {"Authorization": f"Bearer {users[0]['token']}"}
        response = requests.post(
            f"{server}/api/game/chat",
            json={
                "session_id": session_id,
                "message": "This should work!"
            },
            headers=participant_headers
        )
        assert response.status_code == 200
        print("✅ Session participant can send messages")
        
        print("\n🎉 Access control test passed!")