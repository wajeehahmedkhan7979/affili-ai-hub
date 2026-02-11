
import pytest
import sys

class Tee(object):
    def __init__(self, name, mode):
        self.file = open(name, mode)
        self.stdout = sys.stdout
        sys.stdout = self
    def __del__(self):
        sys.stdout = self.stdout
        self.file.close()
    def write(self, data):
        self.file.write(data)
        self.stdout.write(data)
    def flush(self):
        self.file.flush()

# Redirect stdout to file
sys.stdout = open('test_logs_direct.txt', 'w', encoding='utf-8')
sys.stderr = sys.stdout

# Run pytest
ret = pytest.main(["-vv", "tests/test_layer1_hitl.py"])
sys.exit(ret)

