# Сервис по сокращению url ссылок

Данный сервис позволяет создать короткую url ссылку

## Запуск проекта

1. Клонируем репозиторий и переходим в папку Short-url
```
git clone https://github.com/IvanMakhrov/Short-url.git
cd short-links
```

2. Запускаем контейнер
```
docker-compose up -d --build
```

## Технологии
1. Postgres<br>
База данных, в которой хранятся данные о пользователях и созданных ссылках<br>
url: jdbc:postgresql://localhost:5432/shortlinks<br>
username: postgres<br>
password: postgres<br>

2. FastApi
Api сервис<br>
http://0.0.0.0:8000/docs<br>

3. Redis
Кеширование запросов<br>

## Структура базы данных
1. Таблица links<br>
link_id - id ссылки (primary key)<br>
original_url - url ссылка<br>
short_code - Сокращенный код ссылки<br>
created_at - Дата создания ссылки<br>
expires_at - Дата истечения действия ссылки<br>
user_id - id пользователя (foreign key)<br>
click_count - Кол-во переходов по ссылке<br>
last_accessed - Дата предыдущего открытия ссылки<br>

2. Таблица users<br>
id - id пользователя (primary key)<br>
email - email пользователя<br>
hashed_password - Пароль<br>
registered_at - Дата регистрации<br>
is_active - Аккаунт пользователя активен (не используется)<br>
is_superuser - Аккаунт пользователя с расширенным доступом (не используется)<br>
is_verified - Аккаунт подтвержден (не используется)<br>

## Основные роутеры

1. Авторизация
* POST /auth/register - Регистрация пользователя
* POST auth/jwt/login - Авторизация пользователя
* POST auth/jwt/logout - Выход пользователя

2. Взаимодействие с url ссылками
* POST /links/shorten - Создать короткую ссылку<br>
Доступно всем пользователям<br>
Есть возможность добавить свой alias и указать дату истечения действия ссылки<br>
original_url - обязательное поле<br>
custom_alias - опционально<br>
expires_at - опционально<br>

Пример запроса:<br>
```
{
  "original_url": "https://example.com/",
  "custom_alias": "custom_link"
}
```
Пример ответа:<br>
```
{
  "short_code": "http://localhost:8000/links/my-link"
}
```

* GET/links/{short_code} - Перейти на url адрес по короткой ссылке<br>
Доступно всем пользователям<br>

Пример запроса:<br>
```
GET http://localhost:8000/links/custom_link
```
В результате происходит редирект на https://example.com/

* DELETE /links/{short_code} - Удаление короткой ссылки из БД<br>
Доступно только авторизованным пользователям. Можно удалять только свои ссылки<br>

Пример запроса:<br>
```
DETELE http://localhost:8000/links/custom_link
```
Пример ответа:<br>
```
{
  "message": "Link deleted"
}
```

* PUT /links/{short_code} - Изменение url который привязан к короткой ссылке<br>
Доступно только авторизованным пользователям. Можно изменять только свои ссылки<br>

Пример запроса:<br>
```
PUT http://localhost:8000/links/custom_link?new_url=https%3A%2F%2Fwww.google.com%2F
```
Пример ответа:<br>
```
{
  "message": "Link updated"
}
```

* GET /links/{short_code}/stats - Показать статистику короткой ссылки<br>
Доступно всем пользователям<br>

Пример запроса:<br>
```
GET http://localhost:8000/links/custom_link/stats
```
Пример ответа:<br>
```
{
  "original_url": "https://example.com/",
  "created_at": "2025-03-30T12:00:00",
  "expires_at": null,
  "click_count": 1,
  "last_accessed": "2025-03-30T15:30:00"
}
```

* GET /links/search/{original_url} - Найти короткую ссылку по url адресу и отобразить статистику<br>
Доступно всем пользователям<br>

Пример запроса:<br>
```
GET http://localhost:8000/links/search/custom_link
```
Пример ответа:<br>
```
{
    "short_code": "custom_link",
    "created_at": "2025-03-30T12:00:00",
    "expires_at": null,
    "click_count": 1,
    "last_accessed": "2025-03-30T15:30:00"
  }
  ```

* PATCH /links{short_link}/expiration - Обновить дату когда ссылка станет недействительной (дополнительный роутер)<br>
Доступно только авторизованным пользователям. Можно обновлять только свои ссылки<br>

Пример запроса:<br>
```
PATCH http://localhost:8000/links/82cc5b/expiration?expires_at=2025-03-31T15%3A30%3A00
```
Пример ответа:<br>
```
{
  "message": "Expiration updated",
  "expires_at": "2025-03-30T15:30:00"
}
```

3. Тестовые роутеры
* GET /protected-route - Доступно только авторизованным пользователям<br>

Пример запроса:<br>
```
GET http://localhost:8000/protected-route
```
Пример ответа:<br>
```
{
  "detail": "Unauthorized"
}
```

* GET /unprotected-route - Доступно всем пользователям<br>

Пример запроса:<br>
```
GET http://localhost:8000/unprotected-route
```
Пример ответа:<br>
```
"Hello, anonym"
```

## Дополнительные функции

1. Автоматическое удаление истекших ссылок<br>
Удаление происходит каждый день<br>

2. Автоматическое удаление неиспольуемых ссылок<br>
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
