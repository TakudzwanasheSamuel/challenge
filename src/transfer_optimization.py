import os
import pandas as pd
from dotenv import load_dotenv

# Add parent directory to path to import local modules
import sys
sys.path.append('.') # Assuming the script is run from the root directory

from src.client import SportsClient
# Assuming fetch_epl_player_data also brings in engineered features from Challenge 1
# and calculate_progressive_pass_metrics from Challenge 2 can augment this data.
from src.talent_identification import fetch_epl_player_data, engineer_features
from src.performance_analytics import calculate_progressive_pass_metrics, simulate_player_pass_events # For prog_passes_p90

# Load API key
load_dotenv()
api_key = os.getenv("BALLDONTLIE_API_KEY", "44212920-29e5-46e6-a4dc-945d70701669")
client = SportsClient(api_key=api_key)

def get_team_standings(season=2023):
    """Fetches league standings."""
    if not client:
        print("API client not initialized. Cannot fetch standings.")
        return pd.DataFrame()
    try:
        standings_response = client.epl.standings.get(season=season)
        if standings_response.data:
            standings_data = [s.model_dump(exclude_none=True) for s in standings_response.data]
            # The 'team' field is a dict, we might want to flatten it or extract team_id/name
            processed_standings = []
            for record in standings_data:
                team_info = record.pop('team', {})
                record['team_id'] = team_info.get('id')
                record['team_name'] = team_info.get('name')
                processed_standings.append(record)
            return pd.DataFrame(processed_standings)
    except Exception as e:
        print(f"Error fetching standings: {e}")
    return pd.DataFrame()

def analyze_team_needs(team_id, team_name, standings_df, all_players_df, league_avg_goals_scored, league_avg_goals_conceded):
    """
    Simplified analysis of team needs based on performance and squad depth.
    Returns a list of positions (str) that might need reinforcement.
    """
    needs = []
    team_data = standings_df[standings_df['team_id'] == team_id]

    if team_data.empty:
        print(f"No standings data found for team {team_name} (ID: {team_id})")
        return ["Unknown - No data"]

    # Performance-based needs
    if team_data['overall_goals_for'].iloc[0] < league_avg_goals_scored * 0.85: # Significantly below avg
        needs.append("Forward")
    if team_data['overall_goals_against'].iloc[0] > league_avg_goals_conceded * 1.15: # Significantly above avg
        needs.append("Defender")

    # Squad depth analysis (example for Strikers)
    team_players = all_players_df[all_players_df['team_name'] == team_name] # Assuming team_name is consistent

    # General positional categories for simplicity
    def get_general_position(pos_string):
        if not pos_string or pd.isna(pos_string): return "Unknown"
        pos_string = pos_string.lower()
        if "striker" in pos_string or "forward" in pos_string: return "Forward"
        if "midfielder" in pos_string or "mf" in pos_string: return "Midfielder"
        if "defender" in pos_string or "full back" in pos_string or "centre back" in pos_string : return "Defender"
        if "goalkeeper" in pos_string: return "Goalkeeper"
        return "Other"

    team_players['general_position'] = team_players['position'].apply(get_general_position)

    striker_count = team_players[team_players['general_position'] == "Forward"].shape[0]
    if striker_count < 3 and "Forward" not in needs: # Example threshold
        print(f"Team {team_name} has only {striker_count} forwards. Suggesting Forward.")
        needs.append("Forward")

    midfielder_count = team_players[team_players['general_position'] == "Midfielder"].shape[0]
    if midfielder_count < 5: # Example threshold
         print(f"Team {team_name} has only {midfielder_count} midfielders. Suggesting Midfielder.")
         if "Midfielder" not in needs: needs.append("Midfielder")

    defender_count = team_players[team_players['general_position'] == "Defender"].shape[0]
    if defender_count < 6: # Example threshold
         print(f"Team {team_name} has only {defender_count} defenders. Suggesting Defender.")
         if "Defender" not in needs: needs.append("Defender")

    if not needs:
        needs.append("No obvious immediate gaps based on simplified analysis.")

    return list(set(needs)) # Unique needs

