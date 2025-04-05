import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import pandas as pd
from player_manager import PlayerManager
import team_generator

class TeamBuilderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Team Generator")

        self.manager = PlayerManager()
        self.num_teams = tk.IntVar(value=2)
        self.check_vars = {}
        self.sort_column = None
        self.sort_reverse = False
        self.gender_filter = tk.StringVar(value="All")

        self.setup_widgets()

    def setup_widgets(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Main tab
        self.main_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.main_frame, text="Players")

        self.setup_main_tab(self.main_frame)

        # Teams tab
        self.teams_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.teams_frame, text="Teams")

        # Frame for the persistent "Generate Teams" button
        self.teams_button_frame = ttk.Frame(self.teams_frame)
        self.teams_button_frame.pack(fill=tk.X, pady=5)

        gen_btn_teams = ttk.Button(self.teams_button_frame, text="Generate Teams", command=self.generate_teams)
        gen_btn_teams.pack(padx=10, pady=5, anchor="center")

        # Frame where team tables will be refreshed
        self.teams_table_area = ttk.Frame(self.teams_frame)
        self.teams_table_area.pack(fill=tk.BOTH, expand=True)

        self.team_tables = []

    def setup_main_tab(self, parent):
        frame = ttk.Frame(parent, padding=10)
        # Frame for live counters
        self.counter_frame = ttk.Frame(parent, padding=(10, 5), height=30)
        self.counter_frame.grid(row=1, column=0, sticky="w")
        self.counter_frame.grid_propagate(False)  # Prevent frame from resizing to fit content

        self.checkin_label = ttk.Label(self.counter_frame, text="Checked-in Players: 0")
        self.checkin_label.pack(side=tk.LEFT, padx=(0, 20))

        self.gender_label = ttk.Label(self.counter_frame, text="Males: 0 | Females: 0")
        self.gender_label.pack(side=tk.LEFT, padx=(0, 20))

        self.team_count_label = ttk.Label(self.counter_frame, text="Checked-in per Team: None")
        self.team_count_label.pack(side=tk.LEFT)

        frame.grid(row=0, column=0, sticky="ew")

        load_btn = ttk.Button(frame, text="Load CSV", command=self.load_csv)
        load_btn.grid(row=0, column=0, padx=5, pady=5)

        save_btn = ttk.Button(frame, text="Save CSV", command=self.save_csv)
        save_btn.grid(row=0, column=1, padx=5, pady=5)

        gen_btn = ttk.Button(frame, text="Generate Teams", command=self.generate_teams)
        gen_btn.grid(row=0, column=2, padx=5, pady=5)

        team_options = [i for i in range(2, 11)]
        ttk.Label(frame, text="Number of Teams:").grid(row=0, column=3, padx=(10, 2), pady=5, sticky="e")
        team_menu = ttk.OptionMenu(frame, self.num_teams, self.num_teams.get(), *team_options, command=lambda _: self.update_checkin_counts())
        team_menu.grid(row=0, column=4, padx=5, pady=5)

        ttk.Label(frame, text="Gender Filter:").grid(row=0, column=5, padx=(10, 2), pady=5, sticky="e")
        gender_options = ttk.OptionMenu(frame, self.gender_filter, "All", "All", "Male", "Female", command=lambda _: self.refresh_tree())
        gender_options.grid(row=0, column=6, padx=5, pady=5)
        
        add_btn = ttk.Button(frame, text="Add Player", command=self.add_player_window)
        add_btn.grid(row=0, column=7, padx=5, pady=5)

        toggle_btn = ttk.Button(frame, text="Toggle Check-In", command=self.toggle_all_checkin)
        toggle_btn.grid(row=0, column=8, padx=5, pady=5)

        self.tree_frame = ttk.Frame(parent)
        self.tree_frame.grid(row=2, column=0, sticky="nsew")

        self.tree_canvas = tk.Canvas(self.tree_frame)
        self.tree_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree_canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree_canvas.configure(yscrollcommand=self.scrollbar.set)
        self.tree_canvas.bind('<Configure>', lambda e: self.tree_canvas.configure(scrollregion=self.tree_canvas.bbox("all")))

        self.inner_frame = ttk.Frame(self.tree_canvas)
        self.tree_canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")

        parent.rowconfigure(2, weight=1)
        parent.columnconfigure(0, weight=1)

    def load_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if file_path:
            self.manager.load_from_csv(file_path)
            self.refresh_tree()

    def save_csv(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if file_path:
            self.manager.save_to_csv(file_path)
            messagebox.showinfo("Saved", f"Saved to {file_path}")

    def refresh_tree(self):
        for widget in self.inner_frame.winfo_children():
            widget.destroy()
        self.check_vars = {}

        header = ["Checked In", "First Name", "Last Name", "Gender", "Skill", "Team"]
        for col_index, col in enumerate(header):
            lbl = ttk.Label(self.inner_frame, text=col, font=("Arial", 10, "bold"))
            lbl.grid(row=0, column=col_index, padx=5, pady=2)
            if col in ["First Name", "Last Name", "Skill", "Team", "Gender"]:
                lbl.bind("<Button-1>", lambda e, c=col: self.sort_by_column(c))

        df = self.manager.get_all_players()
        if self.gender_filter.get() != "All":
            df = df[df['Gender'].str.lower() == self.gender_filter.get().lower()]

        if self.sort_column:
            df = df.sort_values(
                by=['Checked In', self.sort_column],
                key=lambda col: col.str.lower() if col.dtype == 'object' else col,
                ascending=[False, not self.sort_reverse]
                ).reset_index(drop=True)

        for row_num, (_, row) in enumerate(df.iterrows(), start=1):
            check_var = tk.BooleanVar(value=bool(row['Checked In']))
            command = lambda name=row['First Name'], last=row['Last Name'], gender=row['Gender'], var=check_var: (
                self.set_checked_in_by_identity(name, last, gender, var.get()),
                self.update_checkin_counts()
            ) 
            check = ttk.Checkbutton(self.inner_frame, variable=check_var, command=command)
            check.grid(row=row_num, column=0, padx=5, pady=2)
            # No need to track check_vars by index anymore

            ttk.Label(self.inner_frame, text=row['First Name']).grid(row=row_num, column=1)
            ttk.Label(self.inner_frame, text=row['Last Name']).grid(row=row_num, column=2)
            ttk.Label(self.inner_frame, text=row['Gender']).grid(row=row_num, column=3)

            skill_lbl = ttk.Label(self.inner_frame, text=row['Skill'])
            skill_lbl.grid(row=row_num, column=4)
            skill_lbl.bind("<Double-1>", lambda e, fn=row['First Name'], ln=row['Last Name'], g=row['Gender']: self.edit_skill_by_identity(fn, ln, g))

            ttk.Label(self.inner_frame, text=row['Team'] if pd.notna(row['Team']) else "").grid(row=row_num, column=5)

        self.num_teams.trace_add("write", lambda *args: self.update_checkin_counts())

        self.refresh_team_tables()

    def refresh_team_tables(self):
        for widget in self.teams_table_area.winfo_children():
            widget.destroy()
        self.team_tables.clear()

        df = self.manager.get_all_players()
        assigned = df[df['Team'].notna()]

        team_names = sorted(assigned['Team'].dropna().unique())

        for team_name in team_names:
            team_df = assigned[assigned['Team'] == team_name]

            frame = ttk.LabelFrame(self.teams_table_area, text=team_name)
            frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

            table = ttk.Treeview(frame, columns=("First Name", "Last Name", "Gender", "Skill"), show="headings")
            for col in table["columns"]:
                table.heading(col, text=col, command=lambda c=col, t=table, df=team_df: self.sort_team_table(t, df, c))
                table.column(col, width=100)

            for _, row in team_df.iterrows():
                table.insert("", "end", values=(row['First Name'], row['Last Name'], row['Gender'], row['Skill']))

            table.pack(fill=tk.BOTH, expand=True)
            # Show average skill
            avg_skill = team_df['Skill'].mean()
            avg_label = ttk.Label(frame, text=f"Average Skill: {avg_skill:.2f}", font=("Arial", 10, "italic"))
            avg_label.pack(pady=(5, 0))

            self.team_tables.append(table)

    def sort_by_column(self, column):
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False
        self.refresh_tree()

    def edit_skill_by_identity(self, first_name, last_name, gender):
        df = self.manager.get_all_players()
        match = df[(df['First Name'] == first_name) & (df['Last Name'] == last_name) & (df['Gender'] == gender)]

        if not match.empty:
            idx = match.index[0]
            new_value = tk.simpledialog.askinteger("Edit Skill", f"Enter new skill for {first_name} {last_name}:")
            if new_value is not None:
                self.manager.update_skill(idx, new_value)
                self.refresh_tree()


    def add_player_window(self):
        win = tk.Toplevel(self.root)
        win.title("Add Player")
        fields = ["First Name", "Last Name", "Gender", "Skill"]
        entries = {}
        
        for i, field in enumerate(fields):
            ttk.Label(win, text=field).grid(row=i, column=0, padx=5, pady=5)

            if field == "Gender":
                gender_var = tk.StringVar(value="Male")
                dropdown = ttk.OptionMenu(win, gender_var, "Male", "Male", "Female")
                dropdown.grid(row=i, column=1, padx=5, pady=5)
                entries[field] = gender_var
            else:
                entry = ttk.Entry(win)
                entry.grid(row=i, column=1, padx=5, pady=5)
                entries[field] = entry

        def submit():
            try:
                skill = int(entries["Skill"].get())
            except ValueError:
                messagebox.showerror("Invalid Input", "Skill must be an integer")
                return

            self.manager.add_player(
                entries["First Name"].get(),
                entries["Last Name"].get(),
                entries["Gender"].get(),
                skill
            )
            win.destroy()
            self.refresh_tree()

        ttk.Button(win, text="Add", command=submit).grid(row=4, column=0, columnspan=2, pady=10)

    def sort_team_table(self, table, df, column):
        if not hasattr(table, 'last_sorted_column'):
            table.last_sorted_column = None
            table.sort_reverse = False

        if table.last_sorted_column == column:
            table.sort_reverse = not table.sort_reverse
        else:
            table.last_sorted_column = column
            table.sort_reverse = False

        sorted_df = df.sort_values(
            by=column,
            key=lambda col: col.str.lower() if col.dtype == 'object' else col,
            ascending=not table.sort_reverse
        )

        for row in table.get_children():
            table.delete(row)
        for _, row in sorted_df.iterrows():
            table.insert("", "end", values=(row['First Name'], row['Last Name'], row['Gender'], row['Skill']))

    def set_checked_in_by_identity(self, first_name, last_name, gender, checked_in):
        df = self.manager.get_all_players()
        match = df[(df['First Name'] == first_name) & (df['Last Name'] == last_name) & (df['Gender'] == gender)]
        if not match.empty:
            self.manager.set_checked_in(match.index[0], checked_in)

    def generate_teams(self):
        # Sync checkbox states back to manager
        for idx, var in self.check_vars.items():
            self.manager.set_checked_in(idx, var.get())
        # Clear team assignment for any player who is no longer checked in
        for idx, row in self.manager.get_all_players().iterrows():
            if not row['Checked In']:
                self.manager.assign_team(idx, None)

        try:
            team_generator.generate(self.manager, self.num_teams.get())
            self.refresh_tree()
        except Exception as e:
            messagebox.showerror("Error", str(e))

        self.num_teams.trace_add("write", lambda *args: self.update_checkin_counts())

    def toggle_all_checkin(self):
        df = self.manager.get_all_players()
        # Determine majority status and toggle to opposite
        checked_count = df['Checked In'].sum()
        new_status = False if checked_count > len(df) / 2 else True

        for idx in df.index:
            self.manager.set_checked_in(idx, new_status)

        self.num_teams.trace_add("write", lambda *args: self.update_checkin_counts())

        self.refresh_tree()

    def update_checkin_counts(self):
        df = self.manager.get_all_players()
        checked = df[df['Checked In']]

        total = len(checked)
        males = len(checked[checked['Gender'].str.lower() == 'male'])
        females = len(checked[checked['Gender'].str.lower() == 'female'])
        numTeams = float(self.num_teams.get())

        self.checkin_label.config(text=f"Checked-in Players: {total}")
        self.gender_label.config(text=f"Males: {males} | Females: {females}")

        # Count checked-in players per team
        self.team_count_label.config(text=f"Checked-in per Team: {total/numTeams}")

if __name__ == "__main__":
    root = tk.Tk()
    app = TeamBuilderGUI(root)
    root.mainloop()
