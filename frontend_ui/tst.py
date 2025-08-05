import tkinter as tk
from tkinter import Frame, BOTH, LEFT, RIGHT, Y
import customtkinter as ctk
from PIL import Image, ImageTk
import pystray
import os
import time
import threading

# ===============================
# Global Variables
# ===============================
state = None
window = None
tray_icon = None
content_widgets = {}
current_page = None
max_value = 24  # hours
shutdown_event = threading.Event()


# ===============================
# Graceful Shutdown
# ===============================
def graceful_shutdown():
    """Stop background threads, save state, UI, and tray before exiting."""
    shutdown_event.set()
    time.sleep(0.5)

    # Stop tray
    global tray_icon
    if tray_icon:
        try:
            tray_icon.stop()
        except:
            pass

    # Save final state to DB
    try:
        if state:
            from storage.db import Database  # avoid circular import
            user_db = Database()

            with state.lock:
                today = time.strftime("%Y-%m-%d")
                app_data = state.screentime_per_app.copy()
                screen = state.screen_time
                brk = state.total_break_duration

            user_db.update_daily_state(
                date=today,
                screen_time=screen,
                break_time=brk,
                app_usage_dict=app_data
            )
            print("[+] Final state saved before shutdown.")
    except Exception as e:
        print(f"[!] Failed to save state: {e}")

    # Close window
    if window and window.winfo_exists():
        try:
            window.destroy()
        except:
            pass

    os._exit(0)


# ===============================
# Tray Handling
# ===============================
def on_closing(window):
    """Hide window instead of closing."""
    window.withdraw()
    show_tray_icon(window)


def show_tray_icon(window):
    global tray_icon
    icon_image = Image.open(r"C:\Dev\project_pymonitor\frontend_ui\logo.png")

    def _on_show(icon, item):
        window.deiconify()
        icon.stop()

    def _on_exit(icon, item):
        threading.Thread(target=graceful_shutdown, daemon=True).start()

    menu = pystray.Menu(
        pystray.MenuItem("Show", _on_show),
        pystray.MenuItem("Exit", _on_exit)
    )

    tray_icon = pystray.Icon("PyMonitor", icon_image, "PyMonitor", menu)
    threading.Thread(target=tray_icon.run, daemon=True).start()


