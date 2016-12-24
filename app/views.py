from app import app, forms, models, db, functions
from flask import render_template, request, redirect, flash, url_for, session, abort, make_response
from flask.ext.login import login_user, logout_user, login_required, current_user


@app.route('/')
def home():
    _items = models.Item.query.filter_by(hidden=False).order_by(
        models.Item.priority.desc(),
        models.Item.id.desc()).limit(15).all()
    items = []
    for _item in _items:
        if _item.goods_num > 0:
            items.append(_item)
    return render_template('home.html', items=items, page_title='eLot - магазин цифровых товаров')


@app.route('/category/<int:num>')
def category(num):
    _items = models.Item.query.filter_by(hidden=False, category_id=num).order_by(
        models.Item.priority.desc(),
        models.Item.id.desc()).limit(15).all()
    items = []
    for _item in _items:
        if _item.goods_num > 0:
            items.append(_item)
    return render_template('home.html', items=items, cat_id=num,
                           page_title=models.Category.query.get_or_404(num).name+' - eLot')


@app.route('/item/<int:num>')
def item(num):
    itm = models.Item.query.get_or_404(num)
    _orders = reversed(list(models.Order.query.filter_by(item_id=num, paid=True)))
    return render_template('item.html', item=itm, orders=_orders, page_title=itm.name+' - купить в eLot')


@app.route('/profile')
@login_required
def profile():
    orders = list(models.Order.query.filter_by(user_id=current_user.id))
    return render_template('profile.html', orders=reversed(orders), page_title='Мои покупки - eLot')


@app.route('/new_order/<int:num>/<ps>')
@login_required
def new_order(num, ps):
    from datetime import datetime
    _item = models.Item.query.get_or_404(num)
    if ps not in app.config['PAYMENT_SYSTEMS']:
        return redirect(url_for('item', num=num))
    temp_order = models.Order.query.filter_by(user_id=current_user.id, paid=False, canceled=False).first()
    if temp_order:
        flash('Прежде чем сделать новый заказ этого товара оплатите или отмените этот')
        return redirect(url_for('order', num=temp_order.id))

    data = models.Data.query.filter_by(item_id=_item.id, used=False).first()
    if not data:
        flash('Извините, данный товар закончился. Попробуйте позже')
        return redirect(url_for('home'))

    _order = models.Order(
        _item.id,
        current_user.id,
        datetime.utcnow(),
        functions.ps_price(ps, _item.price),
        ps
    )
    if _item.infinite:
        data = models.Data(_item.id, data.data)

    _order.data = data
    data.used = True
    data.order_id = _order.id

    if _item.infinite:
        db.session.add(data)
    db.session.add(_order)
    db.session.commit()
    return redirect(url_for('order', num=_order.id))


@app.route('/cancel_order/<int:num>')
@login_required
def cancel_order(num):
    _order = models.Order.query.get(num)
    if not _order or _order.user_id != current_user.id or _order.canceled:
        return redirect(url_for('home'))
    _order.data.used = False
    _order.canceled = True
    db.session.commit()
    flash('Заказ № '+str(num)+' отменен')
    return redirect(url_for('profile'))


@app.route('/order/<int:num>')
@login_required
def order(num):
    _order = models.Order.query.get_or_404(num)
    if _order.user_id != current_user.id:
        return abort(403)
    from datetime import datetime
    if not _order.item.infinite and (datetime.utcnow()-_order.datetime).total_seconds() > 900:
        redirect(url_for('cancel_order', num=_order.id))
    import base64
    b64desc = str(base64.b64encode(bytes('eLot.xyz: ', "utf-8")+bytes(_order.item.name, "utf-8")))
    return render_template('order.html', order=_order, b64desc=b64desc,
                           page_title='Оплата заказа № ' + str(_order.id) + ' - eLot')


