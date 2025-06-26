import os
import json
import shutil
import time
from datetime import datetime, timedelta
from threading import Lock  # Added for synchronized file access

# File to save and load settings
SETTINGS_FILE = "setting.json"

# Global settings for scheduled tasks
scheduled_files = []
lock = Lock()  # Thread-safe lock for file access


def load_settings():
    """Load settings from `setting.json`."""
    global scheduled_files
    if os.path.exists(SETTINGS_FILE):
        with lock:  # Ensure safe access
            try:
                with open(SETTINGS_FILE, "r") as f:
                    scheduled_files = json.load(f)
            except Exception as e:
                print(f"Error loading settings file: {e}")


def save_settings_safely():
    """Save the updated schedule back to `settings.json`."""
    if len(scheduled_files) == 0:  # Ensure we don't save an empty list unnecessarily
        print("No scheduled files in memory. Skipping save operation.")
        return

    try:
        with lock:  # Ensure safe access
            with open(SETTINGS_FILE, "w") as f:
                json.dump(scheduled_files, f, indent=4)
    except Exception as e:
        print(f"Failed to save settings: {e}")


def calculate_next_copy_time(interval, hours, minutes):
    """Calculate the next copy time based on the interval."""
    now = datetime.now()
    today_target = now.replace(hour=hours, minute=minutes, second=0, microsecond=0)

    if interval == "Daily":
        next_time = today_target if now < today_target else today_target + timedelta(days=1)
    elif interval == "Weekly":
        next_time = today_target if now < today_target else today_target + timedelta(weeks=1)
    elif interval == "Monthly":
        next_time = today_target if now < today_target else today_target + timedelta(days=30)
    elif interval == "Hourly":
        next_time = now + timedelta(hours=1)
    else:  # Custom Interval
        next_time = today_target if now < today_target else today_target + timedelta(hours=hours, minutes=minutes)

    return next_time


def copy_files(entry):
    """Copy only new or updated files from the source to the destination."""
    try:
        source = entry["source"]
        destination = entry["destination"]

        if not os.path.exists(source):
            print(f"Source folder '{source}' does not exist. Skipping...")
            return False

        if not os.path.exists(destination):
            os.makedirs(destination)  # Create destination if it doesn't exist

        for item in os.listdir(source):
            src_path = os.path.join(source, item)
            dst_path = os.path.join(destination, item)

            if os.path.isdir(src_path):
                # Recursively copy subdirectories
                shutil.copytree(src_path, dst_path, dirs_exist_ok=True)  # `dirs_exist_ok` avoids overwriting an existing folder
            else:
                # Check if the file already exists in the destination
                if os.path.exists(dst_path):
                    # Compare modification times
                    src_mtime = os.path.getmtime(src_path)
                    dst_mtime = os.path.getmtime(dst_path)
                    if src_mtime <= dst_mtime:
                        continue  # Skip copying if the destination file is newer or the same
                shutil.copy(src_path, dst_path)  # Copy the file to the destination

        print(f"Copied new or updated files from '{source}' to '{destination}'.")
        return True

    except Exception as e:
        print(f"Error during file copy: {e}")
        return False


def update_next_copy_time(entry):
    """Update the next copy time for the entry."""
    hours = entry["hours"]
    minutes = entry["minutes"]
    interval = entry["interval"]

    next_copy_time = calculate_next_copy_time(interval, hours, minutes)
    entry["next_copy_time"] = next_copy_time.strftime("%Y-%m-%d %H:%M:%S")


def background_scheduler():
    """Start the background scheduler loop."""
    while True:
        # Reload settings to allow external edits
        load_settings()

        now = datetime.now()

        # Track whether we made changes to next_copy_time
        has_changes = False

        for entry in scheduled_files:
            try:
                next_copy_time = datetime.strptime(entry["next_copy_time"], "%Y-%m-%d %H:%M:%S")

                # Check if the next copy time has passed
                if now >= next_copy_time:
                    print(f"Missed copy time for '{entry['project_name']}' at {next_copy_time}. Processing now.")
                    copy_success = copy_files(entry)

                    if copy_success:
                        update_next_copy_time(entry)  # Update the next copy time
                        has_changes = True
                    else:
                        print("Skipping update for next copy time due to an error.")
            except Exception as e:
                print(f"Error processing scheduled entry '{entry['project_name']}': {e}")

        # Only save updates if changes were made
        if has_changes:
            save_settings_safely()

        # Sleep for a short duration before checking again (to reduce CPU usage)
        time.sleep(10)


if __name__ == "__main__":
    print("Waiting for system startup stabilization...")
    time.sleep(30)  # 30-second delay
    print("Background scheduler is now running...")
    background_scheduler()
