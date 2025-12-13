# game_logic.py
import config
import math

class Player:
    def __init__(self, p_id, name, is_bot=False):
        self.id = p_id
        self.name = name # Atribut Nama Baru
        self.score = config.STARTING_SCORE
        self.is_eliminated = False
        self.last_choice = None
        self.is_bot = is_bot

class BeautyContestLogic:
    def __init__(self, num_players, single_player_mode=False, player_names=None):
        self.num_players = num_players
        self.players = []
        
        for i in range(num_players):
            p_id = i + 1
            is_bot = False
            name = f"Player {p_id}" # Nama Default
            
            if single_player_mode:
                # Mode Single: P1 Manusia, Sisanya Bot
                if i == 0:
                    # Jika ada nama custom untuk P1 (Manusia)
                    if player_names and len(player_names) > 0:
                        name = player_names[0]
                else:
                    is_bot = True
                    name = f"Bot {p_id}"
            else:
                # Mode Multiplayer: Gunakan daftar nama yang diinput
                if player_names and i < len(player_names):
                    name = player_names[i]
            
            self.players.append(Player(p_id, name, is_bot))
            
        self.current_player_idx = 0
        self.find_next_active_player()

    def find_next_active_player(self):
        if self.current_player_idx >= self.num_players:
            return False
        while self.current_player_idx < self.num_players and self.players[self.current_player_idx].is_eliminated:
            self.current_player_idx += 1
        if self.current_player_idx >= self.num_players:
            return False
        return True

    def set_choice(self, value):
        current_p = self.players[self.current_player_idx]
        current_p.last_choice = float(value)
        self.current_player_idx += 1
        return self.find_next_active_player()

    def get_current_player(self):
        if self.current_player_idx < self.num_players:
            return self.players[self.current_player_idx]
        return None
        
    def get_current_player_id(self):
        p = self.get_current_player()
        return p.id if p else -1

    def get_active_player_count(self):
        return sum(1 for p in self.players if not p.is_eliminated)

    def calculate_round_results(self):
        active_players = [p for p in self.players if not p.is_eliminated]
        count = len(active_players)
        
        if count == 0: return None

        choices = [p.last_choice for p in active_players]

        raw_avg = sum(choices) / count
        avg = math.floor(raw_avg)
        target = math.floor(raw_avg * 0.8)
        
        winners = []
        losers = []
        invalid_players = [] 
        special_event_log = [] 
        
        current_penalty = config.LOSS_PENALTY

        # Prepare per-player detail records for UI logging
        per_player = []
        for p in active_players:
            per_player.append({
                "id": p.id,
                "name": p.name,
                "choice": p.last_choice,
                "is_invalid": False,
                "diff_to_target": None,
                "diff_to_avg": abs(raw_avg - p.last_choice)
            })

        # --- RULE: 2 PLAYERS (0 vs 100) ---
        rule_2p_triggered = False
        if count == 2:
            vals = [p.last_choice for p in active_players]
            if 0 in vals and 100 in vals:
                rule_2p_triggered = True
                special_event_log.append("DUEL: 0 vs 100! 100 Menang!")
                for p in active_players:
                    if p.last_choice == 100:
                        winners.append(p)
                    else:
                        losers.append(p)

        if not rule_2p_triggered:
            # --- RULE: 4 PLAYERS OR LESS (Duplicate Penalty) ---
            if count <= 4:
                seen = {}
                duplicates = set()
                for p in active_players:
                    val = p.last_choice
                    if val in seen:
                        duplicates.add(val)
                    seen[val] = True
                
                if duplicates:
                    dup_str = ', '.join(map(str, [int(x) for x in duplicates]))
                    special_event_log.append(f"DUPLIKASI: Angka {dup_str} hangus!")
                    for p in active_players:
                        if p.last_choice in duplicates:
                            invalid_players.append(p)
                            # mark per_player
                            for rec in per_player:
                                if rec['id'] == p.id:
                                    rec['is_invalid'] = True
            
            valid_candidates = [p for p in active_players if p not in invalid_players]
            
            if not valid_candidates:
                special_event_log.append("SEMUA INVALID! Tidak ada pemenang.")
                losers = active_players 
            else:
                min_diff = float('inf')
                for p in valid_candidates:
                    diff = abs(target - p.last_choice)
                    if diff < min_diff:
                        min_diff = diff
                    # update per_player diff
                    for rec in per_player:
                        if rec['id'] == p.id:
                            rec['diff_to_target'] = diff
                
                round_winners = [p for p in valid_candidates if abs(target - p.last_choice) == min_diff]
                winners.extend(round_winners)
                
                for p in active_players:
                    if p not in winners:
                        losers.append(p)

                # --- RULE: 3 PLAYERS OR LESS (Exact Match Bonus) ---
                if count <= 3:
                    is_exact = any(p.last_choice == target for p in winners)
                    
                    if is_exact:
                        current_penalty = config.CRITICAL_PENALTY
                        special_event_log.append(f"CRITICAL HIT! Tepat sasaran {target}!")
                        special_event_log.append("Penalti yang kalah menjadi -2!")

        for p in losers:
            p.score -= current_penalty
            if p.score <= config.ELIMINATION_THRESHOLD:
                p.is_eliminated = True

        # Finalize per_player statuses
        for rec in per_player:
            if rec['is_invalid']:
                rec['status'] = 'invalid'
            else:
                # find player object
                p_obj = next((x for x in active_players if x.id == rec['id']), None)
                if p_obj in winners:
                    rec['status'] = 'winner'
                elif p_obj in losers:
                    rec['status'] = 'loser'
                else:
                    rec['status'] = 'unknown'

        return {
            "raw_avg": raw_avg,
            "avg": avg,
            "target": target,
            "winners": winners,
            "losers": losers,
            "all_players": self.players,
            "logs": special_event_log,
            "active_count": count,
            "per_player": per_player
        }

    def get_match_winner(self):
        active_players = [p for p in self.players if not p.is_eliminated]
        if len(active_players) == 1:
            return active_players[0]
        if len(active_players) == 0:
            return "No One"
        return None

    def reset_round(self):
        self.current_player_idx = 0
        self.find_next_active_player()