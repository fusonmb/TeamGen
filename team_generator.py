import random
import numpy as np

def generate(manager, num_teams, lock_teams=False):
    df = manager.get_all_players()
    checked_in = df[df['Checked In']]

    if len(checked_in) < num_teams:
        raise ValueError("Not enough checked-in players to form the requested number of teams.")

    teams = {f"Team {i+1}": [] for i in range(num_teams)}

    if not lock_teams:
        # Clear all previous team assignments
        for idx in df.index:
            manager.assign_team(idx, None)

        def snake_assign(players, start_low=True):
            players = players.copy()
            players['__rand'] = [random.random() for _ in range(len(players))]
            players = players.sort_values(by=['Skill', '__rand'], ascending=[False, True])
            players = players.drop(columns=['__rand'])

            direction = 1 if start_low else -1
            idx = 0 if start_low else num_teams - 1
            going_up = True if start_low else False

            for player_idx in players.index:
                team_name = f"Team {idx + 1}"
                teams[team_name].append(player_idx)

                # Move index
                if going_up:
                    idx += 1
                    if idx >= num_teams:
                        idx = num_teams - 1
                        going_up = False
                else:
                    idx -= 1
                    if idx < 0:
                        idx = 0
                        going_up = True

        # Separate by gender
        males = checked_in[checked_in['Gender'].str.lower() == 'male']
        females = checked_in[checked_in['Gender'].str.lower() == 'female']

        # Females assigned to highest teams first → snake down
        snake_assign(females, start_low=False)
        # Males assigned to lowest teams first → snake up
        snake_assign(males, start_low=True)

    else:
        # Lock team assignments: preserve existing, only assign unassigned
        assigned = checked_in[checked_in['Team'].notna()]
        unassigned = checked_in[checked_in['Team'].isna()]

        for idx, row in assigned.iterrows():
            teams[row['Team']].append(idx)

        for gender in ['Male', 'Female']:
            players = unassigned[unassigned['Gender'].str.lower() == gender.lower()]
            for idx, row in players.iterrows():
                # Gender counts per team
                gender_counts = {
                    team: sum(df.loc[i]['Gender'].lower() == gender.lower() for i in members)
                    for team, members in teams.items()
                }

                # Teams with fewest of this gender
                min_count = min(gender_counts.values())
                candidate_teams = [team for team, count in gender_counts.items() if count == min_count]

                # Choose team that balances skill
                if len(candidate_teams) > 1:
                    avg_skills = {}
                    for team in candidate_teams:
                        skills = [df.loc[i]['Skill'] for i in teams[team]]
                        avg = np.mean(skills) if skills else 0
                        new_avg = (sum(skills) + row['Skill']) / (len(skills) + 1)
                        avg_skills[team] = abs(new_avg - np.mean([np.mean([df.loc[i]['Skill'] for i in t]) if t else 0 for t in teams.values()]))

                    best_team = min(avg_skills, key=avg_skills.get)
                else:
                    best_team = candidate_teams[0]

                teams[best_team].append(idx)

    # Apply assignments
    for team_name, indices in teams.items():
        for idx in indices:
            manager.assign_team(idx, team_name)