# ===============================
# UI Start
# ===============================
def start_ui(shared_state):
    global state, window, content_widgets, right_frame
    state = shared_state

    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    # Window
    window = tk.Tk()
    window.title("PyMonitor")
    window.configure(bg="#222222")
    window.minsize(800, 600)
    window.protocol("WM_DELETE_WINDOW", lambda: on_closing(window))

    # Colors
    blue_color = "#141414"
    hover_color = "#36393B"
    bg_color = "#222222"

    # Main container
    main_container = Frame(window, bg=bg_color)
    main_container.pack(fill=BOTH, expand=True)

    # Sidebar
    left_frame = ctk.CTkFrame(master=main_container, width=210, fg_color=blue_color)
    left_frame.pack(side=LEFT, fill=Y)

    # Content area
    right_frame = Frame(main_container, bg=bg_color)
    right_frame.pack(side=RIGHT, fill=BOTH, expand=True)

    # Hover effects
    def on_enter(e): e.widget.configure(bg=hover_color)
    def on_leave(e): e.widget.configure(bg=blue_color)

    # Nav button factory
    def create_nav_button(parent, text, command=None):
        btn = tk.Button(
            parent, height=2, width=20, text=text, bg=blue_color, fg="white",
            font=("Agency FB", 18), bd=0, activebackground=hover_color,
            activeforeground="#178DED", anchor="w", padx=20, command=command
        )
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    # Load icons
    def create_icon(path, size=(30, 30)):
        img = Image.open(path).resize(size)
        return ImageTk.PhotoImage(img)

    home_icon = create_icon(r"C:\Dev\project_pymonitor\frontend_ui\home.png")
    block_icon = create_icon(r"C:\Dev\project_pymonitor\frontend_ui\block.png")
    history_icon = create_icon(r"C:\Dev\project_pymonitor\frontend_ui\history.png")
    settings_icon = create_icon(r"C:\Dev\project_pymonitor\frontend_ui\settings.png")
    logo_icon = create_icon(r"C:\Dev\project_pymonitor\frontend_ui\logo.png", (80, 80))

    # Content widgets
    def create_content_widgets():
        outer = tk.Frame(right_frame, bg="#e9eae9", height=25)
        filled = tk.Frame(outer, height=25)
        outer2 = tk.Frame(right_frame, bg="#e9eae9", height=25)
        filled2 = tk.Frame(outer2, bg="#e9ff25", height=25)
    
        screen_time_lab = tk.Label(right_frame, font=("Arial Black", 12), bg=bg_color, fg="white")
        screen_time_txt = tk.Label(right_frame, text="Screen time", font=("Agency FB", 20), bg=bg_color, fg="white")
        screen_time_perc_lbl = tk.Label(right_frame, font=("Arial Black", 15), bg=bg_color, fg="white")

        brk_time_label = tk.Label(right_frame, font=("Arial Black", 12), bg=bg_color, fg="white")
        brk_time_txt = tk.Label(right_frame, text="Break time", font=("Agency FB", 20), fg="white", bg=bg_color)
        brk_time_perc_lbl = tk.Label(right_frame, font=("Arial Black", 15), bg=bg_color, fg="white")

        view_usage_btn = ctk.CTkButton(
            right_frame, text="VIEW USAGE", width=160, height=50, font=("Segoe UI", 17, "bold"),
            fg_color="#178DED", hover_color="#1A98FF", text_color="white",
            border_color="black", border_width=2, corner_radius=30
        )

        return {
            'outer': outer, 'filled': filled, 'outer2': outer2, 'filled2': filled2,
            'screen_time_lab': screen_time_lab, 'screen_time_txt': screen_time_txt,
            'screen_time_perc': screen_time_perc_lbl,
            'brk_time_label': brk_time_label, 'brk_time_txt': brk_time_txt,
            'brk_time_perc': brk_time_perc_lbl,
            'view_usage_btn': view_usage_btn
        }

    # Position update
    def update_content_positions(screen_time_value, brk_time_value):
        width = right_frame.winfo_width()
        height = right_frame.winfo_height()

        content_widgets['filled'].configure(width=int(width * 0.5 * (screen_time_value / max_value)))
        content_widgets['filled2'].configure(width=int(width * 0.5 * (brk_time_value / max_value)))

        base_y = height * 0.1
        content_widgets['screen_time_txt'].place(x=width*0.1, y=base_y, anchor="w")
        content_widgets['outer'].place(x=width*0.1, y=base_y+50, width=width*0.5)
        content_widgets['filled'].pack(fill="y", side="left")
        content_widgets['screen_time_perc'].place(x=width*0.1, y=base_y+100, anchor="w")
        content_widgets['screen_time_lab'].place(x=width*0.65, y=base_y+75, anchor="w")

        content_widgets['brk_time_txt'].place(x=width*0.1, y=base_y+150, anchor="w")
        content_widgets['outer2'].place(x=width*0.1, y=base_y+200, width=width*0.5)
        content_widgets['filled2'].pack(fill="y", side="left")
        content_widgets['brk_time_perc'].place(x=width*0.1, y=base_y+250, anchor="w")
        content_widgets['brk_time_label'].place(x=width*0.65, y=base_y+225, anchor="w")

        content_widgets['view_usage_btn'].place(x=width*0.7, y=height*0.8)

    # UI update loop
    def update_ui():
        if shutdown_event.is_set() or current_page != "home" or state is None:
            return

        filled_widget = content_widgets.get('filled')
        filled2_widget = content_widgets.get('filled2')
        if not (filled_widget and filled_widget.winfo_exists()):
            return
        if not (filled2_widget and filled2_widget.winfo_exists()):
            return

        with state.lock:
            snapshot = {
                "screen_time": state.screen_time,
                "break_time": state.total_break_duration
            }

        # After releasing lock, do all UI math from snapshot
        screen_time_value = snapshot["screen_time"] / 3600
        brk_time_value = snapshot["break_time"] / 3600

        screen_time_hours = int(screen_time_value)
        screen_time_mins = int((screen_time_value % 1) * 60)
        screen_perc = (screen_time_value / max_value) * 100

        brk_time_hrs = int(brk_time_value)
        brk_time_mins = int((brk_time_value % 1) * 60)
        brk_perc = (brk_time_value / max_value) * 100

        screen_color = "#3b953a" if screen_perc < 30 else "#3C73BB" if screen_perc < 70 else "#8c1515"
        brk_color = "#ff0000" if brk_perc < 10 else "#ff8000" if brk_perc < 20 else "#ffff00" if brk_perc < 30 else "#00ff00" if brk_perc < 50 else "#3C73BB"

        content_widgets['filled'].configure(bg=screen_color)
        content_widgets['filled2'].configure(bg=brk_color)

        content_widgets['screen_time_lab'].config(text=f"{screen_time_hours}h {screen_time_mins}m / 24h")
        content_widgets['screen_time_perc'].config(text=f"{screen_perc:.2f}%")
        content_widgets['brk_time_label'].config(text=f"{brk_time_hrs}h {brk_time_mins}m / 24h")
        content_widgets['brk_time_perc'].config(text=f"{brk_perc:.2f}%")

        update_content_positions(screen_time_value, brk_time_value)
        window.after(5000, update_ui)

    # Pages
    def home_page():
        clear_right_frame()
        set_page("home")

    def restricted_page():
        clear_right_frame()
        set_page("restricted")
        # TODO: add restricted page widgets

    def history_page():
        clear_right_frame()
        set_page("history")
        # TODO: add history page widgets

    def settings_page():
        clear_right_frame()
        set_page("settings")
        # TODO: add settings page widgets
    
    # ===============================