@app.route('/comment/<int:num>', methods=['GET', 'POST'])
@login_required
def comment(num):
    _order = models.Order.query.get_or_404(num)
    if _order.user_id != current_user.id:
        return redirect(url_for('profile'))
    if _order.rating is not None:
        return redirect(url_for('item', num=_order.item.id))
    form = forms.ReviewForm(request.form)
    if request.method == 'POST' and form.validate_on_submit():
        if form.rating.data == 'good':
            _order.rating = True
        elif form.rating.data == 'bad':
            _order.rating = False
        _order.review = form.review.data
        db.session.commit()
        return redirect(url_for('item', num=_order.item.id))
    return render_template('comment.html', form=form, order=_order, page_title='Отзыв о товаре - eLot')


@app.route("/contacts")
def contacts():
    return render_template('contacts.html', page_title='Контакты - eLot')


@app.route("/about")
def about():
    return render_template('about.html', page_title='О магазине - eLot')


@app.route("/steam_price/<int:num>")
def steam_price(num):
    itm = models.Item.query.get_or_404(num)
    i_price = itm.price
    s_price = functions.get_steam_price(itm.steam_appid)
    if not s_price or s_price <= i_price:
        return ''
    saving = 100 - int(i_price/s_price*100)
    if itm.goods_num > 0:
        return render_template('admin/steam_price.html', price=s_price, saving=saving, in_stock=True)
    else:
        return render_template('admin/steam_price.html', price=s_price, saving=saving, in_stock=False)


@app.route('/sitemap.xml')
def sitemap():
    pages = [
        [url_for('home', _external=True), 'daily', '0.9'],
        [url_for('contacts', _external=True), 'yearly', '0.5'],
        [url_for('about', _external=True), 'yearly', '0.5'],
    ]
    items = models.Item.query.filter_by(hidden=False).all()
    for itm in items:
        pages.append([url_for('item', _external=True, num=itm.id), 'weekly', '1.0'])

    sitemap_xml = render_template('admin/sitemap.xml', pages=pages)
    response = make_response(sitemap_xml)
    response.headers["Content-Type"] = "application/xml"
    return response


class LoginViews:
    @staticmethod
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        form = forms.LoginForm(request.form)
        user_email = session['user_email']
        if request.method == 'POST' and form.validate_on_submit():
            user = models.User.query.filter_by(email=user_email).first()
            if user is not None:
                if user.password == form.password.data.upper():
                    login_user(user, bool(form.remember_me.data))
                    flash('Вы вошли в систему!')
                    session['user_email'] = ''
                    user.password = functions.gen_pw()
                    db.session.commit()
                    try:
                        nxt = session['next_url']
                        session['next_url'] = None
                    except KeyError:
                        nxt = None

                    return redirect(nxt or url_for('profile'))
            form.password.errors.append('Неверный пароль. <a href="'+url_for('signup')+'">Отправить код заново</a>')
        return render_template('login.html', form=form, user_email=user_email, page_title='Вход - eLot')

    @staticmethod
    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash('Вы вышли из системы!')
        return redirect(url_for('home'))

    @staticmethod
    @app.route('/signup', methods=['GET', 'POST'])
    def signup():
        form = forms.SignUpForm(request.form)
        try:
            user_email = session['user_email']
        except KeyError:
            user_email = None
        if request.args.get('next') and functions.is_safe_url(request.args.get('next')):
            session['next_url'] = request.args.get('next')

        if (request.method == 'POST' and form.validate_on_submit()) or user_email:
            if not user_email:
                if not functions.check_captcha(request.form['g-recaptcha-response']):
                    form.email.errors.append('Подтвердите, что вы не робот &darr;')
                    return render_template('signup.html', form=form, page_title='Вход - eLot')
                user_email = form.email.data

            pw = functions.gen_pw()
            user = models.User.query.filter_by(email=user_email).first()
            if user is None:
                user = models.User(user_email, pw)
                db.session.add(user)
            else:
                user.password = pw
            db.session.commit()

            functions.send_email(user_email, 'example.com: доступ к покупкам', app.config['PASSWORD_EMAIL_TEXT'] % pw)
            session['user_email'] = user_email
            flash('Вам на email отправлено письмо с кодом активации, введите его в поле ниже.')
            return redirect(url_for('login'))
        return render_template('signup.html', form=form, page_title='Вход - eLot')


