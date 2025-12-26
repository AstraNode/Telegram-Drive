import os
import zipfile
import time

def create_zip(source_dir, output_zip):
    """
    Create a zip file from all files in source_dir
    """
    if not os.path.exists(source_dir):
        raise Exception(f"Source directory does not exist: {source_dir}")
    
    # Get all files in directory
    files_to_zip = []
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            file_path = os.path.join(root, file)
            files_to_zip.append(file_path)
    
    if not files_to_zip:
        raise Exception("No files found in source directory to zip")
    
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in files_to_zip:
            arcname = os.path.basename(file_path)
            zipf.write(file_path, arcname=arcname)
    
    if not os.path.exists(output_zip):
        raise Exception("Failed to create zip file")
    
    zip_size = os.path.getsize(output_zip)
    if zip_size < 100:
        raise Exception(f"Zip file is too small ({zip_size} bytes)")
    
    return output_zip

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
    
    
                    
                    
