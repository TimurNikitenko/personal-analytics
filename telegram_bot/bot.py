import os
import time
import random
import requests
import io
from PIL import Image
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from apscheduler.schedulers.background import BackgroundScheduler

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
REMINDER_HOUR = int(os.getenv("REMINDER_HOUR", "22")) # Default to 9:00 PM (21:00)
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

# Local in-memory store for registered Chat ID
chat_id_store = CHAT_ID
sessions = {}

PREDEFINED_SUPPLEMENTS = [
    {"name": "Vitamin D3", "dosage": 2000, "unit": "UI"},
    {"name": "Omega 3", "dosage": 600, "unit": "mg"},
    {"name": "Creatine", "dosage": 5, "unit": "g"},
    {"name": "Glycine", "dosage": 3, "unit": "g"},
    {"name": "L-theanine", "dosage": 200, "unit": "mg"},
    {"name": "multivitamins", "dosage": 1, "unit": "pills"},
]

def register_chat_id_on_backend(chat_id):
    """
    Persists the dynamically registered Chat ID to the database via backend.
    """
    try:
        url = f"{BACKEND_URL}/api/telegram/register-chat-id"
        r = requests.post(url, params={"chat_id": str(chat_id)}, timeout=5.0)
        r.raise_for_status()
        print(f"Successfully registered Chat ID {chat_id} on the backend database settings.")
    except Exception as e:
        print(f"Failed to register Chat ID {chat_id} on backend database settings: {e}")

def get_chat_id_from_backend():
    """
    Retrieves the active Chat ID from the database via backend.
    """
    try:
        url = f"{BACKEND_URL}/api/telegram/chat-id"
        r = requests.get(url, timeout=5.0)
        if r.status_code == 200:
            return r.json().get("chat_id")
    except Exception as e:
        print(f"Failed to fetch Chat ID from backend database settings: {e}")
    return None

def send_msg(chat_id, text, reply_markup=None):
    """
    Sends a Markdown message to a Telegram chat.
    """
    if not BOT_TOKEN:
        return None
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        r = requests.post(url, json=payload, timeout=10.0)
        return r.json()
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
        return None

def edit_msg(chat_id, message_id, text, reply_markup=None):
    """
    Edits the text of a previously sent Telegram message.
    """
    if not BOT_TOKEN:
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText"
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        requests.post(url, json=payload, timeout=10.0)
    except Exception as e:
        print(f"Error editing Telegram message: {e}")

def answer_callback(callback_query_id, text=None):
    """
    Acknowledges a CallbackQuery to clear the loading spinner in client.
    """
    if not BOT_TOKEN:
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery"
    payload = {"callback_query_id": callback_query_id}
    if text:
        payload["text"] = text
    try:
        requests.post(url, json=payload, timeout=5.0)
    except Exception as e:
        print(f"Error answering callback query: {e}")

MOTIVATIONAL_QUOTES = [
    "Тот, кто умеет управлять каждым днем, умеет управлять своей жизнью.",
    "Постоянство превосходит интенсивность. Пора записать итоги сегодняшнего дня!",
    "Если вы не измеряете это, вы не можете это улучшить. Уделите пару минут логам.",
    "Каждый шаг вперед приближает вас к цели. Запишите свои показатели за сегодня!",
    "Маленькие ежедневные шаги ведут к большим результатам. Давайте заполним лог!",
    "Анализ прошлого дня — компас для дня завтрашнего. Пора залогировать день.",
    "Ваша жизнь складывается из ваших привычек. Оцифруйте сегодняшний день!",
    "Дисциплина — это мост между целями и достижениями. Жду ваш лог за сегодня.",
    "Узнайте себя лучше через данные. Давайте заполним отчет.",
    "То, что мы делаем каждый день, определяет то, кем мы станем. Сделайте запись в лог!",
    "Запись сегодняшних побед и уроков — залог продуктивного завтра.",
    "Не откладывайте на завтра то, что можно залогировать сегодня!"
]

def send_reminder():
    """
    Background cron job to send daily logs reminder.
    """
    chat_id = get_chat_id_from_backend() or chat_id_store
    if not BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN not configured. Skipping reminder.")
        return
    if not chat_id:
        print("TELEGRAM_CHAT_ID not set. Please send /start to your Telegram bot to register.")
        return
        
    quote = random.choice(MOTIVATIONAL_QUOTES)
    text = (
        f"🔔 **Время заполнить отчет за сегодня!**\n\n"
        f"💬 *«{quote}»*\n\n"
        f"Отправьте `/log` или перейдите в веб-приложение. 📊"
    )
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        r = requests.post(url, json=payload, timeout=10.0)
        r.raise_for_status()
        print(f"[{datetime.now()}] Daily reminder sent successfully to chat ID: {chat_id}")
    except Exception as e:
        print(f"[{datetime.now()}] Error sending daily reminder: {e}")

def send_morning_sleep_survey():
    """
    Background cron job to send morning sleep quality survey.
    """
    chat_id = get_chat_id_from_backend() or chat_id_store
    if not BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN not configured. Skipping sleep survey.")
        return
    if not chat_id:
        print("TELEGRAM_CHAT_ID not set. Please send /start to your Telegram bot to register.")
        return
        
    text = "🌅 **Доброе утро!**\n\nКак вы оцените качество своего сна по шкале от 1 до 10?"
    markup = {
        "inline_keyboard": [
            [{"text": str(i), "callback_data": f"sleepq_{i}"} for i in range(1, 6)],
            [{"text": str(i), "callback_data": f"sleepq_{i}"} for i in range(6, 11)],
            [{"text": "Пропустить ➡️", "callback_data": "sleepq_skip"}]
        ]
    }
    
    try:
        send_msg(chat_id, text, reply_markup=markup)
        print(f"[{datetime.now()}] Morning sleep quality survey sent successfully to chat ID: {chat_id}")
    except Exception as e:
        print(f"[{datetime.now()}] Error sending morning sleep survey: {e}")

# ==================== Meals Logging & Media Helpers ====================

MEAL_PRESETS = {
    "Breakfast": [
        {"product_name": "Овсяные хлопья", "quantity": 150.0, "unit": "грамм"},
        {"product_name": "Банан", "quantity": 1.0, "unit": "штука"},
        {"product_name": "Какао порошок", "quantity": 1.0, "unit": "столовая ложка"}
    ],
    "Lunch": [
        {"product_name": "Чечевица (красная)", "quantity": 150.0, "unit": "грамм"},
        {"product_name": "Оливковое масло холодного отжима", "quantity": 2.0, "unit": "столовая ложка"},
        {"product_name": "Помидоры", "quantity": 2.0, "unit": "штука"}
    ],
    "Dinner": [
        {"product_name": "Гречка", "quantity": 150.0, "unit": "грамм"},
        {"product_name": "Сардины консервированные", "quantity": 125.0, "unit": "грамм"},
        {"product_name": "Квашенная капуста", "quantity": 100.0, "unit": "грамм"}
    ]
}

def save_compressed_image(file_bytes, target_path):
    """
    Saves image bytes as compressed JPEG to target_path to save space.
    """
    try:
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        img = Image.open(io.BytesIO(file_bytes))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(target_path, "JPEG", quality=75, optimize=True)
        print(f"Compressed image saved: {target_path}")
        return True
    except Exception as e:
        print(f"Failed to compress with Pillow: {e}. Saving raw.")
        try:
            with open(target_path, "wb") as f:
                f.write(file_bytes)
            return True
        except Exception as write_err:
            print(f"Failed to save raw: {write_err}")
            return False

def download_telegram_file(file_id, dest_path):
    """
    Downloads file from Telegram by file_id and writes to dest_path.
    """
    if not BOT_TOKEN:
        return False
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}"
        r = requests.get(url, timeout=10.0)
        r.raise_for_status()
        file_path = r.json().get("result", {}).get("file_path")
        if not file_path:
            return False
        download_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
        file_r = requests.get(download_url, timeout=30.0)
        file_r.raise_for_status()
        
        is_image = file_path.lower().endswith((".jpg", ".jpeg", ".png"))
        if is_image:
            return save_compressed_image(file_r.content, dest_path)
        else:
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            with open(dest_path, "wb") as f:
                f.write(file_r.content)
            return True
    except Exception as e:
        print(f"Error downloading Telegram file {file_id}: {e}")
        return False

def send_breakfast_survey():
    send_meal_survey("Breakfast")

def send_lunch_survey():
    send_meal_survey("Lunch")

def send_dinner_survey():
    send_meal_survey("Dinner")

