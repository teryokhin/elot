from app import app, models, db
from datetime import datetime
from urllib.parse import urlparse, urljoin
from flask import request


cat_cache = None


@app.context_processor
def inject_categories():
    global cat_cache
    if not cat_cache:
        cat_cache = models.Category.query.all()
    if app.config['DANGER']:
        send_email('admin@example.com', 'eLot: CRITICAL DANGER!', str(datetime.now()))
        return dict(danger=True)
    return dict(categories=cat_cache, app_debug=app.config['DEBUG'])


def check_captcha(resp):
    import requests
    if app.config['DEBUG']:
        return True
    try:
        g_data = {'secret': app.config['CAPTCHA_SECRET'], 'response': resp}
        r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=g_data)
        if not r.json()['success']:
            raise TypeError
        return True
    except (TypeError, requests.exceptions.RequestException):
        return False


def get_steam_price(appid):
    import requests
    try:
        r = requests.get('http://store.steampowered.com/api/appdetails', {'appids': str(appid), 'cc': 'ru'})
        return int(r.json()[str(appid)]['data']['price_overview']['final']) * 0.01
    except (TypeError, requests.exceptions.RequestException):
        return None


def cancel_unpaid_orders():
    orders = models.Order.query.filter_by(paid=False, canceled=False).all()
    for order in orders:
        if not order.item.infinite:
            if (datetime.utcnow()-order.datetime).total_seconds() > app.config['CANCEL_UNPAID_ORDERS_AFTER_MINS']:
                order.data.used = False
                order.canceled = True
    db.session.commit()


def order_paid(odr):
    odr.paid = True
    odr.canceled = False
    if not odr.item.infinite:
        odr.data.used = True
    send_email(odr.user.email,
               'example.com: заказ оплачен',
               app.config['ORDER_EMAIL_TEXT'] % (odr.id, odr.data.data), html=True)
    db.session.commit()


def send_email(to_email, subject, message, html=False):
        import smtplib
        from email.header import Header
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.utils import formataddr
        nr_email = app.config['NOREPLY_EMAIL']
        nr_pw = app.config['NOREPLY_PW']
        msg = MIMEMultipart()
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = formataddr((str(Header('example.com', 'utf-8')), nr_email))
        msg['To'] = Header(to_email, 'utf-8')
        if html:
            msg.attach(MIMEText(message.encode('utf-8'), 'html', 'utf-8'))
        else:
            msg.attach(MIMEText(message.encode('utf-8'), 'plain', 'utf-8'))
        try:
            s = smtplib.SMTP_SSL(app.config['NOREPLY_SERVER'], 465)
            s.login(nr_email, nr_pw)
            s.sendmail(nr_email, to_email, msg.as_string())
            s.quit()
        except:
            if not app.config['DEBUG']:
                app.config['DANGER'] = True


def gen_pw():
    from random import SystemRandom
    pw_len = app.config['PASSWORD_LENGTH']
    return ''.join(SystemRandom().choice(list('ABCEFGHJKLMNPQRSTUVWXYZ123456789')) for _ in range(pw_len))


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


@app.template_filter('ps_price')
def ps_price(ps, price):
    if ps == 'wm':
        kom = price * 0.008 + 0.005
        if kom < 0.01:
            kom = 0.01
        return round(price + kom, 2)
    elif ps == 'ym':
        kom = price * 0.005 + 0.005
        return round(price + kom, 2)
    elif ps == 'vm':
        kom = price * 0.02 + 0.005
        if price + kom < 1:
            kom = 1 - price
        return round(price + kom, 2)


@app.template_filter('ru_pluralize')
def ru_pluralize(value, endings):
    endings = endings.split(',')
    if value % 100 in (11, 12, 13, 14):
        return endings[2]
    if value % 10 == 1:
        return endings[0]
    if value % 10 in (2, 3, 4):
        return endings[1]
    else:
        return endings[2]


@app.template_filter('hide_email')
def hide_email(value):
    a_pos = value.find('@')
    name = value[0] + '*'*(a_pos-2) + value[a_pos-1:]
    return name