# Page System
# ===============================
    def set_page(page_name):
        """Handles page change and Configure binding/unbinding."""
        global current_page
        current_page = page_name

        if page_name == "home":
            window.bind("<Configure>", lambda e: update_ui())
            update_ui()
        else:
            window.unbind("<Configure>")


    def clear_right_frame():
        """Remove all widgets from the right frame."""
        for widget in right_frame.winfo_children():
            widget.place_forget()

    # Navigation
    home_btn = create_nav_button(left_frame, "Home", home_page)
    home_btn.grid(row=0, column=0, pady=(20, 0), sticky="ew")
    tk.Label(left_frame, image=home_icon, bg=blue_color).grid(row=0, column=1, padx=(0, 20), pady=(20, 0))

    block_btn = create_nav_button(left_frame, "Restricted", restricted_page)
    block_btn.grid(row=1, column=0, pady=10, sticky="ew")
    tk.Label(left_frame, image=block_icon, bg=blue_color).grid(row=1, column=1, padx=(0, 20))

    history_btn = create_nav_button(left_frame, "History", history_page)
    history_btn.grid(row=2, column=0, pady=10, sticky="ew")
    tk.Label(left_frame, image=history_icon, bg=blue_color).grid(row=2, column=1, padx=(0, 20))

    settings_btn = create_nav_button(left_frame, "Settings", settings_page)
    settings_btn.grid(row=3, column=0, pady=10, sticky="ew")
    tk.Label(left_frame, image=settings_icon, bg=blue_color).grid(row=3, column=1, padx=(0, 20))

    # Logo
    tk.Label(left_frame, image=logo_icon, bg=blue_color).grid(row=4, column=0, columnspan=2, pady=(50, 20))

    # Start Home page
    content_widgets = create_content_widgets()
    home_page()

    window.mainloop()

