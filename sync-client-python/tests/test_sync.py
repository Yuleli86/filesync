import unittest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from app.sync import SyncManager
from app.models import FileData
from datetime import datetime


class TestSyncManager(unittest.TestCase):
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
    
    async def test_initialize(self):
        # Test initialization
        await self.sync_manager.initialize()
        self.assertTrue(os.path.exists(self.sync_manager.sync_dir))
    
    @patch('app.sync.SyncClient.login')
    async def test_login(self, mock_login):
        # Mock login response
        mock_login.return_value = True
        
        # Test login
        result = await self.sync_manager.login("testuser", "testpass")
        self.assertTrue(result)
        mock_login.assert_called_once_with("testuser", "testpass")
    
    @patch('app.sync.SyncClient.register')
    async def test_register(self, mock_register):
        # Mock register response
        mock_register.return_value = True
        
        # Test register
        result = await self.sync_manager.register("testuser", "test@example.com", "testpass")
        self.assertTrue(result)
        mock_register.assert_called_once()
    
    @patch('app.sync.SyncClient.init_sync')
    @patch('app.sync.walk_directory')
    async def test_initial_sync(self, mock_walk, mock_init_sync):
        # Mock walk directory
        test_file = os.path.join(self.temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test")
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
        
        # Set token
        self.sync_manager.client.token = "test-token"
        
        # Test initial sync
        with patch('builtins.print') as mock_print:
            await self.sync_manager.initial_sync()
            mock_init_sync.assert_called_once()
    
    @patch('app.sync.SyncClient.resolve_conflict')
    async def test_handle_conflicts(self, mock_resolve):
        # Mock resolve conflict
        mock_resolve.return_value = {"success": True}
        
        # Test handle conflicts
        conflicts = [{
            "file": {
                "path": "",
                "filename": "test.txt",
                "size": 100,
                "file_hash": "local-hash",
                "last_modified": "2023-01-01T00:00:00",
                "is_directory": False
            },
            "existing_file": {
                "id": 1,
                "path": "",
                "filename": "test.txt",
                "size": 200,
                "file_hash": "remote-hash",
                "last_modified": "2023-01-02T00:00:00"
            }
        }]
        
        # Mock input
        with patch('builtins.input', return_value="keep_local"):
            await self.sync_manager._handle_conflicts(1, conflicts)
            mock_resolve.assert_called_once()
    
    @patch('app.sync.SyncWebSocketClient')
    @patch('app.sync.FileWatcher')
    async def test_start_sync(self, mock_watcher, mock_ws_client):
        # Mock objects
        mock_watcher_instance = Mock()
        mock_watcher.return_value = mock_watcher_instance
        
        mock_ws_instance = Mock()
        mock_ws_client.return_value = mock_ws_instance
        
        # Set token
        self.sync_manager.client.token = "test-token"
        
        # Test start sync
        with patch('app.sync.SyncManager.initial_sync') as mock_initial_sync:
            await self.sync_manager.start_sync()
            mock_watcher.assert_called_once()
            mock_ws_client.assert_called_once()
            mock_initial_sync.assert_called_once()
    
    async def test_stop_sync(self):
        # Mock watcher and websocket
        mock_watcher = Mock()
        mock_ws = Mock()
        
        self.sync_manager.watcher = mock_watcher
        self.sync_manager.ws_client = mock_ws
        
        # Test stop sync
        await self.sync_manager.stop_sync()
        mock_watcher.stop.assert_called_once()
        mock_ws.disconnect.assert_called_once()
    
    async def test_close(self):
        # Mock client
        mock_client = Mock()
        self.sync_manager.client = mock_client
        
        # Test close
        with patch('app.sync.SyncManager.stop_sync') as mock_stop_sync:
            await self.sync_manager.close()
            mock_stop_sync.assert_called_once()
            mock_client.close.assert_called_once()


if __name__ == "__main__":
    import asyncio
    asyncio.run(unittest.main())
