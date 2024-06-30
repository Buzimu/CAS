import json
import os

DATA_FILE = 'bot_data.json'

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: {DATA_FILE} is empty or contains invalid JSON. Initializing with empty data.")
    return {"users": {}}

# Initialize data
bot_data = load_data()