import tkinter as tk
from tkinter import Frame, BOTH, LEFT, RIGHT, Y
import customtkinter as ctk
from PIL import Image, ImageTk
import pystray
import os
import time
import threading

# ===============================
# Global Variables
# ===============================
state = None
window = None
tray_icon = None
content_widgets = {}
current_page = None
max_value = 24  # hours
shutdown_event = threading.Event()


# ===============================
# Graceful Shutdown
# ===============================
def graceful_shutdown():
    """Stop background threads, save state, UI, and tray before exiting."""
    shutdown_event.set()
    time.sleep(0.5)

    # Stop tray
    global tray_icon
    if tray_icon:
        try:
            tray_icon.stop()
        except:
            pass

    # Save final state to DB
    try:
        if state:
            from storage.db import Database  # avoid circular import
            user_db = Database()

            with state.lock:
                today = time.strftime("%Y-%m-%d")
                app_data = state.screentime_per_app.copy()
                screen = state.screen_time
                brk = state.total_break_duration

            user_db.update_daily_state(
                date=today,
                screen_time=screen,
                break_time=brk,
                app_usage_dict=app_data
            )
            print("[+] Final state saved before shutdown.")
    except Exception as e:
        print(f"[!] Failed to save state: {e}")

    # Close window
    if window and window.winfo_exists():
        try:
            window.destroy()
        except:
            pass

    os._exit(0)


# ===============================
# Tray Handling
# ===============================
def on_closing(window):
    """Hide window instead of closing."""
    window.withdraw()
    show_tray_icon(window)


def show_tray_icon(window):
    global tray_icon
    icon_image = Image.open(r"C:\Dev\project_pymonitor\frontend_ui\logo.png")

    def _on_show(icon, item):
        window.deiconify()
        icon.stop()

    def _on_exit(icon, item):
        threading.Thread(target=graceful_shutdown, daemon=True).start()

    menu = pystray.Menu(
        pystray.MenuItem("Show", _on_show),
        pystray.MenuItem("Exit", _on_exit)
    )

    tray_icon = pystray.Icon("PyMonitor", icon_image, "PyMonitor", menu)
    threading.Thread(target=tray_icon.run, daemon=True).start()