def send_meal_survey(meal_type):
    chat_id = chat_id_store or get_chat_id_from_backend()
    if not BOT_TOKEN:
        return
    if not chat_id:
        print(f"Skipping {meal_type} survey: chat_id not set.")
        return
        
    sessions.pop(chat_id, None)  # Reset any active logging session
    
    meal_names_ru = {"Breakfast": "завтрак", "Lunch": "обед", "Dinner": "ужин"}
    ru_name = meal_names_ru.get(meal_type, "прием пищи")
    
    text = f"🍽️ **Время логгировать {ru_name}!**\n\nВыберите вариант:"
    markup = {
        "inline_keyboard": [
            [{"text": "🥗 Стандартный пресет", "callback_data": f"meal_preset_{meal_type}"}],
            [{"text": "✍️ Вручную по продуктам", "callback_data": f"meal_manual_{meal_type}"}],
            [{"text": "📷 Отправить фото", "callback_data": f"meal_photo_ask_{meal_type}"}],
            [{"text": "Пропустить ➡️", "callback_data": f"meal_skip_{meal_type}"}]
        ]
    }
    send_msg(chat_id, text, reply_markup=markup)

def send_meal_product_selector(chat_id, message_id=None):
    session = sessions.get(chat_id)
    if not session:
        return
        
    meal_names_ru = {"Breakfast": "завтрак", "Lunch": "обед", "Dinner": "ужин"}
    ru_name = meal_names_ru.get(session["meal_type"], "прием пищи")
    
    text = f"🍽️ **Логгирование: {ru_name.capitalize()}**\n\n"
    if session["items"]:
        text += "**Уже добавлено:**\n"
        for it in session["items"]:
            text += f"- {it['product_name']} — {it['quantity']} {it['unit']}\n"
        text += "\n"
    else:
        text += "*(Пока нет добавленных продуктов)*\n\n"
        
    text += "Выберите продукт из списка или добавьте новый:"
    
    try:
        r = requests.get(f"{BACKEND_URL}/api/meals/food-products", timeout=5.0)
        products = r.json()
    except Exception as e:
        print(f"Error fetching food products: {e}")
        products = []
        
    keyboard = []
    for p in products[:15]:
        keyboard.append([{"text": f"{p['name']} ({p['default_unit']})", "callback_data": f"mealprod_sel_{p['id']}"}])
        
    keyboard.append([{"text": "➕ Добавить новый продукт", "callback_data": "mealprod_addnew"}])
    if session["items"]:
        keyboard.append([{"text": "💾 Сохранить и завершить", "callback_data": "mealprod_done"}])
    keyboard.append([{"text": "❌ Отмена", "callback_data": "mealprod_cancel"}])
    
    markup = {"inline_keyboard": keyboard}
    if message_id:
        edit_msg(chat_id, message_id, text, reply_markup=markup)
    else:
        send_msg(chat_id, text, reply_markup=markup)

def parse_quantity_input(text):
    text = text.strip()
    parts = text.split(None, 1)
    if not parts:
        return None, None
    try:
        qty = float(parts[0].replace(",", "."))
    except ValueError:
        return None, None
    unit = parts[1].strip() if len(parts) > 1 else None
    return qty, unit


def fetch_daily_logs():
    """
    Fetches all daily logs from the backend.
    """
    try:
        url = f"{BACKEND_URL}/api/daily-logs/"
        r = requests.get(url, timeout=10.0)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"Failed to fetch daily logs for bot statistics: {e}")
    return None

def calculate_streaks(logs):
    """
    Calculates current and longest streaks based on daily logs date field.
    """
    if not logs:
        return 0, 0
        
    # Extract unique log dates, parse to date objects, and sort descending
    dates = sorted({datetime.strptime(log["date"], "%Y-%m-%d").date() for log in logs}, reverse=True)
    if not dates:
        return 0, 0
        
    today = datetime.now(ZoneInfo("Europe/Moscow")).date()
    
    # Check if the user logged today or yesterday. If not, current streak is 0.
    if dates[0] != today and dates[0] != today - timedelta(days=1):
        current_streak = 0
    else:
        current_streak = 1
        for i in range(len(dates) - 1):
            diff = dates[i] - dates[i+1]
            if diff == timedelta(days=1):
                current_streak += 1
            elif diff > timedelta(days=1):
                break
                
    # Longest streak calculation
    dates_asc = sorted(dates)
    longest_streak = 0
    temp_streak = 0
    prev_date = None
    for d in dates_asc:
        if prev_date is None:
            temp_streak = 1
        elif d - prev_date == timedelta(days=1):
            temp_streak += 1
        elif d - prev_date > timedelta(days=1):
            longest_streak = max(longest_streak, temp_streak)
            temp_streak = 1
        prev_date = d
    longest_streak = max(longest_streak, temp_streak)
    
    return current_streak, longest_streak

def get_streak_emoji(streak):
    """
    Returns an emoji corresponding to the streak length.
    """
    if streak >= 30:
        return "👑"
    elif streak >= 7:
        return "🔥"
    elif streak > 0:
        return "⚡"
    return "💤"

def get_stats_message():
    """
    Builds a detailed summary statistics message in Russian from backend daily logs.
    """
    logs = fetch_daily_logs()
    if not logs:
        return "📊 **Статистика логов**\n\nНет данных для вывода статистики. Начните заполнять логи с помощью команды `/log`!"
        
    total_logs = len(logs)
    current_streak, longest_streak = calculate_streaks(logs)
    
    today = datetime.now(ZoneInfo("Europe/Moscow")).date()
    last_7_days = {today - timedelta(days=i) for i in range(7)}
    last_30_days = {today - timedelta(days=i) for i in range(30)}
    
    logs_last_7 = 0
    logs_last_30 = 0
    mood_scores = []
    sleep_qualities = []
    steps_counts = []
    
    for log in logs:
        log_date = datetime.strptime(log["date"], "%Y-%m-%d").date()
        if log_date in last_7_days:
            logs_last_7 += 1
        if log_date in last_30_days:
            logs_last_30 += 1
            
        if log.get("mood_score") is not None:
            mood_scores.append(log["mood_score"])
        if log.get("sleep_quality") is not None:
            sleep_qualities.append(log["sleep_quality"])
        if log.get("steps") is not None:
            steps_counts.append(log["steps"])
            
    rate_7 = (logs_last_7 / 7) * 100
    rate_30 = (logs_last_30 / 30) * 100
    
    avg_mood = sum(mood_scores) / len(mood_scores) if mood_scores else None
    avg_sleep = sum(sleep_qualities) / len(sleep_qualities) if sleep_qualities else None
    avg_steps = sum(steps_counts) / len(steps_counts) if steps_counts else None
    
    msg = (
        f"📊 **Подробная статистика отчетов**\n\n"
        f"📈 **Заполняемость:**\n"
        f"- Всего отчетов: `{total_logs}`\n"
        f"- За последние 7 дней: `{logs_last_7}/7` ({rate_7:.0f}%)\n"
        f"- За последние 30 дней: `{logs_last_30}/30` ({rate_30:.0f}%)\n\n"
        f"🔥 **Серии заполнений (Streaks):**\n"
        f"- Текущая серия: `{current_streak}` {get_streak_emoji(current_streak)}\n"
        f"- Рекордная серия: `{longest_streak}` 🏆\n\n"
        f"🧠 **Средние показатели (за все время):**\n"
    )
    if avg_mood is not None:
        msg += f"- Настроение: `{avg_mood:.1f}/10`\n"
    if avg_sleep is not None:
        msg += f"- Качество сна: `{avg_sleep:.1f}/10`\n"
    if avg_steps is not None:
        msg += f"- Шаги: `{int(avg_steps):,}`\n"
        
    return msg

def send_supplements_checklist(chat_id, message_id=None):
    """
    Renders/updates the supplement selection list using an inline keyboard checklist.
    """
    session = sessions[chat_id]
    selected_indices = session["supplements_selected"]
    custom_supps = session["custom_supplements"]
    supp_dosages = session.setdefault("supplements_dosages", {})
    
    text = "💊 **Step 18/18: Supplements**\nSelect the supplements you took today. Click a supplement to toggle it. Custom supplements can be added below. Click **Done** when finished."
    if selected_indices or custom_supps:
        text += "\n\n**Selected Supplements:**"
        for idx in selected_indices:
            s = PREDEFINED_SUPPLEMENTS[idx]
            dosage = supp_dosages.get(idx, s["dosage"])
            text += f"\n- ✅ {s['name']} ({dosage} {s['unit']})"
        for cs in custom_supps:
            text += f"\n- ✅ {cs['name']} ({cs['dosage']} {cs['unit']})"
    else:
        text += "\n\n*(No supplements selected)*"
        
    keyboard = []
    for idx, s in enumerate(PREDEFINED_SUPPLEMENTS):
        checkmark = "✅" if idx in selected_indices else "⬜"
        dosage = supp_dosages.get(idx, s["dosage"])
        keyboard.append([{"text": f"{checkmark} {s['name']} ({dosage} {s['unit']})", "callback_data": f"supp_toggle_{idx}"}])
        
    keyboard.append([{"text": "➕ Add Custom Supplement", "callback_data": "supp_custom"}])
    keyboard.append([
        {"text": "Skip ➡️", "callback_data": "supp_skip"},
        {"text": "Done 💾", "callback_data": "supp_done"}
    ])
    
    markup = {"inline_keyboard": keyboard}
    
    if message_id:
        edit_msg(chat_id, message_id, text, reply_markup=markup)
        session["checklist_message_id"] = message_id
    else:
        res = send_msg(chat_id, text, reply_markup=markup)
        if res and res.get("ok"):
            session["checklist_message_id"] = res["result"]["message_id"]

