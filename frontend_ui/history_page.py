
def history_page():
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
    title_label.place(relx=0.5, rely=0.1, anchor="center")
    
    # Create table frame
    table_frame = ctk.CTkFrame(
        master=content_frame,
        fg_color="#2b2b2b",
        border_width=1,
        border_color="#444444"
    )
    table_frame.place(relx=0.5, rely=0.5, anchor="center", width=800, height=400)
    
    # Table headers
    headers = ["S.No", "Date", "Screen Time", "Break Time", "Details"]
    for col, header in enumerate(headers):
        header_label = ctk.CTkLabel(
            master=table_frame,
            text=header,
            font=("Agency FB", 18, "bold"),
            text_color="#178DED",
            width=150 if col != 4 else 250,
            height=30,
            corner_radius=0
        )
        header_label.grid(row=0, column=col, padx=1, pady=1, sticky="nsew")
    
    # Sample data - in a real app, this would come from your database
    history_data = [
        [1, "2025-08-01", "8 hrs", "2 hrs", "Chrome: 4.2h, VSCode: 2.1h"],
        [2, "2025-08-02", "6 hrs", "1.5 hrs", "Teams: 3.0h, Outlook: 1.5h"],
        [3, "2025-08-03", "7 hrs", "2.5 hrs", "Excel: 2.5h, Word: 1.8h"],
        [4, "2025-08-04", "5 hrs", "3 hrs", "Spotify: 2.0h, Slack: 1.5h"],
        [5, "2025-08-05", "9 hrs", "1 hr", "Zoom: 4.5h, PDF Reader: 2.0h"]
    ]
    
    # Add data rows
    for row, data in enumerate(history_data, start=1):
        for col, value in enumerate(data):
            cell = ctk.CTkLabel(
                master=table_frame,
                text=value,
                font=("Courier New", 14),
                text_color="white",
                fg_color="#363636" if row % 2 == 0 else "#2b2b2b",
                width=150 if col != 4 else 250,
                height=30,
                corner_radius=0
            )
            cell.grid(row=row, column=col, padx=1, pady=1, sticky="nsew")
    
    # Configure grid weights
    for i in range(len(headers)):
        table_frame.grid_columnconfigure(i, weight=1)
    
    # View App Usage button
    def view_app_usage():
        # This would show detailed app usage in a new window
        pass
    
    view_btn = ctk.CTkButton(
        master=content_frame,
        text="View Detailed App Usage",
        command=view_app_usage,
        font=("Agency FB", 16),
        fg_color="#178DED",
        hover_color="#0e5a9e",
        width=200,
        height=40
    )
    view_btn.place(relx=0.5, rely=0.85, anchor="center")