# ===============================
# UI Start
# ===============================
def start_ui(shared_state):
    global state, window, content_widgets, right_frame
    state = shared_state

    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    # Window
    window = tk.Tk()
    window.title("PyMonitor")
    window.configure(bg="#222222")
    window.minsize(800, 600)
    window.protocol("WM_DELETE_WINDOW", lambda: on_closing(window))

    # Colors
    blue_color = "#141414"
    hover_color = "#36393B"
    bg_color = "#222222"

    # Main container
    main_container = Frame(window, bg=bg_color)
    main_container.pack(fill=BOTH, expand=True)

    # Sidebar
    left_frame = ctk.CTkFrame(master=main_container, width=210, fg_color=blue_color)
    left_frame.pack(side=LEFT, fill=Y)

    # Content area
    right_frame = Frame(main_container, bg=bg_color)
    right_frame.pack(side=RIGHT, fill=BOTH, expand=True)

    # Hover effects
    def on_enter(e): e.widget.configure(bg=hover_color)
    def on_leave(e): e.widget.configure(bg=blue_color)

    # Nav button factory
    def create_nav_button(parent, text, command=None):
        btn = tk.Button(
            parent, height=2, width=20, text=text, bg=blue_color, fg="white",
            font=("Agency FB", 18), bd=0, activebackground=hover_color,
            activeforeground="#178DED", anchor="w", padx=20, command=command
        )
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    # Load icons
    def create_icon(path, size=(30, 30)):
        img = Image.open(path).resize(size)
        return ImageTk.PhotoImage(img)

    home_icon = create_icon(r"C:\Dev\project_pymonitor\frontend_ui\home.png")
    block_icon = create_icon(r"C:\Dev\project_pymonitor\frontend_ui\block.png")
    history_icon = create_icon(r"C:\Dev\project_pymonitor\frontend_ui\history.png")
    settings_icon = create_icon(r"C:\Dev\project_pymonitor\frontend_ui\settings.png")
    logo_icon = create_icon(r"C:\Dev\project_pymonitor\frontend_ui\logo.png", (80, 80))

    # Content widgets
    def create_content_widgets():
        outer = tk.Frame(right_frame, bg="#e9eae9", height=25)
        filled = tk.Frame(outer, height=25)
        outer2 = tk.Frame(right_frame, bg="#e9eae9", height=25)
        filled2 = tk.Frame(outer2, bg="#e9ff25", height=25)
    
        screen_time_lab = tk.Label(right_frame, font=("Arial Black", 12), bg=bg_color, fg="white")
        screen_time_txt = tk.Label(right_frame, text="Screen time", font=("Agency FB", 20), bg=bg_color, fg="white")
        screen_time_perc_lbl = tk.Label(right_frame, font=("Arial Black", 15), bg=bg_color, fg="white")

        brk_time_label = tk.Label(right_frame, font=("Arial Black", 12), bg=bg_color, fg="white")
        brk_time_txt = tk.Label(right_frame, text="Break time", font=("Agency FB", 20), fg="white", bg=bg_color)
        brk_time_perc_lbl = tk.Label(right_frame, font=("Arial Black", 15), bg=bg_color, fg="white")

        view_usage_btn = ctk.CTkButton(
            right_frame, text="VIEW USAGE", width=160, height=50, font=("Segoe UI", 17, "bold"),
            fg_color="#178DED", hover_color="#1A98FF", text_color="white",
            border_color="black", border_width=2, corner_radius=30
        )

        return {
            'outer': outer, 'filled': filled, 'outer2': outer2, 'filled2': filled2,
            'screen_time_lab': screen_time_lab, 'screen_time_txt': screen_time_txt,
            'screen_time_perc': screen_time_perc_lbl,
            'brk_time_label': brk_time_label, 'brk_time_txt': brk_time_txt,
            'brk_time_perc': brk_time_perc_lbl,
            'view_usage_btn': view_usage_btn
        }

    # Position update
    def update_content_positions(screen_time_value, brk_time_value):
        width = right_frame.winfo_width()
        height = right_frame.winfo_height()

        content_widgets['filled'].configure(width=int(width * 0.5 * (screen_time_value / max_value)))
        content_widgets['filled2'].configure(width=int(width * 0.5 * (brk_time_value / max_value)))

        base_y = height * 0.1
        content_widgets['screen_time_txt'].place(x=width*0.1, y=base_y, anchor="w")
        content_widgets['outer'].place(x=width*0.1, y=base_y+50, width=width*0.5)
        content_widgets['filled'].pack(fill="y", side="left")
        content_widgets['screen_time_perc'].place(x=width*0.1, y=base_y+100, anchor="w")
        content_widgets['screen_time_lab'].place(x=width*0.65, y=base_y+75, anchor="w")

        content_widgets['brk_time_txt'].place(x=width*0.1, y=base_y+150, anchor="w")
        content_widgets['outer2'].place(x=width*0.1, y=base_y+200, width=width*0.5)
        content_widgets['filled2'].pack(fill="y", side="left")
        content_widgets['brk_time_perc'].place(x=width*0.1, y=base_y+250, anchor="w")
        content_widgets['brk_time_label'].place(x=width*0.65, y=base_y+225, anchor="w")

        content_widgets['view_usage_btn'].place(x=width*0.7, y=height*0.8)

    # UI update loop
    def update_ui():
        if shutdown_event.is_set() or current_page != "home" or state is None:
            return

        filled_widget = content_widgets.get('filled')
        filled2_widget = content_widgets.get('filled2')
        if not (filled_widget and filled_widget.winfo_exists()):
            return
        if not (filled2_widget and filled2_widget.winfo_exists()):
            return

        with state.lock:
            snapshot = {
                "screen_time": state.screen_time,
                "break_time": state.total_break_duration
            }

        # After releasing lock, do all UI math from snapshot
        screen_time_value = snapshot["screen_time"] / 3600
        brk_time_value = snapshot["break_time"] / 3600

        screen_time_hours = int(screen_time_value)
        screen_time_mins = int((screen_time_value % 1) * 60)
        screen_perc = (screen_time_value / max_value) * 100

        brk_time_hrs = int(brk_time_value)
        brk_time_mins = int((brk_time_value % 1) * 60)
        brk_perc = (brk_time_value / max_value) * 100

        screen_color = "#3b953a" if screen_perc < 30 else "#3C73BB" if screen_perc < 70 else "#8c1515"
        brk_color = "#ff0000" if brk_perc < 10 else "#ff8000" if brk_perc < 20 else "#ffff00" if brk_perc < 30 else "#00ff00" if brk_perc < 50 else "#3C73BB"

        content_widgets['filled'].configure(bg=screen_color)
        content_widgets['filled2'].configure(bg=brk_color)

        content_widgets['screen_time_lab'].config(text=f"{screen_time_hours}h {screen_time_mins}m / 24h")
        content_widgets['screen_time_perc'].config(text=f"{screen_perc:.2f}%")
        content_widgets['brk_time_label'].config(text=f"{brk_time_hrs}h {brk_time_mins}m / 24h")
        content_widgets['brk_time_perc'].config(text=f"{brk_perc:.2f}%")

        update_content_positions(screen_time_value, brk_time_value)
        window.after(5000, update_ui)

    # Pages
    def home_page():
        clear_right_frame()
        set_page("home")

    def restricted_page():
        clear_right_frame()
        set_page("restricted")
        # TODO: add restricted page widgets

    def history_page():
        clear_right_frame()
        set_page("history")
        # TODO: add history page widgets

    def settings_page():
        clear_right_frame()
        set_page("settings")
        # TODO: add settings page widgets
    
    # ===============================
