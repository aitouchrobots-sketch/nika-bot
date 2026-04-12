import os
import json
import logging
import csv
import io
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CommandHandler
from openai import OpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
#  ПРОГРАММА ЭКСПЕДИЦИИ (замени на реальную)
# ─────────────────────────────────────────────
CRUISE_PROGRAM = """
ЭКСПЕДИЦИЯ НА МАЧУ-ПИКЧУ | 8–17 апреля

📅 8 апреля (вторник) — ВЫЛЕТ
  - 06:00 Сбор в аэропорту Шереметьево, терминал D
  - 09:30 Вылет рейсом SU 150 Москва → Мадрид
  - 15:40 Пересадка в Мадриде (2 часа)
  - 17:50 Рейс IB 6825 Мадрид → Лима
  - 23:55 Прилёт в Лиму (местное время)
  - Заселение в отель Casa Andina Premium Miraflores ⭐⭐⭐⭐⭐

📅 9 апреля (среда) — ЛИМА: ЗНАКОМСТВО
  - 09:00 Завтрак в отеле, знакомство группы
  - 10:30 Обзорная экскурсия: исторический центр Лимы, Пласа Майор, Дворец правительства
  - 13:00 Бизнес-ланч в ресторане Maido (в топ-50 лучших ресторанов мира)
  - 15:00 Мастермайнд-сессия #1: "Как масштабироваться в Латинской Америке"
  - 18:00 Свободное время / кофе-брейки
  - 20:00 Вечерний нетворкинг-ужин у океана, Miraflores

📅 10 апреля (четверг) — ЛИМА → КУСКО
  - 07:00 Завтрак, выселение
  - 09:15 Перелёт Лима → Куско (1 час 25 мин)
  - 11:00 Адаптация к высоте (3400 м) — прогулка по Куско, кока-чай
  - 13:00 Обед в ресторане MAP Café (в стенах музея)
  - 15:00 Экскурсия: крепость Саксайуаман, храм Солнца Кориканча
  - 18:30 Мастермайнд-сессия #2: "Управление командой на расстоянии"
  - 20:30 Ужин в отеле Palacio del Inka ⭐⭐⭐⭐⭐

📅 11 апреля (пятница) — КУСКО: ПОГРУЖЕНИЕ
  - 08:00 Завтрак в отеле
  - 09:30 Мастермайнд-сессия #3: "Инвестиции и активы: где держать деньги в 2025"
  - 12:00 Свободное время: рынок Сан-Педро, шопинг, кофе-брейки
  - 14:00 Обед (по группам, свободно)
  - 16:00 Мастер-класс: перуанская кулинария и писко сауэр
  - 20:00 Гала-ужин: "Ночь перуанской кухни", живая музыка

📅 12 апреля (суббота) — СВЯЩЕННАЯ ДОЛИНА
  - 07:30 Завтрак, ранний выезд
  - 09:00 Экскурсия: Ольянтайтамбо — город-крепость инков
  - 12:00 Обед на ранчо с видом на горы
  - 14:00 Рынок мастеров Писак — текстиль, керамика, украшения
  - 17:00 Посадка на поезд Peru Rail в Агуас-Кальентес (2 часа)
  - 19:30 Заселение в Sumaq Machu Picchu Hotel ⭐⭐⭐⭐⭐
  - 21:00 Лёгкий ужин, ранний отбой (завтра подъём!)

📅 13 апреля (воскресенье) — ДЕНЬ МАЧУ-ПИКЧУ ⭐
  - 05:00 Подъём, лёгкий завтрак
  - 05:30 Автобус на вершину (30 мин)
  - 06:00 Встреча рассвета над Мачу-Пикчу 🌅
  - 06:30–10:00 Гид-экскурсия по цитадели: Храм Солнца, Интиуатана, Жилой квартал
  - 10:30 Свободное время для фото и осмотра
  - 13:00 Обед в отеле
  - 15:00 Мастермайнд-сессия #4: "Жизнь и бизнес на новом уровне" (у подножия горы)
  - 19:00 Праздничный ужин: отмечаем главный день экспедиции 🥂

📅 14 апреля (понедельник) — ВОЗВРАЩЕНИЕ В КУСКО
  - 08:00 Завтрак
  - 09:30 Поезд Агуас-Кальентес → Ольянтайтамбо → Куско
  - 14:00 Свободный день в Куско: шопинг, галереи, спа
  - 16:00 Факультатив: шоколадный мастер-класс (какао инков)
  - 19:00 Прощальный нетворкинг-ужин в Куско

📅 15 апреля (вторник) — КУСКО → ЛИМА → ВЫЛЕТ
  - 07:00 Завтрак, выселение
  - 09:00 Трансфер в аэропорт
  - 11:20 Рейс Куско → Лима
  - 13:00 Пересадка в Лиме (3 часа, VIP-зал)
  - 16:10 Рейс Лима → Мадрид (overnight)

📅 16 апреля (среда) — В ПУТИ
  - Перелёт Лима → Мадрид (ночной)
  - 11:40 Прилёт в Мадрид, пересадка
  - 14:30 Рейс Мадрид → Москва

📅 17 апреля (четверг) — ПРИЛЁТ
  - 20:15 Прилёт в Шереметьево
  - Трансфер по городу включён

---
ВАЖНАЯ ИНФОРМАЦИЯ:
- Все переезды, завтраки и ужины включены в программу
- Обеды в свободные дни — за свой счёт
- Дресс-код на гала-ужин: smart casual
- Высота Куско 3400 м, Мачу-Пикчу 2430 м — первые дни возможна горная болезнь
- Рекомендуется таблетки от высоты (диакарб/ацетазоламид) — проконсультируйтесь с врачом
- Организатор экспедиции: Руслан (все срочные вопросы — лично ему)
"""

