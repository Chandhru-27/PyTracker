from tkinter import *
import customtkinter as ctk
from PIL import Image,ImageTk
import tkinter as tk

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


from tkinter import *
from PIL import Image, ImageTk

#creating a window
window = Tk()
screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()
window.geometry(f"{screen_width}x{screen_height}")
window.configure(bg="#222222")

#creating a variable which holds the colour of side bar color
blue_color = "#141414"
hover_color = "#36393B" #variable holds the colour to change when hovered

#creating the left frame to hold the buttons
left_frame = ctk.CTkFrame(master=window, width=210, height=screen_height, fg_color=blue_color)
left_frame.place(x=0, y=0)

#creating function to change color when hovered
def on_enter(e):
    e.widget['bg'] = hover_color

def on_leave(e):
    e.widget['bg'] = blue_color

#creating home button
home_btn=Button(
    left_frame,
    height=4,
    width=21,
    text="      Home",
    bg=blue_color,
    fg="white",
    font=("Agency FB",21),
    bd=0,
    activebackground=hover_color,
    anchor="center",
    activeforeground="#178DED"
)
home_btn.bind("<Enter>",on_enter)#binding home button with hover colours and placing
home_btn.bind("<Leave>",on_leave)
home_btn.place(x=-6,y=4)
#creating and placing home page logo
home_img=Image.open("home.svg").resize((50,50))
home_logo=ImageTk.PhotoImage(home_img)
logo_label_home=Label(window,image=home_logo,bg=blue_color,bd=0,highlightthickness=0,fg="white")
logo_label_home.place(x=8,y=53)
#binding logo and button to react when hovered
home_btn.bind("<Enter>", lambda e: [on_enter(e), logo_label_home.config(bg=hover_color)])
home_btn.bind("<Leave>", lambda e: [on_leave(e), logo_label_home.config(bg=blue_color)])
logo_label_home.bind("<Enter>", lambda e: [on_enter(e), home_btn.config(bg=hover_color)])
logo_label_home.bind("<Leave>", lambda e: [on_leave(e), home_btn.config(bg=blue_color)])

#creating history button
history_btn = Button(
    master=left_frame,
    text="      History",
    height=3,
    width=21,
    bg=blue_color,
    fg="white",
    font=("Agency FB",20),
    bd=0,
    activebackground=hover_color,
    activeforeground="#178DED"

    )     
history_btn.place(x=0, y=254)
#creating history logo and placing
history_img = Image.open("history.svg").resize((50, 50))
history_logo = ImageTk.PhotoImage(history_img)
logo_label_history = Label(window, image=history_logo,bg=blue_color,bd=0, highlightthickness=0,fg="white")
logo_label_history.place(x=8,y=293)
#binding logo and button to react
history_btn.bind("<Enter>", lambda e: [on_enter(e), logo_label_history.config(bg=hover_color)])
history_btn.bind("<Leave>", lambda e: [on_leave(e), logo_label_history.config(bg=blue_color)])
logo_label_history.bind("<Enter>", lambda e: [on_enter(e), history_btn.config(bg=hover_color)])
logo_label_history.bind("<Leave>", lambda e: [on_leave(e), history_btn.config(bg=blue_color)])

#creating block button 
block_app_btn = Button(
    master=left_frame,
    text="      Restricted",
    height=3,
    width=21,
    bg=blue_color,
    fg="white",
    font=("Agency FB",20),
    bd=0,
    activebackground=hover_color,
    activeforeground="#178DED"

)
block_app_btn.place(x=0, y=136)
block_app_btn.bind("<Enter>",on_enter)
block_app_btn.bind("<Leave>",on_leave)
#creating block logo and binding with app
block_img=Image.open("block.svg").resize((50,50))
block_logo=ImageTk.PhotoImage(block_img)
logo_label_block=Label(window,image=block_logo,bg=blue_color,fg="white",bd=0,highlightthickness=0)
logo_label_block.place(x=8,y=167)
block_app_btn.bind("<Enter>", lambda e: [on_enter(e), logo_label_block.config(bg=hover_color)])
block_app_btn.bind("<Leave>", lambda e: [on_leave(e), logo_label_block.config(bg=blue_color)])
logo_label_block.bind("<Enter>", lambda e: [on_enter(e), block_app_btn.config(bg=hover_color)])
logo_label_block.bind("<Leave>", lambda e: [on_leave(e), block_app_btn.config(bg=blue_color)])

