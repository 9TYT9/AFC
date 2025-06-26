import os
import json
import shutil
import subprocess
from tkinter import *
from tkinter import filedialog, messagebox
from datetime import datetime, timedelta
from threading import Lock  # Added for synchronization

# File to save and load settings
SETTINGS_FILE = "setting.json"

# Global settings
scheduled_files = []
lock = Lock()  # Thread-safe lock for file access


def save_settings_safely():
    """Save project settings safely using a lock."""
    try:
        with lock:  # Ensure only one operation at a time
            with open(SETTINGS_FILE, "w") as f:
                json.dump(scheduled_files, f, indent=4)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save settings: {e}")


def load_settings():
    """Load settings from `setting.json`."""
    global scheduled_files
    if os.path.exists(SETTINGS_FILE):
        with lock:  # Ensure safe access
            with open(SETTINGS_FILE, "r") as f:
                scheduled_files = json.load(f)


def calculate_next_copy_time(interval, hours, minutes):
    """Calculate the next copy time based on the user-defined interval."""
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
    else:  # Custom interval
        next_time = today_target if now < today_target else today_target + timedelta(hours=hours, minutes=minutes)
    return next_time


def start_background_scheduler():
    """Start the background scheduler process."""
    scheduler_script = "background_scheduler.py"

    # Start the scheduler in the background
    subprocess.Popen(["python", scheduler_script], shell=True)


def update_settings_list():
    """Update the display list with scheduled entries."""
    setting_list.delete(0, END)
    for idx, entry in enumerate(scheduled_files):
        setting_list.insert(
            END,
            f"{idx + 1}. Project: {entry['project_name']} | Next Copy: {entry['next_copy_time']}"
        )


