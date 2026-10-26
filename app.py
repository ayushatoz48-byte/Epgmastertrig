import os
import base64
import requests
import threading
from flask import Flask, jsonify
from datetime import datetime

app = Flask(__name__)

# Hardcoded Repository Info
REPO_OWNER = 'Ayush8481-dev'
REPO_NAME = 'Epgdata'
FILE_PATH = 'update.json'

# Environment variable (You will set ONLY this in Render)
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')

def update_github_file():
    """Background task to update update.json on GitHub"""
    if not GITHUB_TOKEN:
        print("Missing GITHUB_TOKEN environment variable!")
        return

    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    # 1. Get the files current SHA (required by GitHub to update an existing file)
    sha = None
    get_resp = requests.get(url, headers=headers)
    if get_resp.status_code == 200:
        sha = get_resp.json().get('sha')

    # 2. Prepare the new content for update.json
    current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    new_content = f'{{"Update": "{current_time}"}}'
    
    # GitHub requires content to be base64 encoded
    encoded_content = base64.b64encode(new_content.encode('utf-8')).decode('utf-8')

    # 3. Push the update to GitHub
    data = {
        "message": "Triggered via Render API", # Triggers the GitHub Action!
        "content": encoded_content
    }
    if sha:
        data["sha"] = sha # Attach SHA if the file already exists

    put_resp = requests.put(url, headers=headers, json=data)
    
    if put_resp.status_code in [200, 201]:
        print("Successfully updated update.json on GitHub!")
    else:
        print(f"Failed to update GitHub: {put_resp.text}")

@app.route('/update', methods=['GET', 'POST'])
def trigger_update():
    # Run the GitHub update in the background so the user gets an instant response
    thread = threading.Thread(target=update_github_file)
    thread.start()
    
    return jsonify({
        "status": "success", 
        "message": f"Trigger started for {REPO_OWNER}/{REPO_NAME}! update.json is being updated in the background."
    }), 200

@app.route('/', methods=['GET'])
def home():
    return "Render trigger server is running. Visit /update to trigger."

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