#creating settings button
settings_btn = Button(
    master=left_frame,
    text="      Settings",
    height=3,
    width=21,
    bg=blue_color,
    fg="white",
    font=("Agency FB",22),
    bd=0,
    activebackground=hover_color,
    activeforeground="#178DED"
)
settings_btn.place(x=0, y=372)
#creating settings logo and binding
settings_img = Image.open("settings.svg").resize((50, 50))
settings_logo = ImageTk.PhotoImage(settings_img)
logo_label_settings = Label(window, image=settings_logo,bg=blue_color,bd=0, highlightthickness=0)
logo_label_settings.place(x=8,y=405)
settings_btn.bind("<Enter>", lambda e: [on_enter(e), logo_label_settings.config(bg=hover_color)])
settings_btn.bind("<Leave>", lambda e: [on_leave(e), logo_label_settings.config(bg=blue_color)])
logo_label_settings.bind("<Enter>", lambda e: [on_enter(e), settings_btn.config(bg=hover_color)])
logo_label_settings.bind("<Leave>", lambda e: [on_leave(e), settings_btn.config(bg=blue_color)])

#creating and placing app logo
logo_img=Image.open("logo.svg").resize((120,120))
logo_logo=ImageTk.PhotoImage(logo_img)
logo_label_logo=Label(window,image=logo_logo,bg=blue_color,bd=0,highlightthickness=0,width=200)
logo_label_logo.place(x=10,y=700)

#creating borders for the left column bar
bottom_border = Frame(master=left_frame, bg="#66696D", height=2, width=215)
bottom_border.place(x=0, y=136)
bottom_border2 = Frame(master=left_frame, bg="#66696D", height=2, width=215)
bottom_border2.place(x=0, y=252)
bottom_border3=Frame(master=left_frame,bg="#66696D",height=2,width=215)
bottom_border3.place(x=0,y=370)

#variables to hold screen time values
screen_time_value=2
screen_time_mins=int((screen_time_value-int(screen_time_value))*100)
screen_time_hours=int(screen_time_value)
max_value = 24
screen_perc=(screen_time_value/max_value)*100
#creating bars to fill screentime
outer = tk.Frame(window, bg="#e9eae9", width=700, height=25)
fill_width = int((screen_time_value / max_value)*100)
filled = tk.Frame(outer, bg="#3b953a", width=700*(fill_width/100), height=25)#0cbcd3
if(screen_perc>=0 and screen_perc<30):
    filled.configure(bg="#3b953a")
elif(screen_perc>=30 and screen_perc<70):
    filled.configure(bg="#3C73BB")
elif(screen_perc>=70 and screen_perc<=100):
    filled.configure(bg="#8c1515")
screen_time_lab=Label(text=f"{screen_time_hours}hours {screen_time_mins}minutes / 24 hours",font=("Arial Black",12),bg="#222222",fg="white")
screen_time_txt = Label(window, text="Screen time", font=("Agency FB", 20),bg="#222222",fg="white")
screen_time_perc=Label(window,text=f"{screen_perc:.2f}%",font=("Arial Black",15),bg="#222222",fg="white")

#variables to hold breaktime values
brk_time_value=max_value-screen_time_value
brk_time_hrs=int(brk_time_value)
brk_time_mins=int((brk_time_value-int(brk_time_value))*100)
brk_perc=(brk_time_value/max_value)*100
brk_time_perc=Label(window,text=f"{brk_perc:.2f}%",font=("Arial Black",15),bg="#222222",fg="white")
#creating bars to fill break time
outer2 = tk.Frame(window, bg="#e9eae9", width=700, height=25)
fill_width2 = int((brk_time_value / max_value)*100)
filled2 = tk.Frame(outer2, bg="#e9ff25", width=700*(fill_width2/100), height=25)
brk_time_label=Label(text=f"{brk_time_hrs}hours {brk_time_mins}minutes / 24 hours",font=("Arial Black",12),bg="#222222",fg="white")
brk_time_txt = Label(window, text="Break time", font=("Agency FB", 20), fg="white", bg="#222222")

