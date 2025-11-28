# InteriorBot v1 — FSM Состояния

## Граф состояний процесса создания дизайна

```mermaid
stateDiagram-v2
    [*] --> NO_STATE: /start или main_menu
    
    NO_STATE --> waiting_for_photo: 🎨 Создать дизайн
    
    waiting_for_photo --> choose_room: 📸 Фото получено<br/>(balance > 0)
    waiting_for_photo --> NO_STATE: balance = 0<br/>(меню оплаты)
    waiting_for_photo --> waiting_for_photo: Альбом фото<br/>(предупреждение)
    
    choose_room --> choose_style: Выбрана комната<br/>(balance > 0)
    choose_room --> NO_STATE: balance = 0<br/>(меню оплаты)
    
    choose_style --> choose_room: ⬅️ К выбору комнаты
    choose_style --> GENERATION: Выбран стиль<br/>(balance > 0)
    choose_style --> NO_STATE: balance = 0<br/>(меню оплаты)
    
    GENERATION --> NO_STATE: Генерация завершена<br/>(state.clear)
    
    NO_STATE --> choose_style: 🔄 Другой стиль<br/>(сохранённые photo+room)
    
    waiting_for_photo --> NO_STATE: 🏠 Главное меню
    choose_room --> NO_STATE: 🏠 Главное меню
    choose_style --> NO_STATE: 🏠 Главное меню
    
    note right of NO_STATE
        Главное меню,
        Профиль,
        Результат генерации
    end note
    
    note right of GENERATION
        Процесс, не состояние:
        1. Списание баланса
        2. Replicate API
        3. Показ результата
    end note
```

## Детальные переходы состояний

```mermaid
flowchart TD
    Start([/start]) --> CheckUser{Пользователь<br/>существует?}
    CheckUser -->|NO| CreateUser[create_user<br/>balance=3]
    CheckUser -->|YES| MainMenu
    CreateUser --> MainMenu[NO STATE<br/>🏠 Главное меню]
    
    MainMenu -->|[🎨 Создать дизайн]| WaitPhoto[waiting_for_photo<br/>📸 Ожидание фото]
    MainMenu -->|[👤 Профиль]| Profile[NO STATE<br/>👤 Профиль]
    
    WaitPhoto -->|📸 Фото| CheckBalance1{Баланс > 0?}
    CheckBalance1 -->|YES| SavePhoto[save photo_id]
    CheckBalance1 -->|NO| Payment[Меню оплаты]
    SavePhoto --> ChooseRoom[choose_room<br/>🛋️ Выбор комнаты]
    
    ChooseRoom -->|[Гостиная/Спальня/...]| CheckBalance2{Баланс > 0?}
    CheckBalance2 -->|YES| SaveRoom[save room]
    CheckBalance2 -->|NO| Payment
    SaveRoom --> ChooseStyle[choose_style<br/>🎨 Выбор стиля]
    
    ChooseStyle -->|[⬅️ К выбору комнаты]| ChooseRoom
    ChooseStyle -->|[Современный/...]| CheckBalance3{Баланс > 0?}
    CheckBalance3 -->|YES| Decrease[decrease_balance]
    CheckBalance3 -->|NO| Payment
    
    Decrease --> Generate[⏳ Генерация<br/>Replicate API]
    Generate --> ShowResult[✨ Показ результата]
    ShowResult --> ClearState[state.clear]
    ClearState --> Result[NO STATE<br/>🏞️ Результат]
    
    Result -->|[🔄 Другой стиль]| ChooseStyle
    Result -->|[📸 Новое фото]| WaitPhoto
    Result -->|[🏠 Главное меню]| MainMenu
    
    Payment --> MainMenu
    Profile --> MainMenu
    
    WaitPhoto -->|[🏠 Главное меню]| MainMenu
    ChooseRoom -->|[🏠 Главное меню]| MainMenu
    ChooseStyle -->|[🏠 Главное меню]| MainMenu
    
    style MainMenu fill:#32b8c6,stroke:#1d7480,color:#fff
    style WaitPhoto fill:#ff8c42,stroke:#cc7035,color:#fff
    style ChooseRoom fill:#ff8c42,stroke:#cc7035,color:#fff
    style ChooseStyle fill:#ff8c42,stroke:#cc7035,color:#fff
    style Generate fill:#8b4789,stroke:#5c2e5a,color:#fff
    style Result fill:#5e8040,stroke:#3d5229,color:#fff
```

## Данные в state.data

```mermaid
graph LR
    subgraph "state.data"
        A[menu_message_id]
        B[photo_id]
        C[room]
        D[media_group_id]
    end
    
    subgraph "Жизненный цикл"
        E["/start"] --> A
        F["📸 Фото"] --> B
        G["🛋️ Комната"] --> C
        H["🖼️ Альбом"] --> D
    end
    
    A -.->|persist| I["Сохраняется всегда"]
    B -.->|clear| J["Очищается при новой генерации"]
    C -.->|clear| J
    D -.->|temp| K["Временно при обработке альбома"]
    
    style A fill:#32b8c6,stroke:#1d7480,color:#fff
    style B fill:#ff8c42,stroke:#cc7035,color:#fff
    style C fill:#ff8c42,stroke:#cc7035,color:#fff
    style D fill:#8b4789,stroke:#5c2e5a,color:#fff
```

## Проверка баланса (многоуровневая)

```mermaid
flowchart TD
    A[Пользователь отправляет фото] --> B{Админ?}
    B -->|YES| C[Пропустить проверку]
    B -->|NO| D{Баланс > 0?}
    
    D -->|NO| E[Меню оплаты]
    D -->|YES| F[Сохранить photo_id]
    
    C --> F
    F --> G[Пользователь выбирает комнату]
    
    G --> H{Админ?}
    H -->|YES| I[Пропустить проверку]
    H -->|NO| J{Баланс > 0?}
    
    J -->|NO| E
    J -->|YES| K[Сохранить room]
    
    I --> K
    K --> L[Пользователь выбирает стиль]
    
    L --> M{Админ?}
    M -->|YES| N[Не списывать баланс]
    M -->|NO| O{Баланс > 0?}
    
    O -->|NO| E
    O -->|YES| P[decrease_balance]
    
    N --> Q[Генерация]
    P --> Q
    
    E --> R[Очистка состояния]
    Q --> S[Результат]
    
    style E fill:#c0152f,stroke:#801020,color:#fff
    style Q fill:#5e8040,stroke:#3d5229,color:#fff
    style S fill:#32b8c6,stroke:#1d7480,color:#fff
```

---

## Резюме

**InteriorBot v1** использует:

- **3 основных состояния:** waiting_for_photo, choose_room, choose_style
- **1 базовое состояние:** NO_STATE (главное меню, профиль, результат)
- **Многоуровневую проверку баланса** на каждом шаге
- **Защиту от ошибок:** альбомы фото, нулевой баланс
- **Гибкую навигацию:** возврат на любой этап, главное меню доступно всегда
