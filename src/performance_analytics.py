import os
import pandas as pd
import numpy as np
from dotenv import load_dotenv

# Add parent directory to path to import local modules
import sys
sys.path.append('.') # Assuming the script is run from the root directory

from src.client import SportsClient # For fetching player minutes, basic info
from src.talent_identification import fetch_epl_player_data # To get player list and minutes

# Load API key from .env file
load_dotenv()
api_key = os.getenv("BALLDONTLIE_API_KEY", "44212920-29e5-46e6-a4dc-945d70701669")

# Initialize client (though we'll mostly simulate detailed event data)
# client = SportsClient(api_key=api_key) # Uncomment if real API calls for events are made

# --- Simulation of Detailed Event Data ---
def simulate_player_pass_events(player_ids, num_events_per_player=100):
    """
    Simulates pass event data for a list of players.
    This function would be replaced by actual API calls to fetch event data.
    Pitch dimensions: Assume 100x68 units (length x width)
    x=0 is defensive goal line, x=100 is attacking goal line
    y=0 to y=68 is width
    """
    events = []
    for player_id in player_ids:
        for _ in range(num_events_per_player):
            start_x = np.random.uniform(0, 100)
            start_y = np.random.uniform(0, 68)

            # Simulate tendency for forward passes
            end_x = start_x + np.random.normal(10, 10) # Average 10 units forward
            end_x = np.clip(end_x, 0, 100)

            end_y = start_y + np.random.normal(0, 15) # Can go sideways
            end_y = np.clip(end_y, 0, 68)

            successful = np.random.choice([True, False], p=[0.75, 0.25]) # 75% pass success rate

            # Penalty area: e.g., x > 82 and 20 < y < 48
            # For simplicity, let's define it as x > 82 for now for a pass ending there.

            events.append({
                'player_id': player_id,
                'event_type': 'pass',
                'start_x': start_x,
                'start_y': start_y,
                'end_x': end_x,
                'end_y': end_y,
                'successful': successful
            })
    return pd.DataFrame(events)

# --- Metric Calculation ---
def is_progressive_pass(pass_event, pitch_length=100, penalty_area_x_start=82):
    """
    Determines if a pass is progressive based on defined criteria.
    """
    if not pass_event['successful']:
        return False

    start_x = pass_event['start_x']
    end_x = pass_event['end_x']

    # Passes must originate outside the defensive 40% of the pitch
    if start_x <= 0.4 * pitch_length:
        return False

    distance_to_goal_start = pitch_length - start_x
    distance_to_goal_end = pitch_length - end_x
    progress_made = distance_to_goal_start - distance_to_goal_end

    # Condition 1: Pass starts and ends in own half (start_x <= 50, end_x <= 50)
    # and moves ball at least 10 yards (approx 9.14 units if pitch is 100 units long ~ 110 yards)
    # Let's use 10 units for simplicity for a 100-unit pitch.
    if start_x <= pitch_length / 2 and end_x <= pitch_length / 2:
        if progress_made >= 10:
            return True

    # Condition 2: Pass starts in opponent's half (start_x > 50)
    # and moves ball at least 5 units closer to goal.
    elif start_x > pitch_length / 2:
        if progress_made >= 5:
            return True

    # Condition 3: Any completed pass into the penalty area (end_x > 82 for simplicity)
    if end_x > penalty_area_x_start: # Assuming penalty area starts at x=82
        return True

    return False

