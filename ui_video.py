# -*- coding: utf-8 -*-
import os
import cv2
import math
import yaml
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter.simpledialog import askstring
from tkinter.simpledialog import askinteger
from PIL import Image, ImageTk

import fileops as fops
import imageops as iops

import ui_generics as ui

CROP_RECT_MULTIPLIER = 8
CROP_RECT_STEP_MIN = 2

DEFAULT_ASPECT_X = 1
DEFAULT_ASPECT_Y = 1

DEFAULT_OUTPUT_WIDTH = 512
DEFAULT_OUTPUT_HEIGHT = 512

class VideoTab(tk.Frame):
    
    # params
    current_crop_rect_multiplier_step = CROP_RECT_STEP_MIN

    # widgets
    console = None
    input_path_entry = None
    output_path_entry = None
    extract_frames_button = None
    output_width_entry = None
    output_height_entry = None
    crop_aspect_x_entry = None
    crop_aspect_y_entry = None
    scale_output_checkbox = None
    ask_for_class_name_checkbox = None
    ask_for_image_description_checkbox = None
    ask_for_classes_checkbox = None
    
    # buttons
    seek_backward_button = None
    play_button = None
    pause_button = None
    stop_button = None
    seek_forward_button = None
    progress_bar = None
    
    # video vars
    video_path = ''
    video_length = None
    total_frames = None
    video_fps = None
    seeked = False
    playing = False
    percentage = 0
    cap = None

    # image canvas
    image_canvas = None
    image_container = None
    rectangle_container = None

    # data
    attribute_selector = None
    current_image = None
    current_image_index = None
    current_scaled_image = None
    current_canvas_size_x = None
    current_canvas_size_y = None
    current_mouse_x = None
    current_mouse_y = None
    current_rect_left = None
    current_rect_upper = None
    current_rect_right = None
    current_rect_lower = None
    raw_image = None
    scaled_image = None
    ratio = None
    crop_count = 0

    # appflow
    last_configure_time = None
    
    def __init__(self, console):
        super().__init__()
        self.console = console
        self.init_data()
        self.init_ui()
        
    def init_data(self):
        self.attribute_selector = self.AttributeSelector('tags.yaml')
    
    def init_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        main_frame = tk.Frame(self)
        main_frame.grid(row=0, column=0, sticky='news')
        main_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=2, uniform='x')
        main_frame.columnconfigure(1, weight=10, uniform='x')
        
        # left frame
        left_frame = tk.Frame(main_frame)
        left_frame.grid(column=0, row=0, sticky='news')

        left_widget_canvas = tk.Canvas(left_frame)
        left_widget_canvas.columnconfigure(0, weight=1)
        left_widget_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        paths_frame = tk.LabelFrame(left_widget_canvas, text='Paths')
        paths_frame.grid(column=0, row=0, sticky='news')
        paths_frame.columnconfigure(0, weight=1)
        
        self.input_path_entry = ui.LabelEntryFileBrowse('Input File', paths_frame, self.video_file_selected)
        self.input_path_entry.grid(column=0, row=0, sticky='news')

        self.output_path_entry = ui.LabelEntryFolderBrowse('Output Folder', paths_frame, None)
        self.output_path_entry.grid(column=0, row=1, sticky='news')
        
        self.extract_frames_button = tk.Button(paths_frame, text='Extract Frames', command=self.extract_frames_callback)
        self.extract_frames_button.grid(column=0, row=2, sticky='news')
        
        parameters_frame = tk.LabelFrame(left_widget_canvas, text='Parameters')
        parameters_frame.grid(column=0, row=1, sticky='news')
        parameters_frame.columnconfigure(0, weight=1)
        
        self.scale_output_checkbox = ui.CheckBox('Scale Output', self.scale_output_checkbox_callback, parameters_frame)
        self.scale_output_checkbox.grid(column=0, row=0, sticky='news')

        self.output_width_entry = ui.LabelEntryInt('Output Width', parameters_frame)
        self.output_width_entry.grid(column=0, row=1, sticky='news')
        self.output_width_entry.set_value(DEFAULT_OUTPUT_WIDTH)

        self.output_height_entry = ui.LabelEntryInt('Output Width', parameters_frame)
        self.output_height_entry.grid(column=0, row=2, sticky='news')
        self.output_height_entry.set_value(DEFAULT_OUTPUT_HEIGHT)

        self.crop_aspect_x_entry = ui.LabelEntryInt('Crop Aspect X', parameters_frame)
        self.crop_aspect_x_entry.grid(column=0, row=3, sticky='news')
        self.crop_aspect_x_entry.set_value(DEFAULT_ASPECT_X)

        self.crop_aspect_y_entry = ui.LabelEntryInt('Crop Aspect Y', parameters_frame)
        self.crop_aspect_y_entry.grid(column=0, row=4, sticky='news')
        self.crop_aspect_y_entry.set_value(DEFAULT_ASPECT_Y)
        
        self.ask_for_class_name_checkbox = ui.CheckBox('Ask For Class Name', None, parameters_frame)
        self.ask_for_class_name_checkbox.grid(column=0, row=5, sticky='news')
        
        self.ask_for_image_description_checkbox = ui.CheckBox('Ask For Image Description', None, parameters_frame)
        self.ask_for_image_description_checkbox.grid(column=0, row=6, sticky='news')

        self.ask_for_tags_checkbox = ui.CheckBox('Ask Tags (tags.yaml)', None, parameters_frame)
        self.ask_for_tags_checkbox.grid(column=0, row=7, sticky='news')

        self.scale_output_checkbox.set_value(0)
        self.ask_for_class_name_checkbox.set_value(0)
        
        # right frame
        image_frame = tk.LabelFrame(main_frame, text='Image')
        image_frame.rowconfigure(0, weight=1)
        image_frame.columnconfigure(0, weight=1)
        image_frame.grid(column=1, row=0, sticky='news')
        
        canvas_container = tk.Frame(image_frame)
        canvas_container.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        self.image_canvas = tk.Canvas(canvas_container)
        self.image_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        self.image_canvas.bind("<Motion>", self.canvas_mousemove)
        self.image_canvas.bind('<Enter>', self.bind_actions_to_canvas)
        self.image_canvas.bind('<Leave>', self.unbind_actions_from_canvas)
        self.image_canvas.bind('<ButtonRelease-1>', self.canvas_mouseclick)
        self.image_canvas.configure(bg='black')

        self.rectangle_container = self.image_canvas.create_rectangle(0, 0, self.crop_aspect_x_entry.get_value(),
                                                                      self.crop_aspect_y_entry.get_value(),
                                                                      outline='white', width=3)
                                                                      
        bottom_controls_container = tk.Frame(image_frame)
        bottom_controls_container.pack(side=tk.BOTTOM, fill=tk.X, expand=0)
        
        self.seek_backward_button = tk.Button(bottom_controls_container, text='BACK', command=self.seek_backward_button_callback)
        self.seek_backward_button.pack(side=tk.LEFT, fill=tk.Y)
        
        self.play_button = tk.Button(bottom_controls_container, text='PLAY', command=self.play_button_callback)
        self.play_button.pack(side=tk.LEFT, fill=tk.Y)
        
        self.pause_button = tk.Button(bottom_controls_container, text='PAUSE', command=self.pause_button_callback)
        self.pause_button.pack(side=tk.LEFT, fill=tk.Y)
        
        self.stop_button = tk.Button(bottom_controls_container, text='STOP', command=self.stop_button_callback)
        self.stop_button.pack(side=tk.LEFT, fill=tk.Y)
        
        self.seek_forward_button = tk.Button(bottom_controls_container, text='FORW', command=self.seek_forward_button_callback)
        self.seek_forward_button.pack(side=tk.LEFT, fill=tk.Y)
        
        self.progress_bar = ttk.Progressbar(bottom_controls_container, orient='horizontal', mode='determinate')
        self.progress_bar.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        self.progress_bar.bind('<ButtonPress-1>', self.progress_bar_seek_callback)
        
    def seek_backward_button_callback(self):
        if self.cap is None:
            return

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, int(((self.percentage - 5) / 100) * self.video_length))
        self.percentage = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES) / self.video_length * 100)
        self.progress_bar.config(value=self.percentage)
        
    def play_button_callback(self):
        if self.cap is None:
            if not self.input_path_entry.get_value():
                messagebox.showerror(title='Error', message='No video file selected.')
                return
            if not self.output_path_entry.get_value():
                messagebox.showerror(title='Error', message='No output path given.')
                return
            self.cap = cv2.VideoCapture(self.input_path_entry.get_value())
            self.video_length = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
        self.play_video()
        
    def pause_button_callback(self):
        self.playing = False
        
    def stop_button_callback(self):
        self.playing = False
        self.cap.release()
        self.cap = None
        self.percentage = 0
        self.progress_bar.config(value=0)
        
    def seek_forward_button_callback(self):
        if self.cap is None:
            return

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, int(((self.percentage + 5) / 100) * self.video_length))
        self.percentage = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES) / self.video_length * 100)
        self.progress_bar.config(value=self.percentage)
        
    def progress_bar_seek_callback(self, event):
        if self.cap is None:
            return
        
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, int((self.progress_bar["maximum"] * event.x / self.progress_bar.winfo_width()) / 100 * self.video_length))
        self.percentage = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES) / self.video_length * 100)
        self.progress_bar.config(value=self.percentage)
        
    def play_video(self):
        if self.cap is None:
            return
            
        self.playing = True
        
        self.display_frame()
        
    def display_frame(self):
        ret, frame = self.cap.read()

        if not ret:
            self.stop_button_callback()
            return
            
        self.percentage = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES) / self.video_length * 100)
        self.progress_bar.config(value=self.percentage)

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        self.raw_image = Image.fromarray(frame)
        self.image_canvas.delete('all')
        self.ratio = min(self.image_canvas.winfo_width() / self.raw_image.width,
                         self.image_canvas.winfo_height() / self.raw_image.height)
        self.scaled_image = iops.scale_image(self.raw_image, self.ratio)
        self.current_image = ImageTk.PhotoImage(self.scaled_image)
        
        self.image_container = self.image_canvas.create_image(self.image_canvas.winfo_width() / 2,
                                                              self.image_canvas.winfo_height() / 2, anchor=tk.CENTER,
                                                              image=self.current_image)

        rect_ratio = self.crop_aspect_y_entry.get_value() / self.crop_aspect_x_entry.get_value()
        rect_x = self.current_crop_rect_multiplier_step * CROP_RECT_MULTIPLIER
        rect_y = rect_x * rect_ratio
        self.rectangle_container = self.image_canvas.create_rectangle(self.current_mouse_x, self.current_mouse_y,
                                                                      rect_x,
                                                                      rect_y,
                                                                      outline='white', width=3)
        self.draw_rectangle()

        if self.playing:
            self.after(1, self.display_frame)
        
    
    def stop_video(self):
        return

    def pause_video(self):
        self.playing = False
        self.current_frame = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))

    def scale_output_checkbox_callback(self, value):
        if value == 1:
            self.output_height_entry.enable()
            self.output_width_entry.enable()
        else:
            self.output_height_entry.disable()
            self.output_width_entry.disable()

    def video_file_selected(self, path):
        if not path.endswith(('.mp4', '.avi', '.webm')):
            self.input_path_entry.clear()
            messagebox.showerror(title='Error', message='Selected file is not supported.')
            return
            
        self.video_path = path

    def extract_frames_callback(self):
        if not self.input_path_entry.get_value():
            messagebox.showerror(title='Error', message='No video file selected.')
            return
        
        initialpath = os.path.expanduser('~')
        path = tk.filedialog.askdirectory(initialdir=initialpath)
        if path:
            if not fops.check_path_valid(path):
                messagebox.showerror(title='Error', message='Path not valid.')
                return
            
            cap = cv2.VideoCapture(self.video_path)
            video_fps = round(cap.get(cv2.CAP_PROP_FPS))
            target_fps = askinteger('FPS', 'What FPS to extract? (Video FPS: ' + str(video_fps) + ')')
            
            if target_fps == 0:
                target_fps = video_fps
                
            hop = round(video_fps / target_fps)
            current_frame = 0
            
            while(True):
                ret, frame = cap.read()
                if not ret:
                    break
                if current_frame % hop == 0:
                    target_file = path + '/' + str(current_frame) + '.png'
                    cv2.imwrite(target_file, frame)
                    self.console.write_info('Extracted frame ' + str(current_frame) + '.')
                current_frame += 1
                    
            cap.release()
            self.console.write_info('Frame extraction complete.')

    def space_button_callback(self, event):
        if self.playing:
            self.pause_video()
        else:
            self.play_video()

    def draw_rectangle(self):
        rect_aspect_ratio = self.crop_aspect_y_entry.get_value() / self.crop_aspect_x_entry.get_value()
        rect_half_x = self.current_crop_rect_multiplier_step * CROP_RECT_MULTIPLIER / 2
        rect_half_y = int(rect_half_x * rect_aspect_ratio)
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

    def canvas_mousemove(self, event):
        self.current_mouse_x = event.x
        self.current_mouse_y = event.y
        self.current_canvas_size_x = self.image_canvas.winfo_width()
        self.current_canvas_size_y = self.image_canvas.winfo_height()

        self.draw_rectangle()

    def bind_actions_to_canvas(self, event):
        self.image_canvas.focus_set()
        self.bind_all("<MouseWheel>", self.canvas_mousewheel)
        self.bind_all("<Button-4>", self.canvas_mousewheel)
        self.bind_all("<Button-5>", self.canvas_mousewheel)
        self.bind_all('<space>', self.space_button_callback)

    def unbind_actions_from_canvas(self, event):
        self.unbind_all("<MouseWheel>")
        self.unbind_all("<Button-4>")
        self.unbind_all("<Button-5>")
        self.unbind_all('<space>')

    def canvas_mousewheel(self, event):
        if self.current_image is not None:
            if event.num == 4 or event.delta == -120:
                rect_ratio = self.crop_aspect_y_entry.get_value() / self.crop_aspect_x_entry.get_value()
                new_multiplier_step = self.current_crop_rect_multiplier_step + 1

                if (CROP_RECT_MULTIPLIER * new_multiplier_step < self.scaled_image.width) and (
                        CROP_RECT_MULTIPLIER * new_multiplier_step * rect_ratio < self.scaled_image.height):
                    self.current_crop_rect_multiplier_step = new_multiplier_step

            if event.num == 5 or event.delta == 120:
                self.current_crop_rect_multiplier_step = self.current_crop_rect_multiplier_step - 1
                if self.current_crop_rect_multiplier_step < CROP_RECT_STEP_MIN:
                    self.current_crop_rect_multiplier_step = CROP_RECT_STEP_MIN

        self.draw_rectangle()

    def canvas_mouseclick(self, event):
        # check output path given
        if not self.output_path_entry.get_value():
            messagebox.showerror(title='Error', message='No output path given.')
            return
        
        if self.cap is None:
            messagebox.showerror(title='Error', message='No video.')
            return
            
        self.pause_video()

        # if ask for class name checked
        class_name = None
        if self.ask_for_class_name_checkbox.get_value():
            class_name = askstring('Class name', 'What is the class name?')
            
        # if ask for image description checked
        image_description = None
        if self.ask_for_image_description_checkbox.get_value():
            image_description = askstring('Image description', 'What is in the image?')
        elif self.ask_for_tags_checkbox.get_value():
            image_description = self.attribute_selector.ask_attributes()

        # take coordinates and crop
        cropped_image = self.get_image_inside_rectangle()
        if self.scale_output_checkbox.get_value():
            cropped_image = iops.resize_image(cropped_image, height=self.output_height_entry.get_value(),
                                              width=self.output_width_entry.get_value())

        output_basefilename = os.path.basename(self.input_path_entry.get_value()).split('.')[0]
        output_image_name = output_basefilename + '_' + str(self.crop_count) + '.png'
        output_image_description_name = output_basefilename + '_' + str(self.crop_count) + '.txt'

        # check output path
        output_image_path = self.output_path_entry.get_value()
        if not fops.check_path_valid(output_image_path):
            output_image_path = self.input_path_entry.get_value() + '/' + output_image_path

        output_image_description_file_path = ""
        if class_name is not None:
            output_image_file_path = output_image_path + '/' + class_name + '/' + output_image_name
            output_image_description_file_path = output_image_path + '/' + class_name + '/' + output_image_description_name
        else:
            output_image_file_path = output_image_path + '/' + output_image_name
            output_image_description_file_path = output_image_path + '/' + output_image_description_name
        
	
        fops.save_image_to_file(cropped_image, filepath=output_image_file_path)
        fops.save_image_description_to_file(image_description, filepath=output_image_description_file_path)
        self.console.write_info('Image saved to: ' + output_image_file_path)
        self.crop_count = self.crop_count + 1
        
    def get_image_inside_rectangle(self):
        box_rel_tl_x = self.current_rect_left - ((self.current_canvas_size_x - self.scaled_image.width) / 2)
        box_rel_tl_y = self.current_rect_upper - ((self.current_canvas_size_y - self.scaled_image.height) / 2)
        box_rel_bl_x = box_rel_tl_x + (self.current_rect_right - self.current_rect_left)
        box_rel_bl_y = box_rel_tl_y + (self.current_rect_lower - self.current_rect_upper)
        # get rect data and crop image
        return iops.crop_image(self.raw_image, self.ratio, (box_rel_tl_x, box_rel_tl_y, box_rel_bl_x, box_rel_bl_y))
    
    class AttributeSelector:
        def __init__(self, file_path):
            with open(file_path, 'r') as f:
                self.attributes = yaml.load(f, Loader=yaml.FullLoader)
    
        def ask_attributes(self):
            top_level = tk.Toplevel()
            top_level.title('Choose attributes')
    
            selected_values = []
    
            def on_button_click():
                nonlocal selected_values
                selected_values = [var.get() for var in self.vars.values()]
                top_level.destroy()
    
            num_attributes = len(self.attributes)
            num_values = max(len(values) for values in self.attributes.values())
            num_columns = 8
            num_rows = (num_attributes + num_columns - 1) // num_columns
    
            self.vars = {}
            for i, (attribute, values) in enumerate(self.attributes.items()):
                row = i // num_columns
                col = i % num_columns
                lf = tk.LabelFrame(top_level, text=attribute)
                lf.grid(row=row, column=col, padx=10, pady=5, sticky='news')
                var = tk.StringVar(value=values[0])
                self.vars[attribute] = var
                for value in values:
                    rb = tk.Radiobutton(lf, text=value, value=value, variable=var)
                    rb.pack(padx=5, pady=2, expand=True)
    
            button_ok = tk.Button(top_level, text='OK', command=on_button_click)
            button_ok.grid(row=num_rows, column=0, columnspan=num_columns, pady=10)
    
            top_level.grab_set()
            top_level.protocol("WM_DELETE_WINDOW", top_level.quit)
            top_level.wait_window()
    
            selected_values_str = ', '.join([v for v in selected_values if v])
            return selected_values_str
    