def save_entry_to_settings():
    """Save a new or updated entry."""
    source = src_folder.get()
    destination = dest_folder.get()
    project_name = file_name_var.get()
    interval = interval_var.get()
    try:
        hours = int(hour_var.get())
        minutes = int(minute_var.get())
    except ValueError:
        messagebox.showerror("Error", "Invalid hours or minutes value")
        return

    if not source or not destination or not project_name:
        messagebox.showerror("Error", "All fields are required!")
        return

    next_copy_time = calculate_next_copy_time(interval, hours, minutes)

    entry = {
        "source": source,
        "destination": destination,
        "project_name": project_name,
        "interval": interval,
        "hours": hours,
        "minutes": minutes,
        "next_copy_time": next_copy_time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    selected_idx = setting_list.curselection()
    if selected_idx:
        scheduled_files[selected_idx[0]] = entry  # Update existing entry
    else:
        scheduled_files.append(entry)  # Add new entry

    save_settings_safely()
    update_settings_list()
    messagebox.showinfo("Success", "Entry saved successfully!")

    # Start the background scheduler
    start_background_scheduler()


def delete_entry_from_settings():
    """Delete the selected entry."""
    selected_idx = setting_list.curselection()
    if selected_idx:
        del scheduled_files[selected_idx[0]]
        save_settings_safely()
        update_settings_list()
        messagebox.showinfo("Success", "Entry deleted successfully!")
    else:
        messagebox.showerror("Error", "Please select an entry to delete.")


def edit_entry_from_settings():
    """Load an existing entry into the input fields for editing."""
    selected_idx = setting_list.curselection()
    if selected_idx:
        entry = scheduled_files[selected_idx[0]]
        src_folder.set(entry["source"])
        dest_folder.set(entry["destination"])
        file_name_var.set(entry["project_name"])
        interval_var.set(entry["interval"])
        hour_var.set(str(entry["hours"]))
        minute_var.set(str(entry["minutes"]))
    else:
        messagebox.showerror("Error", "Please select an entry to edit.")

def clear_inputs():
    """Clear the input fields."""
    src_folder.set("")
    dest_folder.set("")
    file_name_var.set("")
    interval_var.set("Daily")
    hour_var.set("0")
    minute_var.set("0")

def add_new_entry():
    """Clear input fields to allow adding a new entry."""
    clear_inputs()
    messagebox.showinfo("Add Entry", "Cleared input fields. Ready to add a new entry.")

def move_entry_up():
    """Move the selected entry up in the list."""
    selected_idx = setting_list.curselection()
    if selected_idx and selected_idx[0] > 0:
        idx = selected_idx[0]
        # Swap the selected entry with the one above
        scheduled_files[idx], scheduled_files[idx - 1] = scheduled_files[idx - 1], scheduled_files[idx]
        update_settings_list()  # Update the display of the Listbox
        setting_list.select_set(idx - 1)  # Highlight the new position
        setting_list.activate(idx - 1)  # Set the active focus
        setting_list.see(idx - 1)  # Ensure the moved item is visible
        save_settings()  # Save changes to the file for persistence
    else:
        messagebox.showwarning("Warning", "Cannot move the selected entry up.")

def move_entry_down():
    """Move the selected entry down in the list."""
    selected_idx = setting_list.curselection()
    if selected_idx and selected_idx[0] < len(scheduled_files) - 1:
        idx = selected_idx[0]
        # Swap the selected entry with the one below
        scheduled_files[idx], scheduled_files[idx + 1] = scheduled_files[idx + 1], scheduled_files[idx]
        update_settings_list()  # Update the display of the Listbox
        setting_list.select_set(idx + 1)  # Highlight the new position
        setting_list.activate(idx + 1)  # Set the active focus
        setting_list.see(idx + 1)  # Ensure the moved item is visible
        save_settings()  # Save changes to the file for persistence
    else:
        messagebox.showwarning("Warning", "Cannot move the selected entry down.")

# Initialize Tkinter Application
app = Tk()
app.title("Automated File Copier")
app.geometry("600x600")  # Adjusted window dimensions
app.resizable(False, False)  # Fixed window size
app.configure(bg="#f0f0f0")  # Set background color

# UI Components
src_folder = StringVar()
dest_folder = StringVar()
file_name_var = StringVar()
interval_var = StringVar(value="Daily")
hour_var = StringVar(value="0")
minute_var = StringVar(value="0")

# Create sections for better organization
frame_file_settings = LabelFrame(app, text="File Settings", padx=10, pady=10, bg="#ffffff", fg="#000000", font=("Arial", 10, "bold"))
frame_file_settings.grid(row=0, column=0, columnspan=4, padx=10, pady=10, sticky=W+E)

Label(frame_file_settings, text="Source Folder:", bg="#ffffff").grid(row=0, column=0, padx=5, pady=5, sticky=W)
Entry(frame_file_settings, textvariable=src_folder, width=40).grid(row=0, column=1, padx=5, pady=5)
Button(frame_file_settings, text="Browse", command=lambda: src_folder.set(filedialog.askdirectory()), bg="#d0e1f9", fg="#00007f", width=10).grid(row=0, column=2, padx=5, pady=5)

Label(frame_file_settings, text="Destination Folder:", bg="#ffffff").grid(row=1, column=0, padx=5, pady=5, sticky=W)
Entry(frame_file_settings, textvariable=dest_folder, width=40).grid(row=1, column=1, padx=5, pady=5)
Button(frame_file_settings, text="Browse", command=lambda: dest_folder.set(filedialog.askdirectory()), bg="#d0e1f9", fg="#00007f", width=10).grid(row=1, column=2, padx=5, pady=5)

Label(frame_file_settings, text="Project Name:", bg="#ffffff").grid(row=2, column=0, padx=5, pady=5, sticky=W)
Entry(frame_file_settings, textvariable=file_name_var, width=40).grid(row=2, column=1, padx=5, pady=5)

Label(frame_file_settings, text="Interval:", bg="#ffffff").grid(row=3, column=0, padx=5, pady=5, sticky=W)
OptionMenu(frame_file_settings, interval_var, "Daily", "Weekly", "Monthly", "Hourly", "Custom").grid(row=3, column=1, padx=5, pady=5, sticky=W)

# Row for Hour and Minutes Together (Compact Layout)
Label(frame_file_settings, text="Time:", bg="#ffffff").grid(row=4, column=0, padx=5, pady=5, sticky=W)
OptionMenu(frame_file_settings, hour_var, *[str(h) for h in range(24)]).grid(row=4, column=1, padx=2, pady=5, sticky=W)  # Minimal padding
Entry(frame_file_settings, textvariable=minute_var, width=5).grid(row=4, column=2, padx=2, pady=5, sticky=W)  # Closer alignment with minimal width

# Button section and Scheduled File Entries remain unchanged
button_frame = Frame(app, bg="#f0f0f0")
button_frame.grid(row=1, column=0, columnspan=4, pady=10)

Button(button_frame, text="Add Entry", command=add_new_entry, width=15, bg="#d0e1f9", fg="#00007f").grid(row=0, column=0, padx=5, pady=5)
Button(button_frame, text="Save Entry", command=save_entry_to_settings, width=15, bg="#d0e1f9", fg="#00007f").grid(row=0, column=1, padx=5, pady=5)
Button(button_frame, text="Edit Entry", command=edit_entry_from_settings, width=15, bg="#d0e1f9", fg="#00007f").grid(row=0, column=2, padx=5, pady=5)
Button(button_frame, text="Delete Entry", command=delete_entry_from_settings, width=15, bg="#d0e1f9", fg="#00007f").grid(row=0, column=3, padx=5, pady=5)
Button(button_frame, text="Move Up", command=move_entry_up, width=15, bg="#d0e1f9", fg="#00007f").grid(row=1, column=1, padx=5, pady=5)
Button(button_frame, text="Move Down", command=move_entry_down, width=15, bg="#d0e1f9", fg="#00007f").grid(row=1, column=2, padx=5, pady=5)
Button(button_frame, text="Clear Inputs", command=clear_inputs, width=15, bg="#d0e1f9", fg="#00007f").grid(row=1, column=0, padx=5, pady=5)

Label(app, text="Scheduled File Entries:", bg="#f0f0f0", font=("Arial", 10, "bold")).grid(row=2, column=0, padx=10, pady=10, sticky=W)

setting_list = Listbox(app, width=80, height=12, bg="#ffffff", fg="#000000", font=("Arial", 10))
setting_list.grid(row=3, column=0, columnspan=4, padx=10, pady=5)

# Load settings
load_settings()
update_settings_list()

app.mainloop()
