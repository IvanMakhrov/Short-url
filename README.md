# Сервис по сокращению url ссылок

Данный сервис позволяет создать короткую url ссылку

## Запуск проекта

1. Клонируем репозиторий и переходим в папку Short-url
```
git clone <ваш-репозиторий>
cd short-links
```

2. Запускаем контейнер
```
docker-compose up -d --build
```

## Технологии
1. Postgres
База данных, в которой хранятся данные о пользователях и созданных ссылках<br>
url: jdbc:postgresql://localhost:5432/shortlinks<br>
username: postgres<br>
password: postgres<br>

### Структура БД
* links
link_id - id ссылки (primary key)<br>
original_url - url ссылка<br>
short_code - Сокращенный код ссылки<br>
created_at - Дата создания ссылки<br>
expires_at - Дата истечения действия ссылки<br>
user_id - id пользователя (foreign key)<br>
click_count - Кол-во переходов по ссылке<br>
last_accessed - Дата предыдущего открытия ссылки<br>

* users
id - id пользователя (primary key)<br>
email - email пользователя<br>
hashed_password - Пароль<br>
registered_at - Дата регистрации<br>
is_active - Аккаунт пользователя активен (не используется)<br>
is_superuser - Аккаунт пользователя с расширенным доступом (не используется)<br>
is_verified - Аккаунт подтвержден (не используется)<br>

2. FastApi
Api сервис<br>
http://0.0.0.0:8000/docs<br>

3. Redis
Кеширование запросов<br>

## Основные роутеры

1. Авторизация
* POST /auth/register - Регистрация пользователя
* POST auth/jwt/login - Авторизация пользователя
* POST auth/jwt/logout - Выход пользователя

2. Взаимодействие с url ссылками
* POST /links/shorten - Создать короткую ссылку
Доступно всем пользователям<br>
original_url - обязательное поле<br>
custom_alias - опционально<br>
expires_at - опционально<br>
* GET/links/{short_code} - Перейти на url адрес по короткой ссылке
Доступно всем пользователям
* DELETE /links/{short_code} - Удаление короткой ссылки из БД
Доступно только авторизованным пользователям. Можно удалять только свои ссылки
* PUT /links/{short_code} - Изменение url который привязан к короткой ссылке
Доступно только авторизованным пользователям. Можно изменять только свои ссылки
* GET /links/{short_code}/stats - Показать статистику короткой ссылки
Доступно всем пользователям
* GET /links/search/{original_url} - Найти короткую ссылку по url адресу и отобразить статистику
Доступно всем пользователям
* PATCH /links{short_link}/expiration - Обновить дату когда ссылка станет недействительной
Доступно только авторизованным пользователям. Можно обновлять только свои ссылки

3. Тестовые роутеры
* GET /protected-route - Доступно только авторизованным пользователям
* GET /unprotected-route - Доступно всем пользователям

## Дополнительные функции

1. Автоматическое удаление истекших ссылок
Удаление происходит каждый день

2. Автоматическое удаление неиспольуемых ссылок
Если ссылкой не пользовались более 7 дней, то она будет автоматически удалена<br>
Проверка на старые ссылки происходит каждый день<br>

## Тесты и деплой
Ниже представлены скриншоты деплоя сервиса и тестов

### Деплой сервиса
![Alt text](https://github.com/IvanMakhrov/Short-url/blob/main/images/docker.png?raw=true)

### Тестирование
![Alt text](https://github.com/IvanMakhrov/Short-url/blob/main/images/tests_success.png?raw=true)

### Покрытие тестами
![Alt text](https://github.com/IvanMakhrov/Short-url/blob/main/images/tests_coverage.png?raw=true)

### Нагрузочное тестирование
![Alt text](https://github.com/IvanMakhrov/Short-url/blob/main/images/locust_tests.png?raw=true)
