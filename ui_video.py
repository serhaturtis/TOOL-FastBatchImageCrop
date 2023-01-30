# -*- coding: utf-8 -*-
import os
import cv2
import time
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter.simpledialog import askstring
from tkinter.simpledialog import askinteger

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
    
    # buttons
    seek_back_button = None
    play_button = None
    pause_button = None
    stop_button = None
    seek_forward_button = None
    progress_bar = None
    
    # video vars
    video_path = ''
    seeked = False
    playing = False
    total_frames = None
    video_loaded = None
    cap = None

    # image canvas
    image_canvas = None
    image_container = None
    rectangle_container = None

    # data
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
        return
    
    def init_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        main_frame = tk.Frame(self)
        main_frame.grid(row=0, column=0, sticky='news')
        main_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=7)
        
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

        self.scale_output_checkbox.set_value(0)
        self.roll_on_crop_checkbox.set_value(1)
        self.ask_for_class_name_checkbox.set_value(0)
        
        # right frame
        image_frame = tk.LabelFrame(main_frame, text='Image')
        image_frame.rowconfigure(0, weight=1)
        image_frame.columnconfigure(0, weight=1)
        image_frame.grid(column=1, row=0, sticky='news')

        self.image_canvas = tk.Canvas(image_frame)
        self.image_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        self.image_canvas.bind("<Motion>", self.canvas_mousemove)
        self.image_canvas.bind('<Enter>', self.bind_actions_to_canvas)
        self.image_canvas.bind('<Leave>', self.unbind_actions_from_canvas)
        self.image_canvas.bind('<ButtonRelease-1>', self.canvas_mouseclick)
        self.image_canvas.configure(bg='black')

        # self.image_container = self.image_canvas.create_image(0, 0, anchor=tk.CENTER, image=self.current_image)
        self.rectangle_container = self.image_canvas.create_rectangle(0, 0, self.crop_aspect_x_entry.get_value(),
                                                                      self.crop_aspect_y_entry.get_value(),
                                                                      outline='white', width=3)

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
            
            target_fps = askinteger('FPS', 'What FPS to extract? (0 for video fps)')
            cap = cv2.VideoCapture(self.video_path)
            video_fps = round(cap.get(cv2.CAP_PROP_FPS))
            
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

    def play_video(self):
        if self.cap is None:
            if not self.input_path_entry.get_value():
                messagebox.showerror(title='Error', message='No video file selected.')
                return
            if not self.output_path_entry.get_value():
                messagebox.showerror(title='Error', message='No output path given.')
                return
            self.cap = cv2.VideoCapture(self.video)
    
    def stop_video(self):
        return

    def pause_video(self):
        self.playing = False
        self.current_frame = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))

    def space_button_callback(self):
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
        if self.input_files is None:
            messagebox.showerror(title='Error', message='No input images.')
            return
        elif len(self.input_files) == 0:
            messagebox.showerror(title='Error', message='No input images.')
            return

        class_name = ""
        # if ask for class name checked
        if self.ask_for_class_name_checkbox.get_value():
            class_name = askstring('Class name', 'What is the class name?')
            
        # if ask for image description checked
        if self.ask_for_image_description_checkbox.get_value():
            image_description = askstring('Image description', 'What is in the image?')

        # take coordinates and crop
        cropped_image = self.get_image_inside_rectangle()
        if self.scale_output_checkbox.get_value():
            cropped_image = iops.resize_image(cropped_image, height=self.output_height_entry.get_value(),
                                              width=self.output_width_entry.get_value())

        output_image_name = self.input_files[self.current_image_index][0].split('.')[0] + '_' + str(
            self.crop_count) + '.png'
        output_image_description_name = self.input_files[self.current_image_index][0].split('.')[0] + '_' + str(
            self.crop_count) + '.txt'

        # check output path
        output_image_path = self.output_path_entry.get_value()
        if not fops.check_path_valid(output_image_path):
            output_image_path = self.input_path_entry.get_value() + '/' + output_image_path

        output_image_description_file_path = ""
        if class_name != "":
            output_image_file_path = output_image_path + '/' + class_name + '/' + output_image_name
            output_image_description_file_path = output_image_path + '/' + class_name + '/' + output_image_description_name
        else:
            output_image_file_path = output_image_path + '/' + output_image_name
            output_image_description_file_path = output_image_path + '/' + output_image_description_name
        
	
        fops.save_image_to_file(cropped_image, filepath=output_image_file_path)
        fops.save_image_description_to_file(image_description, filepath=output_image_description_file_path)
        self.console.write_info('Image saved to: ' + output_image_file_path)
        self.crop_count = self.crop_count + 1