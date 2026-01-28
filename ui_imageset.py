import tkinter as tk
from tkinter import messagebox
import math
from typing import Optional, Tuple, List

import os
import fileops as fops
import imageops as iops
import ui_generics as ui
from attribute_selector import AttributeSelector
from rectangle_mixin import RectangleMixin

from PIL import ImageTk

CROP_RECT_MULTIPLIER = 8
CROP_RECT_STEP_MIN = 2

DEFAULT_ASPECT_X = 1
DEFAULT_ASPECT_Y = 1

DEFAULT_OUTPUT_WIDTH = 512
DEFAULT_OUTPUT_HEIGHT = 512

TAGS_FILE = "tags.yaml"
CLASSES_FILE = "classes.txt"


class ImagesetTab(tk.Frame, RectangleMixin):
    def __init__(self, console):
        super().__init__()
        self.current_crop_rect_multiplier_step = CROP_RECT_STEP_MIN

        self.console = console
        self.input_path_entry = None
        self.output_path_entry = None
        self.output_width_entry = None
        self.output_height_entry = None
        self.crop_aspect_x_entry = None
        self.crop_aspect_y_entry = None
        self.files_listbox = None
        self.scale_output_checkbox = None
        self.roll_on_crop_checkbox = None
        self.use_class_name_checkbox = None
        self.use_image_description_checkbox = None
        self.ask_for_classes_checkbox = None
        self.ask_for_tags_checkbox = None
        self.class_name_entry = None
        self.image_description_entry = None

        self.image_canvas = None
        self.image_container = None
        self.rectangle_container = None

        self.current_image = None
        self.current_image_index = None
        self.current_scaled_image = None
        self.current_canvas_size_x = None
        self.current_canvas_size_y = None
        self.current_mouse_x = 0
        self.current_mouse_y = 0
        self.current_rect_left = None
        self.current_rect_upper = None
        self.current_rect_right = None
        self.current_rect_lower = None
        self.input_files = None
        self.raw_image = None
        self.scaled_image = None
        self.ratio = None
        self.crop_count = 0
        self.attribute_selector = None

        self.init_data()
        self.init_ui()
        self.console.write_info("Imageset Tab init complete.")

    def init_data(self):
        self.attribute_selector = AttributeSelector(TAGS_FILE)

    def init_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        main_frame = tk.Frame(self)
        main_frame.grid(row=0, column=0, sticky="news")
        main_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=2, uniform="x")
        main_frame.columnconfigure(1, weight=2, uniform="x")
        main_frame.columnconfigure(2, weight=8, uniform="x")

        left_frame = tk.Frame(main_frame)
        left_frame.grid(column=0, row=0, sticky="news")

        left_widget_frame = tk.Frame(left_frame)
        left_widget_frame.columnconfigure(0, weight=1)
        left_widget_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        paths_frame = tk.LabelFrame(left_widget_frame, text="Paths")
        paths_frame.grid(column=0, row=0, sticky="news")
        paths_frame.columnconfigure(0, weight=1)

        self.input_path_entry = ui.LabelEntryFolderBrowse(
            "Input Folder", paths_frame, callback=self.set_files_to_listbox
        )
        self.input_path_entry.grid(column=0, row=0, sticky="news")

        self.output_path_entry = ui.LabelEntryFolderBrowse("Output Folder", paths_frame)
        self.output_path_entry.grid(column=0, row=1, sticky="news")

        parameters_frame = tk.LabelFrame(left_widget_frame, text="Parameters")
        parameters_frame.grid(column=0, row=1, sticky="news")
        parameters_frame.columnconfigure(0, weight=1)

        self.scale_output_checkbox = ui.CheckBox(
            "Scale Output", self.scale_output_checkbox_callback, parameters_frame
        )
        self.scale_output_checkbox.grid(column=0, row=0, sticky="news")

        self.roll_on_crop_checkbox = ui.CheckBox("Roll On Crop", None, parameters_frame)
        self.roll_on_crop_checkbox.grid(column=0, row=1, sticky="news")

        self.output_width_entry = ui.LabelEntryInt("Output Width", parameters_frame)
        self.output_width_entry.grid(column=0, row=2, sticky="news")
        self.output_width_entry.set_value(DEFAULT_OUTPUT_WIDTH)

        self.output_height_entry = ui.LabelEntryInt("Output Height", parameters_frame)
        self.output_height_entry.grid(column=0, row=3, sticky="news")
        self.output_height_entry.set_value(DEFAULT_OUTPUT_HEIGHT)

        self.crop_aspect_x_entry = ui.LabelEntryInt("Crop Aspect X", parameters_frame)
        self.crop_aspect_x_entry.grid(column=0, row=4, sticky="news")
        self.crop_aspect_x_entry.set_value(DEFAULT_ASPECT_X)

        self.crop_aspect_y_entry = ui.LabelEntryInt("Crop Aspect Y", parameters_frame)
        self.crop_aspect_y_entry.grid(column=0, row=5, sticky="news")
        self.crop_aspect_y_entry.set_value(DEFAULT_ASPECT_Y)

        self.use_class_name_checkbox = ui.CheckBox(
            "Use Class Name", None, parameters_frame
        )
        self.use_class_name_checkbox.grid(column=0, row=6, sticky="news")

        self.use_image_description_checkbox = ui.CheckBox(
            "Use Image Description", None, parameters_frame
        )
        self.use_image_description_checkbox.grid(column=0, row=7, sticky="news")

        self.ask_for_classes_checkbox = ui.CheckBox(
            "Ask Classes (classes.txt)", None, parameters_frame
        )
        self.ask_for_classes_checkbox.grid(column=0, row=8, sticky="news")

        self.ask_for_tags_checkbox = ui.CheckBox(
            "Ask Tags (tags.yaml)", None, parameters_frame
        )
        self.ask_for_tags_checkbox.grid(column=0, row=9, sticky="news")

        self.scale_output_checkbox.set_value(0)
        self.roll_on_crop_checkbox.set_value(1)
        self.use_class_name_checkbox.set_value(0)
        self.use_image_description_checkbox.set_value(0)
        self.ask_for_classes_checkbox.set_value(0)

        mid_frame = tk.Frame(main_frame)
        mid_frame.grid(column=1, row=0, sticky="news")
        mid_frame.rowconfigure(0, weight=1)
        mid_frame.columnconfigure(0, weight=1)

        self.files_listbox = ui.ScrollableListbox("Files", mid_frame)
        self.files_listbox.grid(column=0, row=0, sticky="news")
        self.files_listbox.bind_onclick(self.listbox_onclick)

        image_frame = tk.LabelFrame(main_frame, text="Image")
        image_frame.rowconfigure(0, weight=1)
        image_frame.columnconfigure(0, weight=1)
        image_frame.grid(column=2, row=0, sticky="news")

        self.image_canvas = tk.Canvas(image_frame)
        self.image_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        self.image_canvas.bind("<Motion>", self.on_canvas_motion)
        self.image_canvas.bind("<Enter>", self.on_canvas_enter)
        self.image_canvas.bind("<Leave>", self.on_canvas_leave)
        self.image_canvas.bind("<ButtonRelease-1>", self.canvas_mouseclick)
        self.image_canvas.configure(bg="black")

        self.image_description_entry = ui.LabelEntryText(
            "Image Description", image_frame
        )
        self.image_description_entry.pack(side=tk.BOTTOM, fill=tk.X)

        self.class_name_entry = ui.LabelEntryText("Class Name", image_frame)
        self.class_name_entry.pack(side=tk.BOTTOM, fill=tk.X)

        self.rectangle_container = self.image_canvas.create_rectangle(
            self.current_mouse_x,
            self.current_mouse_y,
            self.crop_aspect_x_entry.get_value(),
            self.crop_aspect_y_entry.get_value(),
            outline="white",
            width=3,
        )

    def window_reconfigure(self, event):
        if self.current_image is not None:
            try:
                if not (
                    (self.current_image.width() == self.image_canvas.winfo_width())
                    or (self.current_image.height() == self.image_canvas.winfo_height())
                ):
                    self.load_image_to_canvas()
            except tk.TclError:
                pass  # Canvas not ready or destroyed

    def scale_output_checkbox_callback(self, value):
        if value == 1:
            self.output_height_entry.enable()
            self.output_width_entry.enable()
        else:
            self.output_height_entry.disable()
            self.output_width_entry.disable()

    def set_files_to_listbox(self, path):
        self.output_path_entry.set_value(os.path.join(path, "out"))
        self.image_canvas.delete("all")
        self.files_listbox.clear()
        self.crop_count = 0  # Reset crop count for new folder
        self.input_files = fops.get_image_files(path)
        self.files_listbox.set_data(self.input_files)

        if self.files_listbox.get_list_length() != 0:
            self.files_listbox.get_widget().selection_clear(0, tk.END)
            self.files_listbox.get_widget().select_set(0)
            self.current_image_index = 0
            self.files_listbox.get_widget().event_generate("<<ListboxSelect>>")

        self.console.write_info("Found " + str(len(self.input_files)) + " image(s).")

    def get_rect_half_size(self):
        """Return the half-size of the crop rectangle based on current settings."""
        aspect_x = self.crop_aspect_x_entry.get_value() or 1
        rect_aspect_ratio = self.crop_aspect_y_entry.get_value() / aspect_x
        rect_half_x = self.current_crop_rect_multiplier_step * CROP_RECT_MULTIPLIER / 2
        rect_half_y = int(rect_half_x * rect_aspect_ratio)
        return rect_half_x, rect_half_y

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

        self.image_canvas.delete("all")

        self.ratio = min(
            self.image_canvas.winfo_width() / self.raw_image.width,
            self.image_canvas.winfo_height() / self.raw_image.height,
        )
        self.scaled_image = iops.scale_image(self.raw_image, self.ratio)
        self.current_image = ImageTk.PhotoImage(self.scaled_image)

        self.image_container = self.image_canvas.create_image(
            self.image_canvas.winfo_width() / 2,
            self.image_canvas.winfo_height() / 2,
            anchor=tk.CENTER,
            image=self.current_image,
        )

        aspect_x = self.crop_aspect_x_entry.get_value() or 1
        rect_ratio = self.crop_aspect_y_entry.get_value() / aspect_x
        rect_x = self.current_crop_rect_multiplier_step * CROP_RECT_MULTIPLIER
        rect_y = rect_x * rect_ratio
        self.rectangle_container = self.image_canvas.create_rectangle(
            self.current_mouse_x - rect_x / 2,
            self.current_mouse_y - rect_y / 2,
            self.current_mouse_x + rect_x / 2,
            self.current_mouse_y + rect_y / 2,
            outline="white",
            width=3,
        )
        self.move_rectangle()

    def on_canvas_motion(self, event):
        self.current_mouse_x = event.x
        self.current_mouse_y = event.y
        self.current_canvas_size_x = self.image_canvas.winfo_width()
        self.current_canvas_size_y = self.image_canvas.winfo_height()

        self.move_rectangle()

    def on_canvas_enter(self, event):
        self.image_canvas.focus_set()
        self.bind_all("<MouseWheel>", self.canvas_mousewheel)
        self.bind_all("<Button-4>", self.canvas_mousewheel)
        self.bind_all("<Button-5>", self.canvas_mousewheel)
        self.bind_all("<space>", self.roll)
        self.bind_all("<e>", self.rotate_image_cw)
        self.bind_all("<q>", self.rotate_image_ccw)
        self.bind_all("r", self.toggle_roll)

    def on_canvas_leave(self, event):
        self.unbind_all("<MouseWheel>")
        self.unbind_all("<Button-4>")
        self.unbind_all("<Button-5>")
        self.unbind_all("<space>")
        self.unbind_all("<e>")
        self.unbind_all("<q>")
        self.unbind_all("r")

    def canvas_mousewheel(self, event):
        if self.current_image is not None:
            if event.num == 4 or event.delta == -120:
                aspect_x = self.crop_aspect_x_entry.get_value() or 1
                rect_ratio = self.crop_aspect_y_entry.get_value() / aspect_x
                new_multiplier_step = self.current_crop_rect_multiplier_step + 1

                if (
                    CROP_RECT_MULTIPLIER * new_multiplier_step < self.scaled_image.width
                ) and (
                    CROP_RECT_MULTIPLIER * new_multiplier_step * rect_ratio
                    < self.scaled_image.height
                ):
                    self.current_crop_rect_multiplier_step = new_multiplier_step

            if event.num == 5 or event.delta == 120:
                self.current_crop_rect_multiplier_step = (
                    self.current_crop_rect_multiplier_step - 1
                )
                if self.current_crop_rect_multiplier_step < CROP_RECT_STEP_MIN:
                    self.current_crop_rect_multiplier_step = CROP_RECT_STEP_MIN

        self.move_rectangle()

    def get_image_inside_rectangle(self):
        box_rel_tl_x = self.current_rect_left - (
            (self.current_canvas_size_x - self.scaled_image.width) / 2
        )
        box_rel_tl_y = self.current_rect_upper - (
            (self.current_canvas_size_y - self.scaled_image.height) / 2
        )
        box_rel_bl_x = box_rel_tl_x + (self.current_rect_right - self.current_rect_left)
        box_rel_bl_y = box_rel_tl_y + (
            self.current_rect_lower - self.current_rect_upper
        )
        return iops.crop_image(
            self.raw_image,
            self.ratio,
            (box_rel_tl_x, box_rel_tl_y, box_rel_bl_x, box_rel_bl_y),
        )

    def toggle_roll(self, event):
        self.roll_on_crop_checkbox.set_value(not self.roll_on_crop_checkbox.get_value())

    def rotate_image_cw(self, event):
        self.raw_image = iops.rotate_image(self.raw_image, 270)
        self.load_image_to_canvas()

    def rotate_image_ccw(self, event):
        self.raw_image = iops.rotate_image(self.raw_image, 90)
        self.load_image_to_canvas()

    def roll(self, event):
        if self.files_listbox.get_list_length() == 0:
            return

        if self.current_image_index is not None:
            self.current_image_index = self.current_image_index + 1
            if self.current_image_index == self.files_listbox.get_list_length():
                messagebox.showwarning(
                    title="Warning",
                    message="Image list reached to end, rolling back to zero.",
                )
                self.current_image_index = 0

            self.files_listbox.get_widget().selection_clear(0, tk.END)
            self.files_listbox.get_widget().select_set(self.current_image_index)
            self.files_listbox.get_widget().event_generate("<<ListboxSelect>>")

    def _validate_crop_inputs(self) -> bool:
        """Validate inputs before cropping.

        Returns:
            True if all inputs are valid, False otherwise
        """
        if not self.output_path_entry.get_value():
            messagebox.showerror(title="Error", message="No output path given.")
            return False
        if not self.input_files or len(self.input_files) == 0:
            messagebox.showerror(title="Error", message="No input images.")
            return False
        return True

    def _get_class_name(self) -> Optional[str]:
        """Get class name based on checkbox settings.

        Returns:
            Class name string or None if not applicable
        """
        if self.use_class_name_checkbox.get_value():
            return self.class_name_entry.get_value()
        elif self.ask_for_classes_checkbox.get_value():
            if not os.path.exists(CLASSES_FILE):
                messagebox.showerror(
                    title="Error", message=f"{CLASSES_FILE} not found."
                )
                return None
            with open(CLASSES_FILE, "r") as file:
                content = file.read()
                items = [item.strip() for item in content.split(",") if item.strip()]
            return self.ask_class_window(items)
        return None

    def _get_image_description(self) -> Optional[str]:
        """Get image description based on checkbox settings.

        Returns:
            Image description string or None if not applicable
        """
        if self.use_image_description_checkbox.get_value():
            return self.image_description_entry.get_value()
        elif self.ask_for_tags_checkbox.get_value():
            return self.attribute_selector.ask_attributes()
        return None

    def _build_output_paths(self, class_name: Optional[str]) -> Tuple[str, str]:
        """Build output file paths for image and description.

        Args:
            class_name: Optional class name for subdirectory

        Returns:
            Tuple of (image_path, description_path)
        """
        base_name = self.input_files[self.current_image_index][0].split(".")[0]
        output_image_name = f"{base_name}_{self.crop_count}.png"
        output_description_name = f"{base_name}_{self.crop_count}.txt"

        output_path = self.output_path_entry.get_value()
        if not fops.check_path_valid(output_path):
            output_path = os.path.join(self.input_path_entry.get_value(), output_path)

        if class_name is not None:
            return (
                os.path.join(output_path, class_name, output_image_name),
                os.path.join(output_path, class_name, output_description_name),
            )
        return (
            os.path.join(output_path, output_image_name),
            os.path.join(output_path, output_description_name),
        )

    def canvas_mouseclick(self, event):
        if not self._validate_crop_inputs():
            return

        class_name = self._get_class_name()
        image_description = self._get_image_description()

        cropped_image = self.get_image_inside_rectangle()
        if self.scale_output_checkbox.get_value():
            cropped_image = iops.resize_image(
                cropped_image,
                height=self.output_height_entry.get_value(),
                width=self.output_width_entry.get_value(),
            )

        image_path, description_path = self._build_output_paths(class_name)

        fops.save_image_to_file(cropped_image, filepath=image_path)
        fops.save_image_description_to_file(
            image_description, filepath=description_path
        )
        self.console.write_info("Image saved to: " + image_path)
        self.crop_count += 1

        if self.roll_on_crop_checkbox.get_value():
            self.image_description_entry.clear()
            self.roll(None)

    def ask_class_window(self, items):
        top_level = tk.Toplevel()
        top_level.title("Choose an item")

        selected_item = None

        def on_button_click(item):
            nonlocal selected_item
            selected_item = item
            top_level.destroy()

        num_columns = int(math.sqrt(len(items)))
        for i, item in enumerate(items):
            row, col = divmod(i, num_columns)
            button = tk.Button(
                top_level, text=item, command=lambda item=item: on_button_click(item)
            )
            button.grid(row=row, column=col, padx=5, pady=5, sticky="news")

        top_level.grab_set()
        top_level.protocol("WM_DELETE_WINDOW", top_level.quit)
        top_level.wait_window()

        return selected_item
