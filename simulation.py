import requests
import time
import random
import json

# The address of your "Mailbox"
url = "http://127.0.0.1:8000/record/"

print("🥊 Virtual Sandbag Activated! Press Ctrl+C to stop.")

while True:
    # 1. Generate fake sensor data
    # Force between 10N and 150N
    force = round(random.uniform(10.0, 150.0), 2)
    # Volume between 40dB and 90dB
    volume = round(random.uniform(40.0, 90.0), 2)
    
    # 2. Pack it into JSON
    payload = {
        "force": force, 
        "volume": volume
    }
    
    try:
        # 3. Send it to the Django Server
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            print(f"✅ Punch sent: {force}N Force")
        else:
            print(f"⚠️ Server Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Connection Failed: Is the server running?")

    # 4. Wait a bit before the next punch (2 seconds)
    time.sleep(2)