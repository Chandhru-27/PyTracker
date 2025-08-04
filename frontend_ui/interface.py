from tkinter import *
import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk
from tkinter import Frame, BOTH, LEFT, RIGHT, Y
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
current_page = "home"  # Initialize current_page
max_value = 24  # hours
shutdown_event = threading.Event()
screen_time_value = 12
screen_time_mins = 0
screen_time_hours = 0
screen_perc = 0

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


def start_ui(shared_state):
    global window, current_page, state, screen_time_hours , screen_time_mins , screen_time_perc , max_value
    state = shared_state
   
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    # Creating a window
    window = tk.Tk()
    window.title("Screen Time Tracker")
    window.minsize(1000, 700)  # Set minimum window size
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    window.geometry(f"{int(screen_width*0.8)}x{int(screen_height*0.8)}")  # Start at 80% of screen size
    window.configure(bg="#222222")

    # Colors
    blue_color = "#141414"
    hover_color = "#36393B"
    separator_color = "#66696D"

    # Creating the left frame
    left_frame = ctk.CTkFrame(master=window, width=210, fg_color=blue_color)
    left_frame.pack(side="left", fill="y")
    left_frame.pack_propagate(False)  # Prevent frame from shrinking

    # Hover functions
    def on_enter(e):
        e.widget['bg'] = hover_color
        if hasattr(e.widget, 'logo'):
            e.widget.logo['bg'] = hover_color

    def on_leave(e):
        e.widget['bg'] = blue_color
        if hasattr(e.widget, 'logo'):
            e.widget.logo['bg'] = blue_color

    # Function to create sidebar buttons with icons
    def create_nav_button(parent, text, icon_path, command=None):
        # Button container
        btn_frame = Frame(parent, bg=blue_color)
        btn_frame.pack(fill="x", pady=0)
        
        # Load and resize icon
        icon_img = Image.open(icon_path).resize((30, 30))
        icon_photo = ImageTk.PhotoImage(icon_img)
        
        # Icon label
        icon_label = Label(btn_frame, image=icon_photo, bg=blue_color, height=97)
        icon_label.image = icon_photo  # Keep reference
        icon_label.pack(side="left", padx=0, pady=20)
        
        # Button
        btn = Button(btn_frame, 
                    text=f"  {text}", 
                    font=("Agency FB", 18), 
                    bg=blue_color, 
                    fg="white",
                    bd=0,
                    height=3,
                    activebackground=hover_color,
                    activeforeground="#178DED",
                    anchor="w",
                    command=command)
        btn.pack(side="left", fill="x", expand=True, pady=20)
        
        # Store reference to icon
        btn.logo = icon_label
        
        # Bind hover events
        btn.bind("<Enter>", lambda e: [on_enter(e), icon_label.config(bg=hover_color)])
        btn.bind("<Leave>", lambda e: [on_leave(e), icon_label.config(bg=blue_color)])
        icon_label.bind("<Enter>", lambda e: [on_enter(e), btn.config(bg=hover_color)])
        icon_label.bind("<Leave>", lambda e: [on_leave(e), btn.config(bg=blue_color)])
        
        return btn_frame

    # Navigation buttons container
    nav_frame = Frame(left_frame, bg=blue_color)
    nav_frame.pack(side="top", fill="x", expand=True)

    # Main content frame (right side)
    content_frame = Frame(window, bg="#222222")
    content_frame.pack(side="right", fill="both", expand=True)

    # Variables for responsive widgets

    def update_content_positions(screen_time, break_time):
        """Update widget positions based on current values"""
        pass  # Implement this if needed

    # Create widgets that need to be responsive
    def update_ui():
        if shutdown_event.is_set() or current_page != "home" or state is None:
            window.after(5000, update_ui)
            return

        with state.lock:
            st_value = state.screen_time / 3600
            bt_value = state.total_break_duration / 3600

        screen_perc = (st_value / max_value) * 100
        brk_perc = (bt_value / max_value) * 100

        st_hours, st_mins = int(st_value), int((st_value % 1) * 60)
        bt_hours, bt_mins = int(bt_value), int((bt_value % 1) * 60)

        screen_color = "#3b953a" if screen_perc < 30 else "#3C73BB" if screen_perc < 70 else "#8c1515"
        brk_color = "#ff0000" if brk_perc < 10 else "#ff8000" if brk_perc < 20 else "#ffff00" if brk_perc < 30 else "#00ff00" if brk_perc < 50 else "#3C73BB"

        bar_width = content_widgets['outer_width']
        content_widgets['filled'].configure(bg=screen_color, width=int((st_value / max_value) * bar_width))
        content_widgets['filled2'].configure(bg=brk_color, width=int((bt_value / max_value) * bar_width))

        content_widgets['screen_time_lab'].config(text=f"{st_hours}h {st_mins}m / 24h")
        content_widgets['screen_time_perc'].config(text=f"{screen_perc:.2f}%")
        content_widgets['brk_time_label'].config(text=f"{bt_hours}h {bt_mins}m / 24h")
        content_widgets['brk_time_perc'].config(text=f"{brk_perc:.2f}%")

        window.after(500, update_ui)

    def create_responsive_widgets():
        for widget in content_frame.winfo_children():
            widget.destroy()

        frame_width = content_frame.winfo_width()
        bar_width = min(700, frame_width - 300)
        content_widgets['outer_width'] = bar_width

        # Screen time bar
        outer = tk.Frame(content_frame, bg="#e9eae9", width=bar_width, height=25)
        outer.place(relx=0.5, rely=0.35, anchor="center")
        content_widgets['outer'] = outer

        filled = tk.Frame(outer, height=25)
        filled.place(x=0, y=0)
        content_widgets['filled'] = filled

        screen_time_txt = Label(content_frame, text="Screen time",
                                font=("Agency FB", 20), bg="#222222", fg="white")
        screen_time_txt.place(relx=0.2, rely=0.30, anchor="center")

        content_widgets['screen_time_perc'] = Label(content_frame,
            font=("Arial Black", 15), bg="#222222", fg="white")
        content_widgets['screen_time_perc'].place(relx=0.2, rely=0.40, anchor="center")

        content_widgets['screen_time_lab'] = Label(content_frame,
            font=("Arial Black", 12), bg="#222222", fg="white")
        content_widgets['screen_time_lab'].place(relx=0.7, rely=0.40, anchor="center")

        # Break time bar
        outer2 = tk.Frame(content_frame, bg="#e9eae9", width=bar_width, height=25)
        outer2.place(relx=0.5, rely=0.55, anchor="center")
        content_widgets['outer2'] = outer2

        filled2 = tk.Frame(outer2, height=25)
        filled2.place(x=0, y=0)
        content_widgets['filled2'] = filled2

        brk_time_txt = Label(content_frame, text="Break time",
                            font=("Agency FB", 20), fg="white", bg="#222222")
        brk_time_txt.place(relx=0.2, rely=0.50, anchor="center")

        content_widgets['brk_time_perc'] = Label(content_frame,
            font=("Arial Black", 15), bg="#222222", fg="white")
        content_widgets['brk_time_perc'].place(relx=0.2, rely=0.60, anchor="center")

        content_widgets['brk_time_label'] = Label(content_frame,
            font=("Arial Black", 12), bg="#222222", fg="white")
        content_widgets['brk_time_label'].place(relx=0.7, rely=0.60, anchor="center")


    # Page functions
    def home_page():
        global current_page
        current_page = "home"
        create_responsive_widgets()
        update_ui()

    def restricted_page():
        global current_page
        current_page = "restricted"
        for widget in content_frame.winfo_children():
            widget.destroy()
        # Add restricted page content here

    def history_page():
        global current_page
        current_page = "history"
        for widget in content_frame.winfo_children():
            widget.destroy()
        
        history = [
            [1, '5h 12m', '18h 48m', 'VSCode: 3.84h'],
            [2, '6h 48m', '17h 12m', 'YouTube: 4.2h'],
            [3, '3h 30m', '20h 30m', 'Zoom: 1.89h'],
            [4, '4h 6m', '19h 54m', 'Slack: 2.9h'],
            [5, '8h 0m', '16h 0m', 'Netflix: 6.4h']
        ]

        y = 200
        for x in history:
            history_row = tk.Label(
                content_frame,
                text=f"{x[0]:<3}| {x[1]:<12}| {x[2]:<12}| {x[3]:<12}",
                font=("Courier", 17),
                anchor="w", bg="#222222",
                fg="white"
            )
            history_row.place(x=250, y=y)
            y += 40

    def settings_page():
        global current_page
        current_page = "settings"
        for widget in content_frame.winfo_children():
            widget.destroy()
        # Add settings page content here

    # Make the window responsive
    def on_resize(event):
        if event.widget == window and current_page == "home":
            create_responsive_widgets()

    window.bind('<Configure>', on_resize)

    # Navigation buttons
    home_btn = create_nav_button(nav_frame, "Home", r"C:\Dev\project_pymonitor\frontend_ui\home.png", home_page)

    # Separator
    separator1 = Frame(nav_frame, bg=separator_color, height=2)
    separator1.pack(fill="x", pady=5)

    block_app_btn = create_nav_button(nav_frame, "Restricted", r"C:\Dev\project_pymonitor\frontend_ui\block.png", restricted_page)

    # Separator
    separator2 = Frame(nav_frame, bg=separator_color, height=2)
    separator2.pack(fill="x", pady=5)

    history_btn = create_nav_button(nav_frame, "History", r"C:\Dev\project_pymonitor\frontend_ui\history.png", history_page)

    # Separator
    separator3 = Frame(nav_frame, bg=separator_color, height=2)
    separator3.pack(fill="x", pady=5)

    settings_btn = create_nav_button(nav_frame, "Settings", r"C:\Dev\project_pymonitor\frontend_ui\settings.png", settings_page)

    # Bottom space to push buttons up
    bottom_spacer = Frame(left_frame, bg=blue_color, height=20)
    bottom_spacer.pack(side="bottom", fill="x")

    # Top section for logo
    top_frame = Frame(left_frame, bg=blue_color)
    top_frame.pack(side="top", fill="x", pady=(20, 40))

    # App logo
    logo_img = Image.open(r"C:\Dev\project_pymonitor\frontend_ui\logo.png").resize((120, 120))
    logo_photo = ImageTk.PhotoImage(logo_img)
    logo_label = Label(top_frame, image=logo_photo, bg=blue_color)
    logo_label.image = logo_photo
    logo_label.pack()

    # Initialize with home page
    home_page()

    window.protocol("WM_DELETE_WINDOW", lambda: on_closing(window))
    window.mainloop()

