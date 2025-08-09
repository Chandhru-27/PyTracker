from tkinter import *
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
from PIL import Image, ImageTk
from tkinter import Frame, BOTH, LEFT, RIGHT, Y
import pystray
import os
import time
import threading
from storage.db import Database
from state.userstate import UserActivityState
from utils.utilities import Utility
from logs.app_logger import logger


HOST_PATH = r"C:\Windows\System32\drivers\etc\hosts"

# ===============================
# Global Variables
# ===============================
state = UserActivityState
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
user_db = Database()
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

def get_threads():
    from main import tracker_thread, reminder_thread
    return tracker_thread, reminder_thread

# ===============================
# Tray Handling
# ===============================
def on_closing(window):
    """Hide window instead of closing."""
    window.withdraw()
    show_tray_icon(window)


def show_tray_icon(window):
    global tray_icon
    icon_image = Image.open(r"C:\Dev\PyTracker\frontend_ui\logo.png")

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

    sidebar_width = 180  # default

    # Creating the left frame
    left_frame = ctk.CTkFrame(master=window, width=sidebar_width, fg_color=blue_color)    
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
        btn_frame = Frame(parent, bg=blue_color)
        btn_frame.pack(fill="x", pady=0)

        icon_img = Image.open(icon_path).resize((22, 22))  # smaller icon
        icon_photo = ImageTk.PhotoImage(icon_img)

        icon_label = Label(btn_frame, image=icon_photo, bg=blue_color, height=55)
        icon_label.image = icon_photo
        icon_label.pack(side="left", padx=8, pady=10)

        btn = Button(btn_frame,
                    text=f"  {text}",
                    font=("Segoe UI", 14),  # smaller font
                    bg=blue_color,
                    fg="white",
                    bd=0,
                    height=2,
                    activebackground=hover_color,
                    activeforeground="#178DED",
                    anchor="w",
                    command=command)
        btn.pack(side="left", fill="x", expand=True, pady=5)

        btn.logo = icon_label

        # Hover events (unchanged)
        
        btn.bind("<Leave>", lambda e: [on_leave(e), icon_label.config(bg=blue_color)])
        icon_label.bind("<Leave>", lambda e: [on_leave(e), btn.config(bg=blue_color)])

        return btn_frame


    # Navigation buttons container
    nav_frame = Frame(left_frame, bg=blue_color)
    nav_frame.pack(side="top", fill="x", expand=True)

    # Main content frame (right side)
    content_frame = Frame(window, bg="#222222")
    content_frame.pack(side="right", fill="both", expand=True)

    # Variables for responsive widgets

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

    ROWS_PER_PAGE = 10
    current_page_index = 0  # start at page 0

    def history_page(page_index=0):
        global current_page_index
        current_page_index = page_index
        global current_page
        current_page = "history"
        for widget in content_frame.winfo_children():
            widget.destroy()
        
        # Title
        title_label = ctk.CTkLabel(
            master=content_frame,
            text="Usage History",
            font=("Agency FB", 30),
            text_color="white"
        )
        title_label.pack(pady=(20, 10))
        
        # Create table frame
        table_frame = ctk.CTkFrame(
            master=content_frame,
            fg_color="#2b2b2b",
            border_width=1,
            border_color="#444444"
        )
        table_frame.pack(pady=25, padx=20, fill="both", expand=True)
        
        # Table headers
        headers = ["S.No", "Date", "Screen Time", "Break Time", "View App Usage"]
        for col, header in enumerate(headers):
            header_label = ctk.CTkLabel(
                master=table_frame,
                text=header,
                font=("Segoe UI Semibold", 20),
                text_color="#178DED",
                anchor="center"
            )
            header_label.grid(row=0, column=col, sticky="nsew", padx=5, pady=5)
        
        db = Database()
        history_data = db.get_user_history()
        
        # Slice for this page
        start_index = page_index * ROWS_PER_PAGE
        end_index = start_index + ROWS_PER_PAGE
        page_data = history_data[start_index:end_index]
        
        # Fill with placeholders if less than ROWS_PER_PAGE
        while len(page_data) < ROWS_PER_PAGE:
            page_data.append(["", "", "", ""])
        
        # Add rows
        for row, data in enumerate(page_data, start=1):
            for col, value in enumerate(data):
                cell = ctk.CTkLabel(
                    master=table_frame,
                    text=value,
                    font=("Segoe UI", 18),
                    text_color="white" if value else "#2b2b2b",  # hide placeholder text
                    fg_color="#333333" if row % 2 == 0 else "#2b2b2b",
                    anchor="center",
                    height=50  # FIXED height for every row
                )
                cell.grid(row=row, column=col, sticky="nsew", padx=0, pady=5)
            
            # View button only if valid data
            if data[0] != "":
                btn = ctk.CTkButton(
                    master=table_frame,
                    text="View Usage",
                    font=("Segoe UI", 18),
                    fg_color="#474747",
                    hover_color="#0e5a9e",
                    width=100,
                    height=40,
                    command=lambda r=start_index + row: print(f"Viewing usage for row {r}")
                )
                btn.grid(row=row, column=len(headers)-1, padx=0, pady=5, sticky="nsew")
            else:
                # Empty placeholder for button column
                empty = ctk.CTkLabel(
                    master=table_frame,
                    text="",
                    fg_color="#333333" if row % 2 == 0 else "#2b2b2b"
                )
                empty.grid(row=row, column=len(headers)-1, sticky="nsew", padx=0, pady=5)
        
        # Make columns expand evenly
        for col in range(len(headers)):
            table_frame.grid_columnconfigure(col, weight=1)
        
        # Pagination controls
        pagination_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        pagination_frame.pack(pady=(0, 10))
        
        total_pages = (len(history_data) + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE
        for i in range(total_pages):
            btn_color = "#178DED" if i != page_index else "white"
            page_btn = ctk.CTkButton(
                master=pagination_frame,
                text=str(i + 1),
                font=("Segoe UI", 16),
                fg_color="transparent",
                hover_color="#0e5a9e",
                text_color=btn_color,
                width=30,
                command=lambda i=i: history_page(i)
            )
            page_btn.pack(side="left", padx=5)

    def restricted_page():
        global current_page
        current_page = "restricted"

        # Dummy Data (Replace with actual database fetch logic)
        blocked_apps = user_db.load_blocked_apps()
        blocked_urls = user_db.load_blocked_urls()

        # Section containers
        app_section_frame = None
        url_section_frame = None

        def render_app_table():
            for widget in app_section_frame.winfo_children():
                widget.destroy()
            create_blocked_table(app_section_frame, "Blocked Apps", blocked_apps, render_app_table, is_app=True)

        def render_url_table():
            for widget in url_section_frame.winfo_children():
                widget.destroy()
            create_blocked_table(url_section_frame, "Blocked URLs", blocked_urls, render_url_table, is_app=False)

        def render_page():
            for widget in content_frame.winfo_children():
                widget.destroy()

            nonlocal app_section_frame, url_section_frame

            app_section_frame = Frame(content_frame, bg="#222222")
            app_section_frame.pack(fill="x", padx=10, pady=(10, 5))

            url_section_frame = Frame(content_frame, bg="#222222")
            url_section_frame.pack(fill="x", padx=10, pady=(10, 5))

            render_app_table()
            render_url_table()

        def create_blocked_table(master, title, data_list, refresh_callback, is_app=True):
        # Title
            section_title = ctk.CTkLabel(
                master=master,
                text=title,
                font=("Agency FB", 25),
                text_color="white"
            )
            section_title.pack(pady=(10, 5))

            # Scrollable Frame
            scroll_container = ctk.CTkFrame(master, fg_color="#2b2b2b", border_width=1, border_color="#444444")
            scroll_container.pack(padx=20, pady=10, fill="both", expand=False)

            canvas = tk.Canvas(scroll_container, bg="#2b2b2b", highlightthickness=0)
            scrollbar = tk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)
            scrollable_frame = Frame(canvas, bg="#2b2b2b")

            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )

            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

            # Table Headers
            headers = ["S.No", "App Name" if is_app else "Domain"]
            for col, header in enumerate(headers):
                header_label = ctk.CTkLabel(
                    master=scrollable_frame,
                    text=header,
                    font=("Segoe UI Semibold", 18),
                    text_color="#178DED",
                    width=25,
                    anchor="center"
                )
                header_label.grid(row=0, column=col, padx=10, pady=10, sticky="w")

            # Add '+' button at the end of header row
            
            def on_add_click():
                if is_app:
                    file_path = filedialog.askopenfilename(
                        title="Select an application",
                        filetypes=[("Executable Files", "*.exe")]
                    )
                    if file_path:
                        exe_name = os.path.basename(file_path)
                        if exe_name not in data_list:
                            Utility.stop_app_blocker()
                            user_db.insert_blocked_app(app_name=exe_name)
                            state.blocked_apps = user_db.load_blocked_apps()
                            if state.blocked_apps:
                                Utility.start_app_blocker(state.blocked_apps, scan_interval=1)
                            data_list.add(exe_name)
                            refresh_callback()
                else:
                    # For URLs — open a centered input dialog with warning
                    def submit_url():
                        url = url_entry.get().strip()
                        if url and url not in data_list:
                            Utility.block_url(HOST_PATH , url)
                            user_db.insert_blocked_url(url=url)
                            data_list.add(url)
                            input_window.destroy()
                            refresh_callback()
                    input_window = tk.Toplevel()
                    input_window.title("Add URL")
                    input_window.configure(bg="#2b2b2b")
                    width, height = 360, 180
                    input_window.geometry(f"{width}x{height}")
                    input_window.resizable(False, False)
                    input_window.update_idletasks()
                    x = (input_window.winfo_screenwidth() // 2) - (width // 2)
                    y = (input_window.winfo_screenheight() // 2) - (height // 2)
                    input_window.geometry(f"{width}x{height}+{x}+{y}")

                    label = tk.Label(input_window, text="Enter URL:", font=("Segoe UI", 12), bg="#2b2b2b", fg="white")
                    label.pack(pady=(15, 5))

                    url_entry = tk.Entry(input_window, font=("Segoe UI", 12), width=35)
                    url_entry.pack(pady=(0, 10))
                    url_entry.focus()

                    warn = tk.Label(
                        input_window,
                        text=(
                            "Warning: Blocking may require admin privileges. "
                            "Enter a domain only (e.g., example.com)."
                        ),
                        font=("Segoe UI", 10),
                        bg="#2b2b2b",
                        fg="#b0b8c1",
                        wraplength=320,
                        justify="center",
                    )
                    warn.pack(pady=(0, 6))

                    submit_btn = tk.Button(input_window, text="Add", font=("Segoe UI", 10), command=submit_url)
                    submit_btn.pack()

                    input_window.grab_set()  # Makes the popup modal

            add_button = ctk.CTkButton(
                master=scrollable_frame,
                text="+",
                font=("Segoe UI", 20, "bold"),
                fg_color="#0e5a9e",
                hover_color="#1077ce",
                width=40,
                height=35,
                command=on_add_click
            )
            add_button.grid(row=0, column=len(headers), padx=10, pady=5, sticky="e")

            # Rows
            for idx, value in enumerate(data_list.copy(), start=1):
                bg_color = "#333333" if idx % 2 == 0 else "#2b2b2b"

                sno_label = ctk.CTkLabel(
                    master=scrollable_frame,
                    text=str(idx),
                    font=("Segoe UI", 16),
                    text_color="white",
                    fg_color=bg_color,
                    width=50,
                    anchor="center"
                )
                sno_label.grid(row=idx, column=0, padx=10, pady=8, sticky="w")

                item_frame = Frame(scrollable_frame, bg=bg_color)
                item_frame.grid(row=idx, column=1, sticky="w", padx=10, pady=5)

                item_label = Label(
                    item_frame,
                    text=value,
                    font=("Segoe UI", 15),
                    bg=bg_color,
                    fg="white"
                )
                item_label.pack(side="left", padx=(0, 15))

                def unblock_and_refresh(val=value):
                    print(f"Unblocked: {val}")
                    if is_app:
                        Utility.stop_app_blocker()
                        user_db.remove_from_blocked_apps(app_name=val)
                        state.blocked_apps = user_db.load_blocked_apps()
                        if state.blocked_apps:
                            logger.debug(f"Loaded blocked apps data again!.")
                            logger.debug(f"Blocked apps: {state.blocked_apps}")
                            Utility.start_app_blocker(state.blocked_apps, scan_interval=1)
                    else:
                        Utility.clean_hosts_file(HOST_PATH , val)
                        Utility.restart_dns_service()
                        Utility.flush_dns()
                        user_db.remove_from_blocked_url(url=val)
                        
                    data_list.remove(val)
                    refresh_callback()  # Only refresh this section

                unblock_btn = ctk.CTkButton(
                    master=item_frame,
                    text="Unblock",
                    font=("Segoe UI", 14),
                    fg_color="#474747",
                    hover_color="#0e5a9e",
                    width=80,
                    height=30,
                    command=unblock_and_refresh
                )
                unblock_btn.pack(side="left")

        render_page()

    def settings_page():
        global current_page
        current_page = "settings"
        for widget in content_frame.winfo_children():
            widget.destroy()
        # Add settings page content here

    last_size = [None, None]  # [width, height]

    def on_resize(event):
        if event.widget == window:
            width = window.winfo_width()
            height = window.winfo_height()

            # Only trigger resize logic when size changes
            if (width, height) != tuple(last_size):
                last_size[0], last_size[1] = width, height

                # Adjust sidebar width
                new_sidebar_width = 160 if width < 1100 else 180
                left_frame.configure(width=new_sidebar_width)

                # Resize logo
                new_logo_size = 70 if width < 1100 else 90
                update_logo(new_logo_size)

                # Regenerate home widgets if visible
                if current_page == "home":
                    create_responsive_widgets()


    window.bind('<Configure>', on_resize)

    # Navigation buttons
    home_btn = create_nav_button(nav_frame, "Home", r"C:\Dev\PyTracker\frontend_ui\home.png", home_page)

    # Separator
    separator1 = Frame(nav_frame, bg=separator_color, height=2)
    separator1.pack(fill="x", pady=5)

    block_app_btn = create_nav_button(nav_frame, "Restricted", r"C:\Dev\PyTracker\frontend_ui\block.png", restricted_page)

    # Separator
    separator2 = Frame(nav_frame, bg=separator_color, height=2)
    separator2.pack(fill="x", pady=5)

    history_btn = create_nav_button(nav_frame, "History", r"C:\Dev\PyTracker\frontend_ui\history.png", history_page)

    # Separator
    separator3 = Frame(nav_frame, bg=separator_color, height=2)
    separator3.pack(fill="x", pady=5)

    # settings_btn = create_nav_button(nav_frame, "Settings", r"C:\Dev\PyTracker\frontend_ui\settings.png", settings_page)

    # # Bottom space to push buttons up
    # bottom_spacer = Frame(left_frame, bg=blue_color, height=20)
    # bottom_spacer.pack(side="bottom", fill="x")

    # Dynamic Logo Resize
    def update_logo(size=90):
        for widget in top_frame.winfo_children():
            widget.destroy()

        logo_img = Image.open(r"C:\Dev\PyTracker\frontend_ui\logo.png").resize((size, size))
        logo_photo = ImageTk.PhotoImage(logo_img)
        logo_label = Label(top_frame, image=logo_photo, bg=blue_color)
        logo_label.image = logo_photo
        logo_label.pack()

    # Top section for logo
    top_frame = Frame(left_frame, bg=blue_color)
    top_frame.pack(side="top", fill="x", pady=(20, 20))
    update_logo()

    # App logo
    logo_img = Image.open(r"C:\Dev\PyTracker\frontend_ui\logo.png").resize((120, 120))
    logo_photo = ImageTk.PhotoImage(logo_img)
    logo_label = Label(top_frame, image=logo_photo, bg=blue_color)
    logo_label.image = logo_photo
    logo_label.pack()

    # Initialize with home page
    
    home_page()
    
    window.protocol("WM_DELETE_WINDOW", lambda: on_closing(window))
    window.mainloop()