def calculate_progressive_pass_metrics(player_df, pass_events_df):
    """
    Calculates progressive pass metrics for each player.
    Requires player_df to have 'id' and 'minutes_played'.
    """
    if player_df.empty or pass_events_df.empty:
        return player_df

    player_prog_passes = []
    for player_id, group in pass_events_df.groupby('player_id'):
        total_passes = len(group)
        progressive_passes_count = 0
        successful_prog_passes_count = 0

        for _, pass_event in group.iterrows():
            if is_progressive_pass(pass_event):
                progressive_passes_count += 1 # Counts attempts that meet criteria before success check
                if pass_event['successful']: # This is redundant due to check in is_progressive_pass
                    successful_prog_passes_count +=1

        # is_progressive_pass already checks for success, so progressive_passes_count IS successful ones.
        # Let's adjust to count attempts vs successful progressive.
        # For this version, is_progressive_pass implies success.

        player_prog_passes.append({
            'id': player_id,
            'total_passes_recorded': total_passes,
            'successful_progressive_passes': successful_prog_passes_count
        })

    prog_pass_df = pd.DataFrame(player_prog_passes)

    # Merge with player main data (especially for minutes_played)
    if not prog_pass_df.empty:
        player_df = player_df.merge(prog_pass_df, on='id', how='left')
        player_df['successful_progressive_passes'] = player_df['successful_progressive_passes'].fillna(0)
        player_df['total_passes_recorded'] = player_df['total_passes_recorded'].fillna(0)

        # Calculate per 90 metrics
        player_df['minutes_played'] = pd.to_numeric(player_df['minutes_played'], errors='coerce').fillna(0)
        player_df['prog_passes_p90'] = player_df.apply(
            lambda row: (row['successful_progressive_passes'] * 90 / row['minutes_played']) if row['minutes_played'] > 0 else 0,
            axis=1
        )
        # Progressive pass accuracy (of all recorded passes for the player)
        player_df['prog_pass_accuracy'] = player_df.apply(
            lambda row: (row['successful_progressive_passes'] / row['total_passes_recorded']) if row['total_passes_recorded'] > 0 else 0,
            axis=1
        )
    else:
        player_df['successful_progressive_passes'] = 0
        player_df['total_passes_recorded'] = 0
        player_df['prog_passes_p90'] = 0
        player_df['prog_pass_accuracy'] = 0

    return player_df

if __name__ == "__main__":
    print("Fetching base player data (names, minutes played)...")
    # We use fetch_epl_player_data to get a list of players and their minutes played.
        # This function from Challenge 1 already fetches season stats including 'minutes_played'.
        # In a real scenario, you might fetch this differently if not doing Challenge 1 first.
        base_player_data_df = fetch_epl_player_data(season=2023) # Fetches bio and aggregated stats

        if not base_player_data_df.empty and 'id' in base_player_data_df.columns:
            player_ids_with_minutes = base_player_data_df[pd.to_numeric(base_player_data_df['minutes_played'], errors='coerce').fillna(0) > 0]['id'].tolist()

            if not player_ids_with_minutes:
                print("No players with minutes played found from base data.")
            else:
                print(f"Simulating pass events for {len(player_ids_with_minutes)} players...")
                # Simulate pass events - replace with actual data loading if available
                simulated_pass_df = simulate_player_pass_events(player_ids_with_minutes, num_events_per_player=200) # ~200 passes per player
                print(f"Generated {len(simulated_pass_df)} simulated pass events.")

                print("\nCalculating progressive pass metrics...")
                # Select relevant columns for merging, especially 'id' and 'minutes_played'
                # Ensure 'minutes_played' is numeric
                base_player_data_df['minutes_played'] = pd.to_numeric(base_player_data_df['minutes_played'], errors='coerce').fillna(0)

                # Columns needed from base_player_data for context and calculation
                context_columns = ['id', 'name', 'position', 'team_name', 'minutes_played', 'assists', 'passes_total'] # Assuming 'passes_total' and 'assists' come from fetch_epl_player_data

                # Ensure these stat columns exist from fetch_epl_player_data, if not, add them with 0
                for col in ['assists', 'passes_total']:
                    if col not in base_player_data_df.columns:
                        base_player_data_df[col] = 0

                player_metrics_df = calculate_progressive_pass_metrics(base_player_data_df[context_columns].copy(), simulated_pass_df)

                print("\nTop players by Progressive Passes P90 (Simulated Data):")
                # Filter for players with substantial minutes for meaningful P90 stats
                min_minutes_for_ranking = 450
                ranked_players = player_metrics_df[player_metrics_df['minutes_played'] > min_minutes_for_ranking]
                ranked_players = ranked_players.sort_values(by='prog_passes_p90', ascending=False)

                print(ranked_players[['name', 'position', 'team_name', 'minutes_played', 'assists', 'passes_total', 'successful_progressive_passes', 'prog_passes_p90', 'prog_pass_accuracy']].head(15))

                # To demonstrate added value:
                # One could compare prog_passes_p90 with assists_p90 or total_passes_p90
                # Look for players high in prog_passes_p90 but maybe not top in assists (undervalued playmakers)
                if 'assists' in ranked_players.columns:
                    ranked_players['assists_p90'] = ranked_players.apply(
                        lambda row: (pd.to_numeric(row['assists'], errors='coerce') * 90 / row['minutes_played']) if row['minutes_played'] > 0 else 0,
                        axis=1
                    )
                    print("\nComparison with Assists P90:")
                    print(ranked_players[['name', 'prog_passes_p90', 'assists_p90']].head(15))

        else:
            print("No base player data fetched or 'id' column missing. Cannot proceed.")

    print("\nPerformance Analytics script finished.")
