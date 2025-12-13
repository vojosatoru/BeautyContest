# game_instance.py
from game_logic import BeautyContestLogic, Player

class WebGameManager(BeautyContestLogic):
    def __init__(self):
        # Kita inisialisasi kosong dulu
        self.players = []
        self.num_players = 0
        self.current_player_idx = 0
        self.game_started = False
        self.player_map = {} # Mapping session_id (socket) ke Player Object

    def add_player(self, session_id, name):
        if self.game_started:
            return False
        
        p_id = len(self.players) + 1
        new_player = Player(p_id, name)
        self.players.append(new_player)
        self.player_map[session_id] = new_player
        self.num_players = len(self.players)
        return True

    def start_game(self):
        if self.num_players >= 2: # Minimal 2 orang
            self.game_started = True
            return True
        return False

    def handle_choice(self, session_id, choice):
        if not self.game_started: return False
        
        player = self.player_map.get(session_id)
        if not player or player.is_eliminated: return False

        # Simpan pilihan player (tanpa menunggu giliran urut seperti desktop)
        player.last_choice = float(choice)
        
        # Cek apakah semua pemain aktif sudah memilih?
        active_players = [p for p in self.players if not p.is_eliminated]
        all_chosen = all(p.last_choice is not None for p in active_players)
        
        return all_chosen # True jika ronde selesai

    def reset_choices(self):
        for p in self.players:
            p.last_choice = None