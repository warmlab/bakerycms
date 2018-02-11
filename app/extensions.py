from flask_login import LoginManager
from flask_migrate import Migrate
#from flask_mail import Mail
#from flask_moment import Moment
#from flask_pagedown import PageDown

#bootstrap = Bootstrap()
#mail = Mail()
#moment = Moment()
#api = APIManager()
#pagedown = PageDown()

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'
