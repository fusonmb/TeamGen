def generate(manager, num_teams):
    import random
    df = manager.get_all_players()
    checked_in = df[df['Checked In']]

    if len(checked_in) < num_teams:
        raise ValueError("Not enough checked-in players to form the requested number of teams.")

    teams = {f"Team {i+1}": [] for i in range(num_teams)}

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

    # Apply assignments
    for team_name, indices in teams.items():
        for idx in indices:
            manager.assign_team(idx, team_name)
