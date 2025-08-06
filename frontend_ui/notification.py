from winotify import Notification, audio
import tkinter as tk

def notify():
    toast = Notification(
    app_id="PyTracker",  # App name shown in the toast
    title="PyTracker - Reminder ⚠️",
    msg="You’ve been active for 45 mins. Break for 5 mins.",
    icon=r"C:\Dev\PyTracker\frontend_ui\logo.png"  # PNG works fine
    )
    toast.set_audio(audio.Reminder, loop=False)
    toast.add_actions(label="OK", launch="")
    toast.show()


def customnotify():
    root = tk.Tk()
    root.title("Reminder - PyTracker")
    root.configure(bg="#222222")
    root.resizable(False, False)

    # Fixed size
    window_width, window_height = 500, 150
    root.geometry(f"{window_width}x{window_height}")

    # Center the window
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")

    # Modern label
    label = tk.Label(
        root,
        text="You’ve been active for 45 mins. Break for 5 mins.",
        font=("Arial", 14),
        fg="white",
        bg="#222222",
        wraplength=window_width - 40,
        justify="center"
    )
    label.pack(pady=(25, 10))

    # Modern button style
    close_btn = tk.Button(
        root,
        text="Close",
        command=root.destroy,
        bg="#444444",
        fg="white",
        font=("Segoe UI", 11, "bold"),
        relief="flat",
        activebackground="#666666",
        activeforeground="white",
        cursor="hand2",
        padx=15,
        pady=5
    )
    close_btn.pack(pady=(0, 15))

    # Hover effect
    def on_enter(e):
        close_btn.config(bg="#555555")
    def on_leave(e):
        close_btn.config(bg="#444444")
    close_btn.bind("<Enter>", on_enter)
    close_btn.bind("<Leave>", on_leave)

    root.mainloop()

