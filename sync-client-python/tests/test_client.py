import unittest
import httpx
from unittest.mock import Mock, patch
from app.client import SyncClient
from app.models import UserCreate, FileData
from datetime import datetime


class TestSyncClient(unittest.TestCase):
    def setUp(self):
        self.client = SyncClient()
    
    @patch('httpx.AsyncClient.post')
    async def test_register(self, mock_post):
        # Mock response
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "success": True,
            "data": {
                "user": {
                    "id": 1,
                    "username": "testuser",
                    "email": "test@example.com",
                    "role": "user"
                },
                "token": "test-token"
            },
            "message": "User registered successfully"
        }
        mock_post.return_value = mock_response
        
        # Test register
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="testpass"
        )
        
        result = await self.client.register(user_data)
        
        # Verify
        self.assertTrue(result["success"])
        self.assertEqual(result["data"]["user"]["username"], "testuser")
        mock_post.assert_called_once()
    
    @patch('httpx.AsyncClient.post')
    async def test_login(self, mock_post):
        # Mock response
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "success": True,
            "data": {
                "user": {
                    "id": 1,
                    "username": "testuser",
                    "email": "test@example.com",
                    "role": "user"
                },
                "token": "test-token"
            },
            "message": "Login successful"
        }
        mock_post.return_value = mock_response
        
        # Test login
        result = await self.client.login("testuser", "testpass")
        
        # Verify
        self.assertTrue(result["success"])
        self.assertEqual(self.client.token, "test-token")
        mock_post.assert_called_once()
    
    @patch('httpx.AsyncClient.post')
    async def test_upload_file_metadata(self, mock_post):
        # Set token
        self.client.token = "test-token"
        
        # Mock response
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "success": True,
            "data": {
                "id": 1,
                "path": "",
                "filename": "test.txt",
                "size": 100,
                "file_hash": "test-hash",
                "last_modified": "2023-01-01T00:00:00",
                "is_directory": False
            },
            "message": "File uploaded successfully"
        }
        mock_post.return_value = mock_response
        
        # Test upload file metadata
        file_data = FileData(
            path="",
            filename="test.txt",
            size=100,
            file_hash="test-hash",
            last_modified=datetime.now(),
            is_directory=False
        )
        
        result = await self.client.upload_file_metadata(file_data)
        
        # Verify
        self.assertTrue(result["success"])
        mock_post.assert_called_once()
    
    @patch('httpx.AsyncClient.get')
    async def test_list_files(self, mock_get):
        # Set token
        self.client.token = "test-token"
        
        # Mock response
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "success": True,
            "data": [],
            "pagination": {
                "total": 0,
                "limit": 50,
                "offset": 0,
                "has_more": False
            },
            "message": "Files listed successfully"
        }
        mock_get.return_value = mock_response
        
        # Test list files
        result = await self.client.list_files()
        
        # Verify
        self.assertTrue(result["success"])
        mock_get.assert_called_once()
    
    @patch('httpx.AsyncClient.delete')
    async def test_delete_file(self, mock_delete):
        # Set token
        self.client.token = "test-token"
        
        # Mock response
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "success": True,
            "message": "File deleted successfully"
        }
        mock_delete.return_value = mock_response
        
        # Test delete file
        result = await self.client.delete_file(1)
        
        # Verify
        self.assertTrue(result["success"])
        mock_delete.assert_called_once()
    
    @patch('httpx.AsyncClient.post')
    async def test_init_sync(self, mock_post):
        # Set token
        self.client.token = "test-token"
        
        # Mock response
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "success": True,
            "data": {
                "sync_id": 1,
                "synced_files": [],
                "conflicts": []
            },
            "message": "Sync completed successfully"
        }
        mock_post.return_value = mock_response
        
        # Test init sync
        file_data = FileData(
            path="",
            filename="test.txt",
            size=100,
            file_hash="test-hash",
            last_modified=datetime.now(),
            is_directory=False
        )
        
        result = await self.client.init_sync([file_data])
        
        # Verify
        self.assertTrue(result["success"])
        mock_post.assert_called_once()
    
    async def test_close(self):
        # Test close method
        with patch.object(self.client.client, 'aclose') as mock_aclose:
            await self.client.close()
            mock_aclose.assert_called_once()


if __name__ == "__main__":
    import asyncio
    asyncio.run(unittest.main())
