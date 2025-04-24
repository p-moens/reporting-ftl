import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import sc2reader
from collections import Counter
from liquipedia_format import generate_liquipedia_format


class ReplayAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Reporting Match FTL")
        self.folder = None
        self.replay_paths = []
        self.clan_a = ""
        self.clan_b = ""
        self.player_clan = {}
        self.all_players = set()
        self.summaries = []
        self.results = Counter()

        self.setup_start_frame()

    def setup_start_frame(self):
        self.clear_root()
        tk.Label(self.root, text="Étape 1 : Sélectionnez le dossier des replays", font=('Arial', 14)).pack(pady=10)
        tk.Button(self.root, text="Choisir dossier", command=self.choose_folder).pack(pady=5)

    def choose_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder = folder
            self.replay_paths = self.get_replay_records(folder)
            if not self.replay_paths:
                messagebox.showerror("Erreur", "Aucun fichier .SC2Replay trouvé dans ce dossier.")
                return
            self.setup_clan_entry_frame()

    def setup_clan_entry_frame(self):
        self.clear_root()
        tk.Label(self.root, text="Étape 2 : Saisir les noms de clans", font=('Arial', 14)).pack(pady=10)
        self.clan_a_var = tk.StringVar()
        self.clan_b_var = tk.StringVar()

        tk.Label(self.root, text="Clan A :").pack()
        tk.Entry(self.root, textvariable=self.clan_a_var).pack(pady=5)
        tk.Label(self.root, text="Clan B :").pack()
        tk.Entry(self.root, textvariable=self.clan_b_var).pack(pady=5)
        tk.Button(self.root, text="Continuer", command=self.collect_players).pack(pady=10)

    def collect_players(self):
        self.clan_a = self.clan_a_var.get().strip()
        self.clan_b = self.clan_b_var.get().strip()
        if not self.clan_a or not self.clan_b:
            messagebox.showerror("Erreur", "Les deux clans doivent être renseignés.")
            return

        players = set()
        for path in self.replay_paths:
            try:
                _, team_info, _ = self.parse_replay(path)
                for _, _, _, members in team_info:
                    for name, _ in members:
                        players.add(name)
            except Exception:
                continue

        self.all_players = sorted(players)
        self.setup_player_assignment_frame()

    def setup_player_assignment_frame(self):
        self.clear_root()
        tk.Label(self.root, text="Étape 3 : Assigner chaque joueur à un clan et ajouter un alias (optionnel)", font=('Arial', 14)).pack(pady=10)
        self.player_vars = {}
        self.player_alias_vars = {}

        frame = tk.Frame(self.root)
        frame.pack()

        for name in self.all_players:
            var = tk.StringVar(value=self.clan_a)
            alias = tk.StringVar()
            self.player_vars[name] = var
            self.player_alias_vars[name] = alias

            row = tk.Frame(frame)
            row.pack(anchor='w', pady=2)

            tk.Label(row, text=name, width=25, anchor='w').pack(side='left')
            tk.Radiobutton(row, text=self.clan_a, variable=var, value=self.clan_a).pack(side='left')
            tk.Radiobutton(row, text=self.clan_b, variable=var, value=self.clan_b).pack(side='left')
            tk.Entry(row, textvariable=alias, width=20).pack(side='left')

        tk.Button(self.root, text="Analyser les replays", command=self.process_replays).pack(pady=10)

    def process_replays(self):
        self.player_clan = {name: var.get() for name, var in self.player_vars.items()}
        self.player_alias = {name: alias.get() for name, alias in self.player_alias_vars.items()}
        self.summaries.clear()
        self.results.clear()

        matches = []

        for path in self.replay_paths:
            try:
                map_name, team_info, winner_id = self.parse_replay(path)
                team_clans = {}
                for team_number, _, _, members in team_info:
                    clans = {self.player_clan[name] for name, _ in members if name in self.player_clan}
                    team_clans[team_number] = clans.pop() if len(clans) == 1 else 'Inconnu'

                if len(team_info) == 2:
                    t1, t2 = team_info[0][0], team_info[1][0]
                    if team_clans[t1] == 'Inconnu' and team_clans[t2] != 'Inconnu':
                        team_clans[t1] = self.clan_b if team_clans[t2] == self.clan_a else self.clan_a
                    elif team_clans[t2] == 'Inconnu' and team_clans[t1] != 'Inconnu':
                        team_clans[t2] = self.clan_b if team_clans[t1] == self.clan_a else self.clan_a

                clan_a_team = next(info for info in team_info if team_clans[info[0]] == self.clan_a)
                clan_b_team = next(info for info in team_info if team_clans[info[0]] == self.clan_b)
                winner_clan = team_clans.get(winner_id, 'Unknown')

                self.results[winner_clan] += 1

                def format_name(name):
                    alias = self.player_alias.get(name)
                    return f"{name} ({alias})" if alias else name

                def format_team(members):
                    return " / ".join(format_name(n) for n, _ in members)

                team_a_str = format_team(clan_a_team[3])
                team_b_str = format_team(clan_b_team[3])

                if winner_clan == self.clan_a:
                    team_a_str = f"**{team_a_str}**"
                else:
                    team_b_str = f"**{team_b_str}**"

                line = f"{team_a_str} vs {team_b_str} --- {map_name}"
                matches.append((len(clan_a_team[3]), line))

            except Exception as e:
                messagebox.showerror("Erreur de parsing", str(e))

        self.summaries = [f"{self.clan_a} vs {self.clan_b}", f"Score : {self.results[self.clan_a]} - {self.results[self.clan_b]}"]

        twov2 = [line for count, line in matches if count == 2]
        onev1 = [line for count, line in matches if count == 1]

        if twov2:
            self.summaries.append("\n[2v2]")
            self.summaries.extend(twov2)
        if onev1:
            self.summaries.append("\n[1v1]")
            self.summaries.extend(onev1)

        self.show_summary()


    def show_summary(self):
        self.clear_root()
        self.summary_box = tk.Text(self.root, width=100, height=20)
        self.summary_box.pack()
        self.refresh_summary_display()

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Enregistrer le fichier", command=self.save_summary).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Liquipedia format", command=self.export_liquipedia_format).pack(side='left', padx=5)

    def refresh_summary_display(self):
        self.summary_box.config(state='normal')
        self.summary_box.delete(1.0, tk.END)
        for line in self.summaries:
            self.summary_box.insert(tk.END, line + "\n")
        self.summary_box.config(state='disabled')

    def save_summary(self):
        try:
            with open(os.path.join(self.folder, "replay_summary.txt"), 'w', encoding='utf-8') as f:
                for line in self.summaries:
                    f.write(line + "\n")
            messagebox.showinfo("Succès", "Résumé enregistré avec succès !")
        except Exception as e:
            messagebox.showerror("Erreur d'enregistrement", str(e))


    def export_liquipedia_format(self):
        matchsection = simpledialog.askstring("MatchSection", "Nom du matchsection (ex: Week 5):")
        if not matchsection:
            return

        opponent1 = simpledialog.askstring("Opponent 1", f"Quel clan est Opponent 1 ? ({self.clan_a} ou {self.clan_b})")
        if opponent1 not in [self.clan_a, self.clan_b]:
            messagebox.showerror("Erreur", "Clan invalide pour Opponent 1.")
            return


        # Construire la structure attendue par generate_liquipedia_format
        parsed_replays = []
        for path in self.replay_paths:
            try:
                replay = sc2reader.load_replay(path, load_map=True)
                map_name = replay.map_name
                winner_team = replay.winner.number
                teams = {}
                for p in replay.players:
                    teams.setdefault(p.team.number, []).append((p.name, p.pick_race))

                sorted_teams = sorted(teams.items(), key=lambda kv: kv[0])
                team1, team2 = [v for _, v in sorted_teams]

                winner = 1 if sorted_teams[0][0] == winner_team else 2

                parsed_replays.append((replay.start_time, map_name, team1, team2, winner))
            except Exception as e:
                messagebox.showerror("Erreur Liquipedia", str(e))
                return

        liqui_format = generate_liquipedia_format(
            parsed_replays,
            self.clan_a,
            self.clan_b,
            self.player_clan,
            self.player_alias,
            matchsection,
            opponent1
        )

        self.summaries = liqui_format.splitlines()
        self.refresh_summary_display()

    def get_replay_records(self, folder):
        records = []
        for fn in os.listdir(folder):
            if fn.lower().endswith(".sc2replay"):
                path = os.path.join(folder, fn)
                try:
                    replay = sc2reader.load_replay(path, load_map=False)
                    records.append((replay.start_time, path))
                except Exception:
                    continue
        records.sort(key=lambda x: x[0])
        return [path for _, path in records]

    def parse_replay(self, path):
        replay = sc2reader.load_replay(path, load_map=True)
        map_name = replay.map_name
        teams = {}
        for player in replay.players:
            teams.setdefault(player.team, []).append((player.name, player.pick_race))
        winner_id = replay.winner.number
        sorted_teams = sorted(teams.items(), key=lambda kv: kv[0].number)
        team_info = []
        for team_obj, members in sorted_teams:
            names = ", ".join(n for n, _ in members)
            races = ", ".join(r for _, r in members)
            team_info.append((team_obj.number, names, races, members))
        return map_name, team_info, winner_id

    def clear_root(self):
        for widget in self.root.winfo_children():
            widget.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    app = ReplayAnalyzerApp(root)
    root.mainloop()