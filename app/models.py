from app import db, login_manager


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    items = db.relationship('Item', backref='category')

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<Category: %s>' % self.name


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    short_description = db.Column(db.String(256), nullable=False)
    description = db.Column(db.String(1024), nullable=False)
    price = db.Column(db.Float, nullable=False)
    infinite = db.Column(db.Boolean)
    ru_cis = db.Column(db.Boolean)
    hidden = db.Column(db.Boolean)
    orders = db.relationship('Order', backref='item')
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    steam_appid = db.Column(db.Integer)
    priority = db.Column(db.Integer)
    info = db.Column(db.String(256))

    def __init__(self, name, short_description, description, price, ru_cis, cat_id):
        self.name = name
        self.short_description = short_description
        self.description = description
        self.price = price
        self.infinite = False
        self.ru_cis = ru_cis
        self.hidden = False
        self.category_id = cat_id
        self.info = ''

    def __getattr__(self, item):
        if item == "order_num":
            count = 0
            for _item in self.orders:
                if _item.paid:
                    count += 1
            return count
        elif item == "goods_all":
            return Data.query.filter_by(item_id=self.id).all()
        elif item == "goods_num":
            if self.infinite:
                return 999999
            return len(Data.query.filter_by(item_id=self.id, used=False).all())
        else:
            raise AttributeError("%r object has no attribute %r" % (self.__class__, item))

    def __repr__(self):
        return '<Item: %s, Category: %s>' % \
               (self.name, Category.query.filter_by(id=self.category_id).first().name)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(256), nullable=False)
    password = db.Column(db.String(10), nullable=False)
    orders = db.relationship('Order', backref='user')
    admin = db.Column(db.Boolean)

    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.admin = False

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def is_admin(self):
        return self.admin

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return '<User: %s>' % self.email


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    datetime = db.Column(db.DateTime)
    price = db.Column(db.Float, nullable=False)
    paid = db.Column(db.Boolean)
    canceled = db.Column(db.Boolean)
    payment_system = db.Column(db.String(4), nullable=False)
    data = db.relationship("Data", uselist=False, backref="order")
    rating = db.Column(db.Boolean)
    review = db.Column(db.String(256))

    def __init__(self, item_id, user_id, datetime, price, payment_system):
        self.item_id = item_id
        self.user_id = user_id
        self.datetime = datetime
        self.price = price
        self.paid = False
        self.canceled = False
        self.payment_system = payment_system

    def __repr__(self):
        return '<Order: %s ordered %s for %f>' % \
               (self.user,
                self.item,
                self.price)

class Data(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    data = db.Column(db.String(512), nullable=False)
    used = db.Column(db.Boolean, nullable=False)

    def __init__(self, item_id, data):
        self.item_id = item_id
        self.data = data
        self.used = False

    def __repr__(self):
        return '<Data: %s>' % self.data


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

