from dotenv import load_dotenv
import os

# Load environment variables from the .env file, if present
load_dotenv()

# Telegram API credentials obtained from https://my.telegram.org/auth
API_ID = int(os.getenv("API_ID", 22884130))  # Your Telegram API ID
API_HASH = os.getenv("API_HASH", "a69e8b16dac958f1bd31eee360ec53fa")  # Your Telegram API Hash

# List of Telegram bot tokens used for file upload/download operations
BOT_TOKENS = os.getenv("BOT_TOKENS", "8203126938:AAFikj0DM2N0YvZM1muJl7G2Rd1YFGwHRSw").strip(", ").split(",")
BOT_TOKENS = [token.strip() for token in BOT_TOKENS if token.strip() != ""]

# List of Premium Telegram Account Pyrogram String Sessions used for file upload/download operations
STRING_SESSIONS = os.getenv("STRING_SESSIONS", "BQJG4TMALOQnGJ9C2UMrInLL-uteYYn_iTvYNgqlVE4v_LTR9zu9u8CGxslnAQQU4jFaK-AYxlBsiDiobCp8BdpmAyQEs1C_LEY5NNrf6P2zGVB316DXNC02eqa08vWtTBCB2pHHRuzjmRlVr8f2wAl7WHVtkULS4DmbukiJExKXZUKthsu5jyDVyROgvDM3ncveSQoVAK6hJP6CJxQYUZ2fprhETWEcvsc9JJzauDyf2XVf9ntQehxTRo8tMLR28fjGTu_vEbl9QMS6e4t_WLeQs5lkkUeoU4xmD-01AisFDCqEXnsIOCyzm-ESCDJVaXk8D1yuv7-HTVRwEmuXoCYxmxV7cQAAAAHuZAbAAA").strip(", ").split(",")
STRING_SESSIONS = [
    session.strip() for session in STRING_SESSIONS if session.strip() != ""
]

# Chat ID of the Telegram storage channel where files will be stored
STORAGE_CHANNEL = int(os.getenv("STORAGE_CHANNEL", "-1003402540259"))  # Your storage channel's chat ID

# Message ID of a file in the storage channel used for storing database backups
DATABASE_BACKUP_MSG_ID = int(
    os.getenv("DATABASE_BACKUP_MSG_ID", "33")
)  # Message ID for database backup

# Password used to access the website's admin panel
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")  # Default to "admin" if not set

# Determine the maximum file size (in bytes) allowed for uploading to Telegram
# 1.98 GB if no premium sessions are provided, otherwise 3.98 GB
if len(STRING_SESSIONS) == 0:
    MAX_FILE_SIZE = 1.98 * 1024 * 1024 * 1024  # 2 GB in bytes
else:
    MAX_FILE_SIZE = 3.98 * 1024 * 1024 * 1024  # 4 GB in bytes

# Database backup interval in seconds. Backups will be sent to the storage channel at this interval
DATABASE_BACKUP_TIME = int(
    os.getenv("DATABASE_BACKUP_TIME", 60)
)  # Default to 60 seconds

# Time delay in seconds before retrying after a Telegram API floodwait error
SLEEP_THRESHOLD = int(os.getenv("SLEEP_THRESHOLD", 60))  # Default to 60 seconds

# Domain to auto-ping and keep the website active
WEBSITE_URL = os.getenv("WEBSITE_URL", "https://inc-calla-nbhi763-7e58a367.koyeb.app")


# For Using TG Drive's Bot Mode

# Main Bot Token for TG Drive's Bot Mode
MAIN_BOT_TOKEN = os.getenv("MAIN_BOT_TOKEN", "8203126938:AAFikj0DM2N0YvZM1muJl7G2Rd1YFGwHRSw")
if MAIN_BOT_TOKEN.strip() == "":
    MAIN_BOT_TOKEN = None

# List of Telegram User IDs who have admin access to the bot mode
TELEGRAM_ADMIN_IDS = os.getenv("TELEGRAM_ADMIN_IDS", "8304839512").strip(", ").split(",")
TELEGRAM_ADMIN_IDS = [int(id) for id in TELEGRAM_ADMIN_IDS if id.strip() != ""]
