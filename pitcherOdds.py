import requests
import json
from datetime import datetime


def check_api_usage(response):
    print('Remaining requests:', response.headers['x-requests-remaining'])
    print('Used requests:', response.headers['x-requests-used'])
    print()

def get_pitcher_strikeout_odds(api_key, sport="baseball_mlb"):
    base_url = "https://api.the-odds-api.com/v4"
    
    events_url = f"{base_url}/sports/{sport}/events"
    events_params = {
        "apiKey": api_key,
    }
    
    events_response = requests.get(events_url, params=events_params)
    if events_response.status_code != 200:
        print(f"Failed to get events: {events_response.status_code}")
        return
    
    print("After getting events:")
    check_api_usage(events_response)
    
    events = events_response.json()
    
    pitcher_strikeout_odds = {}
    
    for event in events:
        event_id = event['id']
        
        odds_url = f"{base_url}/sports/{sport}/events/{event_id}/odds"
        odds_params = {
            "apiKey": api_key,
            "markets": "pitcher_strikeouts",
            "regions": "us",
            "bookmakers": "draftkings"  # Specify DraftKings here
        }
        
        odds_response = requests.get(odds_url, params=odds_params)
        if odds_response.status_code != 200:
            print(f"Failed to get odds for event {event_id}: {odds_response.status_code}")
            continue
        
        print(f"After getting odds for event {event_id}:")
        check_api_usage(odds_response)
        
        odds_data = odds_response.json()
        
        for bookmaker in odds_data.get('bookmakers', []):
                for market in bookmaker.get('markets', []):
                    if market['key'] == 'pitcher_strikeouts':
                        last_update = datetime.strptime(market['last_update'], "%Y-%m-%dT%H:%M:%SZ")
                        for outcome in market['outcomes']:
                            pitcher = outcome['description']
                            if pitcher not in pitcher_strikeout_odds or last_update > datetime.strptime(pitcher_strikeout_odds[pitcher]['last_update'], "%Y-%m-%dT%H:%M:%S"):
                                pitcher_strikeout_odds[pitcher] = {
                                    'event': f"{event['home_team']} vs {event['away_team']}",
                                    'pitcher': pitcher,
                                    'strikeouts': outcome['point'],
                                    # 'over_odds': outcome['price'] if outcome['name'] == 'Over' else None,
                                    # 'under_odds': outcome['price'] if outcome['name'] == 'Under' else None,
                                    'bookmaker': bookmaker['title'],
                                    'last_update': last_update.isoformat()
                                }
    
    return list(pitcher_strikeout_odds.values())

def save_odds_to_json(odds, filename='pitcher_strikeout_odds.json'):
    with open(filename, 'w') as f:
        json.dump(odds, f, indent=2)
    print(f"Odds saved to {filename}")

def load_odds_from_json(filename='pitcher_strikeout_odds.json'):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"File {filename} not found. Will fetch new data.")
        return None

# Usage
api_key = '7ceaebfb8ad303152dfbabdcf2f4dfac'

# Try to load existing odds
odds = load_odds_from_json()

# If odds don't exist or are empty, fetch new ones
if not odds:
    odds = get_pitcher_strikeout_odds(api_key)
    save_odds_to_json(odds)

# Print the results
for odd in odds:
    print(json.dumps(odd, indent=2))