"""Shared AttributeSelector for tag selection dialogs."""

import os
import tkinter as tk
import yaml


class AttributeSelector:
    """Dialog for selecting attributes from a YAML configuration file."""

    def __init__(self, file_path):
        self.attributes = {}
        self.vars = {}
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                self.attributes = yaml.safe_load(f) or {}

    def ask_attributes(self):
        if not self.attributes:
            return ''

        top_level = tk.Toplevel()
        top_level.title('Choose attributes')

        selected_values = []

        def on_button_click():
            nonlocal selected_values
            selected_values = [var.get() for var in self.vars.values()]
            top_level.destroy()

        num_columns = 8

        button_ok = tk.Button(top_level, text='OK', command=on_button_click)
        button_ok.grid(row=0, column=0, columnspan=num_columns, pady=10, sticky='news')

        self.vars = {}
        for i, (attribute, values) in enumerate(self.attributes.items()):
            row = i // num_columns
            col = i % num_columns
            lf = tk.LabelFrame(top_level, text=attribute)
            lf.grid(row=row+1, column=col, padx=10, pady=5, sticky='news')
            var = tk.StringVar(value=values[0])
            self.vars[attribute] = var
            for value in values:
                rb = tk.Radiobutton(lf, text=value, value=value, variable=var)
                rb.pack(padx=5, pady=2, expand=True)

        top_level.grab_set()
        top_level.protocol("WM_DELETE_WINDOW", top_level.quit)
        top_level.wait_window()

        selected_values_str = ', '.join([v for v in selected_values if v])
        return selected_values_str
