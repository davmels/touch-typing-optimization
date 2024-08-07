from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS

import os
from dotenv import load_dotenv

from Controllers.AppController import AppController
from Controllers.SocketController import SocketController

load_dotenv()
vite_server_url = os.getenv('VITE_SERVER_URL')
PORT = int(os.getenv("PORT", 5000))

app = Flask(__name__)
CORS(app, origins=[vite_server_url])
socketio = SocketIO(app, cors_allowed_origins=vite_server_url)

socket_controller = SocketController(socketio)
app_controller = AppController(app)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=PORT)
