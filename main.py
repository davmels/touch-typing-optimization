from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
import threading
import time
import uuid
from controller import Controller
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

vite_server_url = os.getenv('VITE_SERVER_URL')

app = Flask(__name__)
CORS(app, origins=[vite_server_url])
socketio = SocketIO(app, cors_allowed_origins=vite_server_url)

controller = Controller()

tasks = {}
user_sessions = {}


@socketio.on('connect')
def handle_connect():
    print('Client connected')
    register_event_handlers()


def register_event_handlers():
    @socketio.on('disconnect')
    def handle_disconnect():
        print('Client disconnected')

    @socketio.on('custom_event')
    def handle_custom_event(data):
        print('Received custom event:', data)
        data['data'] = "oh nou"
        socketio.emit('custom_event', {'data': data}, to=request.sid)

    @socketio.on('generate_keyboard_layout')
    def generate_keyboard_layout(config):
        task_id = str(uuid.uuid4())
        sid = request.sid
        tasks[sid] = {'progress': 0, 'result': None}
        thread = threading.Thread(target=controller.search, args=(config, socketio, sid))
        thread.start()
        socketio.emit('progress', tasks[sid], to=sid)


@app.route("/")
def home():
    return "Home"


# @app.route("/generate_keyboard_layout", methods=["POST"])
# def generate_keyboard_layout():
#     # request.method == "POST"
#     data = request.get_json()
#
#     character_placement = controller.search(data)
#
#     return character_placement.to_json(), 201


# @socketio.on('generate_keyboard_layout')
# def generate_socket_layout

if __name__ == '__main__':
    socketio.run(app, host='127.0.0.1', port=5000, debug=True)
