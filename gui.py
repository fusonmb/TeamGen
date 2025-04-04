import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from player_manager import PlayerManager
import pandas as pd
import team_generator

class TeamBuilderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Team Generator")

        self.manager = PlayerManager()
        self.num_teams = tk.IntVar(value=2)
        self.check_vars = {}

        self.setup_widgets()

    def setup_widgets(self):
        frame = ttk.Frame(self.root, padding=10)
        frame.grid(row=0, column=0, sticky="nsew")

        # Buttons and controls
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

        # Treeview with checkboxes for check-in
        self.tree_frame = ttk.Frame(self.root)
        self.tree_frame.grid(row=1, column=0, sticky="nsew")

        self.tree_canvas = tk.Canvas(self.tree_frame)
        self.tree_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree_canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree_canvas.configure(yscrollcommand=self.scrollbar.set)
        self.tree_canvas.bind('<Configure>', lambda e: self.tree_canvas.configure(scrollregion=self.tree_canvas.bbox("all")))

        self.inner_frame = ttk.Frame(self.tree_canvas)
        self.tree_canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")

        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)

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
            ttk.Label(self.inner_frame, text=col, font=("Arial", 10, "bold")).grid(row=0, column=col_index, padx=5, pady=2)

        for idx, row in self.manager.get_all_players().iterrows():
            check_var = tk.BooleanVar(value=row['Checked In'])
            check = ttk.Checkbutton(self.inner_frame, variable=check_var, command=lambda i=idx, var=check_var: self.manager.set_checked_in(i, var.get()))
            check.grid(row=idx+1, column=0, padx=5, pady=2)
            self.check_vars[idx] = check_var

            ttk.Label(self.inner_frame, text=row['First Name']).grid(row=idx+1, column=1)
            ttk.Label(self.inner_frame, text=row['Last Name']).grid(row=idx+1, column=2)
            ttk.Label(self.inner_frame, text=row['Gender']).grid(row=idx+1, column=3)

            skill_lbl = ttk.Label(self.inner_frame, text=row['Skill'])
            skill_lbl.grid(row=idx+1, column=4)
            skill_lbl.bind("<Double-1>", lambda e, i=idx: self.edit_skill(i))

            ttk.Label(self.inner_frame, text=row['Team'] if pd.notna(row['Team']) else "").grid(row=idx+1, column=5)

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
        try:
            team_generator.generate(self.manager, self.num_teams.get())
            self.refresh_tree()
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = TeamBuilderGUI(root)
    root.mainloop()
