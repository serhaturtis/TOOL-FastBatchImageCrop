# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import messagebox
from tkinter.simpledialog import askstring

import fileops as fops
import imageops as iops

import ui_generics as ui

from PIL import ImageTk

CROP_RECT_MULTIPLIER = 8
CROP_RECT_STEP_MIN = 2

DEFAULT_ASPECT_X = 1
DEFAULT_ASPECT_Y = 1

DEFAULT_OUTPUT_WIDTH = 512
DEFAULT_OUTPUT_HEIGHT = 512

class ImagesetTab(tk.Frame):
    
    # params
    current_crop_rect_multiplier_step = CROP_RECT_STEP_MIN

    # widgets
    console = None
    input_path_entry = None
    output_path_entry = None
    output_width_entry = None
    output_height_entry = None
    crop_aspect_x_entry = None
    crop_aspect_y_entry = None
    files_listbox = None
    scale_output_checkbox = None
    roll_on_crop_checkbox = None
    use_class_name_checkbox = None
    use_image_description_checkbox = None
    class_name_entry = None
    image_description_entry = None


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
    input_files = None
    raw_image = None
    scaled_image = None
    ratio = None
    crop_count = 0
    
    def __init__(self, console):
        super().__init__()
        self.console = console
        self.init_data()
        self.init_ui()
        self.console.write_info('Imageset Tab init complete.')

    
    def init_data(self):
        return
    
    def init_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        main_frame = tk.Frame(self)
        main_frame.grid(row=0, column=0, sticky='news')
        main_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(2, weight=6)

        # left frame
        left_frame = tk.Frame(main_frame)
        left_frame.grid(column=0, row=0, sticky='news')

        left_widget_canvas = tk.Canvas(left_frame)
        left_widget_canvas.columnconfigure(0, weight=1)
        left_widget_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        paths_frame = tk.LabelFrame(left_widget_canvas, text='Paths')
        paths_frame.grid(column=0, row=0, sticky='news')
        paths_frame.columnconfigure(0, weight=1)

        self.input_path_entry = ui.LabelEntryFolderBrowse('Input Folder', paths_frame,
                                                          callback=self.set_files_to_listbox)
        self.input_path_entry.grid(column=0, row=0, sticky='news')

        self.output_path_entry = ui.LabelEntryFolderBrowse('Output Folder', paths_frame)
        self.output_path_entry.grid(column=0, row=1, sticky='news')

        parameters_frame = tk.LabelFrame(left_widget_canvas, text='Parameters')
        parameters_frame.grid(column=0, row=1, sticky='news')
        parameters_frame.columnconfigure(0, weight=1)

        self.scale_output_checkbox = ui.CheckBox('Scale Output', self.scale_output_checkbox_callback, parameters_frame)
        self.scale_output_checkbox.grid(column=0, row=0, sticky='news')

        self.roll_on_crop_checkbox = ui.CheckBox('Roll On Crop', None, parameters_frame)
        self.roll_on_crop_checkbox.grid(column=0, row=1, sticky='news')

        self.output_width_entry = ui.LabelEntryInt('Output Width', parameters_frame)
        self.output_width_entry.grid(column=0, row=2, sticky='news')
        self.output_width_entry.set_value(DEFAULT_OUTPUT_WIDTH)

        self.output_height_entry = ui.LabelEntryInt('Output Width', parameters_frame)
        self.output_height_entry.grid(column=0, row=3, sticky='news')
        self.output_height_entry.set_value(DEFAULT_OUTPUT_HEIGHT)

        self.crop_aspect_x_entry = ui.LabelEntryInt('Crop Aspect X', parameters_frame)
        self.crop_aspect_x_entry.grid(column=0, row=4, sticky='news')
        self.crop_aspect_x_entry.set_value(DEFAULT_ASPECT_X)

        self.crop_aspect_y_entry = ui.LabelEntryInt('Crop Aspect Y', parameters_frame)
        self.crop_aspect_y_entry.grid(column=0, row=5, sticky='news')
        self.crop_aspect_y_entry.set_value(DEFAULT_ASPECT_Y)
        
        self.use_class_name_checkbox = ui.CheckBox('Use Class Name', None, parameters_frame)
        self.use_class_name_checkbox.grid(column=0, row=6, sticky='news')
        
        self.use_image_description_checkbox = ui.CheckBox('Use Image Description', None, parameters_frame)
        self.use_image_description_checkbox.grid(column=0, row=7, sticky='news')

        self.scale_output_checkbox.set_value(0)
        self.roll_on_crop_checkbox.set_value(1)
        self.use_class_name_checkbox.set_value(0)
        self.use_image_description_checkbox.set_value(0)

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

        self.image_canvas.bind("<Motion>", self.canvas_mousemove)
        self.image_canvas.bind('<Enter>', self.bind_actions_to_canvas)
        self.image_canvas.bind('<Leave>', self.unbind_actions_from_canvas)
        self.image_canvas.bind('<ButtonRelease-1>', self.canvas_mouseclick)
        self.image_canvas.configure(bg='black')

        self.image_description_entry = ui.LabelEntryText('Image Description', image_frame)
        self.image_description_entry.pack(side=tk.BOTTOM, fill=tk.X)

        self.class_name_entry = ui.LabelEntryText('Class Name', image_frame)
        self.class_name_entry.pack(side=tk.BOTTOM, fill=tk.X)

        # self.image_container = self.image_canvas.create_image(0, 0, anchor=tk.CENTER, image=self.current_image)
        self.rectangle_container = self.image_canvas.create_rectangle(0, 0, self.crop_aspect_x_entry.get_value(),
                                                                      self.crop_aspect_y_entry.get_value(),
                                                                      outline='white', width=3)
    
    def window_reconfigure(self, event):
        if self.current_image is not None:
            if not ((self.current_image.width() == self.image_canvas.winfo_width()) or (self.current_image.height() == self.image_canvas.winfo_height())):
                self.load_image_to_canvas()
    
    def scale_output_checkbox_callback(self, value):
        if value == 1:
            self.output_height_entry.enable()
            self.output_width_entry.enable()
        else:
            self.output_height_entry.disable()
            self.output_width_entry.disable()

    def set_files_to_listbox(self, path):
        self.output_path_entry.set_value(path + '/out')
        self.image_canvas.delete('all')
        self.files_listbox.clear()
        self.input_files = fops.get_image_files(path)
        self.files_listbox.set_data(self.input_files)

        if self.files_listbox.get_list_length() != 0:
            self.files_listbox.get_widget().selection_clear(0, tk.END)
            self.files_listbox.get_widget().select_set(0)
            self.current_image_index = 0
            self.files_listbox.get_widget().event_generate("<<ListboxSelect>>")

        self.console.write_info('Found ' + str(len(self.input_files)) + ' image(s).')

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

        rect_ratio = self.crop_aspect_y_entry.get_value() / self.crop_aspect_x_entry.get_value()
        rect_x = self.current_crop_rect_multiplier_step * CROP_RECT_MULTIPLIER
        rect_y = rect_x * rect_ratio
        self.rectangle_container = self.image_canvas.create_rectangle(self.current_mouse_x, self.current_mouse_y,
                                                                      rect_x,
                                                                      rect_y,
                                                                      outline='white', width=3)
        self.draw_rectangle()

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
        self.bind_all('<space>', self.roll)
        self.bind_all('<e>', self.rotate_image_cw)
        self.bind_all('<q>', self.rotate_image_ccw)
        self.bind_all('r', self.toggle_roll)

    def unbind_actions_from_canvas(self, event):
        self.unbind_all("<MouseWheel>")
        self.unbind_all("<Button-4>")
        self.unbind_all("<Button-5>")
        self.unbind_all('<space>')
        self.unbind_all('<e>')
        self.unbind_all('<q>')
        self.unbind_all('r')

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

    def get_image_inside_rectangle(self):
        box_rel_tl_x = self.current_rect_left - ((self.current_canvas_size_x - self.scaled_image.width) / 2)
        box_rel_tl_y = self.current_rect_upper - ((self.current_canvas_size_y - self.scaled_image.height) / 2)
        box_rel_bl_x = box_rel_tl_x + (self.current_rect_right - self.current_rect_left)
        box_rel_bl_y = box_rel_tl_y + (self.current_rect_lower - self.current_rect_upper)
        # get rect data and crop image
        return iops.crop_image(self.raw_image, self.ratio, (box_rel_tl_x, box_rel_tl_y, box_rel_bl_x, box_rel_bl_y))

    def toggle_roll(self, event):
        self.roll_on_crop_checkbox.set_value(not self.roll_on_crop_checkbox.get_value())
        
    def rotate_image_cw(self, event):
        self.raw_image = iops.rotate_image(self.raw_image, 270)
        self.load_image_to_canvas()
        
    def rotate_image_ccw(self, event):
        self.raw_image = iops.rotate_image(self.raw_image, 90)
        self.load_image_to_canvas()

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
            self.files_listbox.get_widget().event_generate("<<ListboxSelect>>")

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

	    # if ask for class name checked
        class_name = None
        if self.use_class_name_checkbox.get_value():
            #class_name = askstring('Class name', 'What is the class name?')
            class_name = self.class_name_entry.get_value()
            
        # if ask for image description checked
        image_description = None
        if self.use_image_description_checkbox.get_value():
            #image_description = askstring('Image description', 'What is in the image?')
            image_description = self.image_description_entry.get_value()

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

        # roll or not
        if self.roll_on_crop_checkbox.get_value():
            # clear image description entry
            self.image_description_entry.clear()
            # roll
            self.roll(None)
