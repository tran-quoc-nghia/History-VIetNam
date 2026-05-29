from flask import Flask
from config import Config
from flask_mail import Mail
import os # Thêm dòng này

mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'default-secret-key-for-dev')

    # Cấu hình gửi Mail (Sử dụng Gmail)
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    
    # Lấy thông tin từ biến môi trường thay vì ghi thẳng vào code
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

    # 2. Gắn cấu hình của app vào đối tượng mail
    mail.init_app(app)

    # Đăng ký blueprints
    from app.routes import user_routes, graph_routes, admin_routes
    app.register_blueprint(user_routes.user_bp)
    app.register_blueprint(graph_routes.graph_bp)
    app.register_blueprint(admin_routes.admin_bp)

    return app