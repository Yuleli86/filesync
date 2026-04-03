import asyncio
import unittest


class AsyncTestRunner(unittest.TextTestRunner):
    def run(self, test):
        """Run the given test case, supporting async tests"""
        result = self.testResultClass(self.stream, self.descriptions, self.verbosity)
        result.failfast = self.failfast
        result.buffer = self.buffer
        result.tb_locals = self.tb_locals
        
        def run_test(test_case):
            if hasattr(test_case, 'run_async'):
                return asyncio.run(test_case.run_async())
            else:
                return test_case.run()
        
        result = run_test(test)
        return result


if __name__ == '__main__':
    unittest.main(testRunner=AsyncTestRunner)
