# InteriorBot v1 — Визуальная схема архитектуры

## Общая архитектура системы

```mermaid
graph TB
    User[👤 Пользователь Telegram] --> Bot[🤖 Bot Main]
    
    Bot --> Dispatcher[Dispatcher aiogram 3.x]
    
    Dispatcher --> R1[Router: user_start]
    Dispatcher --> R2[Router: creation]
    Dispatcher --> R3[Router: payment]
    
    R1 --> KB[Keyboards Generator]
    R2 --> KB
    R3 --> KB
    
    R1 --> DB[(Database SQLite)]
    R2 --> DB
    R3 --> DB
    
    R2 --> Replicate[🎨 Replicate API<br/>Image Generation]
    R3 --> YooKassa[💰 YooKassa API<br/>Payment Processing]
    
    DB --> Users[users table]
    DB --> Payments[payments table]
    
    KB --> Inline[Inline Keyboards]
    
    style Bot fill:#32b8c6,stroke:#1d7480,color:#fff
    style Dispatcher fill:#5e407e,stroke:#3d2952,color:#fff
    style DB fill:#5e8040,stroke:#3d5229,color:#fff
    style Replicate fill:#ff8c42,stroke:#cc7035,color:#fff
    style YooKassa fill:#8b4789,stroke:#5c2e5a,color:#fff
```

## Архитектура по слоям

```mermaid
graph LR
    subgraph "Presentation Layer"
        A[Telegram UI]
        B[Inline Keyboards]
    end
    
    subgraph "Application Layer"
        C[Handlers]
        D[FSM States]
        E[Routers]
    end
    
    subgraph "Business Logic Layer"
        F[Creation Flow]
        G[Payment Flow]
        H[Navigation Utils]
    end
    
    subgraph "Data Access Layer"
        I[Database Class]
        J[Models SQL]
    end
    
    subgraph "External Services"
        K[Replicate API]
        L[YooKassa API]
    end
    
    subgraph "Data Storage"
        M[(SQLite DB)]
    end
    
    A --> C
    B --> C
    C --> D
    C --> E
    E --> F
    E --> G
    F --> H
    G --> H
    F --> I
    G --> I
    I --> J
    J --> M
    F --> K
    G --> L
    
    style A fill:#32b8c6,stroke:#1d7480,color:#fff
    style M fill:#5e8040,stroke:#3d5229,color:#fff
    style K fill:#ff8c42,stroke:#cc7035,color:#fff
    style L fill:#8b4789,stroke:#5c2e5a,color:#fff
```

## Структура проекта (дерево зависимостей)

```mermaid
graph TD
    Main[main.py] --> Config[config.py]
    Main --> DB[database/db.py]
    Main --> US[handlers/user_start.py]
    Main --> CR[handlers/creation.py]
    Main --> PM[handlers/payment.py]
    
    US --> States[states/fsm.py]
    CR --> States
    
    US --> KB[keyboards/inline.py]
    CR --> KB
    PM --> KB
    
    US --> Texts[utils/texts.py]
    CR --> Texts
    PM --> Texts
    
    CR --> RepAPI[services/replicate_api.py]
    PM --> PayAPI[services/payment_api.py]
    
    DB --> Models[database/models.py]
    
    RepAPI --> Config
    PayAPI --> Config
    
    DB --> Config
    
    style Main fill:#32b8c6,stroke:#1d7480,color:#fff
    style DB fill:#5e8040,stroke:#3d5229,color:#fff
    style RepAPI fill:#ff8c42,stroke:#cc7035,color:#fff
    style PayAPI fill:#8b4789,stroke:#5c2e5a,color:#fff
```

## Поток данных при генерации дизайна

```mermaid
sequenceDiagram
    actor User as 👤 Пользователь
    participant Bot as 🤖 Bot
    participant Handler as Creation Handler
    participant DB as 💾 Database
    participant FSM as 🔄 FSM State
    participant Replicate as 🎨 Replicate AI
    
    User->>Bot: /start
    Bot->>DB: create_user(user_id)
    DB-->>Bot: balance=3
    Bot->>User: Главное меню
    
    User->>Bot: [Создать дизайн]
    Bot->>FSM: set_state(waiting_for_photo)
    Bot->>User: Инструкция загрузки фото
    
    User->>Bot: 📸 Фото комнаты
    Handler->>DB: get_balance(user_id)
    DB-->>Handler: balance=3
    Handler->>FSM: save(photo_id), set_state(choose_room)
    Handler->>User: Выбор типа комнаты
    
    User->>Bot: [Гостиная]
    Handler->>DB: get_balance(user_id)
    DB-->>Handler: balance=3
    Handler->>FSM: save(room), set_state(choose_style)
    Handler->>User: Выбор стиля
    
    User->>Bot: [Скандинавский]
    Handler->>DB: get_balance(user_id)
    DB-->>Handler: balance=3
    Handler->>DB: decrease_balance(user_id)
    DB-->>Handler: success
    Handler->>User: ⏳ Генерирую...
    
    Handler->>Replicate: generate_image(photo, room, style)
    Replicate-->>Handler: image_url
    
    Handler->>User: ✨ Новый дизайн [фото]
    Handler->>FSM: clear_state()
    Handler->>User: Меню действий
```

## Поток данных при оплате

```mermaid
sequenceDiagram
    actor User as 👤 Пользователь
    participant Bot as 🤖 Bot
    participant Handler as Payment Handler
    participant DB as 💾 Database
    participant YK as 💰 YooKassa
    
    User->>Bot: [Купить генерации]
    Bot->>User: Выбор пакета
    
    User->>Bot: [25 генераций - 490₽]
    Handler->>YK: create_payment(490₽, 25 tokens)
    YK-->>Handler: payment_id, url
    Handler->>DB: save_payment(user_id, payment_id, pending)
    Handler->>User: Ссылка на оплату + кнопка проверки
    
    User->>YK: Переход по ссылке
    User->>YK: Оплата 490₽
    YK-->>User: Успешно
    
    User->>Bot: [Я оплатил! (Проверить)]
    Handler->>DB: get_last_pending_payment(user_id)
    DB-->>Handler: payment_id
    Handler->>YK: check_status(payment_id)
    YK-->>Handler: status=succeeded
    
    Handler->>DB: update_payment(succeeded)
    Handler->>DB: add_tokens(user_id, 25)
    DB-->>Handler: new_balance=25
    Handler->>User: ✅ Успешно! Баланс: 25
```

---

## Легенда

- 👤 **User** — Пользователь Telegram
- 🤖 **Bot** — Telegram Bot (aiogram)
- 🔄 **FSM** — Finite State Machine (машина состояний)
- 💾 **Database** — SQLite база данных
- 🎨 **Replicate** — AI сервис генерации изображений
- 💰 **YooKassa** — Платежный шлюз
