import pandas as pd

class PlayerManager:
    def __init__(self):
        self.players = pd.DataFrame(columns=[
            'First Name', 'Last Name', 'Gender', 'Skill', 'Points' 'Checked In', 'Team', 'New', 'Modified'
        ])

    def load_from_csv(self, file_path):
        df = pd.read_csv(file_path)

        # Normalize column names
        df.columns = df.columns.str.lower()

        # Map only required columns, ignoring extras
        columns = {
            "first_name": "First Name",
            "last_name": "Last Name",
            "gender": "Gender"
        }
        new_df = df.rename(columns=columns)[list(columns.values())]

        # Add skill column (default to 5 if missing)
        if 'Skill' in df.columns:
            new_df['Skill'] = df['Skill']
        else:
            new_df['Skill'] = 5

        # Add Point column (default to 0 if missing)
        if 'Point' in df.columns:
            new_df['Point'] = df['Point']
        else:
            new_df['Point'] = 0    

        # Add extra columns required by app
        new_df['Checked In'] = False
        new_df['Team'] = None
        new_df['New'] = False
        new_df['Modified'] = False

        self.players = new_df

    def save_to_csv(self, file_path):
        export_df = self.players.copy()

        # Rename headers to lowercase format
        export_df = export_df.rename(columns={
            "First Name": "first_name",
            "Last Name": "last_name",
            "Gender": "gender"
        })

        export_df.to_csv(file_path, index=False)

    def get_checked_in_players(self):
        return self.players[self.players['Checked In'] == True]

    def add_player(self, first_name, last_name, gender, skill):
        new_player = {
            'First Name': first_name,
            'Last Name': last_name,
            'Gender': gender,
            'Skill': skill,
            'Checked In': True,
            'Team': None,
            'New': True,
            'Modified': False
        }
        self.players = pd.concat([self.players, pd.DataFrame([new_player])], ignore_index=True)

    def update_skill(self, index, new_skill):
        if self.players.at[index, 'Skill'] != new_skill:
            self.players.at[index, 'Skill'] = new_skill
            self.players.at[index, 'Modified'] = True

    def set_checked_in(self, index, checked_in):
        self.players.at[index, 'Checked In'] = checked_in

    def assign_team(self, index, team_name):
        self.players.at[index, 'Team'] = team_name

    def get_all_players(self):
        return self.players