def ask_next_question(chat_id):
    """
    Guides the user to the next appropriate questionnaire step.
    """
    session = sessions.get(chat_id)
    if not session:
        return
        
    current_step = session["current_step"]
    
    # Auto-skips based on previous questions
    if current_step == "workout_type":
        workout_mins = session["data"].get("workout_minutes")
        if workout_mins is None or workout_mins <= 0:
            session["current_step"] = "exercise_snacks_count"
            ask_next_question(chat_id)
            return

    elif current_step == "sleep_start":
        sleep_ask = session["data"].get("sleep_window_ask")
        if sleep_ask != "yes":
            session["current_step"] = "water_cups"
            ask_next_question(chat_id)
            return

    elif current_step == "sleep_end":
        if session["data"].get("sleep_start_time") is None:
            session["current_step"] = "water_cups"
            ask_next_question(chat_id)
            return

    elif current_step == "coffee_type":
        coffee_cups = session["data"].get("coffee_cups")
        if coffee_cups is None or coffee_cups <= 0:
            session["current_step"] = "fruits_servings"
            ask_next_question(chat_id)
            return

    if current_step == "done":
        submit_log_session(chat_id)
        return

    step = current_step
    if step == "date":
        markup = {
            "inline_keyboard": [
                [
                    {"text": "Today 📅", "callback_data": "date_today"},
                    {"text": "Yesterday 📅", "callback_data": "date_yesterday"}
                ]
            ]
        }
        send_msg(chat_id, "📅 **Step 1/18: Date Selection**\nWhich date would you like to log?\nSend `/today` for today, or type a date in `YYYY-MM-DD` format (e.g. `2026-05-28`).\nSend `/cancel` to abort.", reply_markup=markup)

    elif step == "mood_score":
        markup = {
            "inline_keyboard": [
                [{"text": str(i), "callback_data": f"mood_{i}"} for i in range(1, 6)],
                [{"text": str(i), "callback_data": f"mood_{i}"} for i in range(6, 11)],
                [{"text": "Skip ➡️", "callback_data": "skip"}]
            ]
        }
        send_msg(chat_id, "🧠 **Step 2/18: Subjective Mood**\nHow was your subjective experience of the day on a scale of 1 to 10?\nSend `/skip` to skip, or `/cancel` to abort.", reply_markup=markup)

    elif step == "diary_text":
        send_msg(chat_id, "✍️ **Step 3/18: Diary Entry / Notes**\nEnter a free-form diary entry or notes about your day.\nSend `/skip` to skip, or `/cancel` to abort.")

    elif step == "work_hours":
        send_msg(chat_id, "💼 **Step 4/18: Work Hours**\nHow many hours did you work today?\nSend `/skip` to skip, or `/cancel` to abort.")

    elif step == "steps":
        send_msg(chat_id, "🏃 **Step 5/18: Steps Count**\nHow many steps did you walk today?\nSend `/skip` to skip, or `/cancel` to abort.")

    elif step == "workout_minutes":
        send_msg(chat_id, "💪 **Step 6/18: Workout Duration**\nHow many minutes of dedicated workout did you do?\nSend `/skip` to skip, or `/cancel` to abort.")

    elif step == "workout_type":
        markup = {
            "inline_keyboard": [
                [{"text": "strength", "callback_data": "wtype_strength"}, {"text": "moderate intensity", "callback_data": "wtype_moderate"}],
                [{"text": "HIIT", "callback_data": "wtype_HIIT"}, {"text": "None", "callback_data": "wtype_None"}],
                [{"text": "Skip ➡️", "callback_data": "skip"}]
            ]
        }
        send_msg(chat_id, "🏋️ **Step 7/18: Workout Type**\nWhat was the workout type?\nSend `/skip` to skip, or `/cancel` to abort.", reply_markup=markup)

    elif step == "exercise_snacks_count":
        send_msg(chat_id, "⏱️ **Step 8/18: Exercise Snacks**\nHow many exercise snacks (<5 mins, squats/pushups) did you do?\nSend `/skip` to skip, or `/cancel` to abort.")

    elif step == "sleep_window_ask":
        markup = {
            "inline_keyboard": [
                [{"text": "Yes 👍", "callback_data": "sleepask_yes"}, {"text": "No 👎", "callback_data": "sleepask_no"}],
                [{"text": "Skip ➡️", "callback_data": "skip"}]
            ]
        }
        send_msg(chat_id, "🛌 **Step 9/18: Log Sleep Window?**\nDo you want to log your sleep timing window?\nSend `/skip` to skip, or `/cancel` to abort.", reply_markup=markup)

    elif step == "sleep_start":
        send_msg(chat_id, "🛌 **Step 10/18: Sleep Start Time**\nWhat time did you go to sleep? Format `HH:MM` (e.g. `23:30` or `00:15`).\nSend `/skip` to skip, or `/cancel` to abort.")

    elif step == "sleep_end":
        send_msg(chat_id, "🛌 **Step 11/18: Sleep End Time**\nWhat time did you wake up? Format `HH:MM` (e.g. `07:30`).\nSend `/skip` to skip, or `/cancel` to abort.")

    elif step == "water_cups":
        send_msg(chat_id, "💧 **Step 12/18: Water Intake**\nHow many cups of water did you drink?\nSend `/skip` to skip, or `/cancel` to abort.")

    elif step == "coffee_cups":
        send_msg(chat_id, "☕ **Step 13/18: Coffee Intake**\nHow many cups of coffee did you drink?\nSend `/skip` to skip, or `/cancel` to abort.")

    elif step == "coffee_type":
        markup = {
            "inline_keyboard": [
                [{"text": "Filter", "callback_data": "ctype_Filter"}, {"text": "Espresso", "callback_data": "ctype_Espresso"}],
                [{"text": "Instant", "callback_data": "ctype_Instant"}, {"text": "Decaf", "callback_data": "ctype_Decaf"}],
                [{"text": "Skip ➡️", "callback_data": "skip"}]
            ]
        }
        send_msg(chat_id, "☕ **Step 14/18: Coffee Type**\nWhat type of coffee did you drink?\nSend `/skip` to skip, or `/cancel` to abort.", reply_markup=markup)

    elif step == "fruits_servings":
        send_msg(chat_id, "🍎 **Step 15/18: Fruits Intake**\nHow many servings of fruits did you eat?\nSend `/skip` to skip, or `/cancel` to abort.")

    elif step == "vegetables_servings":
        send_msg(chat_id, "🥦 **Step 16/18: Vegetables Intake**\nHow many servings of vegetables did you eat?\nSend `/skip` to skip, or `/cancel` to abort.")

    elif step == "harmful_foods":
        send_msg(chat_id, "🍔 **Step 17/18: Junk Foods Notes**\nAny notes on junk or harmful foods? (e.g., `2 cookies, 1 slice of pizza`)\nSend `/skip` to skip, or `/cancel` to abort.")

    elif step == "supplements":
        send_supplements_checklist(chat_id)

