from flask import Flask


def create_app():
    app = Flask(__name__)

    from routes import tasks_bp

    app.register_blueprint(tasks_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
