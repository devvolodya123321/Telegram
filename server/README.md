# Custom Messenger Server

Python-сервер, который заменяет бэкенд Telegram, позволяя использовать
модифицированный клиент Telegram для Android как основу собственного мессенджера.

## Архитектура

```
┌─────────────────────┐         ┌──────────────────────────┐
│  Android-клиент     │  HTTP   │  Python-сервер (FastAPI)  │
│  (Telegram fork)    │ ──────> │                          │
│                     │  WS     │  SQLite + файловое       │
│  CustomApiClient    │ <────── │  хранилище медиа         │
└─────────────────────┘         └──────────────────────────┘
```

Сервер предоставляет REST API и WebSocket-соединение для real-time обновлений.

## Быстрый старт

### 1. Локальный запуск

```bash
cd server
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # отредактируйте SECRET_KEY

python -m uvicorn app.main:app --host 0.0.0.0 --port 8443 --reload
```

Сервер будет доступен по адресу `http://localhost:8443`.
Swagger-документация: `http://localhost:8443/docs`

### 2. Запуск через Docker

```bash
cd server
docker compose up -d --build
```

## API-эндпоинты

### Аутентификация (`/api/auth/`)

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/api/auth/sendCode` | Отправить SMS-код (в dev-режиме код возвращается в ответе) |
| POST | `/api/auth/signIn` | Войти по коду |
| POST | `/api/auth/signUp` | Регистрация нового пользователя |
| POST | `/api/auth/logOut` | Выход / инвалидация сессии |
| POST | `/api/auth/setPassword` | Установить 2FA-пароль |
| POST | `/api/auth/checkPassword` | Проверить 2FA-пароль |

### Пользователи (`/api/users/`)

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/api/users/getMe` | Получить информацию о текущем пользователе |
| POST | `/api/users/getUser` | Получить профиль пользователя по ID |
| POST | `/api/users/getUsers` | Получить профили нескольких пользователей |
| POST | `/api/users/updateProfile` | Обновить имя / фамилию / био |
| POST | `/api/users/updateUsername` | Установить/изменить username |

### Сообщения (`/api/messages/`)

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/api/messages/sendMessage` | Отправить текстовое сообщение |
| POST | `/api/messages/getHistory` | Получить историю чата |
| POST | `/api/messages/getDialogs` | Получить список диалогов |
| POST | `/api/messages/readHistory` | Пометить сообщения прочитанными |
| POST | `/api/messages/deleteMessages` | Удалить сообщения |
| POST | `/api/messages/editMessage` | Редактировать сообщение |
| POST | `/api/messages/forwardMessages` | Переслать сообщения |
| POST | `/api/messages/search` | Поиск по сообщениям |

### Контакты (`/api/contacts/`)

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/api/contacts/importContacts` | Импорт контактов по номерам телефонов |
| POST | `/api/contacts/getContacts` | Получить список контактов |
| POST | `/api/contacts/search` | Поиск пользователей |
| POST | `/api/contacts/deleteContacts` | Удалить контакт |
| POST | `/api/contacts/block` | Заблокировать пользователя |
| POST | `/api/contacts/unblock` | Разблокировать пользователя |
| POST | `/api/contacts/getBlocked` | Список заблокированных |

### Чаты и группы (`/api/chats/`)

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/api/chats/createChat` | Создать группу |
| POST | `/api/chats/createChannel` | Создать канал |
| POST | `/api/chats/editTitle` | Изменить название |
| POST | `/api/chats/addUser` | Добавить участника |
| POST | `/api/chats/deleteUser` | Удалить участника |
| POST | `/api/chats/getFullChat` | Информация о чате |
| POST | `/api/chats/getMembers` | Список участников |
| POST | `/api/chats/leaveChat` | Выйти из чата |
| POST | `/api/chats/startPrivate` | Начать личный чат |

### Медиа (`/api/media/`)

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/api/media/upload` | Загрузить файл |
| GET | `/api/media/download/{file_id}` | Скачать файл |
| POST | `/api/media/sendMedia` | Отправить сообщение с вложением |

### Real-time обновления

```
WebSocket: ws://<host>:<port>/api/updates/ws?token=<auth_token>
```

Типы обновлений:
- `updateNewMessage` — новое сообщение
- `updateEditMessage` — сообщение отредактировано
- `updateDeleteMessages` — сообщения удалены
- `updateReadHistoryOutbox` — собеседник прочитал сообщения
- `updateUserStatus` — пользователь онлайн/оффлайн
- `updateChatParticipantAdd` — пользователь добавлен в чат

## Пример использования (curl)

```bash
# 1. Запросить код
curl -X POST http://localhost:8443/api/auth/sendCode \
  -H "Content-Type: application/json" \
  -d '{"phone": "+79001234567"}'

# 2. Зарегистрироваться
curl -X POST http://localhost:8443/api/auth/signUp \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+79001234567",
    "phone_code_hash": "<hash из шага 1>",
    "code": "<code из шага 1>",
    "first_name": "Иван",
    "last_name": "Иванов"
  }'

# 3. Отправить сообщение (используя токен из шага 2)
curl -X POST http://localhost:8443/api/messages/sendMessage \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <auth_token>" \
  -d '{"chat_id": 1, "text": "Привет!"}'
```

## Настройка Android-клиента

В файле `CustomServerConfig.java`:

```java
// Включить свой сервер
CustomServerConfig.USE_CUSTOM_SERVER = true;

// Указать адрес сервера
CustomServerConfig.CUSTOM_SERVER_URL = "http://192.168.1.100:8443";
```

Клиент использует `CustomApiClient.java` для HTTP-запросов к серверу.

## Структура проекта

```
server/
├── app/
│   ├── main.py              # Точка входа FastAPI
│   ├── config.py            # Настройки (из .env)
│   ├── database.py          # SQLAlchemy async engine
│   ├── models/
│   │   ├── user.py          # User, AuthCode, Session
│   │   ├── message.py       # Chat, ChatMember, Message, Dialog
│   │   ├── contact.py       # Contact, BlockedUser
│   │   └── media.py         # MediaFile
│   ├── routers/
│   │   ├── auth.py          # Аутентификация
│   │   ├── users.py         # Профили пользователей
│   │   ├── contacts.py      # Контакты
│   │   ├── chats.py         # Чаты / группы / каналы
│   │   ├── messages.py      # Сообщения
│   │   ├── media.py         # Загрузка / скачивание файлов
│   │   └── updates.py       # WebSocket real-time обновления
│   ├── services/
│   │   └── updates.py       # Менеджер WebSocket-соединений
│   └── utils/
│       ├── security.py      # JWT, bcrypt
│       └── auth.py          # Middleware авторизации
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

## Дальнейшее развитие

- Подключить реальный SMS-провайдер (Twilio, SMS.ru и т.д.)
- Добавить push-уведомления (Firebase Cloud Messaging)
- Перейти на PostgreSQL для продакшн-нагрузок
- Добавить шифрование end-to-end
- Реализовать голосовые/видеозвонки (WebRTC)
- Добавить стикеры и реакции