def handle_step_input(chat_id, val):
    """
    Validates and stores the current step value, updating state machine forward.
    """
    session = sessions[chat_id]
    step = session["current_step"]
    
    if step == "date":
        if val == "today":
            session["log_date"] = datetime.now().date().isoformat()
        elif val == "yesterday":
            session["log_date"] = (datetime.now() - timedelta(days=1)).date().isoformat()
        else:
            try:
                parsed_date = datetime.strptime(val, "%Y-%m-%d").date()
                session["log_date"] = parsed_date.isoformat()
            except Exception:
                send_msg(chat_id, "⚠️ Invalid date format. Please send a date as `YYYY-MM-DD` (e.g. `2026-05-28`), or type `/today` / click buttons.")
                return False
        session["current_step"] = "mood_score"

    elif step == "mood_score":
        if val == "skip":
            session["data"]["mood_score"] = None
        else:
            try:
                score = int(val)
                if 1 <= score <= 10:
                    session["data"]["mood_score"] = score
                else:
                    raise ValueError()
            except Exception:
                send_msg(chat_id, "⚠️ Please enter an integer between 1 and 10, or send `/skip`.")
                return False
        session["current_step"] = "diary_text"

    elif step == "diary_text":
        if val == "skip":
            session["data"]["diary_text"] = None
        else:
            session["data"]["diary_text"] = val
        session["current_step"] = "work_hours"

    elif step == "work_hours":
        if val == "skip":
            session["data"]["work_hours"] = None
        else:
            try:
                hours = float(val)
                if 0 <= hours <= 24:
                    session["data"]["work_hours"] = hours
                else:
                    raise ValueError()
            except Exception:
                send_msg(chat_id, "⚠️ Please enter a number of hours between 0 and 24, or send `/skip`.")
                return False
        session["current_step"] = "steps"

    elif step == "steps":
        if val == "skip":
            session["data"]["steps"] = None
        else:
            try:
                steps_count = int(val)
                if steps_count >= 0:
                    session["data"]["steps"] = steps_count
                else:
                    raise ValueError()
            except Exception:
                send_msg(chat_id, "⚠️ Please enter a non-negative integer for steps, or send `/skip`.")
                return False
        session["current_step"] = "workout_minutes"

    elif step == "workout_minutes":
        if val == "skip":
            session["data"]["workout_minutes"] = None
        else:
            try:
                mins = int(val)
                if mins >= 0:
                    session["data"]["workout_minutes"] = mins
                else:
                    raise ValueError()
            except Exception:
                send_msg(chat_id, "⚠️ Please enter a non-negative integer for minutes, or send `/skip`.")
                return False
        session["current_step"] = "workout_type"

    elif step == "workout_type":
        if val == "skip" or val == "None":
            session["data"]["workout_type"] = None
        else:
            # Map shorthand to exact match in DB/Frontend
            if val in ("moderate", "moderate intensity"):
                val = "moderate intensity aerobic workouts"
            session["data"]["workout_type"] = val[:50]
        session["current_step"] = "exercise_snacks_count"

    elif step == "exercise_snacks_count":
        if val == "skip":
            session["data"]["exercise_snacks_count"] = None
        else:
            try:
                snacks = int(val)
                if snacks >= 0:
                    session["data"]["exercise_snacks_count"] = snacks
                else:
                    raise ValueError()
            except Exception:
                send_msg(chat_id, "⚠️ Please enter a non-negative integer, or send `/skip`.")
                return False
        session["current_step"] = "sleep_window_ask"

    elif step == "sleep_window_ask":
        if val == "skip" or val == "no":
            session["data"]["sleep_window_ask"] = "no"
            session["data"]["sleep_start_time"] = None
            session["data"]["sleep_end_time"] = None
            session["current_step"] = "water_cups"
        else:
            session["data"]["sleep_window_ask"] = "yes"
            session["current_step"] = "sleep_start"

    elif step == "sleep_start":
        if val == "skip":
            session["data"]["sleep_start_time"] = None
            session["current_step"] = "water_cups"
        else:
            try:
                # Simple validation
                datetime.strptime(val.strip(), "%H:%M")
                session["data"]["sleep_start_time"] = val.strip()
                session["current_step"] = "sleep_end"
            except Exception:
                send_msg(chat_id, "⚠️ Invalid time format. Please enter as `HH:MM` (e.g. `23:30`), or send `/skip`.")
                return False

    elif step == "sleep_end":
        if val == "skip":
            session["data"]["sleep_end_time"] = None
        else:
            try:
                datetime.strptime(val.strip(), "%H:%M")
                session["data"]["sleep_end_time"] = val.strip()
            except Exception:
                send_msg(chat_id, "⚠️ Invalid time format. Please enter as `HH:MM` (e.g. `07:15`), or send `/skip`.")
                return False
        session["current_step"] = "water_cups"

    elif step == "water_cups":
        if val == "skip":
            session["data"]["water_cups"] = None
        else:
            try:
                water = float(val)
                if water >= 0:
                    session["data"]["water_cups"] = water
                else:
                    raise ValueError()
            except Exception:
                send_msg(chat_id, "⚠️ Please enter a non-negative number, or send `/skip`.")
                return False
        session["current_step"] = "coffee_cups"

    elif step == "coffee_cups":
        if val == "skip":
            session["data"]["coffee_cups"] = None
        else:
            try:
                coffee = float(val)
                if coffee >= 0:
                    session["data"]["coffee_cups"] = coffee
                else:
                    raise ValueError()
            except Exception:
                send_msg(chat_id, "⚠️ Please enter a non-negative number, or send `/skip`.")
                return False
        session["current_step"] = "coffee_type"

    elif step == "coffee_type":
        if val == "skip":
            session["data"]["coffee_type"] = None
        else:
            session["data"]["coffee_type"] = val
        session["current_step"] = "fruits_servings"

    elif step == "fruits_servings":
        if val == "skip":
            session["data"]["fruits_servings"] = None
        else:
            try:
                fruits = float(val)
                if fruits >= 0:
                    session["data"]["fruits_servings"] = fruits
                else:
                    raise ValueError()
            except Exception:
                send_msg(chat_id, "⚠️ Please enter a non-negative number, or send `/skip`.")
                return False
        session["current_step"] = "vegetables_servings"

    elif step == "vegetables_servings":
        if val == "skip":
            session["data"]["vegetables_servings"] = None
        else:
            try:
                veggies = float(val)
                if veggies >= 0:
                    session["data"]["vegetables_servings"] = veggies
                else:
                    raise ValueError()
            except Exception:
                send_msg(chat_id, "⚠️ Please enter a non-negative number, or send `/skip`.")
                return False
        session["current_step"] = "harmful_foods"

    elif step == "harmful_foods":
        if val == "skip":
            session["data"]["harmful_foods"] = None
        else:
            session["data"]["harmful_foods"] = val
        session["current_step"] = "supplements"

    return True

def submit_log_session(chat_id):
    """
    Submits compiled questionnaire logs to the backend database endpoints.
    """
    session = sessions[chat_id]
    log_date = session["log_date"]
    data = session["data"]
    
    sleep_start_iso = None
    sleep_end_iso = None
    if data.get("sleep_start_time"):
        try:
            t_start = datetime.strptime(data["sleep_start_time"].strip(), "%H:%M").time()
            sleep_start_iso = f"{log_date}T{t_start.strftime('%H:%M:%S')}"
        except Exception:
            sleep_start_iso = f"{log_date}T{data['sleep_start_time']}:00"
    if data.get("sleep_end_time"):
        try:
            t_end = datetime.strptime(data["sleep_end_time"].strip(), "%H:%M").time()
            sleep_end_iso = f"{log_date}T{t_end.strftime('%H:%M:%S')}"
        except Exception:
            sleep_end_iso = f"{log_date}T{data['sleep_end_time']}:00"

    supplements_payload = []
    for idx in session["supplements_selected"]:
        s = PREDEFINED_SUPPLEMENTS[idx]
        dosage = session.setdefault("supplements_dosages", {}).get(idx, s["dosage"])
        supplements_payload.append({
            "name": s["name"],
            "dosage": dosage,
            "unit": s["unit"]
        })
    for cs in session["custom_supplements"]:
        supplements_payload.append({
            "name": cs["name"],
            "dosage": cs["dosage"],
            "unit": cs["unit"]
        })

    daily_log_payload = {
        "date": log_date,
        "mood_score": data.get("mood_score"),
        "diary_text": data.get("diary_text"),
        "sleep_start": sleep_start_iso,
        "sleep_end": sleep_end_iso,
        "steps": data.get("steps"),
        "workout_minutes": data.get("workout_minutes"),
        "workout_type": data.get("workout_type"),
        "exercise_snacks_count": data.get("exercise_snacks_count"),
        "work_hours": data.get("work_hours"),
        "supplements": supplements_payload
    }

    nutrition_payload = {
        "date": log_date,
        "water_cups": data.get("water_cups"),
        "coffee_cups": data.get("coffee_cups"),
        "coffee_type": data.get("coffee_type"),
        "fruits_servings": data.get("fruits_servings"),
        "vegetables_servings": data.get("vegetables_servings"),
        "harmful_foods": data.get("harmful_foods")
    }

    try:
        r1 = requests.post(f"{BACKEND_URL}/api/daily-logs/", json=daily_log_payload, timeout=10.0)
        r1.raise_for_status()

        r2 = requests.post(f"{BACKEND_URL}/api/nutrition/", json=nutrition_payload, timeout=10.0)
        r2.raise_for_status()

        send_msg(chat_id, f"🎉 **Daily Log and Nutrition successfully submitted for {log_date}!**\n\nThank you! Keep up the great tracking! 🚀")
    except Exception as e:
        err_msg = f"❌ **Failed to submit log to backend:** {e}"
        if hasattr(e, 'response') and e.response is not None:
            try:
                response_json = e.response.json()
                if "detail" in response_json:
                    err_msg += f"\n\n**Details:** {response_json['detail']}"
            except Exception:
                if e.response.text:
                    err_msg += f"\n\n**Details:** {e.response.text[:200]}"
        send_msg(chat_id, err_msg + "\n\nPlease check connection settings or try again.")
        print(f"Error submitting bot logs: {e}")
        
    sessions.pop(chat_id, None)

