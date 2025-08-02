import tkinter as tk

def draw_gradient(canvas, width, height):
    # Gradient color stops
    colors = [
        (0, (2, 0, 36)),       # 0%
        (0.42, (9, 9, 121)),   # 42%
        (1, (0, 212, 255))     # 100%
    ]

    steps = width
    for i in range(steps):
        # Normalize current position
        t = i / steps

        # Find the two color stops we're between
        for j in range(len(colors) - 1):
            t0, c0 = colors[j]
            t1, c1 = colors[j + 1]
            if t0 <= t <= t1:
                ratio = (t - t0) / (t1 - t0)
                r = int(c0[0] + (c1[0] - c0[0]) * ratio)
                g = int(c0[1] + (c1[1] - c0[1]) * ratio)
                b = int(c0[2] + (c1[2] - c0[2]) * ratio)
                hex_color = f'#{r:02x}{g:02x}{b:02x}'
                canvas.create_line(i, 0, i, height, fill=hex_color)
                break

# Tkinter window setup
root = tk.Tk()
w, h = 600, 400
canvas = tk.Canvas(root, width=w, height=h)
canvas.pack()

draw_gradient(canvas, w, h)

root.mainloop()