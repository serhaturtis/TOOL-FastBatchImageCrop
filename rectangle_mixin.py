"""Shared rectangle movement logic for canvas-based tabs."""


class RectangleMixin:
    """Mixin providing rectangle movement logic for image canvas tabs.

    Requires the following attributes on the class:
    - image_canvas: tk.Canvas
    - rectangle_container: canvas rectangle id
    - current_image: ImageTk.PhotoImage
    - current_mouse_x, current_mouse_y: int
    - current_rect_left, current_rect_upper, current_rect_right, current_rect_lower: int

    And method:
    - get_rect_half_size() -> tuple[float, float]: returns (rect_half_x, rect_half_y)
    """

    def move_rectangle(self):
        """Move the crop rectangle based on mouse position, constrained to image bounds."""
        rect_half_x, rect_half_y = self.get_rect_half_size()
        canvas_half_x = self.image_canvas.winfo_width() / 2
        canvas_half_y = self.image_canvas.winfo_height() / 2

        if self.current_image is not None:
            image_half_x = self.current_image.width() / 2
            image_half_y = self.current_image.height() / 2

            if self.current_mouse_x < canvas_half_x - image_half_x + rect_half_x:
                self.current_rect_left = canvas_half_x - image_half_x
                self.current_rect_right = canvas_half_x - image_half_x + rect_half_x * 2
            elif self.current_mouse_x + rect_half_x > canvas_half_x + image_half_x:
                self.current_rect_left = canvas_half_x + image_half_x - rect_half_x * 2
                self.current_rect_right = canvas_half_x + image_half_x
            else:
                self.current_rect_left = self.current_mouse_x - rect_half_x
                self.current_rect_right = self.current_mouse_x + rect_half_x

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

        self.current_rect_left = int(self.current_rect_left)
        self.current_rect_upper = int(self.current_rect_upper)
        self.current_rect_right = int(self.current_rect_right)
        self.current_rect_lower = int(self.current_rect_lower)

        if self.rectangle_container is not None:
            self.image_canvas.coords(
                self.rectangle_container,
                self.current_rect_left,
                self.current_rect_upper,
                self.current_rect_right,
                self.current_rect_lower,
            )