def handle_callback(callback_query):
    """
    Processes CallbackQuery events originating from inline keyboard presses.
    """
    callback_query_id = callback_query.get("id")
    message = callback_query.get("message", {})
    chat = message.get("chat", {})
    chat_id = str(chat.get("id"))
    data = callback_query.get("data")
    message_id = message.get("message_id")
    
    if data.startswith("sleepq_"):
        q_val = data.split("_")[1]
        moscow_time = datetime.now(ZoneInfo("Europe/Moscow"))
        log_date = moscow_time.date().isoformat()
        
        if q_val == "skip":
            answer_callback(callback_query_id, "Пропущено")
            edit_msg(chat_id, message_id, f"💤 Оценка качества сна за {log_date} пропущена.")
        else:
            try:
                score = int(q_val)
                answer_callback(callback_query_id, f"Оценка: {score}")
                
                payload = {
                    "date": log_date,
                    "sleep_quality": score
                }
                url = f"{BACKEND_URL}/api/daily-logs"
                r = requests.post(url, json=payload, timeout=10.0)
                r.raise_for_status()
                
                edit_msg(chat_id, message_id, f"✅ Сохранена оценка качества сна за {log_date}: **{score}/10**")
            except Exception as e:
                print(f"Error saving morning sleep quality: {e}")
                edit_msg(chat_id, message_id, f"❌ Не удалось сохранить оценку сна: {e}")
        return

    # === MEALS CALLBACKS (outside active logging session check) ===
    if data.startswith("meal_"):
        moscow_time = datetime.now(ZoneInfo("Europe/Moscow"))
        today_iso = moscow_time.date().isoformat()
        meal_names_ru = {"Breakfast": "завтрак", "Lunch": "обед", "Dinner": "ужин"}
        
        if data.startswith("meal_preset_"):
            meal_type = data.split("_")[2]
            ru_name = meal_names_ru.get(meal_type, "прием пищи")
            items = MEAL_PRESETS.get(meal_type, [])
            
            payload = {
                "date": today_iso,
                "meal_type": meal_type,
                "items": items,
                "photo_path": None
            }
            try:
                r = requests.post(f"{BACKEND_URL}/api/meals/", json=payload, timeout=10.0)
                r.raise_for_status()
                answer_callback(callback_query_id, "Пресет сохранен")
                edit_msg(chat_id, message_id, f"✅ Записан стандартный {ru_name} за {today_iso}!")
            except Exception as e:
                print(f"Error saving meal preset: {e}")
                answer_callback(callback_query_id, "Ошибка сохранения")
                edit_msg(chat_id, message_id, f"❌ Ошибка сохранения пресета: {e}")
            return

        elif data.startswith("meal_skip_"):
            meal_type = data.split("_")[2]
            ru_name = meal_names_ru.get(meal_type, "прием пищи")
            answer_callback(callback_query_id, "Пропущено")
            edit_msg(chat_id, message_id, f"➡️ Логгирование {ru_name} за {today_iso} пропущено.")
            return

        elif data.startswith("meal_photo_ask_"):
            meal_type = data.split("_")[3]
            ru_name = meal_names_ru.get(meal_type, "прием пищи")
            answer_callback(callback_query_id)
            sessions[chat_id] = {
                "session_type": "meal_photo",
                "meal_type": meal_type
            }
            edit_msg(chat_id, message_id, f"📷 Пожалуйста, пришлите фотографию вашего приема пищи ({ru_name}).\nОтправьте `/cancel` для отмены.")
            return

        elif data.startswith("meal_photo_save_"):
            choice = data.split("_")[3]
            photo_path = sessions.get(chat_id, {}).get("photo_path")
            
            if not photo_path:
                answer_callback(callback_query_id, "Ошибка сессии")
                edit_msg(chat_id, message_id, "❌ Сессия истекла.")
                sessions.pop(chat_id, None)
                return
                
            if choice == "Note":
                payload = {
                    "note_text": "[Фото заметка]",
                    "file_path": photo_path,
                    "file_type": "image"
                }
                try:
                    r = requests.post(f"{BACKEND_URL}/api/notes/", json=payload, timeout=10.0)
                    r.raise_for_status()
                    answer_callback(callback_query_id, "Фото сохранено")
                    edit_msg(chat_id, message_id, "📷 Фото-заметка успешно сохранена!")
                except Exception as e:
                    print(f"Error saving image note: {e}")
                    answer_callback(callback_query_id, "Ошибка")
                    edit_msg(chat_id, message_id, f"❌ Ошибка: {e}")
            else:
                ru_name = meal_names_ru.get(choice, "прием пищи")
                payload = {
                    "date": today_iso,
                    "meal_type": choice,
                    "items": [],
                    "photo_path": photo_path
                }
                try:
                    r = requests.post(f"{BACKEND_URL}/api/meals/", json=payload, timeout=10.0)
                    r.raise_for_status()
                    answer_callback(callback_query_id, "Фото сохранено")
                    edit_msg(chat_id, message_id, f"✅ Фото приема пищи ({ru_name}) успешно сохранено!")
                except Exception as e:
                    print(f"Error saving meal photo: {e}")
                    answer_callback(callback_query_id, "Ошибка")
                    edit_msg(chat_id, message_id, f"❌ Ошибка: {e}")
            sessions.pop(chat_id, None)
            return

        elif data.startswith("meal_manual_"):
            meal_type = data.split("_")[2]
            answer_callback(callback_query_id)
            sessions[chat_id] = {
                "session_type": "meal",
                "meal_type": meal_type,
                "items": [],
                "current_action": "choose_product",
                "temp_product_name": None,
                "temp_product_unit": None,
                "temp_quantity": None
            }
            send_meal_product_selector(chat_id, message_id=message_id)
            return

    # === MEAL MANUAL LOGGING CALLBACKS (inside active logging check but handled separately) ===
    if data.startswith("mealprod_"):
        if chat_id not in sessions or sessions[chat_id].get("session_type") != "meal":
            answer_callback(callback_query_id, "Сессия истекла.")
            return
            
        session = sessions[chat_id]
        
        if data == "mealprod_cancel":
            answer_callback(callback_query_id, "Отменено")
            edit_msg(chat_id, message_id, "❌ Заполнение приема пищи отменено.")
            sessions.pop(chat_id, None)
            return
            
        elif data == "mealprod_done":
            if not session["items"]:
                answer_callback(callback_query_id, "Добавьте продукты!")
                return
                
            moscow_time = datetime.now(ZoneInfo("Europe/Moscow"))
            today_iso = moscow_time.date().isoformat()
            meal_names_ru = {"Breakfast": "завтрак", "Lunch": "обед", "Dinner": "ужин"}
            ru_name = meal_names_ru.get(session["meal_type"], "прием пищи")
            
            payload = {
                "date": today_iso,
                "meal_type": session["meal_type"],
                "items": session["items"],
                "photo_path": None
            }
            try:
                r = requests.post(f"{BACKEND_URL}/api/meals/", json=payload, timeout=10.0)
                r.raise_for_status()
                answer_callback(callback_query_id, "Сохранено")
                edit_msg(chat_id, message_id, f"✅ Прием пищи ({ru_name}) успешно сохранен за {today_iso}!")
            except Exception as e:
                print(f"Error saving custom meal: {e}")
                answer_callback(callback_query_id, "Ошибка сохранения")
                edit_msg(chat_id, message_id, f"❌ Ошибка сохранения: {e}")
            sessions.pop(chat_id, None)
            return
            
        elif data == "mealprod_addnew":
            answer_callback(callback_query_id)
            session["current_action"] = "input_new_product_name"
            edit_msg(chat_id, message_id, "✍️ Введите название нового продукта:")
            return
            
        elif data.startswith("mealprod_sel_"):
            prod_id = int(data.split("_")[2])
            answer_callback(callback_query_id)
            try:
                r = requests.get(f"{BACKEND_URL}/api/meals/food-products", timeout=5.0)
                products = r.json()
                product = next((p for p in products if p["id"] == prod_id), None)
            except Exception:
                product = None
                
            if not product:
                edit_msg(chat_id, message_id, "❌ Продукт не найден. Попробуйте еще раз.")
                send_meal_product_selector(chat_id, message_id=message_id)
                return
                
            session["temp_product_name"] = product["name"]
            session["temp_product_unit"] = product["default_unit"]
            session["current_action"] = "input_quantity"
            
            edit_msg(chat_id, message_id, f"✍️ Введите количество для продукта **{product['name']}** (в {product['default_unit']}):\n\nИли введите количество и единицу через пробел (например, `150 грамм`).")
            return
            
        elif data.startswith("mealprod_unit_"):
            unit = data.split("_")[2]
            answer_callback(callback_query_id)
            if session.get("current_action") == "input_new_product_unit":
                session["temp_product_unit"] = unit
                try:
                    payload = {"name": session["temp_product_name"], "default_unit": unit}
                    requests.post(f"{BACKEND_URL}/api/meals/food-products", json=payload, timeout=5.0)
                except Exception as e:
                    print(f"Error pre-saving new product: {e}")
                
                session["current_action"] = "input_quantity"
                edit_msg(chat_id, message_id, f"✍️ Введите количество для **{session['temp_product_name']}** (в {unit}):\n\nИли введите количество и единицу через пробел (например, `150 грамм`).")
            elif session.get("current_action") == "input_quantity_unit":
                session["items"].append({
                    "product_name": session["temp_product_name"],
                    "quantity": session["temp_quantity"],
                    "unit": unit
                })
                session["current_action"] = "choose_product"
                session["temp_product_name"] = None
                session["temp_product_unit"] = None
                session["temp_quantity"] = None
                send_meal_product_selector(chat_id, message_id=message_id)
            return

    if chat_id not in sessions:
        answer_callback(callback_query_id, "Session expired. Type /log to start.")
        return
        
    session = sessions[chat_id]
    
    if data == "skip":
        answer_callback(callback_query_id, "Skipped")
        if handle_step_input(chat_id, "skip"):
            ask_next_question(chat_id)
            
    elif data.startswith("mood_"):
        score = data.split("_")[1]
        answer_callback(callback_query_id, f"Mood: {score}")
        if handle_step_input(chat_id, score):
            ask_next_question(chat_id)
            
    elif data.startswith("wtype_"):
        wtype = data.split("_")[1]
        answer_callback(callback_query_id, f"Workout: {wtype}")
        if handle_step_input(chat_id, wtype):
            ask_next_question(chat_id)
            
    elif data.startswith("sleepask_"):
        choice = data.split("_")[1]
        answer_callback(callback_query_id, f"Log sleep: {choice}")
        if handle_step_input(chat_id, choice):
            ask_next_question(chat_id)
            
    elif data.startswith("ctype_"):
        ctype = data.split("_")[1]
        answer_callback(callback_query_id, f"Coffee: {ctype}")
        if handle_step_input(chat_id, ctype):
            ask_next_question(chat_id)
            
    elif data.startswith("date_"):
        choice = data.split("_")[1]
        answer_callback(callback_query_id, f"Date: {choice}")
        if handle_step_input(chat_id, choice):
            ask_next_question(chat_id)

    elif data.startswith("supp_toggle_"):
        idx = int(data.split("_")[2])
        answer_callback(callback_query_id, "Toggled")
        if idx in session["supplements_selected"]:
            session["supplements_selected"].remove(idx)
            session.setdefault("supplements_dosages", {}).pop(idx, None)
            send_supplements_checklist(chat_id, message_id=message_id)
        else:
            session["waiting_for_dosage_of"] = idx
            s = PREDEFINED_SUPPLEMENTS[idx]
            markup = {
                "inline_keyboard": [
                    [
                        {"text": f"Keep Default ({s['dosage']} {s['unit']})", "callback_data": f"supp_default_{idx}"},
                        {"text": "Cancel ❌", "callback_data": f"supp_cancel_{idx}"}
                    ]
                ]
            }
            text = f"💊 **Enter dosage for {s['name']}** ({s['unit']}):\nDefault is `{s['dosage']}`. Send a number to customize, or tap buttons below."
            edit_msg(chat_id, message_id, text, reply_markup=markup)

    elif data.startswith("supp_default_"):
        idx = int(data.split("_")[2])
        answer_callback(callback_query_id, "Using default dosage")
        s = PREDEFINED_SUPPLEMENTS[idx]
        session["supplements_selected"].add(idx)
        session.setdefault("supplements_dosages", {})[idx] = s["dosage"]
        session["waiting_for_dosage_of"] = None
        send_supplements_checklist(chat_id, message_id=message_id)

    elif data.startswith("supp_cancel_"):
        idx = int(data.split("_")[2])
        answer_callback(callback_query_id, "Cancelled selection")
        session["waiting_for_dosage_of"] = None
        send_supplements_checklist(chat_id, message_id=message_id)

    elif data == "supp_custom":
        answer_callback(callback_query_id)
        session["waiting_for_custom_supplement"] = True
        send_msg(chat_id, "✍️ Please enter custom supplement name, dosage, and unit (e.g. `Magnesium 400 mg`).\nSend `/skip` to cancel custom addition.")

    elif data == "supp_skip":
        answer_callback(callback_query_id, "Skipped supplements")
        session["current_step"] = "done"
        ask_next_question(chat_id)

    elif data == "supp_done":
        answer_callback(callback_query_id, "Finished supplements")
        session["current_step"] = "done"
        ask_next_question(chat_id)

