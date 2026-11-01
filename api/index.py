import sys
import os

# Add root folder to sys.path so modules like backend, matching, gis can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app
