import tkinter as tk
from tkinter import Canvas
import sys
from pathlib import Path

# Add the parent directory of the 'utilities' folder to the Python path
utilities_parent_path = Path("C:/Users/jared/Documents/GitHub/OSRS-Bot-COLOR/src").resolve()
sys.path.append(str(utilities_parent_path))

# Now you can import the Rectangle class
from utilities.geometry import Rectangle

class RectangleScaler(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Rectangle Cropper")

        self.rect = Rectangle(100, 100, 200, 100)
        self.original_rect = self.rect

        self.canvas = Canvas(self, width=400, height=300)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.draw_rectangle(self.rect, fill="blue")

        self.function_call_label = tk.Label(self, text="")
        self.function_call_label.pack()

        self.clicks = 0
        self.first_click = None

    def on_canvas_click(self, event):
        self.clicks += 1
        if self.clicks == 1:
            self.first_click = (event.x, event.y)
        elif self.clicks == 2:
            self.crop_rectangle(self.first_click, (event.x, event.y))
            self.clicks = 0
            self.first_click = None

    def draw_rectangle(self, rect, fill="blue"):
        self.canvas.create_rectangle(rect.left, rect.top, rect.left + rect.width, rect.top + rect.height, fill=fill, outline='')

    def draw_cropped_rectangle(self, original_rect, new_rect):
        self.canvas.delete("all")
        self.draw_rectangle(original_rect, fill="blue")
        self.draw_rectangle(new_rect, fill="red")

    def crop_rectangle(self, first_click, second_click):
        left_crop = (first_click[0] - self.rect.left) / self.rect.width
        top_crop = (first_click[1] - self.rect.top) / self.rect.height
        right_crop = (self.rect.left + self.rect.width - second_click[0]) / self.rect.width
        bottom_crop = (self.rect.top + self.rect.height - second_click[1]) / self.rect.height

        scale_width = 1 - left_crop - right_crop
        scale_height = 1 - top_crop - bottom_crop

        new_rect = self.original_rect.scale(scale_width, scale_height, anchor_x=left_crop / (1 - right_crop), anchor_y=top_crop / (1 - bottom_crop))
        self.draw_cropped_rectangle(self.rect, new_rect)

        print(f"Parameters to crop rectangle:")
        print(f"  scale_width: {scale_width:.2f}")
        print(f"  scale_height: {scale_height:.2f}")
        print(f"  anchor_x: {left_crop / (1 - right_crop):.2f}")
        print(f"  anchor_y: {top_crop / (1 - bottom_crop):.2f}")

    def update_function_call_label(self, scale_width, scale_height, anchor_x, anchor_y):
        function_call = f"rect.scale({scale_width:.2f}, {scale_height:.2f}, {anchor_x:.2f}, {anchor_y:.2f})"
        self.function_call_label.config(text=function_call)

    def crop_rectangle(self, first_click, second_click):
        left_crop = (first_click[0] - self.rect.left) / self.rect.width
        top_crop = (first_click[1] - self.rect.top) / self.rect.height
        right_crop = (self.rect.left + self.rect.width - second_click[0]) / self.rect.width
        bottom_crop = (self.rect.top + self.rect.height - second_click[1]) / self.rect.height

        scale_width = 1 - left_crop - right_crop
        scale_height = 1 - top_crop - bottom_crop

        new_rect = self.original_rect.scale(scale_width, scale_height, anchor_x=left_crop / (1 - right_crop), anchor_y=top_crop / (1 - bottom_crop))
        self.draw_cropped_rectangle(self.rect, new_rect)

        self.update_function_call_label(scale_width, scale_height, left_crop / (1 - right_crop), top_crop / (1 - bottom_crop))

        print(f"Parameters to crop rectangle:")
        print(f"  scale_width: {scale_width:.2f}")
        print(f"  scale_height: {scale_height:.2f}")
        print(f"  anchor_x: {left_crop / (1 - right_crop):.2f}")
        print(f"  anchor_y: {top_crop / (1 - bottom_crop):.2f}")

if __name__ == "__main__":
    app = RectangleScaler()
    app.mainloop()