def handle_message(chat_id, text, message=None):
    """
    Processes incoming text messages, commands, or answers to logger steps.
    """
    global chat_id_store
    text = text.strip() if text else ""
    
    # 1. Handle commands first (available anytime)
    if text == "/start":
        chat_id_store = chat_id
        register_chat_id_on_backend(chat_id)
        
        reply_text = (
            f"🎉 **Personal Analytics Bot Activated!**\n\n"
            f"Registered Chat ID: `{chat_id}`\n\n"
            f"Available Commands:\n"
            f"📝 `/log` - Начать заполнение отчета за день\n"
            f"📝 `/note` - Сохранить спонтанную заметку\n"
            f"📊 `/stats` - Посмотреть подробную статистику\n"
            f"🔥 `/streak` - Посмотреть серию заполнений\n"
            f"❌ `/cancel` - Отменить текущую сессию\n\n"
            f"Вы будете получать уведомления в 7:00 (сон), 9:00 (завтрак), 13:00 (обед), 18:00 (ужин) и {REMINDER_HOUR:02d}:00 (вечерний отчет) по МСК."
        )
        send_msg(chat_id, reply_text)
        return

    if text == "/cancel":
        if chat_id in sessions:
            sessions.pop(chat_id)
            send_msg(chat_id, "❌ Текущая сессия отменена.")
        else:
            send_msg(chat_id, "Нет активной сессии для отмены.")
        return

    if text == "/stats":
        send_msg(chat_id, "⌛ Загрузка статистики...")
        try:
            stats_msg = get_stats_message()
            send_msg(chat_id, stats_msg)
        except Exception as e:
            send_msg(chat_id, f"❌ Ошибка при получении статистики: {e}")
        return

    if text == "/streak":
        send_msg(chat_id, "⌛ Получение информации о сериях заполнений...")
        try:
            logs = fetch_daily_logs()
            if not logs:
                send_msg(chat_id, "💤 У вас пока нет заполненных отчетов. Начните с команды `/log`!")
            else:
                current_streak, longest_streak = calculate_streaks(logs)
                emoji = get_streak_emoji(current_streak)
                msg = (
                    f"🔥 **Серии заполнений (Streaks)**\n\n"
                    f"Текущая серия: `{current_streak}` {emoji}\n"
                    f"Рекордная серия: `{longest_streak}` 🏆\n\n"
                    f"Продолжайте заполнять логи каждый день, чтобы поддерживать серию! 🚀"
                )
                send_msg(chat_id, msg)
        except Exception as e:
            send_msg(chat_id, f"❌ Ошибка при получении серии заполнений: {e}")
        return

    # 2. Check active sessions
    if chat_id in sessions:
        session = sessions[chat_id]
        session_type = session.get("session_type")
        
        if session_type == "meal":
            action = session.get("current_action")
            
            if action == "input_new_product_name":
                session["temp_product_name"] = text
                session["current_action"] = "input_new_product_unit"
                
                # Ask for unit of measurement
                text_prompt = f"📏 Выберите или введите единицу измерения по умолчанию для **{text}**:"
                markup = {
                    "inline_keyboard": [
                        [{"text": "грамм", "callback_data": "mealprod_unit_грамм"}, {"text": "штука", "callback_data": "mealprod_unit_штука"}],
                        [{"text": "столовая ложка", "callback_data": "mealprod_unit_столовая ложка"}, {"text": "чайная ложка", "callback_data": "mealprod_unit_чайная ложка"}],
                        [{"text": "миллилитр", "callback_data": "mealprod_unit_миллилитр"}, {"text": "стакан", "callback_data": "mealprod_unit_стакан"}],
                        [{"text": "порция", "callback_data": "mealprod_unit_порция"}]
                    ]
                }
                send_msg(chat_id, text_prompt, reply_markup=markup)
                return
                
            elif action == "input_new_product_unit":
                session["temp_product_unit"] = text
                # Pre-save new product in DB
                try:
                    payload = {"name": session["temp_product_name"], "default_unit": text}
                    requests.post(f"{BACKEND_URL}/api/meals/food-products", json=payload, timeout=5.0)
                except Exception as e:
                    print(f"Error pre-saving new product: {e}")
                    
                session["current_action"] = "input_quantity"
                send_msg(chat_id, f"✍️ Введите количество для **{session['temp_product_name']}** ({text}):\n\nИли введите количество и единицу через пробел (например, `150 грамм`).")
                return
                
            elif action == "input_quantity":
                qty, unit = parse_quantity_input(text)
                if qty is None:
                    send_msg(chat_id, "⚠️ Не удалось распознать количество. Пожалуйста, введите положительное число (например, `150` или `2.5`):")
                    return
                
                if unit is None:
                    # No unit was provided, ask if they want to choose a different unit or use the default one
                    session["temp_quantity"] = qty
                    session["current_action"] = "input_quantity_unit"
                    default_unit = session["temp_product_unit"] or "грамм"
                    text_prompt = f"📏 Использовать единицу по умолчанию `{default_unit}` или выбрать другую?"
                    markup = {
                        "inline_keyboard": [
                            [{"text": f"Использовать {default_unit}", "callback_data": f"mealprod_unit_{default_unit}"}],
                            [{"text": "грамм", "callback_data": "mealprod_unit_грамм"}, {"text": "штука", "callback_data": "mealprod_unit_штука"}],
                            [{"text": "столовая ложка", "callback_data": "mealprod_unit_столовая ложка"}, {"text": "чайная ложка", "callback_data": "mealprod_unit_чайная ложка"}],
                            [{"text": "миллилитр", "callback_data": "mealprod_unit_миллилитр"}, {"text": "стакан", "callback_data": "mealprod_unit_стакан"}]
                        ]
                    }
                    send_msg(chat_id, text_prompt, reply_markup=markup)
                    return
                else:
                    # Both quantity and unit were entered
                    session["items"].append({
                        "product_name": session["temp_product_name"],
                        "quantity": qty,
                        "unit": unit
                    })
                    session["current_action"] = "choose_product"
                    session["temp_product_name"] = None
                    session["temp_product_unit"] = None
                    session["temp_quantity"] = None
                    send_meal_product_selector(chat_id)
                    return

            elif action == "input_quantity_unit":
                # If they type the unit manually
                session["items"].append({
                    "product_name": session["temp_product_name"],
                    "quantity": session["temp_quantity"],
                    "unit": text
                })
                session["current_action"] = "choose_product"
                session["temp_product_name"] = None
                session["temp_product_unit"] = None
                session["temp_quantity"] = None
                send_meal_product_selector(chat_id)
                return

        elif session_type == "meal_photo":
            if message and message.get("photo"):
                photo_list = message.get("photo")
                file_id = photo_list[-1].get("file_id")
                timestamp = int(time.time())
                relative_path = f"/uploads/images/meal_{timestamp}.jpg"
                dest_path = f"/app{relative_path}"
                
                success = download_telegram_file(file_id, dest_path)
                if success:
                    moscow_time = datetime.now(ZoneInfo("Europe/Moscow"))
                    today_iso = moscow_time.date().isoformat()
                    payload = {
                        "date": today_iso,
                        "meal_type": session["meal_type"],
                        "items": [],
                        "photo_path": relative_path
                    }
                    try:
                        r = requests.post(f"{BACKEND_URL}/api/meals/", json=payload, timeout=10.0)
                        r.raise_for_status()
                        send_msg(chat_id, f"✅ Фото приема пищи ({session['meal_type']}) успешно сохранено!")
                    except Exception as e:
                        send_msg(chat_id, f"❌ Не удалось сохранить прием пищи на сервере: {e}")
                else:
                    send_msg(chat_id, "❌ Не удалось скачать фото. Попробуйте еще раз.")
                sessions.pop(chat_id, None)
            else:
                send_msg(chat_id, "⚠️ Пожалуйста, пришлите фотографию приема пищи или введите `/cancel` для отмены.")
            return

        elif session_type == "spontaneous_note_input":
            payload = {
                "note_text": text,
                "file_path": None,
                "file_type": "text"
            }
            try:
                r = requests.post(f"{BACKEND_URL}/api/notes/", json=payload, timeout=10.0)
                r.raise_for_status()
                send_msg(chat_id, "📝 Заметка сохранена!")
            except Exception as e:
                send_msg(chat_id, f"❌ Не удалось сохранить заметку: {e}")
            sessions.pop(chat_id, None)
            return

        elif session_type == "spontaneous_photo_select":
            send_msg(chat_id, "Пожалуйста, выберите вариант на клавиатуре выше или введите `/cancel`.")
            return

        # Default daily log session processing
        waiting_idx = session.get("waiting_for_dosage_of")
        if waiting_idx is not None:
            if text == "/skip":
                session["waiting_for_dosage_of"] = None
                send_supplements_checklist(chat_id, message_id=session.get("checklist_message_id"))
            else:
                try:
                    dosage = float(text)
                    if dosage > 0:
                        s = PREDEFINED_SUPPLEMENTS[waiting_idx]
                        session["supplements_selected"].add(waiting_idx)
                        session.setdefault("supplements_dosages", {})[waiting_idx] = dosage
                        session["waiting_for_dosage_of"] = None
                        send_supplements_checklist(chat_id, message_id=session.get("checklist_message_id"))
                    else:
                        raise ValueError()
                except Exception:
                    send_msg(chat_id, "⚠️ Invalid dosage. Please enter a positive number, or send `/skip` to cancel.")
            return

        if session.get("waiting_for_custom_supplement"):
            if text == "/skip":
                session["waiting_for_custom_supplement"] = False
                send_msg(chat_id, "Custom supplement addition cancelled.")
                send_supplements_checklist(chat_id, message_id=session.get("checklist_message_id"))
            else:
                parts = text.split()
                if len(parts) >= 3:
                    unit = parts[-1]
                    try:
                        dosage = float(parts[-2])
                        name = " ".join(parts[:-2])
                        session["custom_supplements"].append({
                            "name": name[:100],
                            "dosage": dosage,
                            "unit": unit[:20]
                        })
                        session["waiting_for_custom_supplement"] = False
                        send_msg(chat_id, f"Added custom supplement: {name[:100]} {dosage} {unit[:20]}")
                        send_supplements_checklist(chat_id, message_id=session.get("checklist_message_id"))
                    except Exception:
                        send_msg(chat_id, "⚠️ Could not parse input. Format: `Name Dosage Unit` (e.g., `Magnesium 400 mg`). Try again or send `/skip`.")
                else:
                    send_msg(chat_id, "⚠️ Could not parse input. Format: `Name Dosage Unit` (e.g., `Magnesium 400 mg`). Try again or send `/skip`.")
            return

        if text == "/skip":
            if handle_step_input(chat_id, "skip"):
                ask_next_question(chat_id)
            return

        if handle_step_input(chat_id, text):
            ask_next_question(chat_id)
            
    # 3. Handle messages outside of active sessions
    else:
        # User wants to start logging
        if text == "/log":
            # A. Fetch and display spontaneous notes first
            try:
                r = requests.get(f"{BACKEND_URL}/api/notes/undisplayed", timeout=5.0)
                if r.status_code == 200:
                    notes = r.json()
                    if notes:
                        notes_text = "📝 **Заметки, сохраненные в течение дня:**\n\n"
                        note_ids = []
                        for n in notes:
                            note_ids.append(n["id"])
                            try:
                                dt = datetime.fromisoformat(n["created_at"].replace("Z", "+00:00")).astimezone(ZoneInfo("Europe/Moscow"))
                                time_str = dt.strftime("%H:%M")
                            except Exception:
                                time_str = ""
                                
                            prefix = f"• [{time_str}] " if time_str else "• "
                            
                            if n["file_type"] == "text":
                                notes_text += f"{prefix}{n['note_text']}\n"
                            elif n["file_type"] == "voice":
                                notes_text += f"{prefix}🎙️ Голосовая заметка\n"
                            elif n["file_type"] == "image":
                                notes_text += f"{prefix}📷 Фото-заметка\n"
                            elif n["file_type"] == "video":
                                notes_text += f"{prefix}🎥 Видео-заметка\n"
                                
                        send_msg(chat_id, notes_text)
                        # Mark notes as displayed on backend
                        requests.post(f"{BACKEND_URL}/api/notes/mark-displayed", json=note_ids, timeout=5.0)
            except Exception as e:
                print(f"Error fetching/displaying spontaneous notes: {e}")
                
            # B. Start interactive daily log questionnaire
            sessions[chat_id] = {
                "current_step": "date",
                "log_date": None,
                "data": {},
                "supplements_selected": set(),
                "supplements_dosages": {},
                "custom_supplements": [],
                "waiting_for_custom_supplement": False,
                "waiting_for_dosage_of": None
            }
            ask_next_question(chat_id)
            return

        # User wants to add a note explicitly via /note command
        elif text == "/note":
            sessions[chat_id] = {"session_type": "spontaneous_note_input"}
            send_msg(chat_id, "✍️ Пожалуйста, введите текст спонтанной заметки:")
            return

        elif text.startswith("/note "):
            note_content = text[6:].strip()
            if note_content:
                payload = {
                    "note_text": note_content,
                    "file_path": None,
                    "file_type": "text"
                }
                try:
                    r = requests.post(f"{BACKEND_URL}/api/notes/", json=payload, timeout=10.0)
                    r.raise_for_status()
                    send_msg(chat_id, "📝 Заметка сохранена!")
                except Exception as e:
                    send_msg(chat_id, f"❌ Не удалось сохранить заметку: {e}")
            return

        # 4. Handle spontaneous media / default text inputs outside active session
        elif message:
            # Voice notes
            if message.get("voice"):
                voice_data = message.get("voice")
                file_id = voice_data.get("file_id")
                timestamp = int(time.time())
                relative_path = f"/uploads/voice/voice_{timestamp}.ogg"
                dest_path = f"/app{relative_path}"
                
                success = download_telegram_file(file_id, dest_path)
                if success:
                    payload = {
                        "note_text": "[Голосовое сообщение]",
                        "file_path": relative_path,
                        "file_type": "voice"
                    }
                    try:
                        requests.post(f"{BACKEND_URL}/api/notes/", json=payload, timeout=10.0)
                        send_msg(chat_id, "🎙️ Голосовая заметка сохранена!")
                    except Exception as e:
                        send_msg(chat_id, f"❌ Не удалось сохранить голосовую заметку: {e}")
                else:
                    send_msg(chat_id, "❌ Не удалось загрузить голосовую заметку.")
                return

            # Photos
            elif message.get("photo"):
                photo_list = message.get("photo")
                file_id = photo_list[-1].get("file_id")
                timestamp = int(time.time())
                relative_path = f"/uploads/images/img_{timestamp}.jpg"
                dest_path = f"/app{relative_path}"
                
                success = download_telegram_file(file_id, dest_path)
                if success:
                    sessions[chat_id] = {
                        "session_type": "spontaneous_photo_select",
                        "photo_path": relative_path
                    }
                    markup = {
                        "inline_keyboard": [
                            [{"text": "🍳 Завтрак", "callback_data": "meal_photo_save_Breakfast"}, {"text": "🍲 Обед", "callback_data": "meal_photo_save_Lunch"}],
                            [{"text": "🥗 Ужин", "callback_data": "meal_photo_save_Dinner"}, {"text": "📝 Спонтанная заметка", "callback_data": "meal_photo_save_Note"}]
                        ]
                    }
                    send_msg(chat_id, "📷 Кажется, вы прислали фото. Что это за изображение?", reply_markup=markup)
                else:
                    send_msg(chat_id, "❌ Не удалось загрузить изображение.")
                return

            # Videos or Video Notes
            elif message.get("video") or message.get("video_note"):
                video_data = message.get("video") or message.get("video_note")
                file_id = video_data.get("file_id")
                timestamp = int(time.time())
                relative_path = f"/uploads/videos/video_{timestamp}.mp4"
                dest_path = f"/app{relative_path}"
                
                success = download_telegram_file(file_id, dest_path)
                if success:
                    payload = {
                        "note_text": "[Видео заметка]",
                        "file_path": relative_path,
                        "file_type": "video"
                    }
                    try:
                        requests.post(f"{BACKEND_URL}/api/notes/", json=payload, timeout=10.0)
                        send_msg(chat_id, "🎥 Видео-заметка сохранена!")
                    except Exception as e:
                        send_msg(chat_id, f"❌ Не удалось сохранить видео-заметку: {e}")
                else:
                    send_msg(chat_id, "❌ Не удалось загрузить видео.")
                return

            # Default text input outside session -> treat as text spontaneous note!
            elif text and not text.startswith("/"):
                payload = {
                    "note_text": text,
                    "file_path": None,
                    "file_type": "text"
                }
                try:
                    r = requests.post(f"{BACKEND_URL}/api/notes/", json=payload, timeout=10.0)
                    r.raise_for_status()
                    send_msg(chat_id, "📝 Заметка сохранена!")
                except Exception as e:
                    send_msg(chat_id, f"❌ Не удалось сохранить заметку: {e}")
                return

            # Unknown command
            elif text.startswith("/"):
                send_msg(chat_id, "Неизвестная команда. Доступные команды: `/log`, `/stats`, `/streak`, `/cancel`, `/note`.")
                return

