import os
import cv2
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter.simpledialog import askstring
from tkinter.simpledialog import askinteger
from typing import Optional, Tuple
from PIL import Image, ImageTk

import fileops as fops
import imageops as iops
import ui_generics as ui
from attribute_selector import AttributeSelector
from rectangle_mixin import RectangleMixin

CROP_RECT_MULTIPLIER = 8
CROP_RECT_STEP_MIN = 2

DEFAULT_ASPECT_X = 1
DEFAULT_ASPECT_Y = 1

DEFAULT_OUTPUT_WIDTH = 512
DEFAULT_OUTPUT_HEIGHT = 512

TAGS_FILE = "tags.yaml"


class VideoTab(tk.Frame, RectangleMixin):
    def __init__(self, console):
        super().__init__()
        self.current_crop_rect_multiplier_step = CROP_RECT_STEP_MIN

        self.console = console
        self.input_path_entry = None
        self.output_path_entry = None
        self.extract_frames_button = None
        self.output_width_entry = None
        self.output_height_entry = None
        self.crop_aspect_x_entry = None
        self.crop_aspect_y_entry = None
        self.scale_output_checkbox = None
        self.ask_for_class_name_checkbox = None
        self.ask_for_image_description_checkbox = None
        self.ask_for_classes_checkbox = None
        self.ask_for_tags_checkbox = None

        self.seek_backward_button = None
        self.play_button = None
        self.pause_button = None
        self.stop_button = None
        self.seek_forward_button = None
        self.progress_bar = None

        self.video_path = ""
        self.video_length = None
        self.playing = False
        self.percentage = 0
        self.cap = None
        self.percentage = 0
        self.cap = None

        self.image_canvas = None
        self.image_container = None
        self.rectangle_container = None

        self.attribute_selector = None
        self.current_image = None
        self.current_scaled_image = None
        self.current_canvas_size_x = None
        self.current_canvas_size_y = None
        self.current_mouse_x = 0
        self.current_mouse_y = 0
        self.current_rect_left = None
        self.current_rect_upper = None
        self.current_rect_right = None
        self.current_rect_lower = None
        self.raw_image = None
        self.scaled_image = None
        self.ratio = None
        self.crop_count = 0

        self.init_data()
        self.init_ui()

    def init_data(self):
        self.attribute_selector = AttributeSelector(TAGS_FILE)

    def init_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        main_frame = tk.Frame(self)
        main_frame.grid(row=0, column=0, sticky="news")
        main_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=2, uniform="x")
        main_frame.columnconfigure(1, weight=10, uniform="x")

        left_frame = tk.Frame(main_frame)
        left_frame.grid(column=0, row=0, sticky="news")

        left_widget_frame = tk.Frame(left_frame)
        left_widget_frame.columnconfigure(0, weight=1)
        left_widget_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        paths_frame = tk.LabelFrame(left_widget_frame, text="Paths")
        paths_frame.grid(column=0, row=0, sticky="news")
        paths_frame.columnconfigure(0, weight=1)

        self.input_path_entry = ui.LabelEntryFileBrowse(
            "Input File",
            paths_frame,
            self.video_file_selected,
            filetypes=[
                ("Video files", "*.mp4 *.avi *.webm *.mov *.mkv"),
                ("All files", "*.*"),
            ],
        )
        self.input_path_entry.grid(column=0, row=0, sticky="news")

        self.output_path_entry = ui.LabelEntryFolderBrowse(
            "Output Folder", paths_frame, None
        )
        self.output_path_entry.grid(column=0, row=1, sticky="news")

        self.extract_frames_button = tk.Button(
            paths_frame, text="Extract Frames", command=self.extract_frames_callback
        )
        self.extract_frames_button.grid(column=0, row=2, sticky="news")

        parameters_frame = tk.LabelFrame(left_widget_frame, text="Parameters")
        parameters_frame.grid(column=0, row=1, sticky="news")
        parameters_frame.columnconfigure(0, weight=1)

        self.scale_output_checkbox = ui.CheckBox(
            "Scale Output", self.scale_output_checkbox_callback, parameters_frame
        )
        self.scale_output_checkbox.grid(column=0, row=0, sticky="news")

        self.output_width_entry = ui.LabelEntryInt("Output Width", parameters_frame)
        self.output_width_entry.grid(column=0, row=1, sticky="news")
        self.output_width_entry.set_value(DEFAULT_OUTPUT_WIDTH)

        self.output_height_entry = ui.LabelEntryInt("Output Height", parameters_frame)
        self.output_height_entry.grid(column=0, row=2, sticky="news")
        self.output_height_entry.set_value(DEFAULT_OUTPUT_HEIGHT)

        self.crop_aspect_x_entry = ui.LabelEntryInt("Crop Aspect X", parameters_frame)
        self.crop_aspect_x_entry.grid(column=0, row=3, sticky="news")
        self.crop_aspect_x_entry.set_value(DEFAULT_ASPECT_X)

        self.crop_aspect_y_entry = ui.LabelEntryInt("Crop Aspect Y", parameters_frame)
        self.crop_aspect_y_entry.grid(column=0, row=4, sticky="news")
        self.crop_aspect_y_entry.set_value(DEFAULT_ASPECT_Y)

        self.ask_for_class_name_checkbox = ui.CheckBox(
            "Ask For Class Name", None, parameters_frame
        )
        self.ask_for_class_name_checkbox.grid(column=0, row=5, sticky="news")

        self.ask_for_image_description_checkbox = ui.CheckBox(
            "Ask For Image Description", None, parameters_frame
        )
        self.ask_for_image_description_checkbox.grid(column=0, row=6, sticky="news")

        self.ask_for_tags_checkbox = ui.CheckBox(
            "Ask Tags (tags.yaml)", None, parameters_frame
        )
        self.ask_for_tags_checkbox.grid(column=0, row=7, sticky="news")

        self.scale_output_checkbox.set_value(0)
        self.ask_for_class_name_checkbox.set_value(0)

        image_frame = tk.LabelFrame(main_frame, text="Image")
        image_frame.rowconfigure(0, weight=1)
        image_frame.columnconfigure(0, weight=1)
        image_frame.grid(column=1, row=0, sticky="news")

        canvas_container = tk.Frame(image_frame)
        canvas_container.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        self.image_canvas = tk.Canvas(canvas_container)
        self.image_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        self.image_canvas.bind("<Motion>", self.on_canvas_motion)
        self.image_canvas.bind("<Enter>", self.on_canvas_enter)
        self.image_canvas.bind("<Leave>", self.on_canvas_leave)
        self.image_canvas.bind("<ButtonRelease-1>", self.canvas_mouseclick)
        self.image_canvas.configure(bg="black")

        bottom_controls_container = tk.Frame(image_frame)
        bottom_controls_container.pack(side=tk.BOTTOM, fill=tk.X, expand=0)

        self.seek_backward_button = tk.Button(
            bottom_controls_container,
            text="BACK",
            command=self.seek_backward_button_callback,
        )
        self.seek_backward_button.pack(side=tk.LEFT, fill=tk.Y)

        self.play_button = tk.Button(
            bottom_controls_container, text="PLAY", command=self.play_button_callback
        )
        self.play_button.pack(side=tk.LEFT, fill=tk.Y)

        self.pause_button = tk.Button(
            bottom_controls_container, text="PAUSE", command=self.pause_button_callback
        )
        self.pause_button.pack(side=tk.LEFT, fill=tk.Y)

        self.stop_button = tk.Button(
            bottom_controls_container, text="STOP", command=self.stop_button_callback
        )
        self.stop_button.pack(side=tk.LEFT, fill=tk.Y)

        self.seek_forward_button = tk.Button(
            bottom_controls_container,
            text="FORW",
            command=self.seek_forward_button_callback,
        )
        self.seek_forward_button.pack(side=tk.LEFT, fill=tk.Y)

        self.progress_bar = ttk.Progressbar(
            bottom_controls_container, orient="horizontal", mode="determinate"
        )
        self.progress_bar.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        self.progress_bar.bind("<ButtonPress-1>", self.progress_bar_seek_callback)

    def seek_backward_button_callback(self):
        if self.cap is None or self.video_length == 0:
            return

        self.cap.set(
            cv2.CAP_PROP_POS_FRAMES,
            int(((self.percentage - 5) / 100) * self.video_length),
        )
        self.percentage = int(
            self.cap.get(cv2.CAP_PROP_POS_FRAMES) / self.video_length * 100
        )
        self.progress_bar.config(value=self.percentage)

    def play_button_callback(self):
        if self.cap is None:
            if not self.input_path_entry.get_value():
                messagebox.showerror(title="Error", message="No video file selected.")
                return
            if not self.output_path_entry.get_value():
                messagebox.showerror(title="Error", message="No output path given.")
                return
            self.cap = cv2.VideoCapture(self.input_path_entry.get_value())
            self.video_length = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

        self.play_video()

    def pause_button_callback(self):
        self.playing = False

    def stop_button_callback(self):
        self.playing = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.percentage = 0
        self.progress_bar.config(value=0)
        self.image_canvas.delete("all")
        self.image_container = None
        self.rectangle_container = None

    def seek_forward_button_callback(self):
        if self.cap is None or self.video_length == 0:
            return

        self.cap.set(
            cv2.CAP_PROP_POS_FRAMES,
            int(((self.percentage + 5) / 100) * self.video_length),
        )
        self.percentage = int(
            self.cap.get(cv2.CAP_PROP_POS_FRAMES) / self.video_length * 100
        )
        self.progress_bar.config(value=self.percentage)

    def progress_bar_seek_callback(self, event):
        if self.cap is None or self.video_length == 0:
            return

        self.cap.set(
            cv2.CAP_PROP_POS_FRAMES,
            int(
                (
                    self.progress_bar["maximum"]
                    * event.x
                    / self.progress_bar.winfo_width()
                )
                / 100
                * self.video_length
            ),
        )
        self.percentage = int(
            self.cap.get(cv2.CAP_PROP_POS_FRAMES) / self.video_length * 100
        )
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

        if self.video_length > 0:
            self.percentage = int(
                self.cap.get(cv2.CAP_PROP_POS_FRAMES) / self.video_length * 100
            )
            self.progress_bar.config(value=self.percentage)

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        self.raw_image = Image.fromarray(frame)
        self.ratio = min(
            self.image_canvas.winfo_width() / self.raw_image.width,
            self.image_canvas.winfo_height() / self.raw_image.height,
        )
        self.scaled_image = iops.scale_image(self.raw_image, self.ratio)
        self.current_image = ImageTk.PhotoImage(self.scaled_image)

        canvas_center_x = self.image_canvas.winfo_width() / 2
        canvas_center_y = self.image_canvas.winfo_height() / 2

        if self.image_container is None:
            self.image_container = self.image_canvas.create_image(
                canvas_center_x,
                canvas_center_y,
                anchor=tk.CENTER,
                image=self.current_image,
            )
        else:
            self.image_canvas.itemconfig(self.image_container, image=self.current_image)
            self.image_canvas.coords(
                self.image_container, canvas_center_x, canvas_center_y
            )

        if self.rectangle_container is None:
            self.rectangle_container = self.image_canvas.create_rectangle(
                0, 0, 1, 1, outline="white", width=3
            )

        self.image_canvas.tag_raise(self.rectangle_container)
        self.move_rectangle()

        if self.playing:
            self.after(1, self.display_frame)

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
        if not path.endswith((".mp4", ".avi", ".webm", ".mov", ".mkv")):
            self.input_path_entry.clear()
            messagebox.showerror(
                title="Error", message="Selected file is not supported."
            )
            return

        self.crop_count = 0  # Reset crop count for new video
        self.video_path = path

        test_cap = cv2.VideoCapture(path)
        if not test_cap.isOpened():
            self.input_path_entry.clear()
            messagebox.showerror(title="Error", message="Could not open video file.")
            test_cap.release()
            return

        frame_count = int(test_cap.get(cv2.CAP_PROP_FRAME_COUNT))
        test_cap.release()

        if frame_count <= 0:
            self.input_path_entry.clear()
            messagebox.showerror(
                title="Error", message="Video file is empty or invalid."
            )
            return

    def extract_frames_callback(self):
        if not self.input_path_entry.get_value():
            messagebox.showerror(title="Error", message="No video file selected.")
            return

        initialpath = os.path.expanduser("~")
        path = tk.filedialog.askdirectory(initialdir=initialpath)
        if path:
            if not fops.check_path_valid(path):
                messagebox.showerror(title="Error", message="Path not valid.")
                return

            cap = cv2.VideoCapture(self.input_path_entry.get_value())
            video_fps = round(cap.get(cv2.CAP_PROP_FPS))
            target_fps = askinteger(
                "FPS", "What FPS to extract? (Video FPS: " + str(video_fps) + ")"
            )

            if target_fps == 0:
                target_fps = video_fps

            hop = round(video_fps / target_fps)
            current_frame = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                if current_frame % hop == 0:
                    target_file = os.path.join(path, f"{current_frame}.png")
                    cv2.imwrite(target_file, frame)
                    self.console.write_info(
                        "Extracted frame " + str(current_frame) + "."
                    )
                current_frame += 1

            cap.release()
            self.console.write_info("Frame extraction complete.")

    def space_button_callback(self, event):
        if self.playing:
            self.pause_video()
        else:
            self.play_video()

    def get_rect_half_size(self):
        """Return the half-size of the crop rectangle based on current settings."""
        aspect_x = self.crop_aspect_x_entry.get_value() or 1
        rect_aspect_ratio = self.crop_aspect_y_entry.get_value() / aspect_x
        rect_half_x = self.current_crop_rect_multiplier_step * CROP_RECT_MULTIPLIER / 2
        rect_half_y = int(rect_half_x * rect_aspect_ratio)
        return rect_half_x, rect_half_y

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
        self.bind_all("<space>", self.space_button_callback)

    def on_canvas_leave(self, event):
        self.unbind_all("<MouseWheel>")
        self.unbind_all("<Button-4>")
        self.unbind_all("<Button-5>")
        self.unbind_all("<space>")

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

    def _validate_crop_inputs(self) -> bool:
        """Validate inputs before cropping.

        Returns:
            True if all inputs are valid, False otherwise
        """
        if not self.output_path_entry.get_value():
            messagebox.showerror(title="Error", message="No output path given.")
            return False
        if self.cap is None:
            messagebox.showerror(title="Error", message="No video.")
            return False
        return True

    def _get_class_name(self) -> Optional[str]:
        """Get class name if checkbox is checked.

        Returns:
            Class name string from dialog, or None if not applicable
        """
        if self.ask_for_class_name_checkbox.get_value():
            return askstring("Class name", "What is the class name?")
        return None

    def _get_image_description(self) -> Optional[str]:
        """Get image description based on checkbox settings.

        Returns:
            Image description string or None if not applicable
        """
        if self.ask_for_image_description_checkbox.get_value():
            return askstring("Image description", "What is in the image?")
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
        base_name = os.path.basename(self.input_path_entry.get_value()).split(".")[0]
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

        self.pause_video()

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

    def get_image_inside_rectangle(self):
        box_rel_tl_x = self.current_rect_left - (
            (self.current_canvas_size_x - self.scaled_image.width) / 2
        )
        box_rel_tl_y = self.current_rect_upper - (
            (self.current_canvas_size_y - self.scaled_image.height) / 2
        )
            box_rel_bl_x = box_rel_tl_x + (self.current_rect_right - self.current_rect_left)
            box_rel_bl_y = box_rel_tl_y + (self.current_rect_upper - self.current_rect_lower)
            return iops.crop_image(
            self.raw_image,
            self.ratio,
            (box_rel_tl_x, box_rel_tl_y, box_rel_bl_x, box_rel_bl_y),
        )
