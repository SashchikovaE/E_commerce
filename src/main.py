import sys
import os
project_root = os.path.abspath(os.path.join(os.getcwd(), '..'))
sys.path.append(project_root)
from preprocessing import Preprocessor

if __name__ == "__main__":
    preprocessor = Preprocessor()
    preprocessor.preprocess()
