# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import messagebox
from tkinter.simpledialog import askstring

import fileops as fops
import imageops as iops

import ui_generics as ui

from PIL import ImageTk

TAG_RECT_SIZE = 16

TAGDATA_TEMPLATE = {
    'class_name': '',
    'tags': []
}

class TagEditorTab(tk.Frame):

    # params

    # widgets
    console = None
    input_path_entry = None
    class_name_entry = None
    image_tags_entry = None

    # image canvas
    image_canvas = None
    image_container = None
    rectangle_container = None
    tag_rectangles = []

    # data
    current_image = None
    current_image_index = None
    current_scaled_image = None
    current_canvas_size_x = None
    current_canvas_size_y = None
    current_mouse_x = 0
    current_mouse_y = 0
    current_rect_left = None
    current_rect_upper = None
    current_rect_right = None
    current_rect_lower = None
    input_files = None
    raw_image = None
    scaled_image = None
    ratio = None
    current_tag_data = {}

    def __init__(self, console):
        super().__init__()
        self.console = console
        self.init_ui()
        self.console.write_info('Tagger Tab init complete.')

    def init_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        main_frame = tk.Frame(self)
        main_frame.grid(row=0, column=0, sticky='news')
        main_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=2, uniform='x')
        main_frame.columnconfigure(1, weight=2, uniform='x')
        main_frame.columnconfigure(2, weight=8, uniform='x')

        # left frame
        left_frame = tk.Frame(main_frame)
        left_frame.grid(column=0, row=0, sticky='news')

        left_widget_canvas = tk.Canvas(left_frame)
        left_widget_canvas.columnconfigure(0, weight=1)
        left_widget_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        paths_frame = tk.LabelFrame(left_widget_canvas, text='Paths')
        paths_frame.grid(column=0, row=0, sticky='news')
        paths_frame.columnconfigure(0, weight=1)

        self.input_path_entry = ui.LabelEntryFolderBrowse('Input Folder', paths_frame, callback=self.set_files_to_listbox)
        self.input_path_entry.grid(column=0, row=0, sticky='news')

        # mid frame
        mid_frame = tk.Frame(main_frame)
        mid_frame.grid(column=1, row=0, sticky='news')
        mid_frame.rowconfigure(0, weight=1)
        mid_frame.columnconfigure(0, weight=1)

        self.files_listbox = ui.ScrollableListbox('Files', mid_frame)
        self.files_listbox.grid(column=0, row=0, sticky='news')
        self.files_listbox.bind_onclick(self.listbox_onclick)

        # right frame
        image_frame = tk.LabelFrame(main_frame, text='Image')
        image_frame.rowconfigure(0, weight=1)
        image_frame.columnconfigure(0, weight=1)
        image_frame.grid(column=2, row=0, sticky='news')

        self.image_canvas = tk.Canvas(image_frame)
        self.image_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        self.image_canvas.bind('<Motion>', self.on_canvas_motion)
        self.image_canvas.bind('<Enter>', self.on_canvas_enter)
        self.image_canvas.bind('<Leave>', self.on_canvas_leave)
        self.image_canvas.bind('<ButtonRelease-1>', self.canvas_mouseclick)
        self.image_canvas.configure(bg='black')

        self.image_tags_entry = ui.LabelEntryText('Image Tags', image_frame)
        self.image_tags_entry.pack(side=tk.BOTTOM, fill=tk.X)

        self.class_name_entry = ui.LabelEntryText('Class Name', image_frame)
        self.class_name_entry.pack(side=tk.BOTTOM, fill=tk.X)

        self.rectangle_container = self.image_canvas.create_rectangle(0, 0, TAG_RECT_SIZE, TAG_RECT_SIZE, outline='white', width=3)

    def window_reconfigure(self, event):
        if self.current_image is not None:
            if not ((self.current_image.width() == self.image_canvas.winfo_width()) or (self.current_image.height() == self.image_canvas.winfo_height())):
                self.load_image_to_canvas()

    def set_files_to_listbox(self, path):
        self.image_canvas.delete('all')
        self.files_listbox.clear()
        self.input_files = fops.get_image_files(path)
        self.files_listbox.set_data(self.input_files)
        if self.files_listbox.get_list_length() != 0:
            self.files_listbox.get_widget().selection_clear(0, tk.END)
            self.files_listbox.get_widget().select_set(0)
            self.current_image_index = 0
            self.files_listbox.get_widget().event_generate('<<ListboxSelect>>')
        self.console.write_info('Found ' + str(len(self.input_files)) + ' image(s).')

    def listbox_onclick(self, event):
        if self.files_listbox.get_list_length() == 0:
            return

        w = event.widget
        index = w.curselection()
        if index:
            index = int(w.curselection()[0])

            self.current_image_index = index
            self.image_canvas.focus_set()
            self.load_image_raw()
            self.load_image_to_canvas()
            self.load_tag_data()

    def load_tag_data(self):
        self.class_name_entry.set_value('')
        self.image_tags_entry.set_value('')
        self.current_tag_data.clear()
        tag_data = fops.load_tag_data(self.input_files[self.current_image_index][1].split('.')[0])
        print(tag_data)
        if tag_data is not None:
            self.current_tag_data = tag_data
            self.class_name_entry.set_value(self.current_tag_data['class_name'])
            tags = self.current_tag_data['tags']

            tags_string = ''
            for rect in self.tag_rectangles:
                self.image_canvas.delete(rect)

            self.tag_rectangles.clear()
            
            scl_img_width, scl_img_height = self.scaled_image.size
            raw_img_width, raw_img_height = self.raw_image.size
            scaling_factor = raw_img_width / scl_img_width

            x_offset = int((self.image_canvas.winfo_width() - scl_img_width) / 2)
            y_offset = int((self.image_canvas.winfo_height() - scl_img_height) / 2)

            for tag in tags:
                coord_x = int((tag['x'] /scaling_factor) + x_offset)
                coord_y = int((tag['y'] /scaling_factor) + y_offset)

                self.tag_rectangles.append(self.image_canvas.create_rectangle(coord_x - TAG_RECT_SIZE/2, 
                                                                      coord_y - TAG_RECT_SIZE/2,
                                                                      coord_x + TAG_RECT_SIZE/2,
                                                                      coord_y + TAG_RECT_SIZE/2,
                                                                      outline='white', width=3))
                tags_string += '{tag}'.format(tag=tag['tag']) if tags_string == '' else ', {tag}'.format(tag=tag['tag'])
                self.image_tags_entry.set_value(tags_string)
        else:
            self.current_tag_data = TAGDATA_TEMPLATE.copy()

    def load_image_raw(self):
        self.raw_image = iops.load_image(self.input_files[self.current_image_index][1])

    def load_image_to_canvas(self):
        if self.input_files is None or self.raw_image is None:
            return

        self.image_canvas.delete('all')

        self.ratio = min(self.image_canvas.winfo_width() / self.raw_image.width,
                         self.image_canvas.winfo_height() / self.raw_image.height)
        self.scaled_image = iops.scale_image(self.raw_image, self.ratio)
        self.current_image = ImageTk.PhotoImage(self.scaled_image)

        self.image_container = self.image_canvas.create_image(self.image_canvas.winfo_width() / 2,
                                                              self.image_canvas.winfo_height() / 2, anchor=tk.CENTER,
                                                              image=self.current_image)

        self.rectangle_container = self.image_canvas.create_rectangle(self.current_mouse_x - TAG_RECT_SIZE/2, 
                                                                      self.current_mouse_y - TAG_RECT_SIZE/2,
                                                                      self.current_mouse_x + TAG_RECT_SIZE/2,
                                                                      self.current_mouse_y + TAG_RECT_SIZE/2,
                                                                      outline='white', width=3)
        self.move_rectangle()
    
    def move_rectangle(self):
        rect_half_x = TAG_RECT_SIZE / 2
        rect_half_y = TAG_RECT_SIZE / 2
        canvas_half_x = self.image_canvas.winfo_width() / 2
        canvas_half_y = self.image_canvas.winfo_height() / 2

        # left
        if self.current_image is not None:
            image_half_x = self.current_image.width() / 2
            image_half_y = self.current_image.height() / 2

            # x axis
            if self.current_mouse_x < canvas_half_x - image_half_x + rect_half_x:
                self.current_rect_left = canvas_half_x - image_half_x
                self.current_rect_right = canvas_half_x - image_half_x + rect_half_x * 2
            elif self.current_mouse_x + rect_half_x > canvas_half_x + image_half_x:
                self.current_rect_left = canvas_half_x + image_half_x - rect_half_x * 2
                self.current_rect_right = canvas_half_x + image_half_x
            else:
                self.current_rect_left = self.current_mouse_x - rect_half_x
                self.current_rect_right = self.current_mouse_x + rect_half_x

            # y axis
            if self.current_mouse_y < canvas_half_y - image_half_y + rect_half_y:
                self.current_rect_upper = canvas_half_y - image_half_y
                self.current_rect_lower = canvas_half_y - image_half_y + rect_half_y * 2
            elif self.current_mouse_y + rect_half_y > canvas_half_y + image_half_y:
                self.current_rect_upper = canvas_half_y + image_half_y - rect_half_y * 2
                self.current_rect_lower = canvas_half_y + image_half_y
            else:
                self.current_rect_upper = self.current_mouse_y - rect_half_y
                self.current_rect_lower = self.current_mouse_y + rect_half_y
        else:
            self.current_rect_left = self.current_mouse_x - rect_half_x
            self.current_rect_right = self.current_mouse_x + rect_half_x
            self.current_rect_upper = self.current_mouse_y - rect_half_y
            self.current_rect_lower = self.current_mouse_y + rect_half_y

        # set coords to int
        self.current_rect_left = int(self.current_rect_left)
        self.current_rect_upper = int(self.current_rect_upper)
        self.current_rect_right = int(self.current_rect_right)
        self.current_rect_lower = int(self.current_rect_lower)

        self.image_canvas.coords(self.rectangle_container, self.current_rect_left, self.current_rect_upper,
                                 self.current_rect_right, self.current_rect_lower)

        self.image_canvas.update()

    def on_canvas_motion(self, event):
        self.current_mouse_x = event.x
        self.current_mouse_y = event.y
        self.current_canvas_size_x = self.image_canvas.winfo_width()
        self.current_canvas_size_y = self.image_canvas.winfo_height()

        self.move_rectangle()
    
    def on_canvas_enter(self, event):
        self.image_canvas.focus_set()
        self.bind_all('<space>', self.roll)

    def on_canvas_leave(self, event):
        self.unbind_all('<space>')

    def roll(self, event):
        # roll
        if self.files_listbox.get_list_length() == 0:
            return

        if self.current_image_index is not None:
            self.current_image_index = self.current_image_index + 1
            if self.current_image_index == self.files_listbox.get_list_length():
                messagebox.showwarning(title='Warning', message='Image list reached to end, rolling back to zero.')
                self.current_image_index = 0

            self.files_listbox.get_widget().selection_clear(0, tk.END)
            self.files_listbox.get_widget().select_set(self.current_image_index)
            self.files_listbox.get_widget().event_generate('<<ListboxSelect>>')

    def canvas_mouseclick(self, event):
        if self.input_files is None:
            messagebox.showerror(title='Error', message='No input images.')
            return 
        elif len(self.input_files) == 0:
            messagebox.showerror(title='Error', message='No input images.')
            return

	    # get clicked coordinates on the image
        x = self.image_canvas.canvasx(event.x)
        y = self.image_canvas.canvasy(event.y)

        scl_img_width, scl_img_height = self.scaled_image.size
        raw_img_width, raw_img_height = self.raw_image.size

        scaling_factor = raw_img_width / scl_img_width

        x_offset = int((self.image_canvas.winfo_width() - scl_img_width) / 2)
        y_offset = int((self.image_canvas.winfo_height() - scl_img_height) / 2)

        orig_x = int((x - x_offset) * scaling_factor)
        orig_y = int((y - y_offset) * scaling_factor)

        print('X: {val}'.format(val=orig_x))
        print('Y: {val}'.format(val=orig_y))

        # ask for tag
        tag = askstring('Tag', 'Enter the tag.')
        if tag != '':
            new_tag = {}
            new_tag['x'] = orig_x
            new_tag['y'] = orig_y
            new_tag['tag'] = tag
            self.current_tag_data['tags'].append(new_tag)
        else:
            return

        self.current_tag_data['class_name'] = self.class_name_entry.get_value()

        fops.save_tag_data(self.input_files[self.current_image_index][1].split('.')[0], self.current_tag_data)
        self.files_listbox.get_widget().event_generate('<<ListboxSelect>>')