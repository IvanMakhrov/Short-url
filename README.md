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

---

## 🛠 Технологии

| Технология | Описание |
|------------|----------|
| Postgres | База данных для хранения информации о пользователях и ссылках <br> **URL:** jdbc:postgresql://localhost:5432/shortlinks <br> **Username:** postgres <br> **Password:** postgres |
| FastAPI | API сервис <br> Документация: http://0.0.0.0:8000/docs |
| Redis | Кеширование запросов |

## 📊 Структура базы данных

### Таблица links
| Поле | Тип | Описание |
|------|-----|----------|
| link_id | PRIMARY KEY | ID ссылки |
| original_url | VARCHAR | Оригинальный URL |
| short_code | VARCHAR | Сокращенный код ссылки |
| created_at | TIMESTAMP | Дата создания |
| expires_at | TIMESTAMP | Дата истечения |
| user_id | FOREIGN KEY | ID пользователя |
| click_count | INTEGER | Количество переходов |
| last_accessed | TIMESTAMP | Дата последнего доступа |

### Таблица users
| Поле | Тип | Описание |
|------|-----|----------|
| id | PRIMARY KEY | ID пользователя |
| email | VARCHAR | Email пользователя |
| hashed_password | VARCHAR | Хеш пароля |
| registered_at | TIMESTAMP | Дата регистрации |
| is_active | BOOLEAN | Активен ли аккаунт (не используется) |
| is_superuser | BOOLEAN | Расширенные права (не используется) |
| is_verified | BOOLEAN | Подтвержден ли аккаунт (не используется) |

### Таблица alembic_version
| Поле | Тип | Описание |
|------|-----|----------|
| version_num | PRIMARY KEY | ID миграции |

---

## 🌐 Основные роутеры

### 🔐 Авторизация

#### 1. POST http://localhost:8000/auth/register
Регистрация пользователя<br>
Пример запроса:<br>
```json
{
  "email": "string",
  "password": "string",
  "is_active": true,
  "is_superuser": false,
  "is_verified": false
}
```
Пример ответа:<br>
```json
{
  "id": 2,
  "email": "string1",
  "is_active": true,
  "is_superuser": false,
  "is_verified": false
}
```

#### 2. POST http://localhost:8000/auth/jwt/login
Авторизация пользователя<br>
Параметры:
- username (обязательно)
- password (обязательно)

Пример ответа:<br>
```json
{
  "access_token": "token",
  "token_type": "bearer"
}
```

#### 3. POST http://localhost:8000/auth/jwt/logout
Выход пользователя<br>
Пример запроса:<br>
```
http://localhost:8000/auth/jwt/logout
```

### 🔗 Взаимодействие с URL

#### 1. POST /links/shorten<br>
Доступ: всем пользователям<br>
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

#### 2. GET /links/{short_code}
Перейти на url адрес по короткой ссылке<br>
Доступно всем пользователям<br>

Пример запроса:<br>
```
GET http://localhost:8000/links/custom_link
```
В результате происходит редирект на https://example.com/

#### 3. DELETE /links/{short_code}
Удаление короткой ссылки из БД<br>
Доступно только авторизованным пользователям. Можно удалять только свои ссылки<br>

Пример запроса:<br>
```
DETELE http://localhost:8000/links/custom_link
```
Пример ответа:<br>
```json
{"message": "Link deleted"}
```

#### 4. PUT /links/{short_code}
Изменение url который привязан к короткой ссылке<br>
Доступно только авторизованным пользователям. Можно изменять только свои ссылки<br>

Пример запроса:<br>
```
PUT http://localhost:8000/links/custom_link?new_url=https%3A%2F%2Fwww.google.com%2F
```
Пример ответа:<br>
```json
{"message": "Link updated"}
```

#### 5. GET /links/{short_code}/stats
Показать статистику короткой ссылки<br>
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

#### 6. GET /links/search/{original_url}
Найти короткую ссылку по url адресу и отобразить статистику<br>
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

#### 7.PATCH /links{short_link}/expiration
Обновить дату когда ссылка станет недействительной (дополнительный роутер)<br>
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

### 🔧 Тестовые роутеры
#### 1. GET /protected-route
Доступно только авторизованным пользователям<br>

Пример запроса:<br>
```
GET http://localhost:8000/protected-route
```
Пример ответа:<br>
```json
{"detail": "Unauthorized"}
```

#### 2. GET /unprotected-route
Доступно всем пользователям<br>

Пример запроса:<br>
```
GET http://localhost:8000/unprotected-route
```
Пример ответа:<br>
```
"Hello, anonym"
```

## ⚙️ Дополнительные функции
- 🗑️ Автоматическое удаление истекших ссылок (ежедневно)
- 🕒 Автоматическое удаление неиспользуемых ссылок (более 7 дней без использования)

---

## 📊 Тесты и деплой
Запуск тестов<br>
```bash
pytest --cov=src --cov-report=html tests/ 
```

Покрытие тестами<br>
```bash
python3 -m coverage report 
```

Также можно посмотреть отчет о покрытии тестами<br>
```bash
open index.html
```

Ниже представлены скриншоты деплоя сервиса и тестов

### Деплой сервиса
![Alt text](https://github.com/IvanMakhrov/Short-url/blob/main/images/docker.png?raw=true)

### Тестирование
![Alt text](https://github.com/IvanMakhrov/Short-url/blob/main/images/tests_success.png?raw=true)

### Покрытие тестами
![Alt text](https://github.com/IvanMakhrov/Short-url/blob/main/images/tests_coverage.png?raw=true)

### Нагрузочное тестирование
![Alt text](https://github.com/IvanMakhrov/Short-url/blob/main/images/locust_tests.png?raw=true)
