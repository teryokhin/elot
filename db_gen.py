from app import db
import app.models as models


db.drop_all()
db.create_all()

it = models.User('admin@example.com', 'examplepass')
it.admin = True
db.session.add(it)

db.session.add(models.Category("Экшен"))  # 1
db.session.add(models.Category("Приключения"))
db.session.add(models.Category("Стратегии"))
db.session.add(models.Category("Симуляторы"))
db.session.add(models.Category("Ролевые"))  # 5
db.session.add(models.Category("Казуальные"))
db.session.add(models.Category("Инди"))
db.session.add(models.Category("Гонки"))
db.session.add(models.Category("Спорт"))
db.session.add(models.Category("Файтинги"))
db.session.add(models.Category("Другое"))  # 11

it = models.Item(
    "Тестовая покупка",
    "Купите этот товар и убедитесь в простоте процесса оплаты и получения заказа",
    "Купите этот товар и убедитесь в простоте процесса оплаты и получения заказа",
    0.01,
    False,
    11
)
it.infinite = True
db.session.add(it)

db.session.add(models.Item(
    "New kind of adventure",
    """
New kind of adventure - приключенческая игра с элементами РПГ.<br/>
Мария прячется в шкаф после ссоры ее родителей. Там она засыпает. А когда просыпается...
    """,
    """
New kind of adventure - приключенческая игра с элементами РПГ.<br/>
Мария прячется в шкаф после ссоры ее родителей. Там она засыпает. А когда просыпается, оказывается в красивом, волшебном мире с гигантской клубникой и магическими друидоми!<br/>
С ее новым другом Водолей, Мэри должна найти способ вернуться в реальный мир!<br/>
<br/>
Особенности:<br/>
Используйте новые найденные силы Марии и магические способности Водолея решатя головоломки и выполняя задания.<br/>
Собирайте артефакты, чтобы разблокировать новые магические силы и способности.<br/>
Огромный яркий мир, с красочными дикими животными.<br/>
Собирайте предметы и ресурсы для торговли с друидами.<br/>
Оригинальный саундтрек.
    """,
    4.6,
    True,
    7
))
db.session.commit()

db.session.add(models.Data(
    1,
    "Поздравляем! Вы успешно совершили вашу тестовую покупку. Теперь пора купить что-то более полезное :)"
))

db.session.add(models.Data(
    2,
    'Ссылка на получение игры в Steam: <a href="http://examle.com">http://examle.com</a>'
))

db.session.commit()
