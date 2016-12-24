class Config(object):
    DEBUG = True
    CSRF_ENABLED = True
    SECRET_KEY = 'YOUR_SECRET_HERE'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///elot.db'
    DANGER = False
    CANCEL_UNPAID_ORDERS_AFTER_MINS = 15
    PASSWORD_LENGTH = 5
    NOREPLY_SERVER = 'smtp.example.com'
    NOREPLY_EMAIL = 'no-reply@example.com'
    NOREPLY_PW = 'examplepass'
    PASSWORD_EMAIL_TEXT = 'Уважаемый покупатель!\r\n\r\nВаш код для доступа к покупкам на сайте example.com:\r\n\r\n%s'
    ORDER_EMAIL_TEXT = 'Уважаемый покупатель!<br/><br/>Заказ № %d на сайте example.com был оплачен. Ваши данные:<br/><br/>%s'
    PAYMENT_SYSTEMS = ['ym', 'wm', 'vm']
    PAYMENT_SYSTEMS_NAMES = {'ym': 'Яндекс.Деньги', 'wm': 'WebMoney', 'vm': 'Банковская карта'}
    YM_PURSE = 'YOUR_PURSE_HERE'
    YM_SECRET = 'YOUR_SECRET_HERE'
    WM_PURSE = 'YOUR_PURSE_HERE'
    WM_SECRET = 'YOUR_SECRET_HERE'
    CAPTCHA_SECRET = 'YOUR_SECRET_HERE'


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://USERNAME:PASSWORD@HOST'


class DevelopmentConfig(Config):
    DEBUG = True
