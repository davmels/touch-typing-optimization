class AppController:
    def __init__(self, app):
        self.app = app
        self.register_endpoints()

    def register_endpoints(self):
        @self.app.route("/")
        def home():
            return "Home"