# Page System
# ===============================
    def set_page(page_name):
        """Handles page change and Configure binding/unbinding."""
        global current_page
        current_page = page_name

        if page_name == "home":
            window.bind("<Configure>", lambda e: update_ui())
            update_ui()
        else:
            window.unbind("<Configure>")


    def clear_right_frame():
        """Remove all widgets from the right frame."""
        for widget in right_frame.winfo_children():
            widget.place_forget()

    # Navigation
    home_btn = create_nav_button(left_frame, "Home", home_page)
    home_btn.grid(row=0, column=0, pady=(20, 0), sticky="ew")
    tk.Label(left_frame, image=home_icon, bg=blue_color).grid(row=0, column=1, padx=(0, 20), pady=(20, 0))

    block_btn = create_nav_button(left_frame, "Restricted", restricted_page)
    block_btn.grid(row=1, column=0, pady=10, sticky="ew")
    tk.Label(left_frame, image=block_icon, bg=blue_color).grid(row=1, column=1, padx=(0, 20))

    history_btn = create_nav_button(left_frame, "History", history_page)
    history_btn.grid(row=2, column=0, pady=10, sticky="ew")
    tk.Label(left_frame, image=history_icon, bg=blue_color).grid(row=2, column=1, padx=(0, 20))

    settings_btn = create_nav_button(left_frame, "Settings", settings_page)
    settings_btn.grid(row=3, column=0, pady=10, sticky="ew")
    tk.Label(left_frame, image=settings_icon, bg=blue_color).grid(row=3, column=1, padx=(0, 20))

    # Logo
    tk.Label(left_frame, image=logo_icon, bg=blue_color).grid(row=4, column=0, columnspan=2, pady=(50, 20))

    # Start Home page
    content_widgets = create_content_widgets()
    home_page()

    window.mainloop()
