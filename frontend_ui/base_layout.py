from frontend_ui.notification import show_reset_warning
from state.userstate import UserActivityState
from pystray import MenuItem as item
from utils.utilities import Utility
from logs.app_logger import logger
from storage.db import Database
from tkinter import filedialog
from datetime import datetime 
import customtkinter as ctk
from PIL import Image
import threading
import pystray
import time
import os

shutdown_event = threading.Event()
tray_icon = None
HOST_PATH = r"C:\Windows\System32\drivers\etc\hosts"
db = Database()

class TimeTrackerApp(ctk.CTk):
    def __init__(self , state: UserActivityState):
        super().__init__()
        self.user_state = state
        self.tracker_thread = None
        self.reminder_thread = None
        self.add_url_warning_message = (
            "Warning: Make sure to close all the browsers to block an url. Enter a domain only (e.g., xyz.com or www.xyz.com)."
        )
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.title("PyTracker")
        self.minsize(900, 700)
        self.bind("<Configure>", self.on_window_resize)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        
        self.configure(fg_color="#181f2a")
        
        try:
            self.attributes('-alpha', 1.0)  
        except:
            pass 

        self.is_tracking = True
        self.current_page_index = 0
        self.rows_per_page = 10

        self.blocked_apps = set(db.load_blocked_apps())
        self.blocked_urls = set(db.load_blocked_urls())
        if self.blocked_apps:
            Utility.start_app_blocker(self.blocked_apps, scan_interval=1)

        # ==== Modern Sidebar with Modern Colors ==== #
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=20, fg_color="#232b3b")
        self.sidebar_frame.pack(side="left", fill="y", padx=0, pady=0)
        self.sidebar_frame.pack_propagate(False)

        # ==== Navigation Buttons with Modern Colors ===== #
        self.nav_buttons = {}
        self._nav_icon_sources = {}
        self._nav_ctk_images = {}
        nav_items = [
            ("Home", "home.png"),
            ("Restricted", "block.png"),
            ("History", "history.png")
        ]
        for name, icon_file in nav_items:
            icon_path = os.path.join("frontend_ui", icon_file)
            icon_img = Image.open(icon_path)
            self._nav_icon_sources[name] = icon_img
            icon = ctk.CTkImage(icon_img, size=(28, 28))
            self._nav_ctk_images[name] = icon
            btn = ctk.CTkButton(
                self.sidebar_frame, text=name, image=icon, compound="left",
                font=("Segoe UI", 15), corner_radius=12, fg_color="#232b3b", hover_color="#2979ff",
                text_color="#ffffff", anchor="w", width=180, height=40,
                command=lambda n=name: self.load_page(n)
            )
            btn.pack(fill="x", padx=20, pady=8)
            self.nav_buttons[name] = btn

        # ========= Main Frame with Transparent/Blurred Look ====== #
        self.main_frame = ctk.CTkFrame(self, corner_radius=20, fg_color="#181824")
        self.main_frame.pack(side="right", expand=True, fill="both", padx=0, pady=0)

        self.current_page = None
        self.load_page("Home")

        self.current_breakpoint = None
        self.responsive_rules = {
            "xl": {
                "sidebar_w": 220, "nav_font": 15, "nav_height": 40, "nav_icon": 28,
                "heading": 40, "pause": 48, "reset": 48, "progress": 22,
                "stat_icon": 28, "stat_title": 17, "stat_value": 28,
            },
            "lg": {
                "sidebar_w": 210, "nav_font": 15, "nav_height": 38, "nav_icon": 26,
                "heading": 38, "pause": 46, "reset": 46, "progress": 21,
                "stat_icon": 26, "stat_title": 16, "stat_value": 26,
            },
            "md": {
                "sidebar_w": 195, "nav_font": 14, "nav_height": 36, "nav_icon": 24,
                "heading": 36, "pause": 44, "reset": 44, "progress": 20,
                "stat_icon": 24, "stat_title": 15, "stat_value": 24,
            },
            "sm": {
                "sidebar_w": 180, "nav_font": 13, "nav_height": 36, "nav_icon": 22,
                "heading": 34, "pause": 42, "reset": 42, "progress": 19,
                "stat_icon": 22, "stat_title": 14, "stat_value": 22,
            },
            "xs": {
                "sidebar_w": 170, "nav_font": 13, "nav_height": 34, "nav_icon": 20,
                "heading": 32, "pause": 42, "reset": 42, "progress": 18,
                "stat_icon": 20, "stat_title": 13, "stat_value": 20,
            },
        }
    
    def build_warning_card(self, parent, compact: bool = False):
        # Clear any previous warning widgets in the given parent
        for child in parent.winfo_children():
            try:
                child.destroy()
            except Exception:
                pass

        if compact:
            # Compact single-line/paragraph label to avoid layout issues on small screens
            if self.is_tracking:
                text = "💡 Reminder: While taking a break, minimize all activity and let your system idle or enter sleep mode."
                color = "#fcc326"
            else:
                text = "⚠️ Warning: Tracking disabled. Resume immediately to continue logging activity and breaks."
                color = "#CF0000"

            self.warning_card = None
            self.warning_compact_label = ctk.CTkLabel(
                parent,
                text=text,
                font=("Segoe UI", 13, "bold"),
                text_color=color,
                wraplength=900,
                justify="left",
            )
            self.warning_compact_label.pack(fill="x", padx=30, pady=(6, 10))

            def update_warning_message():
                if self.is_tracking:
                    self.warning_compact_label.configure(
                        text=(
                            "💡 Reminder: While taking a break, minimize all activity and let your system idle or enter sleep mode."
                        ),
                        text_color="#fcc326",
                    )
                else:
                    self.warning_compact_label.configure(
                        text=(
                            "⚠️ Warning: Tracking disabled. Resume immediately to continue logging activity and breaks."
                        ),
                        text_color="#CF0000",
                    )
            self.update_warning_message = update_warning_message
            update_warning_message()
            return

        self.warning_card = ctk.CTkFrame(parent, fg_color="#232b3b", corner_radius=16)
        self.warning_card.pack(fill="x", padx=30, pady=(0, 18))

        content_frame = ctk.CTkFrame(self.warning_card, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=6)

        header_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        header_frame.pack(anchor="w")

        head = text = ""
        head_color = text_color = None
        if not self.is_tracking:
            head = "Warning"
            text = "Tracking disabled. Resume immediately to continue logging activity and breaks."
            text_color = "#CF0000"
            head_color = "#ff0000"
        else:
            head = "Reminder"
            text = "While taking a break, minimize all activity and let your system idle or enter sleep mode."
            text_color = "#fcc326"
            head_color = "#e7b500"

        self.warning_icon_label = ctk.CTkLabel(header_frame, text="⚠️", font=("Segoe UI", 24), text_color=head_color)
        self.warning_icon_label.pack(side="left", padx=(0, 10))

        self.warning_head_label = ctk.CTkLabel(header_frame, text=head, font=("Segoe UI", 18, "bold"), text_color=head_color)
        self.warning_head_label.pack(side="left")

        self.warning_message_label = ctk.CTkLabel(
            content_frame,
            text=text,
            font=("Segoe UI", 16, "bold"),
            text_color=text_color,
            wraplength=800,
            justify="left",
        )
        self.warning_message_label.pack(anchor="w", pady=(4, 0))

        def update_warning_message():
            if self.is_tracking:
                self.warning_icon_label.configure(text="💡", text_color="#e7b500")
                self.warning_head_label.configure(text="Reminder", text_color="#e7b500")
                self.warning_message_label.configure(
                    text="While taking a break, minimize all activity and let your system idle or enter sleep mode.",
                    text_color="#fcc326",
                )
            else:
                self.warning_icon_label.configure(text="⚠️", text_color="#ff0000")
                self.warning_head_label.configure(text="Warning", text_color="#ff0000")
                self.warning_message_label.configure(
                    text="Tracking disabled. Resume immediately to continue logging activity and breaks.",
                    text_color="#CF0000",
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
        icon_image = Image.open(icon_path)

        def _on_show(icon, item):
            self.deiconify()
            icon.stop()

        def _on_exit(icon, item):
            threading.Thread(target=self.graceful_shutdown, daemon=True).start()

        menu = pystray.Menu(
            item("Show", _on_show),
            item("Exit", _on_exit)
        )

        tray_icon = pystray.Icon("PyTracker", icon_image, "PyTracker", menu)
        threading.Thread(target=tray_icon.run, daemon=True).start()

    def on_closing(self):
        """Hide the window to tray instead of exiting."""
        self.withdraw()
        self.show_tray_icon()

    def load_page(self, name):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        if name == "Home":
            self.load_dashboard()
        elif name == "Restricted":
            self.load_restricted_page()
        elif name == "History":
            self.load_history_page(self.current_page_index)

    def create_stat_card(self, parent, title, value, icon, bg_color, wide=False):
        card_width = 260 if wide else 170
        card_height = 110 if wide else 80
        card = ctk.CTkFrame(parent, width=card_width, height=card_height, fg_color="transparent", corner_radius=16)
        card.pack_propagate(False)

        ctk.CTkLabel(card, text=icon, font=("Segoe UI", 28 if wide else 22), text_color=bg_color).pack(pady=(8, 0))
        ctk.CTkLabel(card, text=title, font=("Segoe UI", 17 if wide else 14, "bold"), text_color="#b0b8c1").pack()
        value_label = ctk.CTkLabel(card, text=value, font=("Segoe UI", 28 if wide else 18, "bold"), text_color=bg_color)
        value_label.pack()
        return card , value_label

    def load_dashboard(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        self.main_frame.pack_propagate(False)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        dashboard_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        dashboard_container.grid(row=0, column=0, sticky="nsew")

        bottom_warning_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        bottom_warning_container.pack(side="bottom", fill="x")

        dashboard_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        dashboard_container.pack(side="top", fill="both", expand=True)
        
        heading_row = ctk.CTkFrame(dashboard_container, fg_color="transparent")
        heading_row.pack(fill="x", padx=30, pady=(40, 0))

        self.dashboard_heading = ctk.CTkLabel(heading_row, text="Dashboard",
                                      font=("Segoe UI", 40, "bold"), text_color="#00bfae")
        self.dashboard_heading.pack(side="left")

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
        self.pause_btn = ctk.CTkButton(heading_row, width=48, height=48, corner_radius=24, font=("Segoe UI", 28),
                                  command=toggle_tracking, text="⏸", fg_color="#ff5252", hover_color="#ff1744", text_color="#fff")
        self.pause_btn.pack(side="right", padx=(0, 10))
        update_pause_btn()

        def on_reset_click():
            def reset_timer():
                today = datetime.now().strftime("%Y-%m-%d")
                db.reset_data(date=today)
                with self.user_state.lock:
                    self.user_state.screen_time = 0
                    self.user_state.total_break_duration = 0
                    self.user_state.screentime_per_app.clear()
                print("Reset performed")
            show_reset_warning(reset_timer)
        
        self.reset_btn = ctk.CTkButton(heading_row, width=48, height=48, corner_radius=24, font=("Segoe UI", 24),
                                  text="⟳", fg_color="#232b3b", hover_color="#2979ff", text_color="#fff",
                                  command=on_reset_click)
        self.reset_btn.pack(side="right", padx=(0, 10))

        date_label = ctk.CTkLabel(dashboard_container, text=datetime.now().strftime("%A, %B %d, %Y"),
                                      font=("Segoe UI", 18), text_color="#b0b8c1")
        date_label.pack(anchor="w", padx=30, pady=(0, 20))

        # ========== Time & Tracking Status ==========
        top_bar = ctk.CTkFrame(dashboard_container, fg_color="transparent")
        top_bar.pack(fill="x", padx=30)

        right_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        right_frame.pack(side="right", padx=10)

        """TODO: Replace with some other element in future"""
        time_label = ctk.CTkLabel(right_frame, text="", font=("Segoe UI", 20, "bold"), text_color="#ffffff")
        time_label.pack(anchor="e")
        status_label = ctk.CTkLabel(right_frame, text="", font=("Segoe UI", 14), text_color="#00c853")
        status_label.pack(anchor="e")

        # ========== Centered Stats Cards (Today & Weekly) ==========
        stats_frame = ctk.CTkFrame(dashboard_container, fg_color="transparent")
        stats_frame.pack(pady=(0, 0))

        todays_card, self.todays_usage_label = self.create_stat_card(
            stats_frame, "Today's Usage", "0h 0m", "🕒", "#2979ff", wide=True
        )
        todays_card.pack(side="left", padx=30)

        self.weekly_card, self.weekly_avg_label = self.create_stat_card(
            stats_frame, "Weekly Avg", "0h 0m", "📈", "#00bfae", wide=True
        )
        self.weekly_card.pack(side="left", padx=30)
        
        # ========== Screen Time Progress ==========
        st_frame = ctk.CTkFrame(dashboard_container, fg_color="transparent")
        st_frame.pack(pady=(20, 0), padx=30, fill="x")

        ctk.CTkLabel(st_frame, text="Screen Time Progress", font=("Segoe UI", 18, "bold"), text_color="#00bfae").pack(anchor="w", padx=15, pady=(10, 5))

        self.screen_time_progress = ctk.CTkProgressBar(st_frame, height=22, progress_color="#00bfae")
        self.screen_time_progress.pack(fill="x", padx=15)

        status_frame = ctk.CTkFrame(st_frame, fg_color="transparent")
        status_frame.pack(fill="x", padx=15, pady=5)

        self.screen_time_percent_label = ctk.CTkLabel(status_frame, text="0%", text_color="#ffffff", font=("Segoe UI", 15))
        self.screen_time_percent_label.pack(side="left")

        self.screen_time_time_label = ctk.CTkLabel(status_frame, text="0h 0m / 24h", text_color="#b0b8c1", font=("Segoe UI", 14))
        self.screen_time_time_label.pack(side="right")

        self.tracking_status_label = ctk.CTkLabel(
            st_frame,
            text="On Track" if self.is_tracking else "Paused",
            text_color="#ffffff",
            fg_color="#00c853" if self.is_tracking else "#ff5252",
            corner_radius=12,
            font=("Segoe UI", 13),
            width=80
        )
        self.tracking_status_label.pack(pady=5, padx=15, anchor="e")

        def update_tracking_status_label():
            if self.is_tracking:
                self.tracking_status_label.configure(text="On Track", fg_color="#00c853", text_color="#ffffff")
            else:
                self.tracking_status_label.configure(text="Paused", fg_color="#ff5252", text_color="#ffffff")
            if hasattr(self, 'update_warning_message'):
                self.update_warning_message()
        self.update_tracking_status_label = update_tracking_status_label

        # ========== Break Time Progress ==========
        bt_frame = ctk.CTkFrame(dashboard_container, fg_color="transparent")
        bt_frame.pack(pady=(5, 0), padx=30, fill="x")

        ctk.CTkLabel(bt_frame, text="Break Time Today", font=("Segoe UI", 18, "bold"), text_color="#2979ff").pack(anchor="w", padx=15, pady=(6, 4))

        self.break_time_progress = ctk.CTkProgressBar(bt_frame, height=22, progress_color="#2979ff")
        self.break_time_progress.pack(fill="x", padx=15)

        status_frame2 = ctk.CTkFrame(bt_frame, fg_color="transparent")
        status_frame2.pack(fill="x", padx=15, pady=(2, 4))
        self.break_time_percent_label = ctk.CTkLabel(status_frame2, text="0%", font=("Segoe UI", 15), text_color="#ffffff")
        self.break_time_percent_label.pack(side="left")
        self.break_time_time_label = ctk.CTkLabel(status_frame2, text="0h 0m / 24h", font=("Segoe UI", 14), text_color="#b0b8c1")
        self.break_time_time_label.pack(side="right")

        # ========== Warning Card Section ==========
        # Store container to rebuild warning view on size changes
        self.bottom_warning_container = bottom_warning_container
        # Build full card by default; compact will be applied on resize if needed
        self.build_warning_card(self.bottom_warning_container, compact=False)
        ctk.CTkFrame(dashboard_container, height=1, fg_color="transparent").pack(fill="both", expand=True)
        
        self.current_page = "Home"
        self.update_progress_bars()

        # Reset compact_mode so fresh render applies correctly
        self.compact_mode = None
        # Apply compact layout on first render as needed, forcing rebuild
        self.after(0, lambda: self.apply_compact_layout(self.should_use_compact(), force=True))
        # Also apply breakpoint-driven scaling on first render
        self.after(0, self.apply_breakpoints)

    def should_use_compact(self) -> bool:
        try:
            return self.winfo_height() <= 720 or self.winfo_width() <= 1200
        except Exception:
            return False

    def on_window_resize(self, event):
        if event.widget is not self:
            return
        self.apply_compact_layout(self.should_use_compact())
        self.apply_breakpoints()

    def apply_compact_layout(self, compact: bool, force: bool = False):
        # Avoid redundant reconfiguration
        if not force and getattr(self, "compact_mode", None) == compact:
            return
        self.compact_mode = compact

        # Sidebar scaling
        try:
            self.sidebar_frame.configure(width=(170 if compact else 220))
            for btn in getattr(self, "nav_buttons", {}).values():
                btn.configure(font=("Segoe UI", 13 if compact else 15), height=(36 if compact else 40))
        except Exception:
            pass

        # Heading and control buttons
        try:
            if hasattr(self, "dashboard_heading") and self.dashboard_heading.winfo_exists():
                self.dashboard_heading.configure(font=("Segoe UI", 32 if compact else 40, "bold"))
            if hasattr(self, "pause_btn") and self.pause_btn.winfo_exists():
                self.pause_btn.configure(width=(42 if compact else 48), height=(42 if compact else 48), font=("Segoe UI", 24 if compact else 28))
            if hasattr(self, "reset_btn") and self.reset_btn.winfo_exists():
                self.reset_btn.configure(width=(42 if compact else 48), height=(42 if compact else 48), font=("Segoe UI", 20 if compact else 24))
        except Exception:
            pass

        # Progress bars thickness
        try:
            if hasattr(self, "screen_time_progress") and self.screen_time_progress.winfo_exists():
                self.screen_time_progress.configure(height=(18 if compact else 22))
            if hasattr(self, "break_time_progress") and self.break_time_progress.winfo_exists():
                self.break_time_progress.configure(height=(18 if compact else 22))
        except Exception:
            pass

        # Warning presentation: compact text for small, full card for large
        try:
            if hasattr(self, "bottom_warning_container") and self.bottom_warning_container.winfo_exists():
                self.build_warning_card(self.bottom_warning_container, compact=compact)
        except Exception:
            pass

    def get_breakpoint(self) -> str:
        """Return responsive breakpoint similar to CSS media queries.
        xl: >1400, lg: >1200, md: >1000, sm: >850, xs: <=850
        """
        w = 0
        try:
            w = self.winfo_width()
        except Exception:
            return "md"
        if w > 1400:
            return "xl"
        if w > 1200:
            return "lg"
        if w > 1000:
            return "md"
        if w > 850:
            return "sm"
        return "xs"

    def apply_breakpoints(self):
        bp = self.get_breakpoint()
        if self.current_breakpoint == bp:
            return
        self.current_breakpoint = bp
        rules = self.responsive_rules.get(bp, self.responsive_rules["md"])

        # Sidebar and nav buttons
        try:
            self.sidebar_frame.configure(width=rules["sidebar_w"])
            for name, btn in self.nav_buttons.items():
                btn.configure(font=("Segoe UI", rules["nav_font"]), height=rules["nav_height"], width=rules["sidebar_w"] - 40)
                # Resize icons
                if name in self._nav_icon_sources:
                    src = self._nav_icon_sources[name]
                    img = ctk.CTkImage(src, size=(rules["nav_icon"], rules["nav_icon"]))
                    self._nav_ctk_images[name] = img
                    btn.configure(image=img)
        except Exception:
            pass

        # Headings and buttons
        try:
            if hasattr(self, "dashboard_heading") and self.dashboard_heading.winfo_exists():
                self.dashboard_heading.configure(font=("Segoe UI", rules["heading"], "bold"))
            if hasattr(self, "pause_btn") and self.pause_btn.winfo_exists():
                self.pause_btn.configure(width=rules["pause"], height=rules["pause"], font=("Segoe UI", max(20, rules["pause"] - 20)))
            if hasattr(self, "reset_btn") and self.reset_btn.winfo_exists():
                self.reset_btn.configure(width=rules["reset"], height=rules["reset"], font=("Segoe UI", max(18, rules["reset"] - 22)))
        except Exception:
            pass

        # Progress bars
        try:
            if hasattr(self, "screen_time_progress") and self.screen_time_progress.winfo_exists():
                self.screen_time_progress.configure(height=rules["progress"])
            if hasattr(self, "break_time_progress") and self.break_time_progress.winfo_exists():
                self.break_time_progress.configure(height=rules["progress"])
        except Exception:
            pass


    def update_progress_bars(self):
        try:
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

            # Update weekly average label dynamically from DB
            try:
                weekly_avg_seconds = db.get_weekly_average_screen_time(days=7)
                wa_hours = int(weekly_avg_seconds // 3600)
                wa_mins = int((weekly_avg_seconds % 3600) // 60)
                if hasattr(self, "weekly_avg_label") and self.weekly_avg_label.winfo_exists():
                    self.weekly_avg_label.configure(text=f"{wa_hours}h {wa_mins}m")
            except Exception:
                pass

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

        self.after(500, self.update_progress_bars)


    def load_history_page(self, page_index=0):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        top_label = ctk.CTkLabel(self.main_frame, text="Usage History",
                                      font=("Segoe UI", 40, "bold"), text_color="#00bfae")
        top_label.pack(anchor="w", padx=30, pady=(40, 5))

        date_label = ctk.CTkLabel(self.main_frame, text=datetime.now().strftime("%A, %B %d, %Y"),
                                      font=("Segoe UI", 18), text_color="#b0b8c1")
        date_label.pack(anchor="w", padx=30, pady=(0, 20))

        db = Database()
        historu_data = db.get_user_history()

        start = page_index * self.rows_per_page
        end = start + self.rows_per_page
        paged_data = historu_data[start:end]

        history_frame = ctk.CTkFrame(self.main_frame, fg_color="#232b3b")
        history_frame.pack(fill="both", expand=True, padx=30, pady=20)

        headers = ["Sno", "Date", "Screen Time", "Break Time", "App Usage"]
        for col, header in enumerate(headers):
            lbl = ctk.CTkLabel(history_frame, text=header, font=("Segoe UI", 18, "bold"), text_color="#2979ff")
            lbl.grid(row=0, column=col, padx=10, pady=10, sticky="nsew")

        for i, row in enumerate(paged_data, start=1):
            for j, val in enumerate(row):
                row_bg = "#181f2a" if i % 2 == 0 else "#232b3b"
                cell = ctk.CTkLabel(history_frame, text=val, font=("Segoe UI", 16), text_color="#ffffff", fg_color=row_bg)
                cell.grid(row=i, column=j, padx=10, pady=8, sticky="nsew")

            date_value = row[1] if len(row) > 1 else None
            view_btn = ctk.CTkButton(
                history_frame,
                text="View",
                width=60,
                height=30,
                fg_color="#355691",
                hover_color="#008b7f",
                font=("Segoe UI", 14),
                text_color="#ffffff",
                command=(lambda d=date_value: self.load_app_usage_page(d)) if date_value else None,
            )
            view_btn.grid(row=i, column=4, padx=10, pady=8)

        for col in range(len(headers)):
            history_frame.grid_columnconfigure(col, weight=1)

        total_pages = (len(historu_data) + self.rows_per_page - 1) // self.rows_per_page

        if total_pages > 1:
            pagination = ctk.CTkFrame(self.main_frame, fg_color="#232b3b")
            pagination.pack(pady=10)
            for i in range(total_pages):
                btn = ctk.CTkButton(pagination, text=str(i+1), width=35, font=("Segoe UI", 14),
                                    fg_color="#232b3b" if i != page_index else "#00bfae",
                                    hover_color="#2979ff" if i == page_index else "#232b3b",
                                    text_color="#ffffff" if i == page_index else "#b0b8c1",
                                    command=lambda i=i: self.load_history_page(i))
                btn.pack(side="left", padx=5)

        self.current_page_index = page_index

    def load_restricted_page(self):
        self.blocked_apps = set(db.load_blocked_apps())
        self.blocked_urls = set(db.load_blocked_urls())

        if self.blocked_apps:
            Utility.start_app_blocker(self.blocked_apps, scan_interval=1)

        # Title
        top_label = ctk.CTkLabel(self.main_frame, text="Restricted Apps and Domains",
                                font=("Segoe UI", 40, "bold"), text_color="#00bfae")
        top_label.pack(anchor="w", padx=30, pady=(40, 5))

        date_label = ctk.CTkLabel(self.main_frame, text=datetime.now().strftime("%A, %B %d, %Y"),
                                font=("Segoe UI", 18), text_color="#b0b8c1")
        date_label.pack(anchor="w", padx=30, pady=(0, 20))

        container = ctk.CTkScrollableFrame(self.main_frame, fg_color="#232b3b")
        container.pack(fill="both", expand=True, padx=30, pady=20)

        def refresh_blocked():
            for widget in container.winfo_children():
                widget.destroy()
            add_table_section("Blocked Apps", self.blocked_apps, is_app=True)
            add_table_section("Blocked URLs", self.blocked_urls, is_app=False)

        def unblock_item(item, is_app):
            if is_app:
                Utility.stop_app_blocker()
                db.remove_from_blocked_apps(app_name=item)
                self.blocked_apps = set(db.load_blocked_apps())
                logger.debug(f"Blocked apps after removal: {self.blocked_apps}")
                if self.blocked_apps:
                    Utility.start_app_blocker(self.blocked_apps, scan_interval=1)
            else:
                Utility.clean_hosts_file(HOST_PATH, item)
                Utility.restart_dns_service()
                Utility.flush_dns()
                db.remove_from_blocked_url(url=item)
                self.blocked_urls = set(db.load_blocked_urls())

            refresh_blocked()

        def add_table_section(title, items, is_app):
            table_frame = ctk.CTkFrame(container, fg_color="#232b3b", corner_radius=14)
            table_frame.pack(fill="x", pady=(0, 20))

            header = ctk.CTkFrame(table_frame, fg_color="#205080", corner_radius=8)
            header.pack(fill="x")
            ctk.CTkLabel(header, text=title, font=("Segoe UI", 18, "bold"), text_color="#ffffff").grid(row=0, column=0, padx=12, pady=8, sticky="w")
            ctk.CTkLabel(header, text="Action", font=("Segoe UI", 16, "bold"), text_color="#ffffff").grid(row=0, column=1, padx=12, pady=8, sticky="e")
            header.grid_columnconfigure(0, weight=1)
            header.grid_columnconfigure(1, weight=0)

            for idx, item in enumerate(items, 1):
                row_bg = "#181f2a" if idx % 2 == 0 else "#232b3b"
                row = ctk.CTkFrame(table_frame, fg_color=row_bg)
                row.pack(fill="x")
                ctk.CTkLabel(row, text=f"{idx}. {item}", font=("Segoe UI", 16), text_color="#ffffff").grid(row=0, column=0, padx=12, pady=10, sticky="w")
                unblock_btn = ctk.CTkButton(row, text="Unblock", width=80, height=30, font=("Segoe UI", 14, "bold"),
                                            fg_color="#205080", hover_color="#00bfae", text_color="#ffffff",
                                            corner_radius=8,
                                            command=lambda item=item, is_app=is_app: unblock_item(item, is_app))
                unblock_btn.grid(row=0, column=1, padx=12, pady=6, sticky="e")
                row.grid_columnconfigure(0, weight=1)
                row.grid_columnconfigure(1, weight=0)
                if idx < len(items):
                    ctk.CTkFrame(table_frame, height=2, fg_color="#181f2a").pack(fill="x", padx=8)

            if is_app:
                add_btn = ctk.CTkButton(table_frame, text="+ Add App", font=("Segoe UI", 15, "bold"), fg_color="#205080",
                                        hover_color="#00bfae", text_color="#ffffff", corner_radius=8,
                                        command=lambda: add_app_db())
            else:
                add_btn = ctk.CTkButton(table_frame, text="+ Add URL", font=("Segoe UI", 15, "bold"), fg_color="#205080",
                                        hover_color="#00bfae", text_color="#ffffff", corner_radius=8,
                                        command=lambda: add_url_db())
            add_btn.pack(pady=10)
            add_btn.pack_configure(anchor="center")

        def add_app_db():
            """adds """
            file_path = filedialog.askopenfilename(filetypes=[("Executable Files", "*.exe")])
            if file_path:
                exe_name = os.path.basename(file_path)
                if exe_name not in self.blocked_apps:
                    Utility.stop_app_blocker()
                    db.insert_blocked_app(app_name=exe_name)
                    self.blocked_apps = set(db.load_blocked_apps())
                    if self.blocked_apps:
                        Utility.start_app_blocker(self.blocked_apps, scan_interval=1)
                    refresh_blocked()

        def add_url_db():
            """Creates the textbox popup to add url."""
            popup = ctk.CTkToplevel(self)
            popup.geometry("420x190")
            popup.title("Add Blocked URL")
            popup.configure(fg_color="#1c1c1c")
            popup.grab_set()

            popup.update_idletasks()
            width, height = 420, 190
            x = (popup.winfo_screenwidth() // 2) - (width // 2)
            y = (popup.winfo_screenheight() // 2) - (height // 2)
            popup.geometry(f"{width}x{height}+{x}+{y}")

            label = ctk.CTkLabel(popup, text="Enter URL to block:", font=("Segoe UI", 15), text_color="white")
            label.pack(pady=(20, 5))

            entry = ctk.CTkEntry(popup, placeholder_text="e.g. facebook.com", font=("Segoe UI", 14))
            entry.pack(padx=20, pady=10, fill="x")

            warn = ctk.CTkLabel(
                popup,
                text=getattr(self, "add_url_warning_message", ""),
                font=("Segoe UI", 12),
                text_color="#ca0000",
                wraplength=360,
                justify="center"
            )
            warn.pack(padx=16, pady=(0, 8))

            def submit():
                """Holds the logic to accumulate url from textbox and database."""
                url = entry.get().strip()
                if url and url not in self.blocked_urls:
                    Utility.block_url(HOST_PATH, url)
                    db.insert_blocked_url(url=url)
                    self.blocked_urls = set(db.load_blocked_urls())
                    popup.destroy()
                    refresh_blocked()

            submit_btn = ctk.CTkButton(popup, text="Add", font=("Segoe UI", 14), fg_color="#3CBF8F", command=submit)
            submit_btn.pack(pady=10)

        refresh_blocked()

    def load_app_usage_page(self, date: str):
        """Open a centered window showing a bar chart of app usage percentages for the given date."""
        try:
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            from matplotlib.figure import Figure

            db.run_cleanup()
            usage = db.load_existing_appwise_usage(date)
            if not usage:
                info = ctk.CTkToplevel(self)
                info.title("App Usage")
                w, h = 360, 140
                info.geometry(f"{w}x{h}")
                info.configure(fg_color="#181f2a")
                info.resizable(False, False)
                info.update_idletasks()
                x = (info.winfo_screenwidth() // 2) - (w // 2)
                y = (info.winfo_screenheight() // 2) - (h // 2)
                info.geometry(f"{w}x{h}+{x}+{y}")
                ctk.CTkLabel(info, text=f"No usage data for {date}", font=("Segoe UI", 16), text_color="#ffffff").pack(pady=20)
                ctk.CTkButton(info, text="Close", command=info.destroy, fg_color="#355691", hover_color="#008b7f").pack(pady=10)
                info.grab_set()
                info.focus_set()
                return

            total = sum(float(v) for v in usage.values()) or 1.0
            percent_pairs = [
                (app, (float(dur) / total) * 100.0) for app, dur in usage.items()
            ]
            percent_pairs.sort(key=lambda x: x[1], reverse=True)
            app_names = [a for a, _ in percent_pairs]
            percentages = [p for _, p in percent_pairs]

            win = ctk.CTkToplevel(self)
            win.title("App Usage")
            width, height = 900, 600
            win.geometry(f"{width}x{height}")
            win.configure(fg_color="#181f2a")
            win.resizable(True, True)
            win.grab_set()

            win.update_idletasks()
            x = (win.winfo_screenwidth() // 2) - (width // 2)
            y = (win.winfo_screenheight() // 2) - (height // 2)
            win.geometry(f"{width}x{height}+{x}+{y}")

            date_object = datetime.strptime(date , "%Y-%m-%d")
            formatted_date = date_object.strftime("%A, %B %d, %Y")

            title = ctk.CTkLabel(win, text=f"App Usage for {formatted_date}", font=("Segoe UI", 24, "bold"), text_color="#00bfae")
            title.pack(pady=(20, 10))

            chart_frame = ctk.CTkFrame(win, fg_color="#232b3b")
            chart_frame.pack(fill="both", expand=True, padx=20, pady=10)

            fig = Figure(figsize=(9.5, 5.2), dpi=100)
            fig.patch.set_facecolor("#232b3b")
            ax = fig.add_subplot(111)
            ax.set_facecolor("#232b3b")

            bar_color = "#00bfae"  
            edge_color = "#00d1c6"
            bars = ax.bar(app_names, percentages, color=bar_color, edgecolor=edge_color, linewidth=0.6)

            ax.set_ylim(0, 100)
            ax.set_ylabel("Usage (%)", color="#ffffff", fontsize=13)
            ax.set_xlabel("")

            ax.set_xticks(range(len(app_names)))
            ax.set_xticklabels(app_names, rotation=30, ha='right', fontsize=10, color="#e0e0e0")

            ax.tick_params(axis='y', colors="#e0e0e0", labelsize=10)
            ax.grid(axis='y', linestyle='--', alpha=0.25, color="#9aa7b1")

            for spine in ax.spines.values():
                spine.set_color("#4a5568")

            try:
                ax.bar_label(bars, fmt='%.1f%%', padding=3, fontsize=11, color="#ffffff")
            except Exception:
                for rect, pct in zip(bars, percentages):
                    height = rect.get_height()
                    ax.annotate(f"{pct:.1f}%",
                                xy=(rect.get_x() + rect.get_width() / 2, height),
                                xytext=(0, 3),
                                textcoords="offset points",
                                ha='center', va='bottom', fontsize=11, color="#ffffff")

            fig.tight_layout(pad=1.2)

            canvas = FigureCanvasTkAgg(fig, master=chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

            btn_row = ctk.CTkFrame(win, fg_color="transparent")
            btn_row.pack(fill="x", pady=(0, 16))
            back_btn = ctk.CTkButton(
                btn_row,
                text="Back",
                width=100,
                fg_color="#355691",
                hover_color="#008b7f",
                command=win.destroy,
            )
            back_btn.pack(pady=4)

            win.focus_set()
        except Exception as e:
            logger.exception(f"Failed to render app usage for {date}: {e}")

    def create_info_card(self, parent, title, value, color):
        """Returns a parent card to hold the stats."""
        card = ctk.CTkFrame(parent, width=200, height=100, fg_color=color, corner_radius=12)
        card.pack_propagate(False)
        ctk.CTkLabel(card, text=title, font=("Segoe UI", 14, "bold"), text_color="black").pack(pady=(10, 0))
        ctk.CTkLabel(card, text=value, font=("Segoe UI", 18), text_color="black").pack(pady=(5, 0))
        return card

    def create_progress_section(self, parent, label_text, hours, color):
        """Returns the parent frame to hold the progress bars."""
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
        """Holds the tracking logic initiator."""
        self.is_tracking = not self.is_tracking
        self.update_pause_btn()
        self.update_tracking_status_label()
    
    def set_warning_message(self, message):
        """Sets a warning message to feed the label."""
        if hasattr(self, 'warning_message_label') and self.warning_message_label.winfo_exists():
            self.warning_message_label.configure(text=message)
        else:
            self.load_dashboard()
            if hasattr(self, 'warning_message_label'):
                self.warning_message_label.configure(text=message)

    def get_warning_message(self):
        """Returns a warning message to feed the label."""
        if hasattr(self, 'warning_message_label') and self.warning_message_label.winfo_exists():
            return self.warning_message_label.cget("text")
        return ""