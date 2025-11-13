from flask import Flask, send_from_directory, redirect, url_for
from flask_wtf import CSRFProtect
from flask_login import LoginManager
import os

# Используем единый экземпляр db из models
from models import db, User

csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.login_view = "auth.login"

def create_app():
    app = Flask(__name__, static_folder='static', template_folder='templates')

    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET', 'change-this-secret')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('CONTRACTS_DB', 'sqlite:///C:/ProgramData/ContractsApp/contracts.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Инициализация расширений
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(User, int(user_id))
        except Exception:
            return None

    # Регистрируем блюпринты
    from routes import main_bp
    from auth import auth_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='')

    # favicon route (отдаём png/svg если есть)
    @app.route('/favicon.ico')
    def favicon():
        static_folder = app.static_folder or os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static')
        png = os.path.join(static_folder, 'images', 'favicon.png')
        svg = os.path.join(static_folder, 'images', 'favicon.svg')
        if os.path.exists(png):
            return send_from_directory(os.path.join(static_folder, 'images'), 'favicon.png', mimetype='image/png')
        if os.path.exists(svg):
            return send_from_directory(os.path.join(static_folder, 'images'), 'favicon.svg', mimetype='image/svg+xml')
        return '', 404

    return app

# Простая точка входа для запуска в режиме разработки
if __name__ == "__main__":
    application = create_app()
    application.run(debug=True)