# ─────────────────────────────────────────────
#  ЗАГРУЗКА УЧАСТНИКОВ
# ─────────────────────────────────────────────
def load_participants_from_csv(filepath: str) -> list[dict]:
    participants = []
    with open(filepath, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            participants.append(dict(row))
    return participants

def load_participants() -> list[dict]:
    """Загружает участников из CSV. Пока файла нет — фейковые данные."""
    csv_path = "participants.csv"
    if os.path.exists(csv_path):
        try:
            return load_participants_from_csv(csv_path)
        except Exception as e:
            logger.warning(f"Не удалось загрузить CSV: {e}")
    
    # Если CSV не найден — пустой список (не должно случиться)
    return []

# ─────────────────────────────────────────────
#  ПОСТРОЕНИЕ СИСТЕМНОГО ПРОМПТА
# ─────────────────────────────────────────────
def build_system_prompt() -> str:
    participants = load_participants()
    if participants:
        participants_text = "\n".join([
            f"- {p.get('Имя', p.get('name', '?'))} | Ниша: {p.get('Ниша', p.get('expertise', ''))} | Польза: {p.get('Чем может быть полезен/полезна', p.get('interests', ''))} | Цель: {p.get('Цель участия', '')} | TG: {p.get('Telegram', '')}"
            for p in participants
        ])
    else:
        participants_text = HARDCODED_PARTICIPANTS
    
    return f"""Ты — Ника, умный ИИ-помощник экспедиции предпринимателей на Мачу-Пикчу (8–17 апреля).
Ты находишься в общем Telegram-чате участников группы.

ТВОЙ ХАРАКТЕР:
- Тёплая, дружелюбная, с лёгким юмором
- Говоришь по-русски, иногда вставляешь перуанские словечки (amigos, hola)
- Конкретная: даёшь точные ответы без воды
- Энергичная: заряжаешь на нетворкинг

ТВОИ ФУНКЦИИ:

1. ПРОГРАММА ЭКСПЕДИЦИИ
Ты знаешь точную программу по дням. Отвечай на вопросы о расписании, локациях, логистике.
Примеры: "куда едем завтра?", "что в программе на 13 апреля?", "когда завтрак?", "когда вылет?"

2. КОФЕ-БРЕЙК / МАТЧИНГ УЧАСТНИКОВ
Если участник пишет что хочет познакомиться, найти собеседника, сделать кофе-брейк — предложи назвать себя.
Когда участник называет своё имя/фамилию — найди его в списке, проанализируй компетенции ВСЕХ участников и предложи 1-2 конкретных человека для разговора с объяснением ПОЧЕМУ они совпадают (по темам, синергии, взаимной пользе). Укажи имя, компанию, тему для разговора.

СПИСОК УЧАСТНИКОВ:
{participants_text}

ПРОГРАММА ЭКСПЕДИЦИИ:
{CRUISE_PROGRAM}

ВАЖНО:
- Ты отвечаешь ТОЛЬКО на вопросы связанные с программой, участниками, логистикой экспедиции и нетворкингом
- На посторонние темы мягко отказывай: "Это вне моей экспедиционной компетенции 😄 Спроси меня о программе или участниках!"
- Отвечай кратко и по делу. Используй эмодзи умеренно.
- В групповом чате — отвечай только когда к тебе обращаются (упоминают "Ника" или "Ника,")
"""

# ─────────────────────────────────────────────
#  ХРАНЕНИЕ ИСТОРИИ ДИАЛОГОВ
# ─────────────────────────────────────────────
chat_histories: dict[int, list[dict]] = {}

def get_history(chat_id: int) -> list[dict]:
    return chat_histories.get(chat_id, [])

def add_to_history(chat_id: int, role: str, content: str):
    if chat_id not in chat_histories:
        chat_histories[chat_id] = []
    chat_histories[chat_id].append({"role": role, "content": content})
    # Храним последние 20 сообщений
    if len(chat_histories[chat_id]) > 20:
        chat_histories[chat_id] = chat_histories[chat_id][-20:]

# ─────────────────────────────────────────────
#  ЗАПРОС К CLAUDE AI
# ─────────────────────────────────────────────
def ask_claude(chat_id: int, user_message: str) -> str:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    
    add_to_history(chat_id, "user", user_message)
    
    messages = [{"role": "system", "content": build_system_prompt()}] + get_history(chat_id)
    
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=1024,
        messages=messages
    )
    
    reply = response.choices[0].message.content
    add_to_history(chat_id, "assistant", reply)
    return reply

