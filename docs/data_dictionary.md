# EPL Data Dictionary

This document provides a detailed explanation of all data fields available through the API.

## Team Data

| Field | Type | Description |
|-------|------|-------------|
| id | int | Unique identifier for the team |
| name | string | Full team name (e.g., "Manchester United") |
| short_name | string | Abbreviated team name (e.g., "Man Utd") |
| abbr | string | Team abbreviation (e.g., "MUN") |
| city | string | City where the team is based |
| stadium | string | Home stadium name |

## Player Data

| Field | Type | Description |
|-------|------|-------------|
| id | int | Unique identifier for the player |
| name | string | Full player name |
| first_name | string | Player's first name |
| last_name | string | Player's last name |
| position | string | Player's primary position (e.g., "Forward", "Midfielder") |
| national_team | string | National team the player represents |
| height | float | Player height in cm |
| weight | float | Player weight in kg |
| birth_date | string | Player's date of birth (YYYY-MM-DD) |
| age | string | Player's age |
| team_ids | list[int] | Teams the player has been associated with |

## Game Data

| Field | Type | Description |
|-------|------|-------------|
| id | int | Unique identifier for the game |
| season | int | Season year (e.g., 2023 for 2023-2024 season) |
| week | float | Match week number |
| kickoff | string | Scheduled kickoff time (ISO format) |
| home_team_id | int | ID of the home team |
| away_team_id | int | ID of the away team |
| home_score | float | Goals scored by home team |
| away_score | float | Goals scored by away team |
| status | string | Match status (e.g., "SCHEDULED", "LIVE", "FINISHED") |
| ground | string | Stadium where the match is played |
| clock | float | Match clock in minutes |
| clock_display | string | Formatted match clock display |
| extra_time | boolean | Whether the match went to extra time |

## Player Statistics

The API provides a wide range of player statistics, including:

| Statistic | Description |
|-----------|-------------|
| goals | Number of goals scored |
| goal_assist | Number of goal assists |
| appearances | Number of match appearances |
| mins_played | Minutes played |
| clean_sheet | Clean sheets (for defenders and goalkeepers) |
| yellow_card | Yellow cards received |
| red_card | Red cards received |
| total_pass | Total passes attempted |
| touches | Total ball touches |
| total_scoring_att | Total scoring attempts |
| hit_woodwork | Shots hitting the woodwork |
| big_chance_missed | Big chances missed |
| total_offside | Offsides |
| total_tackle | Tackles made |
| fouls | Fouls committed |
| dispossessed | Times dispossessed |
| own_goals | Own goals scored |
| total_clearance | Clearances made |
| clearance_off_line | Clearances off the line |
| saves | Saves made (for goalkeepers) |
| penalty_save | Penalties saved (for goalkeepers) |
| total_high_claim | High claims (for goalkeepers) |
| punches | Punches (for goalkeepers) |

## Team Statistics

The API provides team statistics, including:

| Statistic | Description |
|-----------|-------------|
| wins | Number of wins |
| losses | Number of losses |
| touches | Total team touches |
| total_pass | Total team passes |
| goals | Total goals scored |
| total_scoring_att | Total scoring attempts |
| total_tackle | Total tackles |
| total_clearance | Total clearances |
| clean_sheet | Clean sheets |
| total_yel_card | Total yellow cards |
| total_red_card | Total red cards |

## Standing Data

Detailed league standings including:

| Field | Type | Description |
|-------|------|-------------|
| team | object | Team object |
| season | int | Season year |
| position | float | Current league position |
| form | string | Recent form (e.g., "WWDLW") |
| overall_played | float | Total matches played |
| overall_won | float | Total matches won |
| overall_drawn | float | Total matches drawn |
| overall_lost | float | Total matches lost |
| overall_goals_for | float | Total goals scored |
| overall_goals_against | float | Total goals conceded |
| overall_goals_difference | float | Goal difference |
| overall_points | float | Total points |
| home_played | float | Home matches played |
| home_won | float | Home matches won |
| home_drawn | float | Home matches drawn |
| home_lost | float | Home matches lost |
| home_goals_for | float | Goals scored at home |
| home_goals_against | float | Goals conceded at home |
| home_goals_difference | float | Home goal difference |
| home_points | float | Points from home matches |
| away_played | float | Away matches played |
| away_won | float | Away matches won |
| away_drawn | float | Away matches drawn |
| away_lost | float | Away matches lost |
| away_goals_for | float | Goals scored away |
| away_goals_against | float | Goals conceded away |
| away_goals_difference | float | Away goal difference |
| away_points | float | Points from away matches |