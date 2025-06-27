import os
import json
import shutil
import time
from datetime import datetime, timedelta
from threading import Lock  # Added for synchronized file access

# File to save and load settings
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "setting.json")

# Global settings for scheduled tasks
scheduled_files = []
lock = Lock()  # Thread-safe lock for file access


def load_settings():
    """Load settings from `setting.json`."""
    global scheduled_files
    if os.path.exists(SETTINGS_FILE):
        with lock:
            try:
                with open(SETTINGS_FILE, "r") as f:
                    scheduled_files = json.load(f)
            except Exception as e:
                print(f"Error loading settings file: {e}")


def save_settings_safely():
    """Save the updated schedule."""
    try:
        with lock:
            with open(SETTINGS_FILE, "w") as f:
                json.dump(scheduled_files, f, indent=4)
    except Exception as e:
        print(f"Error saving settings: {e}")


def calculate_next_copy_time(interval, hours, minutes):
    """Calculate the next copy time."""
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
    else:
        next_time = today_target if now < today_target else today_target + timedelta(hours=hours, minutes=minutes)

    return next_time


def copy_files(entry):
    """Copy files."""
    try:
        source = entry["source"]
        destination = entry["destination"]

        if not os.path.exists(source):
            return False

        if not os.path.exists(destination):
            os.makedirs(destination)  # Create destination

        for item in os.listdir(source):
            src_path = os.path.join(source, item)
            dst_path = os.path.join(destination, item)
            if os.path.isfile(src_path):
                shutil.copy2(src_path, dst_path)

        return True
    except Exception:
        return False


def update_next_copy_time(entry):
    """Update next copy time after execution."""
    hours = entry["hours"]
    minutes = entry["minutes"]
    interval = entry["interval"]

    next_copy_time = calculate_next_copy_time(interval, hours, minutes)
    entry["next_copy_time"] = next_copy_time.strftime("%Y-%m-%d %H:%M:%S")


def background_scheduler():
    """Run the background scheduler in a loop."""
    while True:
        load_settings()
        now = datetime.now()

        for entry in scheduled_files:
            try:
                next_copy_time = datetime.strptime(entry["next_copy_time"], "%Y-%m-%d %H:%M:%S")
                if now >= next_copy_time:
                    if copy_files(entry):
                        update_next_copy_time(entry)
            except Exception:
                continue

        save_settings_safely()
        time.sleep(10)  # Sleep before rechecking


if __name__ == "__main__":
    background_scheduler()
