"""
WebSocket Manager for real-time online user tracking
"""
from typing import Dict, Set, List
from fastapi import WebSocket
import json
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Dictionary: user_id -> WebSocket connection
        self.active_connections: Dict[int, WebSocket] = {}
        # Dictionary: group_name -> Set of user_ids
        self.group_users: Dict[str, Set[int]] = {}
        # Dictionary: user_id -> username (for display)
        self.user_names: Dict[int, str] = {}

    async def connect(self, websocket: WebSocket, user_id: int, username: str):
        """Connect a user and track them"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.user_names[user_id] = username
        logger.info(f"User {username} (ID: {user_id}) connected via WebSocket")

    async def disconnect(self, user_id: int):
        """Disconnect a user and remove from all groups"""
        if user_id in self.active_connections:
            username = self.user_names.get(user_id, "Unknown")
            del self.active_connections[user_id]
            
            # Remove user from all groups and broadcast updates
            groups_to_update = []
            for group_name in list(self.group_users.keys()):
                if user_id in self.group_users[group_name]:
                    self.group_users[group_name].remove(user_id)
                    groups_to_update.append(group_name)
                    if not self.group_users[group_name]:  # If group is empty
                        del self.group_users[group_name]
            
            if user_id in self.user_names:
                del self.user_names[user_id]
                
            logger.info(f"User {username} (ID: {user_id}) disconnected")
            
            # Broadcast updated online users to affected groups
            for group_name in groups_to_update:
                await self._broadcast_online_users_update(group_name)

    def join_group(self, user_id: int, group_name: str):
        """Add user to a group"""
        if group_name not in self.group_users:
            self.group_users[group_name] = set()
        self.group_users[group_name].add(user_id)
        logger.info(f"User {self.user_names.get(user_id)} joined group {group_name}")

    def leave_group(self, user_id: int, group_name: str):
        """Remove user from a group"""
        if group_name in self.group_users and user_id in self.group_users[group_name]:
            self.group_users[group_name].remove(user_id)
            if not self.group_users[group_name]:  # If group is empty
                del self.group_users[group_name]
            logger.info(f"User {self.user_names.get(user_id)} left group {group_name}")

    def get_online_users_in_group(self, group_name: str) -> List[Dict]:
        """Get list of online users in a specific group"""
        if group_name not in self.group_users:
            return []
        
        online_users = []
        for user_id in self.group_users[group_name]:
            if user_id in self.active_connections:  # User is still connected
                username = self.user_names.get(user_id, "Unknown")
                online_users.append({
                    "user_id": user_id,
                    "username": username
                })
        
        return online_users

    async def broadcast_to_group(self, group_name: str, message: dict):
        """Send message to all users in a group"""
        if group_name not in self.group_users:
            return
            
        disconnected_users = []
        for user_id in self.group_users[group_name]:
            if user_id in self.active_connections:
                try:
                    await self.active_connections[user_id].send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {e}")
                    disconnected_users.append(user_id)
        
        # Clean up disconnected users
        for user_id in disconnected_users:
            await self.disconnect(user_id)

    async def send_personal_message(self, message: str, user_id: int):
        """Send message to a specific user"""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(message)
            except Exception as e:
                logger.error(f"Error sending personal message to user {user_id}: {e}")
                await self.disconnect(user_id)

    async def send_invitation_notification(self, user_id: int, invitation_data: dict):
        """Send invitation notification to a specific user"""
        if user_id in self.active_connections:
            message = {
                "type": "new_invitation",
                "invitation": invitation_data
            }
            try:
                await self.active_connections[user_id].send_text(json.dumps(message))
                logger.info(f"Sent invitation notification to user {user_id}")
            except Exception as e:
                logger.error(f"Error sending invitation notification to user {user_id}: {e}")
                await self.disconnect(user_id)

    async def _broadcast_online_users_update(self, group_name: str):
        """Broadcast updated online users list to all users in a group"""
        online_users = self.get_online_users_in_group(group_name)
        message = {
            "type": "online_users_update",
            "group_name": group_name,
            "online_users": online_users
        }
        await self.broadcast_to_group(group_name, message)

# Global connection manager instance
manager = ConnectionManager()