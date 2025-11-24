from flask import Flask, render_template
import threading
from game import UFCGame

app = Flask(__name__)

game_instance = None
game_thread = None

@app.route('/')
def index():
    return render_template('index.html')

def run_game():
    global game_instance
    game_instance = UFCGame()
    game_instance.run()

@app.route('/start-game')
def start_game():
    global game_thread
    if game_thread is None or not game_thread.is_alive():
        game_thread = threading.Thread(target=run_game, daemon=True)
        game_thread.start()
        return {'status': 'Game started'}
    return {'status': 'Game already running'}

if __name__ == '__main__':
    print("Starting Flask server at http://localhost:5000")
    app.run(debug=False, host='localhost', port=5000)