def recommend_players(target_team_name, position_needed, all_players_df, max_age=28, min_potential_score=None, min_prog_passes_p90=None, top_n=5):
    """
    Recommends players for a given position and team.
    all_players_df should be augmented with 'potential_score' and 'prog_passes_p90'.
    """
    candidates = all_players_df[all_players_df['team_name'] != target_team_name].copy() # Exclude own players

    # Filter by general position
    def get_general_position(pos_string):
        if not pos_string or pd.isna(pos_string): return "Unknown"
        pos_string = pos_string.lower()
        if "striker" in pos_string or "forward" in pos_string: return "Forward"
        if "midfielder" in pos_string or "mf" in pos_string: return "Midfielder"
        if "defender" in pos_string or "full back" in pos_string: return "Defender"
        if "goalkeeper" in pos_string: return "Goalkeeper"
        return "Other"

    candidates['general_position'] = candidates['position'].apply(get_general_position)
    candidates = candidates[candidates['general_position'] == position_needed]

    if candidates.empty:
        print(f"No candidates found for position: {position_needed} after initial filter.")
        return pd.DataFrame()

    # Age filter
    if 'age_years' in candidates.columns and max_age:
        candidates = candidates[candidates['age_years'] <= max_age]

    # Performance filter
    sort_by_metric = None
    if position_needed == "Forward" and 'potential_score' in candidates.columns:
        if min_potential_score:
            candidates = candidates[candidates['potential_score'] >= min_potential_score]
        sort_by_metric = 'potential_score'
    elif position_needed == "Midfielder" and 'prog_passes_p90' in candidates.columns:
        if min_prog_passes_p90:
            candidates = candidates[candidates['prog_passes_p90'] >= min_prog_passes_p90]
        sort_by_metric = 'prog_passes_p90'
    elif position_needed == "Defender":
        # Placeholder: would need defensive metrics (e.g. tackles_p90, interceptions_p90)
        # For now, if no specific metric, sort by a general one or don't sort by performance.
        # Let's use 'potential_score' as a generic proxy if available, otherwise no specific sort.
        if 'potential_score' in candidates.columns:
             sort_by_metric = 'potential_score' # Not ideal for defenders, but a placeholder
        print("Warning: No specific defensive metrics available for ranking defenders. Using generic score or age.")


    if sort_by_metric and sort_by_metric in candidates.columns:
        # Ensure players with more minutes are preferred if scores are similar (or add minutes as secondary sort)
        if 'minutes_played' in candidates.columns:
            candidates = candidates.sort_values(by=[sort_by_metric, 'minutes_played'], ascending=[False, False])
        else:
            candidates = candidates.sort_values(by=[sort_by_metric], ascending=[False])
    elif 'age_years' in candidates.columns: # Fallback sort by age (younger preferred)
        candidates = candidates.sort_values(by='age_years', ascending=True)

    return candidates.head(top_n)


