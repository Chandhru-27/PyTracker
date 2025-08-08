import customtkinter as ctk
from PIL import Image
from tkinter import filedialog
import tkinter.messagebox as messagebox
from datetime import datetime
from state.userstate import UserActivityState
from frontend_ui.notification import show_reset_warning
import random
import os
import threading
import time
from storage.db import Database
import pystray
from pystray import MenuItem as item

shutdown_event = threading.Event()
tray_icon = None

class TimeTrackerApp(ctk.CTk):
    def __init__(self , state: UserActivityState):
        super().__init__()
        self.user_state = state
        self.tracker_thread = None
        self.reminder_thread = None
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.title("TimeTracker Pro")
        self.geometry("1200x720")
        self.minsize(900, 700)
        self.maxsize(1920, 1080) 
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        
        # Set window background color to match new app theme
        self.configure(fg_color="#181f2a")
        
        # Remove transparency effect completely
        try:
            self.attributes('-alpha', 1.0)  # Full opacity, no transparency
        except:
            pass  # Not supported on all platforms

        self.is_tracking = True
        self.current_page_index = 0
        self.rows_per_page = 10

        self.blocked_apps = ["chrome.exe", "spotify.exe", "discord.exe"]
        self.blocked_urls = ["youtube.com", "reddit.com"]

        # Performance optimization: Cache for widgets and images
        self._widget_cache = {}
        self._image_cache = {}
        self._current_page_widgets = []
        
        # Performance optimization flags
        self._last_update_time = 0
        self._update_interval = 1000  # 1 second instead of 500ms
        self._widgets_created = False

        # --- Modern Sidebar with Modern Colors ---
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=20, fg_color="#232b3b")
        self.sidebar_frame.pack(side="left", fill="y", padx=0, pady=0)
        self.sidebar_frame.pack_propagate(False)

        # --- Navigation Buttons with Modern Colors ---
        self.nav_buttons = {}
        nav_items = [
            ("Home", "home.png"),
            ("Restricted", "settings.png"),
            ("History", "history.png")
        ]
        for name, icon_file in nav_items:
            icon_path = os.path.join("frontend_ui", icon_file)
            # Cache the image
            if icon_path not in self._image_cache:
                try:
                    icon_img = Image.open(icon_path)
                    self._image_cache[icon_path] = ctk.CTkImage(icon_img, size=(28, 28))
                except:
                    # Fallback if image not found
                    self._image_cache[icon_path] = None
            
            icon = self._image_cache[icon_path]
            btn = ctk.CTkButton(
                self.sidebar_frame, text=name, image=icon, compound="left",
                font=("Segoe UI", 15), corner_radius=12, fg_color="#232b3b", hover_color="#2979ff",
                text_color="#ffffff", anchor="w", width=180, height=40,
                command=lambda n=name: self.load_page(n)
            )
            btn.pack(fill="x", padx=20, pady=8)
            self.nav_buttons[name] = btn

        # --- Main Frame with Transparent/Blurred Look ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=20, fg_color="#181824")
        self.main_frame.pack(side="right", expand=True, fill="both", padx=0, pady=0)

        self.current_page = None
        
        # Performance optimization: Set lower font sizes for low-end devices
        self._optimize_for_performance()
        
        self.load_page("Home")
    
    def _clear_current_page_widgets(self):
        """Clear current page widgets and cache them for reuse"""
        for widget in self._current_page_widgets:
            if widget.winfo_exists():
                widget.destroy()
        self._current_page_widgets.clear()

    def _add_to_current_page(self, widget):
        """Add widget to current page tracking"""
        self._current_page_widgets.append(widget)
        return widget
        
    def _optimize_for_performance(self):
        """Optimize UI for low-end devices"""
        try:
            # Auto-detect based on system resources
            import psutil
            memory_gb = psutil.virtual_memory().total / (1024**3)
            cpu_count = psutil.cpu_count()
            
            if memory_gb < 4 or cpu_count < 4:  # Low-end device criteria
                self._update_interval = 2000  # 2 seconds for very low-end devices
                self._is_low_end_device = True
                self._font_size_multiplier = 0.8  # Reduce font sizes
                print(f"[Performance] Optimized for low-end device (RAM: {memory_gb:.1f}GB, CPU: {cpu_count} cores)")
            else:
                self._update_interval = 1000
                self._is_low_end_device = False
                self._font_size_multiplier = 1.0  # Standard font sizes
                print(f"[Performance] Standard optimization (RAM: {memory_gb:.1f}GB, CPU: {cpu_count} cores)")
        except ImportError:
            # Fallback if psutil not available
            self._update_interval = 1500
            self._is_low_end_device = False
            self._font_size_multiplier = 0.9  # Slightly reduced fonts
            print("[Performance] Using fallback optimization")

    def build_warning_card(self, parent):
        self.warning_card = self._add_to_current_page(ctk.CTkFrame(parent, fg_color="#232b3b", corner_radius=16))
        self.warning_card.pack(fill="x", padx=30, pady=(0, 18))

        # Inner content frame
        content_frame = ctk.CTkFrame(self.warning_card, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=6)

        # Header row
        header_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        header_frame.pack(anchor="w")

        head = text = ""
        head_color =  text_color = None
        if not self.is_tracking:
            head = "Warning"
            text = "Tracking disabled. Resume immediately to continue logging activity and breaks."
            text_color = "#CF0000"
            head_color = "#ff0000"
        else:
            head = "Reminder"
            text = "While taking a break, minimize all activity and let your system idle or enter sleep mode."
            text_color = "#E6E6E6"
            head_color = "#e7b500"

        # Header row
        self.warning_icon_label = self._add_to_current_page(ctk.CTkLabel(header_frame, text="⚠️", font=("Segoe UI", 24), text_color=head_color))
        self.warning_icon_label.pack(side="left", padx=(0, 10))

        self.warning_head_label = self._add_to_current_page(ctk.CTkLabel(header_frame, text=head, font=("Segoe UI", 18, "bold"), text_color=head_color))
        self.warning_head_label.pack(side="left")

        
        # Main warning message
        self.warning_message_label = self._add_to_current_page(ctk.CTkLabel(
            content_frame,
            text=text,
            font=("Segoe UI", 16, "bold"),
            text_color=text_color,
            wraplength=800,
            justify="left"
        ))
        self.warning_message_label.pack(anchor="w", pady=(4, 0))

        # Live update support
        def update_warning_message():
            if self.is_tracking:
                self.warning_icon_label.configure(text="💡", text_color="#e7b500")
                self.warning_head_label.configure(text="Reminder", text_color="#e7b500")
                self.warning_message_label.configure(
                    text="While taking a break, minimize all activity and let your system idle or enter sleep mode.",
                    text_color="#E6E6E6"
                )
            else:
                self.warning_icon_label.configure(text="⚠️", text_color="#ff0000")
                self.warning_head_label.configure(text="Warning", text_color="#ff0000")
                self.warning_message_label.configure(
                    text="Tracking disabled. Resume immediately to continue logging activity and breaks.",
                    text_color="#CF0000"
                )

        self.update_warning_message = update_warning_message
        update_warning_message()

    def get_threads(self):
        return self.tracker_thread, self.reminder_thread

    def graceful_shutdown(self):
        """Stop threads, save state, UI, and tray before exit."""
        shutdown_event.set()
        time.sleep(0.5)

        global tray_icon
        if tray_icon:
            try:
                tray_icon.stop()
            except:
                pass

        try:
            db = Database()
            with self.user_state.lock:
                today = time.strftime("%Y-%m-%d")
                screen = self.user_state.screen_time
                brk = self.user_state.total_break_duration
                app_data = self.user_state.screentime_per_app.copy()

            db.update_daily_state(
                date=today,
                screen_time=screen,
                break_time=brk,
                app_usage_dict=app_data
            )
            print("[✓] Final state saved before shutdown.")
        except Exception as e:
            print(f"[!] Failed to save state: {e}")

        self.destroy()
        os._exit(0)
        
    def show_tray_icon(self):
        global tray_icon

        icon_path = os.path.join("frontend_ui", "logo.png")
        if icon_path not in self._image_cache:
            try:
                icon_image = Image.open(icon_path)
                self._image_cache[icon_path] = icon_image
            except:
                # Create a simple fallback icon
                icon_image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        else:
            icon_image = self._image_cache[icon_path]

        def _on_show(icon, item):
            self.deiconify()
            icon.stop()

        def _on_exit(icon, item):
            threading.Thread(target=self.graceful_shutdown, daemon=True).start()

        menu = pystray.Menu(
            item("Show", _on_show),
            item("Exit", _on_exit)
        )

        tray_icon = pystray.Icon("TimeTracker", icon_image, "TimeTracker", menu)
        threading.Thread(target=tray_icon.run, daemon=True).start()

    def on_closing(self):
        """Hide the window to tray instead of exiting."""
        self.withdraw()
        self.show_tray_icon()

    def load_page(self, name):
        # Performance optimization: only reload if page changed
        if self.current_page == name:
            return
            
        # Clear current page widgets
        self._clear_current_page_widgets()

        if name == "Home":
            self.load_dashboard()
        elif name == "Restricted":
            self.load_restricted_page()
        elif name == "History":
            self.load_history_page(self.current_page_index)
            
        self.current_page = name

    def create_stat_card(self, parent, title, value, icon, bg_color, wide=False):
        card_width = 260 if wide else 170
        card_height = 110 if wide else 80
        # Set card background to transparent
        card = self._add_to_current_page(ctk.CTkFrame(parent, width=card_width, height=card_height, fg_color="transparent", corner_radius=16))
        card.pack_propagate(False)

        self._add_to_current_page(ctk.CTkLabel(card, text=icon, font=("Segoe UI", 28 if wide else 22), text_color=bg_color)).pack(pady=(8, 0))
        self._add_to_current_page(ctk.CTkLabel(card, text=title, font=("Segoe UI", 17 if wide else 14, "bold"), text_color="#b0b8c1")).pack()
        value_label = self._add_to_current_page(ctk.CTkLabel(card, text=value, font=("Segoe UI", 28 if wide else 18, "bold"), text_color=bg_color))
        value_label.pack()
        return card , value_label

    def load_dashboard(self):
        # Clear all widgets from main_frame to prevent overlay
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # Simplified layout - single container
        dashboard_container = self._add_to_current_page(ctk.CTkFrame(self.main_frame, fg_color="transparent"))
        dashboard_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Heading row with right-aligned icon buttons
        heading_row = self._add_to_current_page(ctk.CTkFrame(dashboard_container, fg_color="transparent"))
        heading_row.pack(fill="x", pady=(0, 20))

        top_label = self._add_to_current_page(ctk.CTkLabel(heading_row, text="Dashboard",
                                      font=("Segoe UI", 32, "bold"), text_color="#00bfae"))
        top_label.pack(side="left")

        # Icon-only buttons (Pause/Resume and Reset)
        def toggle_tracking():
            self.is_tracking = not self.is_tracking
            self.user_state.is_paused = not self.is_tracking
            self.update_pause_btn()
            self.update_tracking_status_label()

        def update_pause_btn():
            if self.is_tracking:
                self.pause_btn.configure(text="⏸", fg_color="#ff5252", hover_color="#ff1744", text_color="#fff")
            else:
                self.pause_btn.configure(text="▶", fg_color="#00c853", hover_color="#067d37", text_color="#fff")

        self.update_pause_btn = update_pause_btn
        self.pause_btn = self._add_to_current_page(ctk.CTkButton(heading_row, width=48, height=48, corner_radius=24, font=("Segoe UI", 28),
                                  command=toggle_tracking, text="⏸", fg_color="#ff5252", hover_color="#ff1744", text_color="#fff"))
        self.pause_btn.pack(side="right", padx=(0, 10))
        update_pause_btn()

        def on_reset_click():
            def reset_timer():
                # TODO: Add your backend reset logic here
                print("Reset timer functionality - backend integration needed")
                # Example: Reset the user state
                # with self.user_state.lock:
                #     self.user_state.screen_time = 0
                #     self.user_state.total_break_duration = 0
                #     self.user_state.screentime_per_app.clear()
            
            show_reset_warning(reset_timer)
        
        reset_btn = self._add_to_current_page(ctk.CTkButton(heading_row, width=48, height=48, corner_radius=24, font=("Segoe UI", 24),
                                  text="⟳", fg_color="#232b3b", hover_color="#2979ff", text_color="#fff",
                                  command=on_reset_click))
        reset_btn.pack(side="right", padx=(0, 10))

        date_label = self._add_to_current_page(ctk.CTkLabel(dashboard_container, text=datetime.now().strftime("%A, %B %d, %Y"),
                                      font=("Segoe UI", 16), text_color="#b0b8c1"))
        date_label.pack(anchor="w", pady=(0, 20))

        # ========== Simplified Stats Cards ==========
        stats_frame = self._add_to_current_page(ctk.CTkFrame(dashboard_container, fg_color="transparent"))
        stats_frame.pack(pady=(0, 20))

        # Today's Usage card
        todays_card, self.todays_usage_label = self.create_stat_card(
            stats_frame, "Today's Usage", "0h 0m", "🕒", "#2979ff", wide=True
        )
        todays_card.pack(side="left", padx=(0, 20))

        # Weekly Avg card stays static for now
        weekly_card, _ = self.create_stat_card(
            stats_frame, "Weekly Avg", "5.2h", "📈", "#00bfae", wide=True
        )
        weekly_card.pack(side="left")

        # ========== Screen Time Progress ==========
        st_frame = self._add_to_current_page(ctk.CTkFrame(dashboard_container, fg_color="transparent"))
        st_frame.pack(pady=(0, 20), fill="x")

        self._add_to_current_page(ctk.CTkLabel(st_frame, text="Screen Time Progress", font=("Segoe UI", 18, "bold"), text_color="#00bfae")).pack(anchor="w", pady=(0, 5))

        self.screen_time_progress = self._add_to_current_page(ctk.CTkProgressBar(st_frame, height=20, progress_color="#00bfae"))
        self.screen_time_progress.pack(fill="x")

        # Status row
        status_frame = self._add_to_current_page(ctk.CTkFrame(st_frame, fg_color="transparent"))
        status_frame.pack(fill="x", pady=5)

        self.screen_time_percent_label = self._add_to_current_page(ctk.CTkLabel(status_frame, text="0%", text_color="#ffffff", font=("Segoe UI", 14)))
        self.screen_time_percent_label.pack(side="left")

        self.screen_time_time_label = self._add_to_current_page(ctk.CTkLabel(status_frame, text="0h 0m / 24h", text_color="#b0b8c1", font=("Segoe UI", 14)))
        self.screen_time_time_label.pack(side="right")

        # On Track / Paused Badge
        self.tracking_status_label = self._add_to_current_page(ctk.CTkLabel(
            st_frame,
            text="On Track" if self.is_tracking else "Paused",
            text_color="#ffffff",
            fg_color="#00c853" if self.is_tracking else "#ff5252",
            corner_radius=12,
            font=("Segoe UI", 12),
            width=80
        ))
        self.tracking_status_label.pack(pady=5, anchor="e")
        
        def update_tracking_status_label():
            if self.is_tracking:
                self.tracking_status_label.configure(text="On Track", fg_color="#00c853", text_color="#ffffff")
            else:
                self.tracking_status_label.configure(text="Paused", fg_color="#ff5252", text_color="#ffffff")
            # Also update warning message
            if hasattr(self, 'update_warning_message'):
                self.update_warning_message()
        self.update_tracking_status_label = update_tracking_status_label

        # ========== Break Time Progress ==========
        bt_frame = self._add_to_current_page(ctk.CTkFrame(dashboard_container, fg_color="transparent"))
        bt_frame.pack(pady=(0, 20), fill="x")

        self._add_to_current_page(ctk.CTkLabel(bt_frame, text="Break Time Today", font=("Segoe UI", 18, "bold"), text_color="#2979ff")).pack(anchor="w", pady=(0, 5))

        self.break_time_progress = self._add_to_current_page(ctk.CTkProgressBar(bt_frame, height=20, progress_color="#2979ff"))
        self.break_time_progress.pack(fill="x")

        self.break_time_percent_label = self._add_to_current_page(ctk.CTkLabel(bt_frame, text="0%", font=("Segoe UI", 14), text_color="#ffffff"))
        self.break_time_percent_label.pack(anchor="w")

        self.break_time_time_label = self._add_to_current_page(ctk.CTkLabel(bt_frame, text="0h 0m / 24h", font=("Segoe UI", 14), text_color="#b0b8c1"))
        self.break_time_time_label.pack(anchor="e")

        # ========== Warning Card Section ==========
        self.build_warning_card(dashboard_container)

        self.current_page = "Home"
        self.update_progress_bars()

    def update_progress_bars(self):
        try:
            # Performance optimization: check if enough time has passed
            current_time = time.time()
            if current_time - self._last_update_time < (self._update_interval / 1000):
                self.after(self._update_interval, self.update_progress_bars)
                return
            
            self._last_update_time = current_time

            if not hasattr(self, "screen_time_progress") or not self.screen_time_progress.winfo_exists():
                return 

            if not hasattr(self, "break_time_progress") or not self.break_time_progress.winfo_exists():
                return

            with self.user_state.lock:
                screen_sec = self.user_state.screen_time
                break_sec = self.user_state.total_break_duration

            screen_progress = min(1.0, screen_sec / 86400)
            break_progress = min(1.0, break_sec / 86400)

            self.screen_time_progress.set(screen_progress)
            self.break_time_progress.set(break_progress)

            st_hours = int(screen_sec // 3600)
            st_mins = int((screen_sec % 3600) // 60)

            if hasattr(self, "todays_usage_label") and self.todays_usage_label.winfo_exists():
                self.todays_usage_label.configure(text=f"{st_hours}h {st_mins}m")

            brk_hours = int(break_sec // 3600)
            brk_mins = int((break_sec % 3600) // 60)

            screen_pct = screen_progress * 100
            break_pct = break_progress * 100

            if hasattr(self, "screen_time_percent_label") and self.screen_time_percent_label.winfo_exists():
                self.screen_time_percent_label.configure(text=f"{screen_pct:.1f}%")

            if hasattr(self, "screen_time_time_label") and self.screen_time_time_label.winfo_exists():
                self.screen_time_time_label.configure(text=f"{st_hours}h {st_mins}m / 24h")

            if hasattr(self, "break_time_percent_label") and self.break_time_percent_label.winfo_exists():
                self.break_time_percent_label.configure(text=f"{break_pct:.1f}%")

            if hasattr(self, "break_time_time_label") and self.break_time_time_label.winfo_exists():
                self.break_time_time_label.configure(text=f"{brk_hours}h {brk_mins}m / 24h")

        except Exception as e:
            print(f"[UI Update Error]: {e}")

        self.after(self._update_interval, self.update_progress_bars)

    def load_history_page(self, page_index=0):
        # Clear current page widgets
        self._clear_current_page_widgets()

        # Create heading for history page without background
        top_label = self._add_to_current_page(ctk.CTkLabel(self.main_frame, text="Usage History",
                                      font=("Segoe UI", 32, "bold"), text_color="#00bfae"))
        top_label.pack(anchor="w", padx=30, pady=(40, 5))

        date_label = self._add_to_current_page(ctk.CTkLabel(self.main_frame, text=datetime.now().strftime("%A, %B %d, %Y"),
                                      font=("Segoe UI", 16), text_color="#b0b8c1"))
        date_label.pack(anchor="w", padx=30, pady=(0, 20))

        # Simplified sample data - reduced for better performance
        sample_data = [
            ["2025-08-01", "6h 15m", "1h 30m", "Chrome"],
            ["2025-08-02", "7h 5m", "2h 10m", "VSCode"],
            ["2025-08-03", "5h 45m", "1h", "YouTube"],
        ] * 2  # Further reduced for better performance on low-end devices

        start = page_index * self.rows_per_page
        end = start + self.rows_per_page
        paged_data = sample_data[start:end]

        # Use app theme color for history frame
        history_frame = self._add_to_current_page(ctk.CTkFrame(self.main_frame, fg_color="#232b3b"))
        history_frame.pack(fill="both", expand=True, padx=30, pady=20)

        headers = ["Date", "Screen Time", "Break Time", "Top App", ""]
        for col, header in enumerate(headers):
            lbl = self._add_to_current_page(ctk.CTkLabel(history_frame, text=header, font=("Segoe UI", 16, "bold"), text_color="#2979ff"))
            lbl.grid(row=0, column=col, padx=10, pady=10, sticky="nsew")

        for i, row in enumerate(paged_data, start=1):
            for j, val in enumerate(row):
                # Alternate row color for better readability
                row_bg = "#181f2a" if i % 2 == 0 else "#232b3b"
                cell = self._add_to_current_page(ctk.CTkLabel(history_frame, text=val, font=("Segoe UI", 14), text_color="#ffffff", fg_color=row_bg))
                cell.grid(row=i, column=j, padx=10, pady=8, sticky="nsew")

            self._add_to_current_page(ctk.CTkButton(history_frame, text="View", width=60, height=30, fg_color="#2979ff",
                        hover_color="#00bfae", font=("Segoe UI", 12), text_color="#ffffff")).grid(row=i, column=4, padx=10, pady=8)

        for col in range(len(headers)):
            history_frame.grid_columnconfigure(col, weight=1)

        total_pages = (len(sample_data) + self.rows_per_page - 1) // self.rows_per_page

        if total_pages > 1:
            pagination = self._add_to_current_page(ctk.CTkFrame(self.main_frame, fg_color="#232b3b"))
            pagination.pack(pady=10)
            for i in range(total_pages):
                btn = self._add_to_current_page(ctk.CTkButton(pagination, text=str(i+1), width=35, font=("Segoe UI", 12),
                                    fg_color="#232b3b" if i != page_index else "#00bfae",
                                    hover_color="#2979ff" if i == page_index else "#232b3b",
                                    text_color="#ffffff" if i == page_index else "#b0b8c1",
                                    command=lambda i=i: self.load_history_page(i)))
                btn.pack(side="left", padx=5)

        self.current_page_index = page_index

    def load_restricted_page(self):
        # Clear current page widgets
        self._clear_current_page_widgets()

        # Create heading for restricted page without background
        top_label = self._add_to_current_page(ctk.CTkLabel(self.main_frame, text="Restricted Apps and Domains",
                                      font=("Segoe UI", 32, "bold"), text_color="#00bfae"))
        top_label.pack(anchor="w", padx=30, pady=(40, 5))

        date_label = self._add_to_current_page(ctk.CTkLabel(self.main_frame, text=datetime.now().strftime("%A, %B %d, %Y"),
                                      font=("Segoe UI", 16), text_color="#b0b8c1"))
        date_label.pack(anchor="w", padx=30, pady=(0, 20))

        container = self._add_to_current_page(ctk.CTkScrollableFrame(self.main_frame, fg_color="#232b3b"))
        container.pack(fill="both", expand=True, padx=30, pady=20)

        def refresh_blocked():
            for widget in container.winfo_children():
                widget.destroy()
            add_table_section("Blocked Apps", self.blocked_apps, is_app=True)
            add_table_section("Blocked URLs", self.blocked_urls, is_app=False)

        def add_table_section(title, items, is_app):
            # Table header
            table_frame = ctk.CTkFrame(container, fg_color="#232b3b", corner_radius=14)
            table_frame.pack(fill="x", pady=(0, 20))
            header = ctk.CTkFrame(table_frame, fg_color="#205080", corner_radius=8)  # Less bright blue
            header.pack(fill="x")
            ctk.CTkLabel(header, text=title, font=("Segoe UI", 16, "bold"), text_color="#ffffff").grid(row=0, column=0, padx=12, pady=8, sticky="w")
            ctk.CTkLabel(header, text="Action", font=("Segoe UI", 14, "bold"), text_color="#ffffff").grid(row=0, column=1, padx=12, pady=8, sticky="e")
            header.grid_columnconfigure(0, weight=1)
            header.grid_columnconfigure(1, weight=0)

            # Table rows
            for idx, item in enumerate(items, 1):
                row_bg = "#181f2a" if idx % 2 == 0 else "#232b3b"
                row = ctk.CTkFrame(table_frame, fg_color=row_bg)
                row.pack(fill="x")
                ctk.CTkLabel(row, text=f"{idx}. {item}", font=("Segoe UI", 14), text_color="#ffffff").grid(row=0, column=0, padx=12, pady=10, sticky="w")
                unblock_btn = ctk.CTkButton(row, text="Unblock", width=80, height=30, font=("Segoe UI", 12, "bold"),
                                             fg_color="#205080", hover_color="#00bfae", text_color="#ffffff",
                                             corner_radius=8,
                                             command=lambda item=item, items=items: (items.remove(item), refresh_blocked()))
                unblock_btn.grid(row=0, column=1, padx=12, pady=6, sticky="e")
                row.grid_columnconfigure(0, weight=1)
                row.grid_columnconfigure(1, weight=0)
                # Subtle separator
                if idx < len(items):
                    ctk.CTkFrame(table_frame, height=2, fg_color="#181f2a").pack(fill="x", padx=8)

            # Add button below table, centered
            if is_app:
                add_btn = ctk.CTkButton(table_frame, text="+ Add App", font=("Segoe UI", 14, "bold"), fg_color="#205080",
                                         hover_color="#00bfae", text_color="#ffffff", corner_radius=8, command=self.add_app)
            else:
                add_btn = ctk.CTkButton(table_frame, text="+ Add URL", font=("Segoe UI", 14, "bold"), fg_color="#205080",
                                         hover_color="#205080", text_color="#ffffff", corner_radius=8, command=self.add_url_input)
            add_btn.pack(pady=10)
            add_btn.pack_configure(anchor="center")

        refresh_blocked()

    def add_app(self):
        file_path = filedialog.askopenfilename(filetypes=[("Executable Files", "*.exe")])
        if file_path:
            exe_name = file_path.split("/")[-1]
            if exe_name not in self.blocked_apps:
                self.blocked_apps.append(exe_name)
                self.load_page("Restricted")  # ← better than load_restricted_page()

    def add_url_input(self):
        popup = ctk.CTkToplevel(self)
        popup.geometry("400x150")
        popup.title("Add Blocked URL")
        popup.configure(fg_color="#1c1c1c")
        popup.grab_set()  # <<< Add this to bring it to front and lock focus

        label = ctk.CTkLabel(popup, text="Enter URL to block:", font=("Segoe UI", 15), text_color="white")
        label.pack(pady=(20, 5))

        entry = ctk.CTkEntry(popup, placeholder_text="e.g. facebook.com", font=("Segoe UI", 14))
        entry.pack(padx=20, pady=10, fill="x")

        def submit():
            url = entry.get().strip()
            if url and url not in self.blocked_urls:
                self.blocked_urls.append(url)
                popup.destroy()
                self.load_page("Restricted")  # Ensures clean UI reload

        submit_btn = ctk.CTkButton(popup, text="Add", font=("Segoe UI", 14), fg_color="#3CBF8F", command=submit)
        submit_btn.pack(pady=10)

    def create_info_card(self, parent, title, value, color):
        card = ctk.CTkFrame(parent, width=200, height=100, fg_color=color, corner_radius=12)
        card.pack_propagate(False)
        ctk.CTkLabel(card, text=title, font=("Segoe UI", 14, "bold"), text_color="black").pack(pady=(10, 0))
        ctk.CTkLabel(card, text=value, font=("Segoe UI", 18), text_color="black").pack(pady=(5, 0))
        return card

    def create_progress_section(self, parent, label_text, hours, color):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        label_row = ctk.CTkFrame(frame, fg_color="transparent")
        label_row.pack(fill="x", pady=(0, 5))

        ctk.CTkLabel(label_row, text=label_text, font=("Segoe UI", 18), text_color="#cccccc").pack(side="left", padx=10)
        percent = min(100, round((hours / 24) * 100))
        ctk.CTkLabel(label_row, text=f"{percent}%", font=("Segoe UI", 16), text_color="#DDDDDD").pack(side="left")
        ctk.CTkLabel(label_row, text=f"{int(hours)}h {int((hours % 1) * 60)}m / 24h", font=("Segoe UI", 15), text_color="#999999").pack(side="right", padx=10)

        bar = ctk.CTkProgressBar(frame, height=25, progress_color=color)
        bar.set(hours / 24)
        bar.pack(fill="x", padx=10)
        return frame

    def toggle_tracking(self):
        self.is_tracking = not self.is_tracking
        self.update_pause_btn()
        self.update_tracking_status_label()
    
    def set_warning_message(self, message):
        if hasattr(self, 'warning_message_label') and self.warning_message_label.winfo_exists():
            self.warning_message_label.configure(text=message)
        else:
            self.load_dashboard()  # Fallback in case it was destroyed
            if hasattr(self, 'warning_message_label'):
                self.warning_message_label.configure(text=message)

    def get_warning_message(self):
        """
        Get the current warning message.
        
        Returns:
            str: The current warning message
        """
        if hasattr(self, 'warning_message_label') and self.warning_message_label.winfo_exists():
            return self.warning_message_label.cget("text")
        return ""