class AdminPanel:
    @staticmethod
    @app.route('/admin')
    @login_required
    def admin_home():
        if not current_user.is_admin():
            return abort(403)
        items = models.Item.query.order_by(models.Item.priority.desc(), models.Item.id.desc()).all()
        return render_template('admin/items.html', items=items)

    @staticmethod
    @app.route('/admin/cancel_unpaid')
    def admin_cancel_unpaid():
        functions.cancel_unpaid_orders()
        return '', 200

    @staticmethod
    @app.route('/admin/new')
    @login_required
    def admin_new():
        if not current_user.is_admin():
            return abort(403)
        itm = models.Item('', '', '', 0, True, 1)
        itm.hidden = True
        db.session.add(itm)
        db.session.commit()
        return redirect(url_for('admin_item', num=itm.id))

    @staticmethod
    @app.route('/admin/<int:num>', methods=['GET', 'POST'])
    @login_required
    def admin_item(num):
        if not current_user.is_admin():
            return abort(403)
        itm = models.Item.query.get_or_404(num)
        if request.method == 'POST':
            if request.form['FORM_TYPE'] == 'item':
                itm.name = request.form['name']
                itm.short_description = request.form['short_desc']
                itm.description = request.form['description']
                itm.price = round(float(request.form['price']), 2)
                itm.ru_cis = True if request.form['ru_cis'] == 'true' else False
                itm.hidden = True if request.form['hidden'] == 'true' else False
                itm.category_id = int(request.form['cat_id'])
                itm.priority = None if not request.form['priority'] else int(request.form['priority'])
                itm.steam_appid = None if not request.form['steam_appid'] else int(request.form['steam_appid'])
                itm.info = request.form['info']
                if request.form['img_url'] and str(request.form['img_url']).endswith('.jpg'):
                    import requests
                    import shutil
                    import os.path as pth
                    from os import remove
                    path = pth.abspath(pth.join(pth.dirname(__file__), 'static', 'item_img', str(num)+'.jpg'))
                    r = requests.get(request.form['img_url'], stream=True)
                    if r.status_code == 200:
                        if pth.isfile(path):
                            remove(path)
                        with open(path, 'wb') as f:
                            r.raw.decode_content = True
                            shutil.copyfileobj(r.raw, f)
                db.session.commit()
                flash('Товар изменен')
            elif request.form['FORM_TYPE'] == 'goods':
                db.session.add(models.Data(int(request.form['item_id']), request.form['new_data']))
                db.session.commit()

        from random import getrandbits
        return render_template('admin/item_form.html',
                               item=itm, img_rand=getrandbits(30),
                               categories=models.Category.query.all(),
                               goods=reversed(list(models.Data.query.filter_by(item_id=itm.id, used=False))))

    @staticmethod
    @app.route('/admin/<int:num>/delete')
    @login_required
    def admin_item_delete(num):
        if not current_user.is_admin():
            return abort(403)
        db.session.delete(models.Item.query.get(num))
        db.session.commit()
        return redirect(url_for('admin_home'))

    @staticmethod
    @app.route('/admin/data/<int:num>/delete')
    @login_required
    def admin_data_delete(num):
        if not current_user.is_admin():
            return abort(403)
        data = models.Data.query.get_or_404(num)
        i_id = data.item_id
        db.session.delete(data)
        db.session.commit()
        return redirect(url_for('admin_item', num=i_id))

    @staticmethod
    @app.route('/admin/<int:num>/orders')
    @login_required
    def admin_item_orders(num):
        if not current_user.is_admin():
            return abort(403)
        if num == 0:
            orders = reversed(list(models.Order.query.all()))
            item_name = 'Все'
        else:
            orders = reversed(list(models.Order.query.filter_by(item_id=num)))
            item_name = models.Item.query.get(num).name
        return render_template('admin/item_orders.html', orders=orders, item_name=item_name)



