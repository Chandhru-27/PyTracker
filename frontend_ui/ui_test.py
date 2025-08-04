import tkinter as tk
from tkinter import ttk

class HistoryTable(tk.Frame):
    def __init__(self, parent, on_view_usage):
        super().__init__(parent, bg=parent['bg'])
        self.on_view_usage = on_view_usage
        self.history_data = []

        # Apply style
        style = ttk.Style()
        style.theme_use("clam")
        
        # Configure the Treeview style - set borderwidth here
        style.configure("Custom.Treeview",
                       background=parent['bg'],
                       foreground="white",
                       rowheight=35,
                       fieldbackground=parent['bg'],
                       borderwidth=0,  # This controls the border
                       font=("Segoe UI", 10))
        
        # Configure the Heading style
        style.configure("Custom.Treeview.Heading",
                       background="#2c2c2c",
                       foreground="white",
                       font=("Segoe UI", 11, "bold"),
                       relief="flat",
                       borderwidth=0)
        
        # Remove any hover effects on headings
        style.map("Custom.Treeview.Heading",
                 background=[('active', '#2c2c2c'), ('!active', '#2c2c2c')],
                 foreground=[('active', 'white'), ('!active', 'white')])
        
        style.map("Custom.Treeview",
                 background=[("selected", "#333333")],
                 foreground=[("selected", "white")])

        # Create the Treeview without borderwidth/highlightthickness parameters
        self.tree = ttk.Treeview(self,
                                columns=("sno", "date", "screen_time", "break_time", "view"),
                                show="headings",
                                style="Custom.Treeview")

        # Define headings
        self.tree.heading("sno", text="S.No")
        self.tree.heading("date", text="Date")
        self.tree.heading("screen_time", text="Screen Time")
        self.tree.heading("break_time", text="Break Time")
        self.tree.heading("view", text="View App Usage")

        # Define columns
        self.tree.column("sno", width=50, anchor="center")
        self.tree.column("date", width=120, anchor="center")
        self.tree.column("screen_time", width=120, anchor="center")
        self.tree.column("break_time", width=120, anchor="center")
        self.tree.column("view", width=140, anchor="center")

        self.tree.pack(fill="both", expand=True)

        # Bind events for click & hover
        self.tree.bind("<Button-1>", self._on_click)
        self.tree.bind("<Motion>", self._on_hover)

    def add_row(self, date, screen_time, break_time):
        sno = len(self.history_data) + 1
        self.history_data.append({
            "date": date,
            "screen_time": screen_time,
            "break_time": break_time
        })
        self.tree.insert("", "end", values=(sno, date, screen_time, break_time, "View"))

    def _on_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            row_id = self.tree.identify_row(event.y)
            col_id = self.tree.identify_column(event.x)
            if col_id == "#5" and row_id:
                values = self.tree.item(row_id, "values")
                sno, date = values[0], values[1]
                self.on_view_usage(sno, date)

    def _on_hover(self, event):
        region = self.tree.identify("region", event.x, event.y)
        col_id = self.tree.identify_column(event.x)
        if region == "cell" and col_id == "#5":
            self.tree.config(cursor="hand2")
        else:
            self.tree.config(cursor="")

# Example usage
def on_view_usage(sno, date):
    print(f"Viewing app usage for Row {sno}, Date {date}")

if __name__ == "__main__":
    root = tk.Tk()
    root.title("History Table")
    root.geometry("650x400")
    root.configure(bg="#1e1e1e")

    table = HistoryTable(root, on_view_usage)
    table.pack(fill="both", expand=True, padx=10, pady=10)

    # Sample rows
    table.add_row("2025-08-01", "8 hrs", "2 hrs")
    table.add_row("2025-08-02", "6 hrs", "1.5 hrs")
    table.add_row("2025-08-01", "8 hrs", "2 hrs")
    table.add_row("2025-08-02", "6 hrs", "1.5 hrs")
    table.add_row("2025-08-02", "6 hrs", "1.5 hrs")     

    root.mainloop()