def check_updates():
    """
    Main loop polling Telegram Updates API.
    """
    if not BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN not found. Polling disabled.")
        while True:
            time.sleep(3600)
        return
        
    last_update_id = 0
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    
    print("Telegram Polling active. Send /start or /log to the bot in Telegram.")
    
    while True:
        try:
            params = {"offset": last_update_id + 1, "timeout": 30}
            r = requests.get(url, params=params, timeout=35.0)
            if r.status_code == 200:
                data = r.json()
                for update in data.get("result", []):
                    last_update_id = update["update_id"]
                    
                    callback_query = update.get("callback_query")
                    if callback_query:
                        handle_callback(callback_query)
                        continue
                        
                    message = update.get("message", {})
                    chat = message.get("chat", {})
                    text = message.get("text", "")
                    chat_id = str(chat.get("id"))
                    
                    if not chat_id:
                        continue
                        
                    handle_message(chat_id, text, message=message)
            else:
                print(f"Updates status code error: {r.status_code}")
                time.sleep(10)
        except Exception as e:
            print(f"Error in updates polling loop: {e}")
            time.sleep(10)
            
def set_bot_commands():
    """
    Registers commands in the Telegram Bot menu.
    """
    if not BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN not configured. Skipping command registration.")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setMyCommands"
    payload = {
        "commands": [
            {"command": "log", "description": "Начать заполнение отчета за день"},
            {"command": "note", "description": "Сохранить спонтанную заметку (мысль, фото, видео)"},
            {"command": "stats", "description": "Посмотреть детальную статистику отчетов"},
            {"command": "streak", "description": "Посмотреть серию заполнений (streak)"},
            {"command": "cancel", "description": "Отменить текущую сессию заполнения"},
            {"command": "start", "description": "Запустить или перезапустить бота"}
        ]
    }
    try:
        r = requests.post(url, json=payload, timeout=5.0)
        r.raise_for_status()
        print("Bot commands registered successfully in Telegram menu.")
    except Exception as e:
        print(f"Failed to register bot commands: {e}")

if __name__ == "__main__":
    print("Starting Telegram Bot Service...")
    print(f"Configured Bot Token: {'***' if BOT_TOKEN else 'NONE'}")
    print(f"Configured Chat ID: {chat_id_store if chat_id_store else 'NONE (Dynamic registration active)'}")
    print(f"Reminder Scheduled Daily at: {REMINDER_HOUR:02d}:00 MSK (Europe/Moscow)")

    # Set bot commands in Telegram menu
    set_bot_commands()

    # If static Chat ID configured, register it on backend startup
    if chat_id_store:
        register_chat_id_on_backend(chat_id_store)

    # Start Scheduler
    scheduler = BackgroundScheduler(timezone=ZoneInfo("Europe/Moscow"))
    scheduler.add_job(send_reminder, 'cron', hour=REMINDER_HOUR, minute=0)
    scheduler.add_job(send_morning_sleep_survey, 'cron', hour=7, minute=0)
    scheduler.add_job(send_breakfast_survey, 'cron', hour=9, minute=0)
    scheduler.add_job(send_lunch_survey, 'cron', hour=13, minute=0)
    scheduler.add_job(send_dinner_survey, 'cron', hour=18, minute=0)
    scheduler.start()

    # Start update polling in main thread
    check_updates()
