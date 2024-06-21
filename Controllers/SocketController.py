import threading

from flask import request

from ControllerService.Analyser import Analyser
from ControllerService.Optimizer import Optimizer


class SocketController:
    def __init__(self, socketio):
        self.socketio = socketio
        self.optimizer = Optimizer()
        self.analyser = Analyser()

        self.register_event_handlers()

    def register_event_handlers(self):
        @self.socketio.on('connect')
        def handle_connect():
            print('Client connected, socket id: ', request.sid)

        @self.socketio.on('disconnect')
        def handle_disconnect():
            print('Client disconnected, socket it: ', request.sid)

        @self.socketio.on('custom_event')
        def handle_custom_event(data):
            print('Received custom event:', data)
            data['data'] = "oh nou"
            self.socketio.emit('custom_event', {'data': data}, to=request.sid)

        @self.socketio.on('generate_keyboard_layout')
        def generate_keyboard_layout(optimization_config):
            sid = request.sid

            def socket_progress_emit(current_generation, total_generations):
                self.socketio.emit('progress', {
                    'current_generation': current_generation, 'total_generations': total_generations},
                                   to=sid)

            def initialization_finish_emit():
                self.socketio.emit('initialization_finish',
                                   {'current_generation': 0,
                                    'total_generations': optimization_config['number_of_generations']},
                                   to=sid)

            def result_emit(genetic):
                self.socketio.emit('result', {
                    'characters_set': [character.to_dict() for character in
                                       genetic.best_characters_placement.characters_set]},
                                   to=sid)

            thread = threading.Thread(target=self.optimizer.search,
                                      args=(optimization_config, socket_progress_emit, initialization_finish_emit,
                                            result_emit))

            self.socketio.emit('initialization_start', to=sid)
            thread.start()

        @self.socketio.on("analyse_keyboard")
        def analyse_keyboard(optimization_config):
            sid = request.sid

            def result_emit(analysis):
                self.socketio.emit('analysis_result', {"analysis": analysis}, to=sid)

            thread = threading.Thread(target=self.analyser.analyse,
                                      args=(optimization_config, result_emit))

            self.socketio.emit("analysis_start", to=sid)
            thread.start()
