import tkinter as tk
import ui_generics as ui
import file
import image
from PIL import ImageTk


class Application(tk.Tk):
    console = None

    # paths
    input_entry = None
    output_entry = None
    load_button = None

    # parameters
    scale_output = None
    output_width_entry = None
    output_height_entry = None
    crop_size_x_entry = None
    crop_size_y_entry = None

    # files list
    files_listbox = None

    # image canvas
    image_canvas = None
    image_container = None
    rectangle_container = None

    current_image = None
    current_image_index = None
    current_scaled_image = None
    current_canvas_size_x = None
    current_canvas_size_y = None
    current_mouse_x = None
    current_mouse_y = None

    # current data
    input_files = None

    def __init__(self, geometry):
        super().__init__()
        self.console = ui.Console()
        self.geometry(geometry)
        self.init_data()
        self.init_ui()

    def init_data(self):
        self.console.write_info('Init data complete.')

    def init_ui(self):
        self.title('FastBatchCrop')
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=7)
        self.rowconfigure(1, weight=1)

        # console
        self.console.grid(column=0, row=1, sticky='news')

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

        self.input_entry = ui.LabelEntryFolderBrowse('Input Folder', paths_frame)
        self.input_entry.grid(column=0, row=0, sticky='news')

        self.output_entry = ui.LabelEntryFolderBrowse('Output Folder', paths_frame)
        self.output_entry.grid(column=0, row=1, sticky='news')

        self.load_button = tk.Button(paths_frame, text='Load', command=self.get_images)
        self.load_button.grid(column=0, row=2, sticky='news')

        parameters_frame = tk.LabelFrame(left_widget_canvas, text='Parameters')
        parameters_frame.grid(column=0, row=1, sticky='news')
        parameters_frame.columnconfigure(0, weight=1)

        self.scale_output = ui.CheckBox('Scale Output', self.scale_output_checkbox_callback, parameters_frame)
        self.scale_output.grid(column=0, row=0, sticky='news')

        self.output_width_entry = ui.LabelEntryInt('Output Width', parameters_frame)
        self.output_width_entry.grid(column=0, row=1, sticky='news')
        self.output_width_entry.set_value(512)

        self.output_height_entry = ui.LabelEntryInt('Output Width', parameters_frame)
        self.output_height_entry.grid(column=0, row=2, sticky='news')
        self.output_height_entry.set_value(512)

        self.crop_size_x_entry = ui.LabelEntryInt('Crop Cursor Size X', parameters_frame)
        self.crop_size_x_entry.grid(column=0, row=3, sticky='news')
        self.crop_size_x_entry.set_value(512)

        self.crop_size_y_entry = ui.LabelEntryInt('Crop Cursor Size Y', parameters_frame)
        self.crop_size_y_entry.grid(column=0, row=4, sticky='news')
        self.crop_size_y_entry.set_value(512)

        self.scale_output_checkbox_callback(0)

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
        self.image_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        self.image_canvas.bind("<Motion>", self.canvas_mousemove)
        self.image_canvas.bind('<Enter>', self.bind_mousewheel_to_canvas)
        self.image_canvas.bind('<Leave>', self.unbind_mousewheel_to_canvas)
        self.image_canvas.bind('<ButtonRelease-1>', self.canvas_mouseclick)

        self.image_canvas.configure(bg='blue')

        self.image_container = self.image_canvas.create_image(0, 0, anchor=tk.NW, image=self.current_image)
        self.rectangle_container = self.image_canvas.create_rectangle(0, 0, self.crop_size_x_entry.get_value(), self.crop_size_y_entry.get_value(), outline='white', width=3)

        self.console.write_info('UI init done.')

    def scale_output_checkbox_callback(self, value):
        if value == 1:
            self.output_height_entry.grid()
            self.output_width_entry.grid()
        else:
            self.output_height_entry.grid_remove()
            self.output_width_entry.grid_remove()

    def get_images(self):
        self.files_listbox.clear()
        input_path = self.input_entry.get_value()
        self.input_files = file.get_image_files(input_path)
        self.files_listbox.set_data(self.input_files)
        self.console.write_info('Found ' + str(len(self.input_files)) + ' images.')

    def draw_rectangle(self):
        self.image_canvas.coords(self.rectangle_container,
                                 self.current_mouse_x - self.crop_size_x_entry.get_value() / 2,
                                 self.current_mouse_y - self.crop_size_y_entry.get_value() / 2,
                                 self.current_mouse_x + self.crop_size_x_entry.get_value() / 2,
                                 self.current_mouse_y + self.crop_size_y_entry.get_value() / 2)

        self.image_canvas.update()


    def listbox_onclick(self, event):
        if self.files_listbox.get_list_length() == 0:
            return

        w = event.widget
        index = w.curselection()
        if index:
            index = int(w.curselection()[0])

            self.current_image_index = index
            self.current_image = tk.PhotoImage(file=self.input_files[index][1])

            self.image_canvas.itemconfig(self.image_container, image=self.current_image)
            self.image_canvas.update()

    def canvas_mousemove(self, event):
        print('Currentx: ' + str(event.x) + ' currenty: ' + str(event.y))
        self.current_mouse_x = event.x
        self.current_mouse_y = event.y
        self.current_canvas_size_x = self.image_canvas.winfo_width()
        self.current_canvas_size_y = self.image_canvas.winfo_height()
        print(self.current_canvas_size_x)
        print(self.current_canvas_size_y)
        self.draw_rectangle()


    def bind_mousewheel_to_canvas(self, event):
        self.bind_all("<MouseWheel>", self.canvas_mousewheel)
        self.bind_all("<Button-4>", self.canvas_mousewheel)
        self.bind_all("<Button-5>", self.canvas_mousewheel)

    def unbind_mousewheel_to_canvas(self, event):
        self.unbind_all("<MouseWheel>")
        self.unbind_all("<Button-4>")
        self.unbind_all("<Button-5>")

    def canvas_mousewheel(self, event):
        if event.num == 4 or event.delta == -120:
            new_x_val = (self.crop_size_x_entry.get_value() + 16)
            if new_x_val > 512:
                new_x_val = 512

            new_y_val = (self.crop_size_y_entry.get_value() + 16)
            if new_y_val > 512:
                new_y_val = 512

            self.crop_size_x_entry.set_value(new_x_val)
            self.crop_size_y_entry.set_value(new_y_val)

        if event.num == 5 or event.delta == 120:
            new_x_val = self.crop_size_x_entry.get_value() - 16
            if new_x_val < 32:
                new_x_val = 32

            new_y_val = self.crop_size_y_entry.get_value() - 16
            if new_y_val < 32:
                new_y_val = 32
            self.crop_size_x_entry.set_value(new_x_val)
            self.crop_size_y_entry.set_value(new_y_val)

        self.draw_rectangle()

    def canvas_mouseclick(self, event):
        print('Clicked')