if __name__ == "__main__":
    print("Starting Transfer Strategy Optimization process...")
    current_season = 2023 # Example season

        # 1. Fetch all necessary data
        print("\nFetching team standings...")
        standings_df = get_team_standings(season=current_season)

        if standings_df.empty:
            print("Could not fetch standings. Aborting.")
        else:
            league_avg_gs = standings_df['overall_goals_for'].mean()
            league_avg_gc = standings_df['overall_goals_against'].mean()
            print(f"League Averages: Goals Scored={league_avg_gs:.2f}, Goals Conceded={league_avg_gc:.2f}")

            print("\nFetching all EPL player data with engineered features (Challenge 1)...")
            # This will include bio, stats, and 'potential_score' if logic from C1 is run
            all_players_df = fetch_epl_player_data(season=current_season)
            if not all_players_df.empty:
                all_players_df = engineer_features(all_players_df.copy()) # From talent_identification.py

                # Augment with Challenge 2 metrics (Progressive Passes)
                # This part needs player IDs and simulated pass events
                player_ids_for_prog_pass = all_players_df[pd.to_numeric(all_players_df['minutes_played'], errors='coerce').fillna(0) > 0]['id'].tolist()
                if player_ids_for_prog_pass:
                    print("\nSimulating pass events and calculating progressive pass metrics (Challenge 2)...")
                    simulated_passes = simulate_player_pass_events(player_ids_for_prog_pass, num_events_per_player=50) # Reduced for speed

                    # Ensure required columns for calculate_progressive_pass_metrics are present
                    cols_for_prog_pass = ['id', 'name', 'position', 'team_name', 'minutes_played']
                    # Add 'assists' and 'passes_total' if they exist, otherwise fill with 0
                    for col in ['assists', 'passes_total']:
                         if col not in all_players_df.columns: all_players_df[col] = 0
                         else: all_players_df[col] = pd.to_numeric(all_players_df[col], errors='coerce').fillna(0)

                    all_players_df = calculate_progressive_pass_metrics(all_players_df.copy(), simulated_passes)
                else:
                    print("No players with minutes found to calculate progressive pass metrics.")
                    if 'prog_passes_p90' not in all_players_df.columns: all_players_df['prog_passes_p90'] = 0


                # --- Example: Analyze a specific team ---
                # Let's pick a team. For real use, this could be user input.
                # Find a mid-to-lower table team from standings if possible
                target_team_name_example = ""
                if len(standings_df) > 10 :
                    target_team_name_example = standings_df.sort_values(by='position', ascending=False).iloc[5]['team_name'] # e.g. 15th placed team
                    target_team_id_example = standings_df[standings_df['team_name'] == target_team_name_example]['team_id'].iloc[0]

                if not target_team_name_example:
                     # Fallback if standings are weird or too short
                    if not all_players_df.empty and 'team_name' in all_players_df.columns:
                        target_team_name_example = all_players_df['team_name'].unique()[0] if len(all_players_df['team_name'].unique()) > 0 else "AFC Bournemouth" # Default
                        # Try to get its ID from players_df if possible, or standings_df
                        if target_team_name_example in standings_df['team_name'].values:
                             target_team_id_example = standings_df[standings_df['team_name'] == target_team_name_example]['team_id'].iloc[0]
                        else: # Estimate ID if not in standings (less robust)
                             target_team_id_example = all_players_df[all_players_df['team_name'] == target_team_name_example]['team_ids'].iloc[0] if 'team_ids' in all_players_df.columns else 1 # dummy
                    else:
                        target_team_name_example = "AFC Bournemouth" # Default
                        target_team_id_example = 8 # Default ID for Bournemouth from quickstart
                        print(f"Warning: Could not dynamically select a target team. Using default: {target_team_name_example}")


                print(f"\n--- Analyzing Needs for Team: {target_team_name_example} (ID: {target_team_id_example}) ---")

                # Ensure 'team_name' is present in all_players_df for squad depth analysis
                if 'team_name' not in all_players_df.columns:
                    print("Error: 'team_name' column missing in player data. Cannot perform squad depth analysis.")
                else:
                    identified_needs = analyze_team_needs(target_team_id_example, target_team_name_example, standings_df, all_players_df, league_avg_gs, league_avg_gc)
                    print(f"Suggested positions to reinforce for {target_team_name_example}: {', '.join(identified_needs)}")

                    # 3. Get recommendations for the first identified need
                    if identified_needs and identified_needs[0] != "No obvious immediate gaps based on simplified analysis." and identified_needs[0] != "Unknown - No data":
                        position_to_fill = identified_needs[0]
                        print(f"\n--- Recommending players for {target_team_name_example} - Position: {position_to_fill} (Max Age: 28) ---")

                        # Define thresholds based on position
                        min_potential = 0.05 if position_to_fill == "Forward" else None # Example threshold
                        min_prog_p90 = 5 if position_to_fill == "Midfielder" else None # Example threshold for prog passes

                        recommendations = recommend_players(
                            target_team_name=target_team_name_example,
                            position_needed=position_to_fill,
                            all_players_df=all_players_df,
                            max_age=28,
                            min_potential_score=min_potential,
                            min_prog_passes_p90=min_prog_p90,
                            top_n=5
                        )

                        if not recommendations.empty:
                            print("Top recommendations:")
                            output_cols = ['name', 'age_years', 'team_name', 'position', 'minutes_played']
                            if 'potential_score' in recommendations.columns: output_cols.append('potential_score')
                            if 'prog_passes_p90' in recommendations.columns: output_cols.append('prog_passes_p90')
                            if 'goals' in recommendations.columns: output_cols.append('goals')
                            if 'assists' in recommendations.columns: output_cols.append('assists')

                            # Filter out columns that might not exist or are all NaN to avoid errors printing
                            recommendations_to_print = recommendations[output_cols].copy()
                            recommendations_to_print = recommendations_to_print.dropna(axis=1, how='all')
                            print(recommendations_to_print)
                        else:
                            print(f"No suitable players found for {position_to_fill} based on the criteria.")
                    else:
                        print(f"No specific needs identified for {target_team_name_example} or unable to proceed with recommendations.")
            else:
                print("Could not fetch player data. Aborting transfer optimization.")

    print("\nTransfer Optimization script finished.")
