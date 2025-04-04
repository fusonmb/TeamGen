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
        self.team_tables = []

    def setup_main_tab(self, parent):
        frame = ttk.Frame(parent, padding=10)
        frame.grid(row=0, column=0, sticky="nsew")

        load_btn = ttk.Button(frame, text="Load CSV", command=self.load_csv)
        load_btn.grid(row=0, column=0, padx=5, pady=5)

        save_btn = ttk.Button(frame, text="Save CSV", command=self.save_csv)
        save_btn.grid(row=0, column=1, padx=5, pady=5)

        gen_btn = ttk.Button(frame, text="Generate Teams", command=self.generate_teams)
        gen_btn.grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(frame, text="Number of Teams:").grid(row=0, column=3, padx=5, pady=5)
        team_spin = ttk.Spinbox(frame, from_=2, to=20, textvariable=self.num_teams, width=5)
        team_spin.grid(row=0, column=4, padx=5, pady=5)

        add_btn = ttk.Button(frame, text="Add Player", command=self.add_player_window)
        add_btn.grid(row=0, column=5, padx=5, pady=5)

        gender_options = ttk.OptionMenu(frame, self.gender_filter, "All", "All", "Male", "Female", command=lambda _: self.refresh_tree())
        gender_options.grid(row=0, column=6, padx=5, pady=5)

        self.tree_frame = ttk.Frame(parent)
        self.tree_frame.grid(row=1, column=0, sticky="nsew")

        self.tree_canvas = tk.Canvas(self.tree_frame)
        self.tree_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree_canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree_canvas.configure(yscrollcommand=self.scrollbar.set)
        self.tree_canvas.bind('<Configure>', lambda e: self.tree_canvas.configure(scrollregion=self.tree_canvas.bbox("all")))

        self.inner_frame = ttk.Frame(self.tree_canvas)
        self.tree_canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")

        parent.rowconfigure(1, weight=1)
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
            if col in ["First Name", "Last Name"]:
                lbl.bind("<Button-1>", lambda e, col_name=col: self.sort_by_column(col_name))

        df = self.manager.get_all_players()
        if self.gender_filter.get() != "All":
            df = df[df['Gender'].str.lower() == self.gender_filter.get().lower()]

        if self.sort_column:
            df = df.sort_values(by=self.sort_column, key=lambda col: col.str.lower() if col.dtype == 'object' else col, ascending=not self.sort_reverse)

        for row_num, (idx, row) in enumerate(df.iterrows(), start=1):
            check_var = tk.BooleanVar(value=row['Checked In'])
            check = ttk.Checkbutton(self.inner_frame, variable=check_var, command=lambda i=idx, var=check_var: self.manager.set_checked_in(i, var.get()))
            check.grid(row=row_num, column=0, padx=5, pady=2)
            self.check_vars[idx] = check_var

            ttk.Label(self.inner_frame, text=row['First Name']).grid(row=row_num, column=1)
            ttk.Label(self.inner_frame, text=row['Last Name']).grid(row=row_num, column=2)
            ttk.Label(self.inner_frame, text=row['Gender']).grid(row=row_num, column=3)

            skill_lbl = ttk.Label(self.inner_frame, text=row['Skill'])
            skill_lbl.grid(row=row_num, column=4)
            skill_lbl.bind("<Double-1>", lambda e, i=idx: self.edit_skill(i))

            ttk.Label(self.inner_frame, text=row['Team'] if pd.notna(row['Team']) else "").grid(row=row_num, column=5)

        self.refresh_team_tables()

    def refresh_team_tables(self):
        for widget in self.teams_frame.winfo_children():
            widget.destroy()
        self.team_tables.clear()

        df = self.manager.get_all_players()
        assigned = df[df['Team'].notna()]

        team_names = sorted(assigned['Team'].dropna().unique())

        for team_name in team_names:
            team_df = assigned[assigned['Team'] == team_name]

            frame = ttk.LabelFrame(self.teams_frame, text=team_name)
            frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

            table = ttk.Treeview(frame, columns=("First Name", "Last Name", "Gender", "Skill"), show="headings")
            for col in table["columns"]:
                table.heading(col, text=col)
                table.column(col, width=100)

            for _, row in team_df.iterrows():
                table.insert("", "end", values=(row['First Name'], row['Last Name'], row['Gender'], row['Skill']))

            table.pack(fill=tk.BOTH, expand=True)
            self.team_tables.append(table)

    def sort_by_column(self, column):
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False
        self.refresh_tree()

    def edit_skill(self, index):
        new_value = tk.simpledialog.askinteger("Edit Skill", "Enter new skill:")
        if new_value is not None:
            self.manager.update_skill(index, new_value)
            self.refresh_tree()

    def add_player_window(self):
        win = tk.Toplevel(self.root)
        win.title("Add Player")

        entries = {}
        for i, field in enumerate(["First Name", "Last Name", "Gender", "Skill"]):
            ttk.Label(win, text=field).grid(row=i, column=0, padx=5, pady=5)
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

    def generate_teams(self):
        # Clear team assignment for any player who is no longer checked in
        for idx, row in self.manager.get_all_players().iterrows():
            if not row['Checked In']:
                self.manager.assign_team(idx, None)

        try:
            team_generator.generate(self.manager, self.num_teams.get())
            self.refresh_tree()
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = TeamBuilderGUI(root)
    root.mainloop()
