import asyncio
import os
import shutil
import time
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import config
from utils.logger import Logger
from pathlib import Path
import zipfile

logger = Logger(__name__)

START_CMD = """🚀 **Welcome To TG Drive's Bot Mode**

You can use this bot to upload files to your TG Drive website directly instead of doing it from website.

🗄 **Commands:**
/set_folder - Set folder for file uploads
/current_folder - Check current folder
/zip - Start zip mode to combine multiple files
/done - Finish zip and upload
/cancel - Cancel current zip session

📤 **How To Upload Files:** Send a file to this bot and it will be uploaded to your TG Drive website. You can also set a folder for file uploads using /set_folder command.

🗜 **Zip Mode:** Use /zip to start collecting files, send multiple files, then use /done to create and upload a zip archive.
"""

SET_FOLDER_PATH_CACHE = {}
DRIVE_DATA = None
BOT_MODE = None
ZIP_SESSIONS = {}

session_cache_path = Path(f"./cache")
session_cache_path.parent.mkdir(parents=True, exist_ok=True)

main_bot = Client(
    name="main_bot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.MAIN_BOT_TOKEN,
    sleep_threshold=config.SLEEP_THRESHOLD,
    workdir=session_cache_path,
)

async def progress_bar(current, total, status_msg, start_time, action="Downloading"):
    """Updates progress bar for file operations"""
    if not hasattr(progress_bar, "last_update"):
        progress_bar.last_update = 0
    
    if time.time() - progress_bar.last_update < 3:
        return

    progress_bar.last_update = time.time()
    percentage = current * 100 / total
    elapsed_time = round(time.time() - start_time)
    
    try:
        await status_msg.edit_text(
            f"⚡ **{action} Fɪʟᴇs...**\n\n"
            f"📊 **Pʀᴏɢʀᴇss:** {percentage:.1f}%\n"
            f"⏱ **Eʟᴀᴘsᴇᴅ:** {elapsed_time}s"
        )
    except:
        pass

def create_zip_file(source_dir, output_zip):
    """Create a zip file from all files in source_dir"""
    if not os.path.exists(source_dir):
        raise Exception(f"Source directory does not exist: {source_dir}")
        
    files_to_zip = []
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            file_path = os.path.join(root, file)
            if os.path.isfile(file_path):
                files_to_zip.append(file_path)
    
    if not files_to_zip:
        raise Exception("No files found in source directory to zip")
    
    logger.info(f"Creating zip with {len(files_to_zip)} files: {files_to_zip}")
    
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in files_to_zip:
            arcname = os.path.basename(file_path)
            zipf.write(file_path, arcname=arcname)
            logger.info(f"Added to zip: {arcname}")
    
    if not os.path.exists(output_zip):
        raise Exception("Failed to create zip file")
    
    zip_size = os.path.getsize(output_zip)
    if zip_size < 100:
        raise Exception(f"Zip file is too small ({zip_size} bytes)")
    
    logger.info(f"Zip created successfully: {output_zip} ({zip_size} bytes)")
    return output_zip