# ─────────────────────────────────────────────
#  ОБРАБОТЧИКИ TELEGRAM
# ─────────────────────────────────────────────
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return
    
    chat_id = message.chat_id
    text = message.text
    chat_type = message.chat.type  # 'private', 'group', 'supergroup'
    
    should_respond = False
    
    if chat_type == "private":
        # В личке — всегда отвечаем
        should_respond = True
    else:
        # В группе — только если упомянули Нику
        nika_triggers = ["ника", "nika", "@" + (context.bot.username or "").lower()]
        text_lower = text.lower()
        if any(trigger in text_lower for trigger in nika_triggers):
            should_respond = True
    
    if not should_respond:
        return
    
    # Убираем обращение "Ника," из текста
    clean_text = text
    for trigger in ["Ника, ", "Ника,", "Ника ", "ника, ", "ника,", "ника "]:
        clean_text = clean_text.replace(trigger, "").strip()
    if not clean_text:
        clean_text = text
    
    # Добавляем имя отправителя в контекст
    sender_name = ""
    if message.from_user:
        sender_name = message.from_user.first_name or ""
        if message.from_user.last_name:
            sender_name += f" {message.from_user.last_name}"
    
    full_message = f"[Пишет: {sender_name}] {clean_text}" if sender_name else clean_text
    
    try:
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        reply = ask_claude(chat_id, full_message)
        await message.reply_text(reply)
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await message.reply_text("Ой, что-то пошло не так 😅 Попробуй ещё раз!")

async def handle_csv_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Принимает CSV с участниками от администратора."""
    message = update.message
    if not message or not message.document:
        return
    
    doc = message.document
    if not (doc.file_name.endswith('.csv') or doc.file_name.endswith('.xlsx')):
        return
    
    try:
        file = await context.bot.get_file(doc.file_id)
        file_bytes = await file.download_as_bytearray()
        
        # Сохраняем как CSV
        with open("participants.csv", "wb") as f:
            f.write(file_bytes)
        
        # Проверяем загрузку
        participants = load_participants()
        await message.reply_text(
            f"✅ Список участников обновлён! Загружено {len(participants)} человек.\n"
            f"Ника теперь знает всех amigos! 🎉"
        )
        # Сбрасываем историю чтобы контекст обновился
        chat_histories.clear()
    except Exception as e:
        await message.reply_text(f"❌ Ошибка загрузки файла: {e}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Hola! Я Ника — ваш ИИ-гид по экспедиции на Мачу-Пикчу 🏔️\n\n"
        "Я знаю:\n"
        "📅 Программу по дням\n"
        "👥 Всех участников экспедиции\n"
        "☕ Помогу найти собеседника для кофе-брейка\n\n"
        "В групповом чате обращайтесь: *Ника, [вопрос]*\n"
        "В личке — просто пишите!",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Что я умею:*\n\n"
        "• *Программа:* «Ника, что завтра?» / «Ника, программа на 13 апреля»\n"
        "• *Логистика:* «Ника, когда вылет?» / «Ника, какой отель в Куско?»\n"
        "• *Нетворкинг:* «Ника, хочу познакомиться» → назови себя → получи match!\n"
        "• *Участники:* «Ника, кто едет?» / «Ника, расскажи об участниках»\n\n"
        "📎 Для обновления списка участников — отправь CSV-файл в чат.",
        parse_mode="Markdown"
    )

# ─────────────────────────────────────────────
#  ЗАПУСК БОТА
# ─────────────────────────────────────────────
def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("Не задан TELEGRAM_BOT_TOKEN в переменных окружения!")
    
    
    app = Application.builder().token(token).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_csv_upload))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("🚀 Ника запущена!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
