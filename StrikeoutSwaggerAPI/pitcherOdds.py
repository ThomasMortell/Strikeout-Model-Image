import os
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
        raise Exception(f"Failed to get events: {events_response.status_code}")
    
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
            "bookmakers": "draftkings"
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
                                    'bookmaker': bookmaker['title'],
                                    'last_update': last_update.isoformat()
                                }
    
    return list(pitcher_strikeout_odds.values())

def save_odds_to_json(odds, filename='./Data/pitcher_strikeout_odds.json'):
    with open(filename, 'w') as f:
        json.dump(odds, f, indent=2)
    print(f"Odds saved to {filename}")

def load_odds_from_json(filename='./Data/pitcher_strikeout_odds.json'):
    with open(filename, 'r') as f:
        return json.load(f)

def main(api_key):
    json_file = './Data/pitcher_strikeout_odds.json'
    
    if os.path.exists(json_file):
        print(f"Loading data from {json_file}")
        odds = load_odds_from_json(json_file)
    else:
        print("Fetching data from the API")
        odds = get_pitcher_strikeout_odds(api_key)
        save_odds_to_json(odds, json_file)
    
    return odds

# The API key would be passed to the main function when called
