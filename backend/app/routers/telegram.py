from fastapi import APIRouter, HTTPException, status, Depends
import os
import httpx
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app import models

router = APIRouter(prefix="/telegram", tags=["Telegram Bot"])

@router.post("/register-chat-id")
def register_chat_id(chat_id: str, db: Session = Depends(get_db)):
    """
    Persists the Telegram Chat ID to the database settings.
    """
    db_setting = db.query(models.SystemSetting).filter(models.SystemSetting.key == "telegram_chat_id").first()
    if db_setting:
        db_setting.value = chat_id
    else:
        db_setting = models.SystemSetting(key="telegram_chat_id", value=chat_id)
        db.add(db_setting)
    db.commit()
    return {"status": "success", "chat_id": chat_id}

@router.get("/chat-id")
def get_telegram_chat_id(db: Session = Depends(get_db)):
    """
    Retrieves the configured Telegram Chat ID.
    """
    db_setting = db.query(models.SystemSetting).filter(models.SystemSetting.key == "telegram_chat_id").first()
    chat_id = db_setting.value if db_setting else os.getenv("TELEGRAM_CHAT_ID")
    if not chat_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Telegram Chat ID is not configured. Send /start to the bot to register."
        )
    return {"chat_id": chat_id}

@router.post("/test-reminder")
def send_test_reminder(db: Session = Depends(get_db)):
    """
    Sends a test push notification to the configured Telegram Chat ID.
    Useful to verify that the bot token and chat ID are working.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    # Check DB first, then env
    db_setting = db.query(models.SystemSetting).filter(models.SystemSetting.key == "telegram_chat_id").first()
    chat_id = db_setting.value if db_setting else os.getenv("TELEGRAM_CHAT_ID")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="TELEGRAM_BOT_TOKEN is not configured in the environment variables."
        )
    if not chat_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="TELEGRAM_CHAT_ID is not configured. Please start the bot and send /start or set the environment variable."
        )
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": "🔔 **Personal Analytics Connection Active!**\n\nThis is a test notification from your self-hosted Personal Analytics System. Your Telegram integration is fully working! 🚀",
        "parse_mode": "Markdown"
    }
    
    try:
        response = httpx.post(url, json=payload, timeout=10.0)
        response.raise_for_status()
        return {"status": "success", "detail": "Test message sent successfully!"}
    except httpx.HTTPStatusError as e:
        # Handle specific telegram API errors (e.g. chat not found, token invalid)
        try:
            err_detail = e.response.json().get("description", str(e))
        except Exception:
            err_detail = str(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Telegram API Error: {err_detail}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to communicate with Telegram: {str(e)}"
        )