#creating legends to indicate status of bar
legend_frame_productivity = Frame(window, bg="#222222", bd=1, relief="solid",height=100)
color_box1 = Frame(legend_frame_productivity, bg="#3b953a", width=20, height=20)
label1 = Label(legend_frame_productivity, text="Your'e good to go", font=("Arial", 10, "bold"), bg="#222222", fg="white")
legend_frame_entertainment = Frame(window, bg="#222222", bd=1, relief="solid")
color_box2 = Frame(legend_frame_entertainment, bg="#e9ff25", width=20, height=20)
label2 = Label(legend_frame_entertainment, text="Entertainment", font=("Arial", 10, "bold"), bg="#222222", fg="white")

#creating view usage button
view_usage_btn = ctk.CTkButton(
    master=window,
    text="VIEW USAGE",
    width=160,  
    height=50,
    font=("Segoe UI", 17, "bold"),
    fg_color="#178DED",        #178DED
    hover_color="#1A98FF",  #1A98FF   
    text_color="white",           
    border_color="black",         
    border_width=2,
    corner_radius=30               
)


#home page function where home page content appears and the other page contents dissappears
def home_page():

    outer.place(x=450,y=350)
    filled.place(x=0, y=0)

    screen_time_lab.place(x=1000,y=390)
    screen_time_txt.place(x=350,y=280)

    screen_time_perc.place(x=450,y=380)
    brk_time_perc.place(x=450,y=590)

    outer2.place(x=450,y=560)
    
    filled2.place(x=0, y=0)

    brk_time_label.place(x=1000,y=600)
    brk_time_txt.place(x=350,y=480)

    legend_frame_productivity.place(x=1100, y=200)
    color_box1.grid(row=0, column=0, padx=5, pady=5)
    label1.grid(row=0, column=1, padx=5)

    if(screen_perc>=0 and screen_perc<30):
        color_box1.configure(bg="#3b953a")
        label1.configure(text="Your'e Good to go")
    elif(screen_perc>=30 and screen_perc<70):
        color_box1.configure(bg="#3C73BB")
        label1.configure(text="Your'e doing great! Keep going")
    elif(screen_perc>=70 and screen_perc<=100):
        color_box1.configure(bg="#8c1515")
        label1.configure(text="Take a Break !")

    legend_frame_entertainment.place(x=1100, y=240)
    color_box2.grid(row=0, column=0, padx=5, pady=5)
    label2.grid(row=0, column=1, padx=5)

   
    view_usage_btn.place(x=1100, y=700)

home_page()

#function for restrictions page where home page content dissappears and this page content appears
def restricted_page():
    screen_time_lab.place_forget()
    screen_time_txt.place_forget()
    brk_time_label.place_forget()
    brk_time_txt.place_forget()
    legend_frame_productivity.place_forget()
    legend_frame_entertainment.place_forget()
    outer.place_forget()
    outer2.place_forget()
    view_usage_btn.place_forget()
    screen_time_perc.place_forget()
    brk_time_perc.place_forget()

#similar function like other pages
def history_page():
    screen_time_lab.place_forget()
    screen_time_txt.place_forget()
    brk_time_label.place_forget()
    brk_time_txt.place_forget()
    legend_frame_productivity.place_forget()
    legend_frame_entertainment.place_forget()
    outer.place_forget()
    outer2.place_forget()
    view_usage_btn.place_forget()
    screen_time_perc.place_forget()
    brk_time_perc.place_forget()

#similar function like other pages
def settings_page():
    screen_time_lab.place_forget()
    screen_time_txt.place_forget()
    brk_time_label.place_forget()
    brk_time_txt.place_forget()
    legend_frame_productivity.place_forget()
    legend_frame_entertainment.place_forget()
    outer.place_forget()
    outer2.place_forget()
    view_usage_btn.place_forget()
    screen_time_perc.place_forget()
    brk_time_perc.place_forget()

home_btn.configure(command=home_page)
block_app_btn.configure(command=restricted_page)
history_btn.configure(command=history_page)
settings_btn.config(command=settings_page)


window.mainloop()