async def send_drive_links(message: Message, file_name, file_size, storage_msg_id):
    global DRIVE_DATA, BOT_MODE
    DRIVE_DATA.new_file(
        BOT_MODE.current_folder,
        file_name,
        storage_msg_id,
        file_size,
    )
    if BOT_MODE.current_folder == "/":
        directory_folder = DRIVE_DATA.contents["/"]
    else:
        paths = BOT_MODE.current_folder.strip("/").split("/")
        directory_folder = DRIVE_DATA.contents["/"]
        for path in paths:
            directory_folder = directory_folder.contents[path]
    file_obj = None
    for item_id, item in directory_folder.contents.items():
        if hasattr(item, 'file_id') and item.file_id == storage_msg_id:
            file_obj = item
            break
    if not file_obj:
        logger.error("Failed to find created file object")
        await message.reply_text("❌ Error: Failed to upload file")
        return
    website_url = config.WEBSITE_URL.rstrip('/')
    file_path = f"{BOT_MODE.current_folder}/{file_obj.id}".replace('//', '/')
    download_link = f"{website_url}/file?path={file_path}"
    file_name_lower = (file_name or "file").lower()
    is_video = any(file_name_lower.endswith(ext) for ext in ['.mp4', '.mkv', '.webm', '.mov', '.avi', '.ts', '.ogv'])
    file_size_mb = file_size / (1024 * 1024)
    if file_size_mb >= 1024:
        size_str = f"{file_size_mb / 1024:.2f} GB"
    else:
        size_str = f"{file_size_mb:.2f} MB"
    response_text = f"✨ **Yᴏᴜʀ Lɪɴᴋs ᴀʀᴇ Rᴇᴀᴅʏ!** ✨\n\n"
    response_text += f"> **{file_name}**\n\n"
    response_text += f"📁 **Fɪʟᴇ Sɪᴢᴇ:** {size_str}\n\n"
    response_text += f"🚀 **Dᴏᴡɴʟᴏᴀᴅ Lɪɴᴋ:**\n{download_link}"
    if is_video:
        stream_link = f"{website_url}/stream?url={download_link}"
        response_text += f"\n\n🖥️ **Sᴛʀᴇᴀᴍ Lɪɴᴋ:**\n{stream_link}"
    response_text += f"\n\n⌛️ **Nᴏᴛᴇ: Lɪɴᴋs ʀᴇᴍᴀɪɴ ᴀᴄᴛɪᴠᴇ ᴡʜɪʟᴇ ᴛʜᴇ ʙᴏᴛ ɪs ʀᴜɴɴɪɴɢ ᴀɴᴅ ᴛʜᴇ ғɪʟᴇ ɪs ᴀᴄᴄᴇssɪʙʟᴇ.**"
    buttons = []
    if is_video:
        stream_link = f"{website_url}/stream?url={download_link}"
        buttons.append([
            InlineKeyboardButton("📺 sᴛʀᴇᴀᴍ", url=stream_link),
            InlineKeyboardButton("🚀 ᴅᴏᴡɴʟᴏᴀᴅ", url=download_link)
        ])
    else:
        buttons.append([
            InlineKeyboardButton("🚀 ᴅᴏᴡɴʟᴏᴀᴅ", url=download_link)
        ])
    await message.reply_text(
        response_text,
        reply_markup=InlineKeyboardMarkup(buttons) if buttons else None,
        disable_web_page_preview=True
    )

@main_bot.on_message(
    filters.command(["start", "help"])
    & filters.private
    & filters.user(config.TELEGRAM_ADMIN_IDS),
)
async def start_handler(client: Client, message: Message):
    await message.reply_text(START_CMD)

@main_bot.on_message(
    filters.command("zip")
    & filters.private
    & filters.user(config.TELEGRAM_ADMIN_IDS),
)
async def zip_cmd_handler(client: Client, message: Message):
    ZIP_SESSIONS[message.from_user.id] = []
    await message.reply_text("🗂 **Zɪᴘ Mᴏᴅᴇ Eɴᴀʙʟᴇᴅ**\n\nSend files to add them to the queue. Type /done to zip or /cancel to stop.")

@main_bot.on_message(
    filters.command("cancel")
    & filters.private
    & filters.user(config.TELEGRAM_ADMIN_IDS),
)
async def cancel_handler(client: Client, message: Message):
    if message.from_user.id in ZIP_SESSIONS:
        del ZIP_SESSIONS[message.from_user.id]
        await message.reply_text("❌ Zip session cancelled.")
    else:
        await message.reply_text("⚠️ No active zip session.")

