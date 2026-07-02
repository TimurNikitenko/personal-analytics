import os
import time
import requests
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
        
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": "🔔 **Personal Analytics Reminder**\n\nIt's time to log your day! Send `/log` to this bot to record your metrics here, or head over to the web app. 📊",
        "parse_mode": "Markdown"
    }
    try:
        r = requests.post(url, json=payload, timeout=10.0)
        r.raise_for_status()
        print(f"[{datetime.now()}] Daily reminder sent successfully to chat ID: {chat_id}")
    except Exception as e:
        print(f"[{datetime.now()}] Error sending daily reminder: {e}")

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

def handle_message(chat_id, text):
    """
    Processes incoming text messages, commands, or answers to logger steps.
    """
    global chat_id_store
    text = text.strip()
    
    if text == "/start":
        chat_id_store = chat_id
        register_chat_id_on_backend(chat_id)
        
        reply_text = (
            f"🎉 **Personal Analytics Bot Activated!**\n\n"
            f"Registered Chat ID: `{chat_id}`\n\n"
            f"Available Commands:\n"
            f"📝 `/log` - Start interactive daily log questionnaire\n"
            f"❌ `/cancel` - Cancel active logging session\n"
            f"➡️ `/skip` - Skip current logging question\n\n"
            f"You will receive daily reminders at {REMINDER_HOUR:02d}:00."
        )
        send_msg(chat_id, reply_text)
        return

    if text == "/cancel":
        if chat_id in sessions:
            sessions.pop(chat_id)
            send_msg(chat_id, "❌ Interactive daily logging session cancelled.")
        else:
            send_msg(chat_id, "No active logging session to cancel.")
        return

    if chat_id in sessions:
        session = sessions[chat_id]
        
        # Check if we are waiting for dosage input of a predefined supplement
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
            
    else:
        if text == "/log":
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
        else:
            send_msg(chat_id, "Welcome to Personal Analytics Bot! 📊\n\nSend `/log` to log your day, or `/start` to register.")

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
                        
                    handle_message(chat_id, text)
            else:
                print(f"Updates status code error: {r.status_code}")
                time.sleep(10)
        except Exception as e:
            print(f"Error in updates polling loop: {e}")
            time.sleep(10)
            
if __name__ == "__main__":
    print("Starting Telegram Bot Service...")
    print(f"Configured Bot Token: {'***' if BOT_TOKEN else 'NONE'}")
    print(f"Configured Chat ID: {chat_id_store if chat_id_store else 'NONE (Dynamic registration active)'}")
    print(f"Reminder Scheduled Daily at: {REMINDER_HOUR:02d}:00 MSK (Europe/Moscow)")

    # If static Chat ID configured, register it on backend startup
    if chat_id_store:
        register_chat_id_on_backend(chat_id_store)

    # Start Scheduler
    scheduler = BackgroundScheduler(timezone=ZoneInfo("Europe/Moscow"))
    scheduler.add_job(send_reminder, 'cron', hour=REMINDER_HOUR, minute=0)
    scheduler.start()

    # Start update polling in main thread
    check_updates()
