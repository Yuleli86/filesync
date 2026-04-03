import unittest
from tests.test_utils import TestUtils
from tests.test_client import TestSyncClient
from tests.test_sync import TestSyncManager
from tests.test_integration import TestIntegration


def run_all_tests():
    """Run all tests"""
    # Run utils tests
    utils_suite = unittest.TestLoader().loadTestsFromTestCase(TestUtils)
    utils_result = unittest.TextTestRunner().run(utils_suite)
    
    # Run client tests
    client_suite = unittest.TestLoader().loadTestsFromTestCase(TestSyncClient)
    client_result = unittest.TextTestRunner().run(client_suite)
    
    # Run sync tests
    sync_suite = unittest.TestLoader().loadTestsFromTestCase(TestSyncManager)
    sync_result = unittest.TextTestRunner().run(sync_suite)
    
    # Run integration tests
    integration_suite = unittest.TestLoader().loadTestsFromTestCase(TestIntegration)
    integration_result = unittest.TextTestRunner().run(integration_suite)
    
    # Check results
    all_passed = (utils_result.wasSuccessful() and 
                 client_result.wasSuccessful() and 
                 sync_result.wasSuccessful() and 
                 integration_result.wasSuccessful())
    
    print(f"\n{'All tests passed!' if all_passed else 'Some tests failed!'}")
    return all_passed


if __name__ == '__main__':
    run_all_tests()
