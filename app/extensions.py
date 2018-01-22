from flask_login import LoginManager
from flask_admin import Admin
from flask_migrate import Migrate

#bootstrap = Bootstrap()
#mail = Mail()
#moment = Moment()
admin = Admin(name='小麦芬烘焙工作室', template_mode='bootstrap3')
#api = APIManager()
#pagedown = PageDown()

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'
