# Import the main Flask app from the root directory
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import the main app
from app import app

# Export for Vercel
if __name__ == '__main__':
    app.run(debug=True)