@main_bot.on_message(
    filters.command("done")
    & filters.private
    & filters.user(config.TELEGRAM_ADMIN_IDS),
)
async def done_handler(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in ZIP_SESSIONS or not ZIP_SESSIONS[user_id]:
        return await message.reply_text("⚠️ Qᴜᴇᴜᴇ ɪs ᴇᴍᴘᴛʏ. Usᴇ /zip ᴛᴏ sᴛᴀʀᴛ ᴀ sᴇssɪᴏɴ ᴀɴᴅ sᴇɴᴅ ғɪʟᴇs.")
    
    status = await message.reply_text("⏳ **ɪɴɪᴛɪᴀʟɪᴢɪɴɢ ᴢɪᴘ ᴄʀᴇᴀᴛɪᴏɴ...**")
    queue = ZIP_SESSIONS[user_id]
    
    tmp_dir = os.path.join("cache", f"zip_{user_id}_{int(time.time())}")
    zip_name = f"Archive_{int(time.time())}.zip"
    zip_path = os.path.join("cache", zip_name)
    
    # Clean up any existing files
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    if os.path.exists(zip_path):
        os.remove(zip_path)
        
    os.makedirs(tmp_dir, exist_ok=True)
    logger.info(f"Created temp directory: {tmp_dir}")
    
    try:
        downloaded_count = 0
        for i, msg in enumerate(queue):
            try:
                start_t = time.time()
                await status.edit_text(f"📥 **ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ ғɪʟᴇ {i+1}/{len(queue)}...**")
                
                file = msg.document or msg.video or msg.audio or msg.photo or msg.sticker
                if not file:
                    logger.warning(f"Message {i+1} has no downloadable file, skipping")
                    continue
                
                file_name = getattr(file, 'file_name', None)
                if not file_name:
                    
                    ext = ""
                    if msg.photo:
                        ext = ".jpg"
                    elif msg.video:
                        ext = ".mp4"
                    elif msg.audio:
                        ext = ".mp3"
                    elif msg.sticker:
                        ext = ".webp"
                    file_name = f"file_{i+1}{ext}"
                
                logger.info(f"Downloading file {i+1}: {file_name}")
                
                downloaded_path = await client.download_media(
                    msg,
                    file_name=tmp_dir + "/", 
                    progress=progress_bar,
                    progress_args=(status, start_t, "Downloading")
                )
                
                if downloaded_path and os.path.exists(downloaded_path):
                    file_size = os.path.getsize(downloaded_path)
                    downloaded_count += 1
                    logger.info(f"✅ Downloaded: {downloaded_path} ({file_size} bytes)")
                    
                    final_path = os.path.join(tmp_dir, file_name)
                    if downloaded_path != final_path and not os.path.exists(final_path):
                        shutil.move(downloaded_path, final_path)
                        logger.info(f"Moved to: {final_path}")
                else:
                    logger.error(f"❌ Download failed for file {i+1}")
                    
            except Exception as e:
                logger.error(f"Error downloading file {i+1}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                continue
        
        if downloaded_count == 0:
            raise Exception("No files were downloaded successfully")
        
        files_in_dir = os.listdir(tmp_dir)
        logger.info(f"Files in temp directory ({len(files_in_dir)}): {files_in_dir}")
        
        if not files_in_dir:
            raise Exception("Temp directory is empty after downloads")
        
        total_size = 0
        for fname in files_in_dir:
            fpath = os.path.join(tmp_dir, fname)
            fsize = os.path.getsize(fpath)
            total_size += fsize
            logger.info(f"File: {fname} - Size: {fsize} bytes")
        
        logger.info(f"Total size of all files: {total_size} bytes")
        
        await status.edit_text(f"🗜 **Creating zip archive from {downloaded_count} files...**")
        
        await asyncio.to_thread(create_zip_file, tmp_dir, zip_path)
        
        if not os.path.exists(zip_path):
            raise Exception("Zip file was not created")
        
        zip_size = os.path.getsize(zip_path)
        logger.info(f"✅ Final zip: {zip_path} ({zip_size} bytes)")
        
        await status.edit_text("📤 **ᴜᴘʟᴏᴀᴅɪɴɢ ᴢɪᴘ ᴛᴏ TG Dʀɪᴠᴇ...**")
        
        # Upload to storage channel
        storage_msg = await client.send_document(
            config.STORAGE_CHANNEL, 
            zip_path,
            caption=f"📦 Zip Archive - {downloaded_count} files ({zip_size / (1024*1024):.2f} MB)"
        )
        
        await send_drive_links(message, zip_name, zip_size, storage_msg.id)
        await status.delete()
        
    except Exception as e:
        logger.error(f"❌ Error in zip creation: {e}")
        import traceback
        logger.error(traceback.format_exc())
        await status.edit_text(f"❌ **Error:** {str(e)}")
    finally:
        
        if user_id in ZIP_SESSIONS:
            del ZIP_SESSIONS[user_id]
        if os.path.exists(tmp_dir):
            try:
                shutil.rmtree(tmp_dir)
                logger.info(f"🧹 Cleaned up temp directory: {tmp_dir}")
            except Exception as e:
                logger.error(f"Error cleaning up temp dir: {e}")
        if os.path.exists(zip_path):
            try:
                os.remove(zip_path)
                logger.info(f"🧹 Cleaned up zip file: {zip_path}")
            except Exception as e:
                logger.error(f"Error cleaning up zip file: {e}")

@main_bot.on_message(
    filters.command("set_folder")
    & filters.private
    & filters.user(config.TELEGRAM_ADMIN_IDS),
)
async def set_folder_handler(client: Client, message: Message):
    global SET_FOLDER_PATH_CACHE, DRIVE_DATA
    while True:
        try:
            folder_name = await message.ask(
                "Send the folder name where you want to upload files\n\n/cancel to cancel",
                timeout=60,
                filters=filters.text,
            )
        except asyncio.TimeoutError:
            await message.reply_text("Timeout\n\nUse /set_folder to set folder again")
            return
        if folder_name.text.lower() == "/cancel":
            await message.reply_text("Cancelled")
            return
        folder_name = folder_name.text.strip()
        search_result = DRIVE_DATA.search_file_folder(folder_name)
        folders = {}
        for item in search_result.values():
            if item.type == "folder":
                folders[item.id] = item
        if len(folders) == 0:
            await message.reply_text(f"No Folder found with name {folder_name}")
        else:
            break
    buttons = []
    folder_cache = {}
    folder_cache_id = len(SET_FOLDER_PATH_CACHE) + 1
    for folder in search_result.values():
        path = folder.path.strip("/")
        folder_path = "/" + ("/" + path + "/" + folder.id).strip("/")
        folder_cache[folder.id] = (folder_path, folder.name)
        buttons.append(
            [
                InlineKeyboardButton(
                    folder.name,
                    callback_data=f"set_folder_{folder_cache_id}_{folder.id}",
                )
            ]
        )
    SET_FOLDER_PATH_CACHE[folder_cache_id] = folder_cache
    await message.reply_text(
        "Select the folder where you want to upload files",
        reply_markup=InlineKeyboardMarkup(buttons),
    )

@main_bot.on_callback_query(
    filters.user(config.TELEGRAM_ADMIN_IDS) & filters.regex(r"set_folder_")
)
async def set_folder_callback(client: Client, callback_query: Message):
    global SET_FOLDER_PATH_CACHE, BOT_MODE
    folder_cache_id, folder_id = callback_query.data.split("_")[2:]
    folder_path_cache = SET_FOLDER_PATH_CACHE.get(int(folder_cache_id))
    if folder_path_cache is None:
        await callback_query.answer("Request Expired, Send /set_folder again")
        await callback_query.message.delete()
        return
    folder_path, name = folder_path_cache.get(folder_id)
    del SET_FOLDER_PATH_CACHE[int(folder_cache_id)]
    BOT_MODE.set_folder(folder_path, name)
    await callback_query.answer(f"Folder Set Successfully To : {name}")
    await callback_query.message.edit(
        f"Folder Set Successfully To : {name}\n\nNow you can send / forward files to me and it will be uploaded to this folder."
    )

@main_bot.on_message(
    filters.command("current_folder")
    & filters.private
    & filters.user(config.TELEGRAM_ADMIN_IDS),
)
async def current_folder_handler(client: Client, message: Message):
    global BOT_MODE
    await message.reply_text(f"Current Folder: {BOT_MODE.current_folder_name}")

@main_bot.on_message(
    filters.private
    & filters.user(config.TELEGRAM_ADMIN_IDS)
    & (
        filters.document
        | filters.video
        | filters.audio
        | filters.photo
        | filters.sticker
    )
)
async def file_handler(client: Client, message: Message):
    global BOT_MODE, DRIVE_DATA
    user_id = message.from_user.id
    if user_id in ZIP_SESSIONS:
        ZIP_SESSIONS[user_id].append(message)
        return await message.reply_text(f"✅ **Fɪʟᴇ ᴀᴅᴅᴇᴅ ᴛᴏ ǫᴜᴇᴜᴇ!** ({len(ZIP_SESSIONS[user_id])})\n\nGɪᴠᴇ /done ᴛᴏ sᴛᴀʀᴛ ᴢɪᴘᴘɪɴɢ ᴏʀ /cancel ᴛᴏ sᴛᴏᴘ ᴢɪᴘᴘɪɴɢ")
    copied_message = await message.copy(config.STORAGE_CHANNEL)
    file = (
        copied_message.document
        or copied_message.video
        or copied_message.audio
        or copied_message.photo
        or copied_message.sticker
    )
    await send_drive_links(message, file.file_name or "file", file.file_size, copied_message.id)

async def start_bot_mode(d, b):
    global DRIVE_DATA, BOT_MODE
    DRIVE_DATA = d
    BOT_MODE = b
    logger.info("Starting Main Bot")
    await main_bot.start()
    await main_bot.send_message(
        config.STORAGE_CHANNEL, "Main Bot Started -> TG Drive's Bot Mode Enabled"
    )
    logger.info("Main Bot Started")
    logger.info("TG Drive's Bot Mode Enabled")
