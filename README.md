# 🔗 Сервис по сокращению URL ссылок

Данный сервис позволяет создать короткую URL ссылку

---

## 🚀 Запуск проекта

1. Клонируем репозиторий и переходим в папку Short-url
```bash
git clone https://github.com/IvanMakhrov/Short-url.git
cd short-links
```

2. Запускаем контейнер
```bash
docker-compose up -d --build
```

## 🛠 Технологии

| Технология | Описание |
|------------|----------|
| Postgres | База данных для хранения информации о пользователях и ссылках
URL: jdbc:postgresql://localhost:5432/shortlinks
Username: postgres
Password: postgres |
| FastAPI | API сервис
Документация: http://0.0.0.0:8000/docs |
| Redis | Кеширование запросов |

---

## 🗃 Структура базы данных

### Таблица links
| Поле | Тип | Описание |
|------|-----|----------|
| link_id | PRIMARY KEY | ID ссылки |
| original_url | TEXT | Оригинальный URL |
| short_code | TEXT | Сокращенный код ссылки |
| created_at | TIMESTAMP | Дата создания |
| expires_at | TIMESTAMP | Дата истечения |
| user_id | FOREIGN KEY | ID пользователя |
| click_count | INTEGER | Количество переходов |
| last_accessed | TIMESTAMP | Дата последнего доступа |

### Таблица users
| Поле | Тип | Описание |
|------|-----|----------|
| id | PRIMARY KEY | ID пользователя |
| email | TEXT | Email пользователя |
| hashed_password | TEXT | Хеш пароля |
| registered_at | TIMESTAMP | Дата регистрации |
| is_active | BOOLEAN | Активен ли аккаунт (не используется) |
| is_superuser | BOOLEAN | Расширенные права (не используется) |
| is_verified | BOOLEAN | Подтвержден ли аккаунт (не используется) |

---

## 🌐 Основные роутеры

### 🔐 Авторизация
- POST /auth/register - Регистрация пользователя
- POST /auth/jwt/login - Авторизация пользователя
- POST /auth/jwt/logout - Выход пользователя

### 🔗 Взаимодействие с URL
#### Создание короткой ссылки
POST /links/shorten
Доступ: всем пользователям
Параметры:
- original_url (обязательно)
- custom_alias (опционально)
- expires_at (опционально)

Пример запроса:<br>
```json 
{"original_url": "https://example.com/",  "custom_alias": "custom_link"} 
```
Пример ответа:<br>
```json 
{"short_code": "http://localhost:8000/links/my-link"} 
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
```json
{"message": "Link deleted"}
```

* PUT /links/{short_code} - Изменение url который привязан к короткой ссылке<br>
Доступно только авторизованным пользователям. Можно изменять только свои ссылки<br>

Пример запроса:<br>
```
PUT http://localhost:8000/links/custom_link?new_url=https%3A%2F%2Fwww.google.com%2F
```
Пример ответа:<br>
```json
{"message": "Link updated"}
```

* GET /links/{short_code}/stats - Показать статистику короткой ссылки<br>
Доступно всем пользователям<br>

Пример запроса:<br>
```
GET http://localhost:8000/links/custom_link/stats
```
Пример ответа:<br>
```json
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
```json
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
```json
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
```json
{"detail": "Unauthorized"}
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

---

## ⚙️ Дополнительные функции
- 🗑️ Автоматическое удаление истекших ссылок (ежедневно)
- 🕒 Автоматическое удаление неиспользуемых ссылок (более 7 дней без использования)

## 📊 Тесты и деплой
Ниже представлены скриншоты деплоя сервиса и тестов

### Деплой сервиса
![Alt text](https://github.com/IvanMakhrov/Short-url/blob/main/images/docker.png?raw=true)

### Тестирование
![Alt text](https://github.com/IvanMakhrov/Short-url/blob/main/images/tests_success.png?raw=true)

### Покрытие тестами
![Alt text](https://github.com/IvanMakhrov/Short-url/blob/main/images/tests_coverage.png?raw=true)

### Нагрузочное тестирование
![Alt text](https://github.com/IvanMakhrov/Short-url/blob/main/images/locust_tests.png?raw=true)
