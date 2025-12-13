# app.py
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from game_instance import WebGameManager
import config

app = Flask(__name__)
app.config['SECRET_KEY'] = 'rahasia_negara'
socketio = SocketIO(app)

# Inisialisasi Game Global (Satu room untuk semua)
game = WebGameManager()

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join_game')
def handle_join(data):
    name = data['name']
    session_id = request.sid
    
    if game.add_player(session_id, name):
        # Beritahu semua orang ada yang join
        emit('update_lobby', {
            'players': [p.name for p in game.players],
            'count': game.num_players
        }, broadcast=True)
    else:
        emit('error', {'msg': 'Game sudah berjalan atau penuh!'})

@socketio.on('start_game')
def handle_start():
    if game.start_game():
        emit('game_started', broadcast=True)
        emit('new_round_info', {'active_players': game.get_active_player_count()}, broadcast=True)

@socketio.on('submit_guess')
def handle_guess(data):
    session_id = request.sid
    try:
        val = float(data['value'])
    except ValueError:
        return

    # Logika: Apakah semua orang sudah menjawab?
    round_complete = game.handle_choice(session_id, val)
    
    # Beritahu user ini bahwa jawaban diterima
    emit('guess_accepted', {'val': val})
    
    # Jika semua sudah menjawab, hitung hasil
    if round_complete:
        results = game.calculate_round_results()
        
        # --- BAGIAN YANG DIUBAH ---
        # Kita tambahkan 'last_guess' ke dalam data scoreboard
        formatted_res = {
            'avg': results['avg'],
            'target': results['target'],
            'winners': [p.name for p in results['winners']],
            'losers': [p.name for p in results['losers']],
            'logs': results['logs'],
            'scoreboard': [
                {
                    'name': p.name, 
                    'score': p.score, 
                    'eliminated': p.is_eliminated,
                    
                    # --- PERBAIKAN DI SINI ---
                    # Sesuai game_instance.py, pakai .last_choice
                    'last_guess': p.last_choice 
                } 
                for p in game.players
            ]
        }
        # ---------------------------
        
        emit('round_results', formatted_res, broadcast=True)
        
        # Reset untuk ronde berikutnya
        game.reset_choices()
        
        # Cek Pemenang Game
        winner = game.get_match_winner()
        if winner:
            emit('game_over', {'winner': winner.name if hasattr(winner, 'name') else "Draw"}, broadcast=True)

if __name__ == '__main__':
    # host='0.0.0.0' agar bisa diakses teman satu WiFi
    socketio.run(app, debug=True, host='0.0.0.0', port=5001)