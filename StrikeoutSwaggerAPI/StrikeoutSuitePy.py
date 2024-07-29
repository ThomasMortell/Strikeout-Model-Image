import pandas as pd
import requests
import json
import math

def fetch_data(endpoint):
    try:
        response = requests.get(endpoint)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Failed to fetch data from {endpoint}: {e}")
        return None

def load_league_so_avg():
    data = fetch_data('https://nrfiswaggerapi.onrender.com/fetch-advanced-batting')
    if data and 'league_average' in data and data['league_average']:
        value = data['league_average'][0]['SO%']
        value = float(value.strip('%'))
        return value / 100
    raise ValueError('No data found in league_SO_AVG')

def calculate_lineup_strikeout_avg(batters):
    if not batters:
        return 0
    batters_to_consider = batters[:9]
    
    def parse_so_percent(value):
        if isinstance(value, str):
            return float(value.strip('%'))
        return float(value)

    total_so = sum(parse_so_percent(batter.get('SO%', 0)) for batter in batters_to_consider)
    return total_so / len(batters_to_consider)

def poisson_probability(k, lambda_):
    return (math.exp(-lambda_) * (lambda_ ** k)) / math.factorial(k)

def calculate_strikeout_probability(predicted_so, book_ks):
    probability = sum(poisson_probability(k, predicted_so) for k in range(math.ceil(book_ks), 20))
    return probability

def load_pitcher_odds(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def main():
    pitcher_data = fetch_data('https://nrfiswaggerapi.onrender.com/fetch-pitcher-data')
    batter_data = fetch_data('https://nrfiswaggerapi.onrender.com/fetch-advanced-batting')
    lineup_data = fetch_data('https://nrfiswaggerapi.onrender.com/fetch-daily-lineups')
    league_so_avg = load_league_so_avg()

    if not all([pitcher_data, batter_data, lineup_data, league_so_avg]):
        raise Exception("Failed to fetch all required data.")

    pitcher_odds = load_pitcher_odds('./Data/pitcher_strikeout_odds.json')

    pitchers = {p['Name']: p for p in pitcher_data['pitcher_data']}
    batters = {b['Name']: b for b in batter_data['advanced_batting']}

    unique_results = {}

    for lineup in lineup_data['daily_lineups']:
        home_team = lineup['Team'] if lineup['Home/Away'] == 'Home' else lineup['Opponent']
        away_team = lineup['Team'] if lineup['Home/Away'] == 'Away' else lineup['Opponent']

        home_pitcher = next((p for p in lineup_data['daily_lineups'] if p['Team'] == home_team and p['Position'] == 'P'), None)
        away_pitcher = next((p for p in lineup_data['daily_lineups'] if p['Team'] == away_team and p['Position'] == 'P'), None)

        for pitcher, batting_team in [(home_pitcher, home_team), (away_pitcher, away_team)]:
            if pitcher and pitcher['Name'] in pitchers:
                pitcher_stats = pitchers[pitcher['Name']]
                batting_lineup = [batters.get(b['Name'], {}) for b in lineup_data['daily_lineups'] if b['Team'] == batting_team and b['Position'] != 'P']

                lineup_so_avg = calculate_lineup_strikeout_avg(batting_lineup)
                adjusted_average = lineup_so_avg / league_so_avg

                pitching_so_percent = pitcher_stats['Pitching SO%']
                if isinstance(pitching_so_percent, str):
                    pitching_so_percent = float(pitching_so_percent.strip('%'))
                else:
                    pitching_so_percent = float(pitching_so_percent)

                predicted_strikeouts = (
                    pitching_so_percent *
                    adjusted_average *
                    float(pitcher_stats['xInnings']) *
                    float(pitcher_stats['xBF'])
                ) / 100

                odds = next((odds for odds in pitcher_odds if odds['pitcher'] == pitcher['Name']), None)
                
                if odds:
                    book_ks = odds['strikeouts']
                    book_probability = calculate_strikeout_probability(predicted_strikeouts, book_ks)
                    alt_ks = book_ks - 0.5
                    alt_probability = calculate_strikeout_probability(predicted_strikeouts, alt_ks)
                else:
                    book_ks = None
                    book_probability = None
                    alt_ks = None
                    alt_probability = None

                unique_results[pitcher['Name']] = {
                    'Pitcher': pitcher['Name'],
                    'Team': pitcher['Team'],
                    'Expected Innings': float(pitcher_stats['xInnings']),
                    'Expected Batters Faced Per Inning': float(pitcher_stats['xBF']),
                    'Predicted Strikeouts': predicted_strikeouts,
                    'Book Line': book_ks,
                    'Probability Over': book_probability,
                    'Alternate Line': alt_ks,
                    'Alternate Probability Over': alt_probability
                }

    df = pd.DataFrame(list(unique_results.values()))
    df = df.sort_values('Probability Over', ascending=False)
    
    df.to_csv('./Data/pitcher_strikeout_predictions.csv', index=False)

if __name__ == "__main__":
    main()