import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import datetime
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
        self.lock_teams = tk.BooleanVar(value=False)
        self.team_results = {}
        self.display_order = []
        self.last_sorted_order = []

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

        lock_check_teams = ttk.Checkbutton(self.teams_button_frame, text="Lock Teams", variable=self.lock_teams)
        lock_check_teams.pack(side=tk.LEFT, padx=10)

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

        count_font_style = ("Arial", 12, "bold")  # You can adjust size/style here
        self.checkin_label = ttk.Label(self.counter_frame, text="Players: 0", font=count_font_style)
        self.checkin_label.pack(side=tk.LEFT, padx=(0, 20))

        self.gender_label = ttk.Label(self.counter_frame, text="Males: 0 | Females: 0", font=count_font_style)
        self.gender_label.pack(side=tk.LEFT, padx=(0, 20))

        self.team_count_label = ttk.Label(self.counter_frame, text="Players Per Team: 0 | M: 0 | F: 0", font=count_font_style)
        self.team_count_label.pack(side=tk.LEFT)

        frame.grid(row=0, column=0, sticky="ew")

        load_btn = ttk.Button(frame, text="Load CSV", command=self.load_csv)
        load_btn.grid(row=0, column=0, padx=5, pady=5)

        save_btn = ttk.Button(frame, text="Save CSV", command=self.save_csv)
        save_btn.grid(row=0, column=1, padx=5, pady=5)

        gen_btn = ttk.Button(frame, text="Generate Teams", command=self.generate_teams)
        gen_btn.grid(row=0, column=2, padx=5, pady=5)

        lock_check = ttk.Checkbutton(frame, text="Lock Teams", variable=self.lock_teams)
        lock_check.grid(row=0, column=3, padx=5, pady=5)

        team_options = [i for i in range(2, 11)]
        ttk.Label(frame, text="Number of Teams:").grid(row=0, column=4, padx=(10, 2), pady=5, sticky="e")
        team_menu = ttk.OptionMenu(frame, self.num_teams, self.num_teams.get(), *team_options, command=lambda _: self.update_checkin_counts())
        team_menu.grid(row=0, column=5, padx=5, pady=5)

        ttk.Label(frame, text="Gender Filter:").grid(row=0, column=6, padx=(10, 2), pady=5, sticky="e")
        gender_options = ttk.OptionMenu(frame, self.gender_filter, "All", "All", "Male", "Female", command=lambda _: self.refresh_tree())
        gender_options.grid(row=0, column=7, padx=5, pady=5)
        
        add_btn = ttk.Button(frame, text="Add Player", command=self.add_player_window)
        add_btn.grid(row=0, column=8, padx=5, pady=5)

        # toggle_btn = ttk.Button(frame, text="Toggle Check-In", command=self.toggle_all_checkin)
        # toggle_btn.grid(row=0, column=8, padx=5, pady=5)

        # Container for both headers and scrollable body
        self.table_container = ttk.Frame(parent)
        self.table_container.grid(row=2, column=0, sticky="nsew")
        parent.rowconfigure(2, weight=1)
        parent.columnconfigure(0, weight=1)

        # Canvas wraps both headers and table rows
        self.tree_canvas = tk.Canvas(self.table_container)
        self.tree_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar
        self.scrollbar = ttk.Scrollbar(self.table_container, orient="vertical", command=self.tree_canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Scrollable frame within canvas
        self.scrollable_frame = ttk.Frame(self.tree_canvas)
        self.tree_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Header (inside scrollable frame)
        self.header_frame = ttk.Frame(self.scrollable_frame)
        self.header_frame.pack(fill=tk.X)

        # Inner table (inside scrollable frame)
        self.inner_frame = ttk.Frame(self.scrollable_frame)
        self.inner_frame.pack(fill=tk.BOTH, expand=True)

        # Configure scrolling
        self.tree_canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollable_frame.bind("<Configure>", lambda e: self.tree_canvas.configure(scrollregion=self.tree_canvas.bbox("all")))

        # Scroll wheel support
        self.tree_canvas.bind_all("<MouseWheel>", lambda e: self.tree_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
        self.tree_canvas.bind_all("<Button-4>", lambda e: self.tree_canvas.yview_scroll(-1, "units"))
        self.tree_canvas.bind_all("<Button-5>", lambda e: self.tree_canvas.yview_scroll(1, "units"))


        parent.rowconfigure(2, weight=1)
        parent.columnconfigure(0, weight=1)

    def load_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if file_path:
            self.manager.load_from_csv(file_path)
            self.refresh_tree()

    def save_csv(self):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
        default_name = f"TeamGen_{timestamp}.csv"

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=default_name,
            filetypes=[("CSV Files", "*.csv")]
        )

        if file_path:
            self.manager.save_to_csv(file_path)
            messagebox.showinfo("Saved", f"Saved to {file_path}")

    def refresh_tree(self, preserve_order=False):
        for widget in self.inner_frame.winfo_children():
            widget.destroy()        
        for widget in self.header_frame.winfo_children():
            widget.destroy()

        self.check_vars = {}
        header = ["Checked In", "First Name", "Last Name", "Gender", "Skill", "Points", "Team"]

        for col_index, col in enumerate(header):
            sort_indicator = ""
            if self.sort_column == col:
                sort_indicator = " ▲" if not self.sort_reverse else " ▼"

            lbl = ttk.Label(
                self.header_frame,
                text=col + sort_indicator,
                font=("Arial", 10, "bold"))
            
            lbl.grid(row=0, column=col_index, padx=5, pady=2, sticky="nsew")
            if col in ["Checked In","First Name", "Last Name", "Skill", "Points", "Team", "Gender"]:
                lbl.bind("<Button-1>", lambda e, c=col: self.sort_by_column(c))
            self.header_frame.grid_columnconfigure(col_index, weight=1, uniform="col")
            self.inner_frame.grid_columnconfigure(col_index, weight=1, uniform="col")

        df = self.manager.get_all_players()
        if self.gender_filter.get() != "All":
            df = df[df['Gender'].str.lower() == self.gender_filter.get().lower()]

        if self.sort_column:
            # Create a map from full row tuple to its screen position
            order_map = {row: i for i, row in enumerate(self.last_sorted_order)}

            # Create row identity for each row in the new DataFrame
            df = df.assign(__display_order=df.apply(
                lambda row: order_map.get(tuple(row), len(order_map)),
                axis=1
            ))

            # Sort by selected column, then by previous screen order
            df = df.sort_values(
                by=[self.sort_column, '__display_order'],
                key=lambda col: col.str.lower() if col.dtype == 'object' else col,
                ascending=[not self.sort_reverse, True]
            ).drop(columns='__display_order').reset_index(drop=True)

        for row_num, (_, row) in enumerate(df.iterrows(), start=1):
            check_var = tk.BooleanVar(value=bool(row['Checked In']))
            command = lambda name=row['First Name'], last=row['Last Name'], gender=row['Gender'], var=check_var: (
                self.set_checked_in_by_identity(name, last, gender, var.get()),
                self.update_checkin_counts())
            
            check = ttk.Checkbutton(self.inner_frame, variable=check_var, command=command)
            check.grid(row=row_num, column=0, padx=5, pady=2, sticky="nsew")

            ttk.Label(self.inner_frame, text=row['First Name']).grid(row=row_num, column=1, sticky="nsew")
            ttk.Label(self.inner_frame, text=row['Last Name']).grid(row=row_num, column=2, sticky="nsew")
            ttk.Label(self.inner_frame, text=row['Gender']).grid(row=row_num, column=3, sticky="nsew")

            skill_lbl = ttk.Label(self.inner_frame, text=row['Skill'])
            skill_lbl.grid(row=row_num, column=4, sticky="nsew")
            skill_lbl.bind(
                "<Double-1>",
                lambda e, fn=row['First Name'], ln=row['Last Name'], g=row['Gender']: self.edit_skill_by_identity(fn, ln, g))

            ttk.Label(self.inner_frame, text=row.get('Points', "")).grid(row=row_num, column=5, sticky="nsew")
            ttk.Label(self.inner_frame, text=row['Team'] if pd.notna(row['Team']) else "").grid(row=row_num, column=6, sticky="nsew")
        self.num_teams.trace_add("write", lambda *args: self.update_checkin_counts())

        self.refresh_team_tables()
        self.tree_canvas.configure(scrollregion=self.tree_canvas.bbox("all"))
        self.last_sorted_order = list(df.itertuples(index=False, name=None))

    def refresh_team_tables(self):
        for widget in self.teams_frame.winfo_children():
            widget.destroy()
        self.team_tables.clear()

        # Create scrollable canvas for teams
        canvas = tk.Canvas(self.teams_frame)
        scrollbar = ttk.Scrollbar(self.teams_frame, orient="vertical", command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        canvas.configure(yscrollcommand=scrollbar.set)

        # Container frame inside canvas
        scrollable_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        # Update scrollregion when widgets resize
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        df = self.manager.get_all_players()
        assigned = df[df['Team'].notna()]

        team_names = sorted(assigned['Team'].dropna().unique())

        max_columns = 3  # Adjust this number as desired
        row, col = 0, 0

        for team_name in team_names:
            team_df = assigned[assigned['Team'] == team_name]

            frame = ttk.LabelFrame(scrollable_frame, text=team_name)
            frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

            # Result dropdown
            top_row = ttk.Frame(frame)
            top_row.pack(fill=tk.X, padx=5, pady=(0, 5))

            ttk.Label(top_row, text="Result:").pack(side=tk.LEFT, padx=(0, 5))

            result_var = tk.StringVar(value=self.team_results.get(team_name, "Undecided"))
            result_dropdown = ttk.OptionMenu(
                top_row,
                result_var,
                result_var.get(),
                "Undecided", "Win", "Loss",
                command=lambda _, t=team_name, v=result_var: self.on_result_change(t, v)            )
            result_dropdown.pack(side=tk.LEFT)

            table = ttk.Treeview(frame, columns=("First Name", "Last Name", "Gender", "Skill"), show="headings")
            for col_name in table["columns"]:
                table.heading(col_name, text=col_name, command=lambda c=col_name, t=table, df=team_df: self.sort_team_table(t, df, c))
                table.column(col_name, width=100)

            for _, row_data in team_df.iterrows():
                table.insert("", "end", values=(row_data['First Name'], row_data['Last Name'], row_data['Gender'], row_data['Skill']))

            table.pack(fill=tk.BOTH, expand=True)
            self.team_tables.append(table)

            col += 1
            if col >= max_columns:
                col = 0
                row += 1

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
                gender_var = tk.StringVar(value="male")
                dropdown = ttk.OptionMenu(win, gender_var, "male", "male", "female")
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
            idx = match.index[0]
            current_status = df.at[idx, 'Checked In']
            if current_status != checked_in:
                self.manager.set_checked_in(idx, checked_in)
                # Update points
                if checked_in:
                    self.manager.increment_points(idx, 1)
                else:
                    self.manager.increment_points(idx, -1)

                self.refresh_tree()
                self.update_checkin_counts()

    def generate_teams(self):
        # Sync checkbox states back to manager
        for idx, var in self.check_vars.items():
            self.manager.set_checked_in(idx, var.get())
        # Clear team assignment for any player who is no longer checked in
        for idx, row in self.manager.get_all_players().iterrows():
            if not row['Checked In']:
                self.manager.assign_team(idx, None)

        try:
            team_generator.generate(
                manager=self.manager,
                num_teams=self.num_teams.get(),
                lock_teams=self.lock_teams.get())
            
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

        self.checkin_label.config(text=f"Players: {total}")
        self.gender_label.config(text=f"Males: {males} | Females: {females}")

        # Count checked-in players per team
        self.team_count_label.config(text=f"Players Per Team:  {total/numTeams:.2f} |   M: {males/numTeams:.2f} |   F: {females/numTeams:.2f}")

    def update_team_result_points(self, team_name, old_result, new_result):
        df = self.manager.get_all_players()
        for idx, row in df.iterrows():
            if row['Team'] == team_name:
                if old_result == "Win" and new_result != "Win":
                    self.manager.increment_points(idx, -1)
                elif old_result != "Win" and new_result == "Win":
                    self.manager.increment_points(idx, 1)

    def on_result_change(self, team_name, result_var):
        old_result = self.team_results.get(team_name, "Undecided")
        new_result = result_var.get()
        if old_result != new_result:
            self.team_results[team_name] = new_result
            self.update_team_result_points(team_name, old_result, new_result)
            self.refresh_tree()
            self.update_checkin_counts()  # optional, to keep counters in sync

if __name__ == "__main__":
    root = tk.Tk()
    app = TeamBuilderGUI(root)
    root.mainloop()
