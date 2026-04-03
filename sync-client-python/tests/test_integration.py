import unittest
import os
import tempfile
from unittest.mock import Mock, patch
from app.sync import SyncManager
from app.models import FileData
from datetime import datetime


class TestIntegration(unittest.TestCase):
    def setUp(self):
        # Create temporary sync directory
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock settings
        with patch('app.sync.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.SYNC_DIR = self.temp_dir
            mock_get_settings.return_value = mock_settings
            
            self.sync_manager = SyncManager()
    
    def tearDown(self):
        # Clean up temporary directory
        import shutil
        shutil.rmtree(self.temp_dir)
    
    @patch('app.sync.SyncClient.login')
    @patch('app.sync.SyncClient.init_sync')
    @patch('app.sync.walk_directory')
    @patch('app.sync.SyncWebSocketClient')
    @patch('app.sync.FileWatcher')
    async def test_full_sync_flow(self, mock_watcher, mock_ws_client, mock_walk, mock_init_sync, mock_login):
        """Test the full sync flow"""
        # Mock responses
        mock_login.return_value = True
        
        # Mock walk directory
        test_file = os.path.join(self.temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test content")
        mock_walk.return_value = [test_file]
        
        # Mock init sync response
        mock_init_sync.return_value = {
            "success": True,
            "data": {
                "sync_id": 1,
                "synced_files": [],
                "conflicts": []
            },
            "message": "Sync completed successfully"
        }
        
        # Mock WebSocket and FileWatcher
        mock_watcher_instance = Mock()
        mock_watcher.return_value = mock_watcher_instance
        
        mock_ws_instance = Mock()
        mock_ws_client.return_value = mock_ws_instance
        
        # Test full flow
        await self.sync_manager.initialize()
        
        # Login
        login_success = await self.sync_manager.login("testuser", "testpass")
        self.assertTrue(login_success)
        
        # Start sync
        await self.sync_manager.start_sync()
        
        # Verify all components were initialized
        mock_login.assert_called_once()
        mock_watcher.assert_called_once()
        mock_ws_client.assert_called_once()
        mock_init_sync.assert_called_once()
        
        # Stop sync
        await self.sync_manager.stop_sync()
        
        # Verify cleanup
        mock_watcher_instance.stop.assert_called_once()
        mock_ws_instance.disconnect.assert_called_once()
    
    @patch('app.sync.SyncClient.register')
    async def test_register_flow(self, mock_register):
        """Test the registration flow"""
        # Mock register response
        mock_register.return_value = True
        
        # Test register
        register_success = await self.sync_manager.register(
            "testuser", 
            "test@example.com", 
            "testpass"
        )
        
        self.assertTrue(register_success)
        mock_register.assert_called_once()
    
    @patch('app.sync.SyncClient.login')
    @patch('app.sync.SyncClient.list_files')
    async def test_file_listing(self, mock_list_files, mock_login):
        """Test file listing functionality"""
        # Mock responses
        mock_login.return_value = True
        
        # Mock list files response
        mock_list_files.return_value = {
            "success": True,
            "data": [{
                "id": 1,
                "path": "",
                "filename": "test.txt",
                "size": 100,
                "file_hash": "test-hash",
                "last_modified": "2023-01-01T00:00:00",
                "is_directory": False
            }],
            "pagination": {
                "total": 1,
                "limit": 50,
                "offset": 0,
                "has_more": False
            },
            "message": "Files listed successfully"
        }
        
        # Login and test file listing
        await self.sync_manager.login("testuser", "testpass")
        
        # Access client directly to test list files
        result = await self.sync_manager.client.list_files()
        
        self.assertTrue(result["success"])
        self.assertEqual(len(result["data"]), 1)
        mock_list_files.assert_called_once()


if __name__ == "__main__":
    import asyncio
    asyncio.run(unittest.main())
