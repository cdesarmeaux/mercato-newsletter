from app import app
from app.routes.register import register_bp
from app.routes.confirm import confirm_bp
from app.routes.main import main_bp
from app.routes.unsubscribe import unsubscribe_bp

app.register_blueprint(main_bp)
app.register_blueprint(register_bp)
app.register_blueprint(confirm_bp)
app.register_blueprint(unsubscribe_bp)