class PaymentHTTPNotifications:
    @staticmethod
    @app.route('/ym-http-EXAMPLE-SECRET', methods=['POST'])
    def ym_http():
        with open('payment.log', 'a') as log:
            log.write('='*30+'\n')
            s = '&'.join([
                request.form['notification_type'],
                request.form['operation_id'],
                request.form['amount'],
                request.form['currency'],
                request.form['datetime'],
                request.form['sender'],
                request.form['codepro'],
                app.config['YM_SECRET'],
                request.form['label']
            ])
            log.write(s+'\n')
            from hashlib import sha1
            hh = sha1(s.encode('utf-8')).hexdigest()
            if hh == request.form['sha1_hash']:
                log.write('Hash APPROVED!\n')
                o_id = int(request.form['label'])
                odr = models.Order.query.get(o_id)
                if odr.paid:
                    log.write('YM/VM Repeat OK!\n'+'='*30)
                    return '', 200
                if abs(odr.item.price - round(float(request.form['amount']), 2)) <= 0.05:
                    log.write('Price APPROVED!\n')
                functions.order_paid(odr)
                log.write('YM/VM PAYMENT OK! id=%d\n' % odr.id)
                return '', 200
            else:
                log.write('YM/VM PAYMENT FAIL! id=%d\n' % int(request.form['label']))
                return abort(404)

    @staticmethod
    @app.route('/wm-http-EXAMPLE-SECRET', methods=['POST'])
    def wm_http():
        with open('payment.log', 'a') as log:
            try:
                if request.form['LMI_PREREQUEST'] == '1':
                    log.write('='*30+'\n'+'WM PREREQUEST OK!')
                    # TODO: Check Amount
                    return 'YES', 200
            except KeyError:
                pass
            log.write('='*30+'\n')
            s = ''.join([
                request.form['LMI_PAYEE_PURSE'],
                request.form['LMI_PAYMENT_AMOUNT'],
                request.form['LMI_PAYMENT_NO'],
                request.form['LMI_MODE'],
                request.form['LMI_SYS_INVS_NO'],
                request.form['LMI_SYS_TRANS_NO'],
                request.form['LMI_SYS_TRANS_DATE'],
                app.config['WM_SECRET'],
                request.form['LMI_PAYER_PURSE'],
                request.form['LMI_PAYER_WM']
            ])
            log.write(s+'\n')
            from hashlib import sha256
            hh = str(sha256(s.encode('utf-8')).hexdigest()).upper()
            if hh == request.form['LMI_HASH']:
                log.write('Hash APPROVED!\n')
                o_id = int(request.form['LMI_PAYMENT_NO'])
                odr = models.Order.query.get(o_id)
                if odr.paid:
                    log.write('WM Repeat OK!\n')
                    return '', 200
                if abs(odr.item.price - round(float(request.form['LMI_PAYMENT_AMOUNT']), 2)) <= 0.05:
                    log.write('Price APPROVED!\n')
                    functions.order_paid(odr)
                log.write('WM PAYMENT OK! id=%d\n' % odr.id)
                return '', 200
            else:
                log.write('WM PAYMENT FAIL! id=%d\n' % int(request.form['LMI_PAYMENT_NO']))
                return abort(404)


    @staticmethod
    @app.route('/fake-pay/<int:num>')
    def fake_pay(num):
        if not app.config['DEBUG']:
            return abort(404)
        odr = models.Order.query.get_or_404(num)
        functions.order_paid(odr)
        return 'FAKE PAYMENT ACCEPT!', 200


class HTTPErrorHandlers:
    @staticmethod
    @app.errorhandler(403)
    @app.errorhandler(404)
    @app.errorhandler(500)
    def http_error(e):
        err = 'Ошибка'
        code = 500
        try:
            err = e.name
            code = e.code
            if code == 404:
                err = 'Страница не найдена'
            elif code == 403:
                err = 'Доступ запрещён'
            elif code == 500 or code == 502:
                err = 'Внутренняя ошибка сервера'
        finally:
            return render_template('error.html', code=code, error=err,
                                   page_title='Ошибка '+str(code)+': '+err+' - eLot'), code
