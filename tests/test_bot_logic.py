import os
import sys
from unittest.mock import patch, MagicMock

# Add project root to sys.path so we can import telegram_bot
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock environment variables so bot doesn't complain
os.environ["TELEGRAM_BOT_TOKEN"] = "fake-token"
os.environ["BACKEND_URL"] = "http://fake-backend:8000"

import pytest
from telegram_bot.bot import (
    sessions,
    handle_message,
    handle_callback,
    handle_step_input,
    PREDEFINED_SUPPLEMENTS,
    submit_log_session
)

@pytest.fixture(autouse=True)
def clean_sessions():
    sessions.clear()

@patch("telegram_bot.bot.send_msg")
@patch("telegram_bot.bot.register_chat_id_on_backend")
def test_start_session(mock_register, mock_send_msg):
    chat_id = "12345"
    handle_message(chat_id, "/log")
    
    assert chat_id in sessions
    assert sessions[chat_id]["current_step"] == "date"
    assert sessions[chat_id]["log_date"] is None

@patch("telegram_bot.bot.send_msg")
def test_workout_type_mapping(mock_send_msg):
    chat_id = "12345"
    
    # Initialize session at workout_type step
    sessions[chat_id] = {
        "current_step": "workout_type",
        "log_date": "2026-05-28",
        "data": {},
        "supplements_selected": set(),
        "supplements_dosages": {},
        "custom_supplements": [],
        "waiting_for_custom_supplement": False,
        "waiting_for_dosage_of": None
    }
    
    # Send "moderate" workout type
    handle_message(chat_id, "moderate")
    
    # Check that "moderate" was mapped to "moderate intensity aerobic workouts"
    assert sessions[chat_id]["data"]["workout_type"] == "moderate intensity aerobic workouts"
    assert sessions[chat_id]["current_step"] == "exercise_snacks_count"

@patch("telegram_bot.bot.send_msg")
def test_workout_type_truncation(mock_send_msg):
    chat_id = "12345"
    
    sessions[chat_id] = {
        "current_step": "workout_type",
        "log_date": "2026-05-28",
        "data": {},
        "supplements_selected": set(),
        "supplements_dosages": {},
        "custom_supplements": [],
        "waiting_for_custom_supplement": False,
        "waiting_for_dosage_of": None
    }
    
    # Send a long workout type description
    long_wtype = "a" * 80
    handle_message(chat_id, long_wtype)
    
    # Should truncate to 50 characters
    assert len(sessions[chat_id]["data"]["workout_type"]) == 50
    assert sessions[chat_id]["data"]["workout_type"] == "a" * 50

@patch("telegram_bot.bot.edit_msg")
def test_supplement_toggle_prompts_dosage(mock_edit):
    chat_id = "12345"
    
    sessions[chat_id] = {
        "current_step": "supplements",
        "log_date": "2026-05-28",
        "data": {},
        "supplements_selected": set(),
        "supplements_dosages": {},
        "custom_supplements": [],
        "waiting_for_custom_supplement": False,
        "waiting_for_dosage_of": None,
        "checklist_message_id": 999
    }
    
    callback_query = {
        "id": "cb1",
        "message": {"chat": {"id": chat_id}, "message_id": 999},
        "data": "supp_toggle_0" # Vitamin D3
    }
    
    with patch("telegram_bot.bot.answer_callback") as mock_ans:
        handle_callback(callback_query)
        
    assert sessions[chat_id]["waiting_for_dosage_of"] == 0
    # Should not be in selected list yet
    assert 0 not in sessions[chat_id]["supplements_selected"]
    
    # Now simulate entering custom dosage
    handle_message(chat_id, "5000")
    
    assert sessions[chat_id]["waiting_for_dosage_of"] is None
    assert 0 in sessions[chat_id]["supplements_selected"]
    assert sessions[chat_id]["supplements_dosages"][0] == 5000.0

@patch("telegram_bot.bot.edit_msg")
def test_supplement_keep_default_dosage(mock_edit):
    chat_id = "12345"
    
    sessions[chat_id] = {
        "current_step": "supplements",
        "log_date": "2026-05-28",
        "data": {},
        "supplements_selected": set(),
        "supplements_dosages": {},
        "custom_supplements": [],
        "waiting_for_custom_supplement": False,
        "waiting_for_dosage_of": 0,
        "checklist_message_id": 999
    }
    
    callback_query = {
        "id": "cb2",
        "message": {"chat": {"id": chat_id}, "message_id": 999},
        "data": "supp_default_0"
    }
    
    with patch("telegram_bot.bot.answer_callback") as mock_ans:
        handle_callback(callback_query)
        
    assert sessions[chat_id]["waiting_for_dosage_of"] is None
    assert 0 in sessions[chat_id]["supplements_selected"]
    assert sessions[chat_id]["supplements_dosages"][0] == PREDEFINED_SUPPLEMENTS[0]["dosage"]

@patch("telegram_bot.bot.send_msg")
def test_custom_supplement_length_limit(mock_send):
    chat_id = "12345"
    
    sessions[chat_id] = {
        "current_step": "supplements",
        "log_date": "2026-05-28",
        "data": {},
        "supplements_selected": set(),
        "supplements_dosages": {},
        "custom_supplements": [],
        "waiting_for_custom_supplement": True,
        "waiting_for_dosage_of": None,
        "checklist_message_id": 999
    }
    
    # Send a custom supplement with very long name and unit
    long_name = "b" * 120
    long_unit = "u" * 30
    handle_message(chat_id, f"{long_name} 400 {long_unit}")
    
    assert len(sessions[chat_id]["custom_supplements"]) == 1
    item = sessions[chat_id]["custom_supplements"][0]
    assert item["name"] == "b" * 100
    assert item["dosage"] == 400.0
    assert item["unit"] == "u" * 20

@patch("telegram_bot.bot.send_msg")
@patch("requests.post")
def test_sleep_time_formatting(mock_post, mock_send):
    chat_id = "12345"
    
    sessions[chat_id] = {
        "log_date": "2026-05-28",
        "data": {
            "sleep_start_time": "23:30",
            "sleep_end_time": "7:00"
        },
        "supplements_selected": set(),
        "supplements_dosages": {},
        "custom_supplements": []
    }
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response
    
    submit_log_session(chat_id)
    
    assert mock_post.call_count == 2
    args, kwargs = mock_post.call_args_list[0]
    payload = kwargs["json"]
    
    assert payload["sleep_start"] == "2026-05-28T23:30:00"
    assert payload["sleep_end"] == "2026-05-28T07:00:00"

