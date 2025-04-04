import random
import pandas as pd

def generate(player_manager, num_teams):
    df = player_manager.get_checked_in_players().copy()

    if len(df) < num_teams:
        raise ValueError("Not enough players to create the requested number of teams.")

    # Separate by gender for balancing
    males = df[df['Gender'].str.lower() == 'male']
    females = df[df['Gender'].str.lower() == 'female']

    teams = [[] for _ in range(num_teams)]
    team_skills = [0] * num_teams

    def distribute(players):
        # Sort by skill descending for fair distribution
        sorted_players = players.sort_values(by='Skill', ascending=False)
        for i, (_, row) in enumerate(sorted_players.iterrows()):
            team_index = i % num_teams
            teams[team_index].append(row)
            team_skills[team_index] += row['Skill']

    # Distribute genders separately to balance both skill and gender
    distribute(males)
    distribute(females)

    # Flatten teams and assign team names
    for i, team in enumerate(teams):
        for player in team:
            idx = player_manager.players[(player_manager.players['First Name'] == player['First Name']) &
                                         (player_manager.players['Last Name'] == player['Last Name']) &
                                         (player_manager.players['Gender'] == player['Gender']) &
                                         (player_manager.players['Skill'] == player['Skill'])].index
            if not idx.empty:
                player_manager.assign_team(idx[0], f"Team {i+1}")
