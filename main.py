import os
import sys
from pathlib import Path


oldDir = os.getcwd()
os.chdir(str(Path(__file__).parent))
import scripts
os.chdir(oldDir)

ret = scripts.main(sys.argv[1:])
sys.exit(ret)
