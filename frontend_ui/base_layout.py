import customtkinter as ctk
from PIL import Image
from tkinter import filedialog
import tkinter.messagebox as messagebox
from datetime import datetime
from state.userstate import UserActivityState
import random
import os


class TimeTrackerApp(ctk.CTk):
    def __init__(self , state: UserActivityState):
        super().__init__()
        self.state = state
        self.title("TimeTracker Pro")
        self.geometry("1200x720")
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
            icon_img = Image.open(icon_path)
            icon = ctk.CTkImage(icon_img, size=(28, 28))
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
        self.load_page("Home")

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
        # Set card background to transparent
        card = ctk.CTkFrame(parent, width=card_width, height=card_height, fg_color="transparent", corner_radius=16)
        card.pack_propagate(False)
        ctk.CTkLabel(card, text=icon, font=("Segoe UI", 28 if wide else 22), text_color=bg_color).pack(pady=(8, 0))
        ctk.CTkLabel(card, text=title, font=("Segoe UI", 17 if wide else 14, "bold"), text_color="#b0b8c1").pack()
        ctk.CTkLabel(card, text=value, font=("Segoe UI", 28 if wide else 18, "bold"), text_color=bg_color).pack()
        return card

    def load_dashboard(self):
        # Clear all widgets from main_frame to prevent overlay
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        # Heading row with right-aligned icon buttons
        heading_row = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        heading_row.pack(fill="x", padx=30, pady=(40, 0))

        top_label = ctk.CTkLabel(heading_row, text="Screen Time Dashboard",
                                      font=("Segoe UI", 40, "bold"), text_color="#00bfae")
        top_label.pack(side="left")

        # Icon-only buttons (Pause/Resume and Reset)
        def toggle_tracking():
            self.is_tracking = not self.is_tracking
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

        reset_btn = ctk.CTkButton(heading_row, width=48, height=48, corner_radius=24, font=("Segoe UI", 24),
                                  text="⟳", fg_color="#232b3b", hover_color="#2979ff", text_color="#fff")
        reset_btn.pack(side="right", padx=(0, 10))

        date_label = ctk.CTkLabel(self.main_frame, text=datetime.now().strftime("%A, %B %d, %Y"),
                                      font=("Segoe UI", 18), text_color="#b0b8c1")
        date_label.pack(anchor="w", padx=30, pady=(0, 20))

        # ========== Time & Tracking Status ==========
        # Remove background, use transparent/minimal
        top_bar = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        top_bar.pack(fill="x", padx=30)

        right_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        right_frame.pack(side="right", padx=10)

        time_label = ctk.CTkLabel(right_frame, text=datetime.now().strftime("%I:%M:%S %p"),
                                 font=("Segoe UI", 20, "bold"), text_color="#ffffff")
        time_label.pack(anchor="e")

        status_label = ctk.CTkLabel(right_frame, text="▶ Tracking Active", font=("Segoe UI", 14), text_color="#00c853")
        status_label.pack(anchor="e")

        # ========== Centered Stats Cards (Today & Weekly) ==========
        stats_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        stats_frame.pack(pady=(0, 0))

        self.create_stat_card(stats_frame, "Today's Usage", "1h 9m", "🕒", "#2979ff", wide=True).pack(side="left", padx=30)
        self.create_stat_card(stats_frame, "Weekly Avg", "5.2h", "📈", "#00bfae", wide=True).pack(side="left", padx=30)

        # ========== Screen Time Progress ==========
        st_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        st_frame.pack(pady=(20, 0), padx=30, fill="x")

        ctk.CTkLabel(st_frame, text="Screen Time Progress", font=("Segoe UI", 18, "bold"), text_color="#00bfae").pack(anchor="w", padx=15, pady=(10, 5))

        screen_time_today = 1.15  # 1h 9m
        max_val = 24
        percent = (screen_time_today / max_val) * 100

        bar = ctk.CTkProgressBar(st_frame, height=22, progress_color="#00bfae")
        bar.set(screen_time_today / max_val)
        bar.pack(fill="x", padx=15)

        status_frame = ctk.CTkFrame(st_frame, fg_color="transparent")
        status_frame.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(status_frame, text=f"{round(percent,1)}%", text_color="#ffffff", font=("Segoe UI", 15)).pack(side="left")
        ctk.CTkLabel(status_frame, text="{1h 9m} / 24h", text_color="#b0b8c1", font=("Segoe UI", 14)).pack(side="right")

        # On Track / Paused Badge
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
        self.update_tracking_status_label = update_tracking_status_label


        # ========== Break Time Progress ==========
        bt_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        bt_frame.pack(pady=(5, 0), padx=30, fill="x")

        ctk.CTkLabel(bt_frame, text="Break Time Today", font=("Segoe UI", 18, "bold"), text_color="#2979ff").pack(anchor="w", padx=15, pady=(10, 5))

        break_hours = 0.0
        bar2 = ctk.CTkProgressBar(bt_frame, height=22, progress_color="#2979ff")
        bar2.set(break_hours / 24)
        bar2.pack(fill="x", padx=15)

        status_frame2 = ctk.CTkFrame(bt_frame, fg_color="transparent")
        status_frame2.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(status_frame2, text="0.05%", text_color="#ffffff", font=("Segoe UI", 15)).pack(side="left")
        ctk.CTkLabel(status_frame2, text="0h 0m / 24h", text_color="#b0b8c1", font=("Segoe UI", 14)).pack(side="right")


    def load_history_page(self, page_index=0):
        # Clear all except top label
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # Create heading for history page without background
        top_label = ctk.CTkLabel(self.main_frame, text="Usage History",
                                      font=("Segoe UI", 40, "bold"), text_color="#00bfae")
        top_label.pack(anchor="w", padx=30, pady=(40, 5))

        date_label = ctk.CTkLabel(self.main_frame, text=datetime.now().strftime("%A, %B %d, %Y"),
                                      font=("Segoe UI", 18), text_color="#b0b8c1")
        date_label.pack(anchor="w", padx=30, pady=(0, 20))

        sample_data = [
            ["2025-08-01", "6h 15m", "1h 30m", "Chrome"],
            ["2025-08-02", "7h 5m", "2h 10m", "VSCode"],
            ["2025-08-03", "5h 45m", "1h", "YouTube"],
        ] * 5

        start = page_index * self.rows_per_page
        end = start + self.rows_per_page
        paged_data = sample_data[start:end]

        # Use app theme color for history frame
        history_frame = ctk.CTkFrame(self.main_frame, fg_color="#232b3b")
        history_frame.pack(fill="both", expand=True, padx=30, pady=20)

        headers = ["Date", "Screen Time", "Break Time", "Top App", ""]
        for col, header in enumerate(headers):
            lbl = ctk.CTkLabel(history_frame, text=header, font=("Segoe UI", 18, "bold"), text_color="#2979ff")
            lbl.grid(row=0, column=col, padx=10, pady=10, sticky="nsew")

        for i, row in enumerate(paged_data, start=1):
            for j, val in enumerate(row):
                # Alternate row color for better readability
                row_bg = "#181f2a" if i % 2 == 0 else "#232b3b"
                cell = ctk.CTkLabel(history_frame, text=val, font=("Segoe UI", 16), text_color="#ffffff", fg_color=row_bg)
                cell.grid(row=i, column=j, padx=10, pady=8, sticky="nsew")

            ctk.CTkButton(history_frame, text="View", width=60, height=30, fg_color="#2979ff",
                        hover_color="#00bfae", font=("Segoe UI", 14), text_color="#ffffff").grid(row=i, column=4, padx=10, pady=8)

        for col in range(len(headers)):
            history_frame.grid_columnconfigure(col, weight=1)

        total_pages = (len(sample_data) + self.rows_per_page - 1) // self.rows_per_page

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
        # Create heading for restricted page without background
        top_label = ctk.CTkLabel(self.main_frame, text="Restricted Apps",
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

        def add_table_section(title, items, is_app):
            # Table header
            table_frame = ctk.CTkFrame(container, fg_color="#232b3b", corner_radius=14)
            table_frame.pack(fill="x", pady=(0, 20))
            header = ctk.CTkFrame(table_frame, fg_color="#205080", corner_radius=8)  # Less bright blue
            header.pack(fill="x")
            ctk.CTkLabel(header, text=title, font=("Segoe UI", 18, "bold"), text_color="#ffffff").grid(row=0, column=0, padx=12, pady=8, sticky="w")
            ctk.CTkLabel(header, text="Action", font=("Segoe UI", 16, "bold"), text_color="#ffffff").grid(row=0, column=1, padx=12, pady=8, sticky="e")
            header.grid_columnconfigure(0, weight=1)
            header.grid_columnconfigure(1, weight=0)

            # Table rows
            for idx, item in enumerate(items, 1):
                row_bg = "#181f2a" if idx % 2 == 0 else "#232b3b"
                row = ctk.CTkFrame(table_frame, fg_color=row_bg)
                row.pack(fill="x")
                ctk.CTkLabel(row, text=f"{idx}. {item}", font=("Segoe UI", 16), text_color="#ffffff").grid(row=0, column=0, padx=12, pady=10, sticky="w")
                unblock_btn = ctk.CTkButton(row, text="Unblock", width=80, height=30, font=("Segoe UI", 14, "bold"),
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
                add_btn = ctk.CTkButton(table_frame, text="+ Add App", font=("Segoe UI", 15, "bold"), fg_color="#205080",
                                         hover_color="#00bfae", text_color="#ffffff", corner_radius=8, command=self.add_app)
            else:
                add_btn = ctk.CTkButton(table_frame, text="+ Add URL", font=("Segoe UI", 15, "bold"), fg_color="#205080",
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



# if __name__ == "__main__":
