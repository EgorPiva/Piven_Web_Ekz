# Электронная библиотека

Экзаменационный Flask-проект.

Студент: Пивень Егор  
Группа: 241-371  
Вариант: 4, функциональность учета истории посещений.

Полная инструкция по проекту: [PROJECT_GUIDE.md](PROJECT_GUIDE.md)

## Реализовано

- учет просмотров страниц книг с лимитом 10 просмотров одной книги в день для одного пользователя;
- блок "Популярные книги" на главной странице за последние 3 месяца;
- блок "Недавно просмотренные книги" для авторизованных и неавторизованных пользователей;
- административная страница "Статистика" с журналом действий и статистикой просмотров;
- пагинация по 10 записей в статистике;
- экспорт журнала и статистики в CSV.

## Запуск

```powershell
pip install -r requirements.txt
flask --app app.py init-exam
flask --app app.py run
```

После инициализации доступен администратор:

```text
login: admin
password: admin
```

Для MySQL создайте `instance/config.py`:

```python
SQLALCHEMY_DATABASE_URI = "mysql+pymysql://user:password@localhost/std_NNNN_exam?charset=utf8mb4"
SECRET_KEY = "change-me"
STUDENT_GROUP = "241-371"
STUDENT_NAME = "Пивень Егор"
```

## Перед сдачей

1. Создайте отдельную базу данных MySQL с именем `std_NNNN_exam`.
2. Скопируйте [config.example.py](config.example.py) в `instance/config.py` и укажите свои параметры подключения.
3. Запустите инициализацию данных:

```powershell
flask --app app.py init-exam
```

4. Если проект уже развернут на MySQL, создайте дампы структуры и данных:

```powershell
mysqldump --no-data --column-statistics=0 -u std_NNNN_exam -h std-mysql -p std_NNNN_exam > database-schema.sql
mysqldump --column-statistics=0 -u std_NNNN_exam -h std-mysql -p std_NNNN_exam > database.sql
```

5. Проверьте, что в репозиторий не попали `.venv`, `instance/config.py`, локальные пароли и другие временные файлы.
6. Зафиксируйте в Git свежие изменения вместе с `database-schema.sql` и `database.sql`.
7. Для ответа в LMS подготовьте:
   - ссылку на репозиторий;
   - ссылку на сайт на хостинге;
   - логины и пароли пользователей с разными ролями.

## Запуск на хостинге

На хостинге можно использовать `app.py` или `wsgi.py` как точку входа. Оба файла экспортируют `application` и `app`.
