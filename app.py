# app.py
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from game_instance import WebGameManager
import config

app = Flask(__name__)
app.config['SECRET_KEY'] = 'rahasia_negara'
socketio = SocketIO(app)

game = WebGameManager()

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join_game')
def handle_join(data):
    name = data['name']
    session_id = request.sid
    
    if game.add_player(session_id, name):
        emit('update_lobby', {
            'players': [p.name for p in game.players],
            'count': game.num_players
        }, broadcast=True)
    else:
        emit('error', {'msg': 'Game sudah berjalan atau penuh!'})

@socketio.on('start_game')
def handle_start():
    if game.start_game():
        # Kirim sinyal mulai + Aturan aktif
        emit('game_started', {
            'active_rules': game.get_active_rules_text()
        }, broadcast=True)

@socketio.on('submit_guess')
def handle_guess(data):
    session_id = request.sid
    try:
        val = float(data['value'])
        if val < 0 or val > 100: return # Validasi sederhana
    except ValueError:
        return

    # Kirim ke manager
    round_complete = game.handle_choice(session_id, val)
    emit('guess_accepted', {'val': val}) # Konfirmasi ke pengirim
    
    # Jika semua sudah menjawab, hitung hasil
    if round_complete:
        results = game.calculate_round_results()
        
        formatted_res = {
            'avg': results['avg'],
            'target': results['target'],
            'winners': [p.name for p in results['winners']],
            'losers': [p.name for p in results['losers']],
            'logs': results['logs'],
            'active_rules': game.get_active_rules_text(), # Update aturan
            'scoreboard': [
                {
                    'name': p.name, 
                    'score': p.score, 
                    'eliminated': p.is_eliminated,
                    'last_guess': p.last_choice 
                } 
                for p in game.players
            ]
        }
        
        emit('round_results', formatted_res, broadcast=True)
        
        game.reset_choices()
        
        winner = game.get_match_winner()
        if winner:
            winner_name = winner.name if hasattr(winner, 'name') else "Draw"
            emit('game_over', {'winner': winner_name}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5001)