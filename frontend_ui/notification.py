from customtkinter.windows.widgets.scaling import scaling_tracker
from winotify import Notification, audio
import customtkinter as ctk
import tkinter as tk

def notify():
    """Shows a native Windows toast reminder notification."""
    toast = Notification(
        app_id="PyTracker",
        title="PyTracker - Reminder ⚠️",
        msg="You've been active for 45 mins. Break for 5 mins.",
        icon=r"C:\Dev\PyTracker\frontend_ui\logo.png"
    )
    toast.set_audio(audio.Reminder, loop=False)
    toast.add_actions(label="OK", launch="")
    toast.show()

def customnotify():
    """Display an in-app modal reminder when system notifications are unavailable."""
    root = tk.Tk()
    root.title("Reminder - PyTracker")
    root.configure(bg="#181f2a")  
    root.resizable(False, False)

    window_width, window_height = 500, 150
    root.geometry(f"{window_width}x{window_height}")

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")

    card = tk.Frame(root, bg="#232b3b", bd=0, relief="flat")
    card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.92, relheight=0.85)

    label = tk.Label(
        card,
        text="You’ve been active for 45 mins.\nBreak for 5 mins.",
        font=("Segoe UI", 14, "bold"),
        fg="white",
        bg="#232b3b",
        wraplength=440,
        justify="center"
    )
    label.pack(pady=(15, 5))

    close_btn = tk.Button(
        card,
        text="Close",
        command=root.destroy,
        bg="#2979ff",
        fg="white",
        font=("Segoe UI", 11, "bold"),
        activebackground="#00bfae",
        activeforeground="white",
        relief="flat",
        cursor="hand2",
        padx=15,
        pady=5
    )
    close_btn.pack(pady=(5, 10))

    def on_enter(e): close_btn.config(bg="#00bfae")
    def on_leave(e): close_btn.config(bg="#2979ff")
    close_btn.bind("<Enter>", on_enter)
    close_btn.bind("<Leave>", on_leave)

    root.mainloop()

def show_reset_warning(callback_on_proceed):
    """Display a centered modal to confirm reset, invoking a callback on proceed."""
    warning_dialog = ctk.CTkToplevel()
    warning_dialog.title("Reset Warning")
    warning_dialog.geometry("450x200")
    warning_dialog.configure(fg_color="#181f2a")
    warning_dialog.resizable(False, False)
    warning_dialog.grab_set()  
    
    warning_dialog.update_idletasks()
    x = (warning_dialog.winfo_screenwidth() // 2) - (450 // 2)
    y = (warning_dialog.winfo_screenheight() // 2) - (200 // 2)
    warning_dialog.geometry(f"450x200+{x}+{y}")
    
    title_frame = ctk.CTkFrame(warning_dialog, fg_color="transparent")
    title_frame.pack(fill="x", padx=20, pady=(20, 10))
    
    warning_icon = ctk.CTkLabel(title_frame, text="⚠️", font=("Segoe UI", 32), text_color="#ff9800")
    warning_icon.pack(side="left", padx=(0, 10))
    
    title_label = ctk.CTkLabel(title_frame, text="Reset Timer", font=("Segoe UI", 20, "bold"), text_color="#ffffff")
    title_label.pack(side="left")
    
    message_label = ctk.CTkLabel(
        warning_dialog, 
        text="Are you sure you want to reset the timer?\nThis will clear all current tracking data for today.",
        font=("Segoe UI", 14),
        text_color="#b0b8c1",
        wraplength=400,
        justify="center"
    )
    message_label.pack(pady=10)
    
    button_frame = ctk.CTkFrame(warning_dialog, fg_color="transparent")
    button_frame.pack(fill="x", padx=20, pady=(20, 0))
    
    def on_proceed():
        warning_dialog.destroy()
        callback_on_proceed()
    
    def on_return():
        warning_dialog.destroy()
 
    return_btn = ctk.CTkButton(
        button_frame,
        text="Return",
        font=("Segoe UI", 14, "bold"),
        fg_color="#232b3b",
        hover_color="#2979ff",
        text_color="#ffffff",
        corner_radius=8,
        width=120,
        height=35,
        command=on_return
    )
    return_btn.pack(side="left", padx=(0, 10))
    
    proceed_btn = ctk.CTkButton(
        button_frame,
        text="Proceed",
        font=("Segoe UI", 14, "bold"),
        fg_color="#ff5252",
        hover_color="#ff1744",
        text_color="#ffffff",
        corner_radius=8,
        width=120,
        height=35,
        command=on_proceed
    )
    proceed_btn.pack(side="right", padx=(10, 0))
   
    warning_dialog.focus_set()
    warning_dialog.wait_window()


""" Crashing function, needs fix

def customnotify():
    root = ctk.CTkToplevel()
    root.title("Reminder - PyTracker")
    root.geometry("500x180")
    root.configure(fg_color="#181f2a")
    root.resizable(False, False)
    root.grab_set()  # Make it modal

    # Center the window
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (500 // 2)
    y = (root.winfo_screenheight() // 2) - (180 // 2)
    root.geometry(f"500x180+{x}+{y}")

    # Main container with modern styling
    main_frame = ctk.CTkFrame(root, fg_color="#232b3b", corner_radius=16)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)

    # Header with icon and title
    header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    header_frame.pack(fill="x", padx=20, pady=(20, 10))

    icon_label = ctk.CTkLabel(header_frame, text="⏰", font=("Segoe UI", 28), text_color="#00bfae")
    icon_label.pack(side="left", padx=(0, 10))

    title_label = ctk.CTkLabel(header_frame, text="Break Reminder", font=("Segoe UI", 20, "bold"), text_color="#ffffff")
    title_label.pack(side="left")

    # Message
    message_label = ctk.CTkLabel(
        main_frame,
        text="You've been active for 45 mins. Break for 5 mins.",
        font=("Segoe UI", 14),
        text_color="#b0b8c1",
        wraplength=450,
        justify="center"
    )
    message_label.pack(pady=10)

    # Button frame
    button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    button_frame.pack(fill="x", padx=20, pady=(10, 20))

    # Safe close function
    def safe_close():
        scaling_tracker.ScalingTracker.window_dpi_scaling_dict.pop(root, None)  # remove from tracker
        root.destroy()

    # Modern close button
    close_btn = ctk.CTkButton(
        button_frame,
        text="Got it!",
        font=("Segoe UI", 14, "bold"),
        fg_color="#00bfae",
        hover_color="#00a896",
        text_color="#ffffff",
        corner_radius=8,
        width=120,
        height=35,
        command=safe_close
    )
    close_btn.pack()

    # Handle manual window close (X button)
    root.protocol("WM_DELETE_WINDOW", safe_close)

    # Focus on the dialog
    root.focus_set()
    root.wait_window()

"""