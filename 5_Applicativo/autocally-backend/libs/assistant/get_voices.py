import eventlet
import requests
import os

def get_voices_print():
    def fetch_data():
        params = {
            'q': 'italian',
            'limit': 20
        }
        
        response = requests.get(
            "https://api.cartesia.ai/voices/",
            params=params,
            headers={
                "X-API-Key": os.getenv('CARTESIA_API_KEY'),
                "Cartesia-Version": "2024-06-10"
            },
        )
        return response.json()
    
    # Execute in a green thread
    pool = eventlet.GreenPool()
    result = pool.spawn(fetch_data).wait()
    print('response', result)

    print('PIPPPPPPPA' + r'A' * 100)

    # Check if the request was successful
    """ if response.status_code == 200:
        voices = response.json()
        # Print each voice's details in a more readable format
        for voice in voices:
            print(f"Voice ID: {voice.get('id')}")
            print(f"Name: {voice.get('name')}")
            print(f"Language: {voice.get('language')}")
            print("-" * 30)
    else:
        print(f"Error: {response.status_code}")
        print(response.text) """