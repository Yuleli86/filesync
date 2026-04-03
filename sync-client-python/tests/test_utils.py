import os
import tempfile
import unittest
from app.utils import calculate_file_hash, get_file_size, get_last_modified, create_file_data, walk_directory, ensure_directory
from app.models import FileData


class TestUtils(unittest.TestCase):
    def setUp(self):
        # Create temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test files
        self.test_file1 = os.path.join(self.temp_dir, "test1.txt")
        self.test_file2 = os.path.join(self.temp_dir, "test2.txt")
        self.test_dir = os.path.join(self.temp_dir, "subdir")
        
        # Create test directory
        os.makedirs(self.test_dir)
        
        # Write test content
        with open(self.test_file1, "w") as f:
            f.write("Hello, World!")
        
        with open(self.test_file2, "w") as f:
            f.write("Test content")
    
    def tearDown(self):
        # Clean up temporary files
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_calculate_file_hash(self):
        # Test file hash calculation
        hash1 = calculate_file_hash(self.test_file1)
        hash2 = calculate_file_hash(self.test_file2)
        self.assertNotEqual(hash1, hash2)
        
        # Test directory hash
        dir_hash = calculate_file_hash(self.test_dir)
        self.assertIsInstance(dir_hash, str)
        self.assertEqual(len(dir_hash), 32)  # MD5 hash length
    
    def test_get_file_size(self):
        # Test file size
        size1 = get_file_size(self.test_file1)
        self.assertEqual(size1, 13)  # "Hello, World!" length
        
        # Test directory size (should be 0)
        dir_size = get_file_size(self.test_dir)
        self.assertEqual(dir_size, 0)
    
    def test_get_last_modified(self):
        # Test last modified time
        last_modified = get_last_modified(self.test_file1)
        self.assertIsNotNone(last_modified)
    
    def test_create_file_data(self):
        # Test create file data for file
        file_data = create_file_data(self.test_file1, self.temp_dir)
        self.assertIsInstance(file_data, FileData)
        self.assertEqual(file_data.filename, "test1.txt")
        self.assertEqual(file_data.path, "")
        self.assertEqual(file_data.size, 13)
        self.assertFalse(file_data.is_directory)
        
        # Test create file data for directory
        dir_data = create_file_data(self.test_dir, self.temp_dir)
        self.assertIsInstance(dir_data, FileData)
        self.assertEqual(dir_data.filename, "subdir")
        self.assertEqual(dir_data.path, "")
        self.assertEqual(dir_data.size, 0)
        self.assertTrue(dir_data.is_directory)
    
    def test_walk_directory(self):
        # Test directory walking
        files = walk_directory(self.temp_dir)
        self.assertEqual(len(files), 3)  # 2 files + 1 directory
        
        # Check if all expected paths are present
        expected_paths = [self.test_file1, self.test_file2, self.test_dir]
        for path in expected_paths:
            self.assertIn(path, files)
    
    def test_ensure_directory(self):
        # Test directory creation
        new_dir = os.path.join(self.temp_dir, "new_dir")
        ensure_directory(new_dir)
        self.assertTrue(os.path.exists(new_dir))
        
        # Test existing directory (should not throw error)
        ensure_directory(self.temp_dir)
        self.assertTrue(os.path.exists(self.temp_dir))


if __name__ == "__main__":
    unittest.main()
