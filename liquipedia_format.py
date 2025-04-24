from datetime import datetime
from collections import defaultdict

def generate_liquipedia_format(replays, clan1, clan2, player_clans, player_alias, matchsection, opponent1_clan):
    if not replays:
        return ""

    match_datetime = replays[0][0].strftime("%Y-%m-%d %H:%M")

    lines = []
    lines.append(f"{{{{Match|dateheader=true|bestof=7|matchsection={matchsection}")
    lines.append(f"    |date={match_datetime} {{Abbr/CEST}}")
    lines.append(f"    |opponent1={{{{TeamOpponent|{opponent1_clan}}}}}")
    opponent2_clan = clan2 if opponent1_clan == clan1 else clan1
    lines.append(f"    |opponent2={{{{TeamOpponent|{opponent2_clan}}}}}")

    for i, (_, map_name, team1, team2, winner) in enumerate(replays):
        map_num = i + 1

        def format_player(name):
            alias = player_alias.get(name, "")
            return alias if alias else name

        # Réorganise les équipes pour que l'équipe opponent1 soit toujours t1
        team1_clan = {player_clans.get(name, '') for name, _ in team1}
        if opponent1_clan in team1_clan:
            t1, t2 = team1, team2
            final_winner = winner
        else:
            t1, t2 = team2, team1
            final_winner = 1 if winner == 2 else 2

        t1_entries = [f"t1p{i+1}={format_player(name)}" for i, (name, _) in enumerate(t1)]
        t2_entries = []
        for i, (name, race) in enumerate(t2):
            t2_entries.append(f"t2p{i+1}={format_player(name)}")
            if race:
                t2_entries.append(f"t2p{i+1}race={race.lower()}")

        entries = t1_entries + t2_entries + [f"map={map_name}", f"winner={final_winner}"]
        entry_line = "|".join(entries)

        lines.append(f"    |map{map_num}={{{{Map|{entry_line}}}}}")

    lines.append("}}")
    return "\n".join(lines)
