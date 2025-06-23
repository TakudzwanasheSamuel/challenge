import os
import pandas as pd
from dotenv import load_dotenv
from dateutil.parser import parse as parse_datetime
from datetime import datetime

# Add parent directory to path to import local modules
import sys
sys.path.append('.') # Assuming the script is run from the root directory

from src.client import SportsClient

# Load API key from .env file
load_dotenv()
api_key = os.getenv("BALLDONTLIE_API_KEY")

# Initialize client
client = SportsClient(api_key=api_key)

def get_age(birth_date_str):
    if not birth_date_str:
        return None
    birth_date = parse_datetime(birth_date_str)
    today = datetime.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

def fetch_epl_player_data(season=2023):
    """
    Fetches player biographical data and detailed season statistics for all EPL players.
    """
    print(f"Fetching EPL teams for season {season}...")
    try:
        epl_teams = client.epl.teams.list(season=season)
        if not epl_teams.data:
            print(f"No teams found for EPL season {season}.")
            return pd.DataFrame()
    except Exception as e:
        print(f"Error fetching EPL teams: {e}")
        return pd.DataFrame()

    all_players_data = []
    print(f"Found {len(epl_teams.data)} EPL teams.")

    for team in epl_teams.data:
        print(f"Fetching players for team: {team.name} (ID: {team.id})...")
        try:
            team_players = client.epl.teams.get_players(team_id=team.id, season=season)
            if not team_players.data:
                print(f"No players found for team {team.name}")
                continue

            for player_bio in team_players.data:
                player_detail = player_bio.model_dump()
                player_detail['team_name'] = team.name
                player_detail['age_years'] = get_age(player_detail.get('birth_date'))

                print(f"Fetching stats for player: {player_bio.name} (ID: {player_bio.id})...")
                try:
                    player_stats_response = client.epl.players.get_season_stats(player_id=player_bio.id, season=season)
                    player_stats = {}
                    if player_stats_response.data:
                        for stat in player_stats_response.data:
                            player_stats[stat.name] = stat.value

                    player_detail.update(player_stats)
                    all_players_data.append(player_detail)
                except Exception as e:
                    print(f"Error fetching stats for player {player_bio.name} (ID: {player_bio.id}): {e}")
                    # Add player bio even if stats are missing, with NaN for stats
                    all_players_data.append(player_detail)

        except Exception as e:
            print(f"Error fetching players for team {team.name} (ID: {team.id}): {e}")
            continue

    if not all_players_data:
        print("No player data fetched.")
        return pd.DataFrame()

    df = pd.DataFrame(all_players_data)
    return df

def engineer_features(df):
    """
    Engineers features for talent identification.
    """
    if df.empty:
        return df

    # Fill NaN for calculation-critical columns to avoid errors
    # For stats that might be missing, fill with 0
    stats_cols = ['goals', 'assists', 'minutes_played']
    for col in stats_cols:
        if col not in df.columns:
            df[col] = 0 # Add column if it doesn't exist
        else:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Calculate per 90 minute stats
    # Avoid division by zero if minutes_played is 0
    df['minutes_played'] = pd.to_numeric(df['minutes_played'], errors='coerce').fillna(0)

    df['goals_per_90'] = df.apply(lambda row: (row['goals'] * 90 / row['minutes_played']) if row['minutes_played'] > 0 else 0, axis=1)
    df['assists_per_90'] = df.apply(lambda row: (row['assists'] * 90 / row['minutes_played']) if row['minutes_played'] > 0 else 0, axis=1)

    # Age-adjusted potential score (simple version)
    # Younger players with good stats get a higher score.
    # This is a placeholder; a more sophisticated model would be needed.
    df['potential_score'] = (df['goals_per_90'] + df['assists_per_90']) * (1 / (df['age_years'].fillna(30) + 1))

    # Filter for attacking players (Forwards, Wingers, Attacking Midfielders)
    attacking_positions = [
        'Striker', 'Centre Striker', 'Second Striker',
        'Left Winger', 'Right Winger',
        'Attacking Midfielder', 'Left/Centre/Right Winger',
        'Left/Centre/Right Second Striker', 'Centre/Right Attacking Midfielder',
        'Left Attacking Midfielder', 'Right Attacking Midfielder'
    ]
    df['is_attacker'] = df['position'].apply(lambda x: x in attacking_positions if pd.notnull(x) else False)

    return df

def identify_top_talents(df, top_n=10):
    """
    Identifies top talents based on the potential score, focusing on young attackers.
    """
    if df.empty or 'potential_score' not in df.columns:
        print("DataFrame is empty or 'potential_score' column is missing.")
        return pd.DataFrame()

    # Consider players younger than 23, who are attackers, and have played a reasonable amount of time (e.g., > 450 minutes)
    talents_df = df[
        (df['age_years'] < 23) &
        (df['is_attacker']) &
        (df['minutes_played'] > 450)
    ]

    if talents_df.empty:
        print("No young attacking talents found matching the criteria.")
        return pd.DataFrame()

    return talents_df.sort_values(by='potential_score', ascending=False).head(top_n)

if __name__ == "__main__":
    # This requires the BALLDONTLIE_API_KEY to be set in a .env file or environment
    # Create a .env file in the root with: BALLDONTLIE_API_KEY="your_api_key_here"

    # Check if API key is available
    if not api_key:
        print("BALLDONTLIE_API_KEY not found. Please set it in a .env file or as an environment variable.")
        print("Example .env file content: BALLDONTLIE_API_KEY=\"your_actual_api_key\"")
        # Create a dummy .env if it doesn't exist to guide the user
        if not os.path.exists(".env"):
            with open(".env", "w") as f:
                f.write("BALLDONTLIE_API_KEY=\"your_api_key_here\"\n")
            print("Created a template .env file. Please fill in your API key.")
    else:
        print("Fetching and processing player data...")
        player_data_df = fetch_epl_player_data(season=2023) # Using 2023 as an example season

        if not player_data_df.empty:
            print("\nRaw data sample:")
            print(player_data_df.head())

            print("\nEngineering features...")
            featured_df = engineer_features(player_data_df.copy())
            print("\nFeatured data sample (all players):")
            print(featured_df[['name', 'age_years', 'position', 'minutes_played', 'goals', 'assists', 'goals_per_90', 'assists_per_90', 'potential_score', 'is_attacker']].head())

            print("\nIdentifying top talents (young attackers under 23 with > 450 minutes played)...")
            top_talents = identify_top_talents(featured_df)

            if not top_talents.empty:
                print("\nTop identified talents:")
                print(top_talents[['name', 'age_years', 'team_name', 'position', 'minutes_played', 'goals', 'assists', 'potential_score']])
            else:
                print("No top talents identified based on current criteria.")
        else:
            print("No player data was fetched. Cannot proceed with feature engineering and talent identification.")

    print("\nScript finished.")
