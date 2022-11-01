import tkinter as tk
import tkinter.filedialog
from tkinter import ttk
import os


def validate_int(p):
    if str.isdigit(p) or p == '':
        return True
    else:
        return False


def validate_float(p):
    if p == '':
        return True
    else:
        try:
            float(p)
            return True
        except ValueError:
            return False


class CheckBox(tk.Frame):
    int_variable = None
    callback_function = None
    button = None

    def __init__(self, text, callback, master=None):
        super().__init__()
        tk.Frame.__init__(self, master)

        self.callback_function = callback
        self.int_variable = tk.IntVar()

        self.button = tk.Checkbutton(self, text=text, variable=self.int_variable, command=self.state_callback,
                                     onvalue=1, offvalue=0)
        self.button.grid(column=0, row=0, sticky='news')

    def state_callback(self):
        if self.callback_function is not None:
            self.callback_function(self.get_value())

    def get_value(self):
        return self.int_variable.get()

    def set_value(self, value):
        self.int_variable.set(value)
        if self.callback_function is not None:
            self.callback_function(self.get_value())


class ScrollableListbox(tk.LabelFrame):
    data = None

    listbox = None
    scrollbar = None

    onclick_callback = None

    def __init__(self, label, master=None):
        super().__init__()
        tk.LabelFrame.__init__(self, master, text=label)

        self.listbox = tk.Listbox(self)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        self.scrollbar = tk.Scrollbar(self)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.BOTH)

        self.listbox.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.listbox.yview)

    def clear(self):
        self.listbox.delete(0, tk.END)

    def get_list_length(self):
        return self.listbox.size()

    def set_data(self, data):
        self.data = data
        for item in self.data:
            self.listbox.insert(tk.END, item[0])

    def bind_onclick(self, callback):
        self.onclick_callback = callback
        self.listbox.bind('<<ListboxSelect>>', callback)

    def get_widget(self):
        return self.listbox


class LabelEntryFileBrowse(tk.LabelFrame):
    text_variable = None
    last_path = ''

    def __init__(self, label, master=None):
        super().__init__()
        tk.LabelFrame.__init__(self, master, text=label)

        self.text_variable = tk.StringVar()
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=1)

        entry = tk.Entry(self, textvariable=self.text_variable)
        entry.grid(column=0, row=0, sticky='news')

        button = tk.Button(self, text='Browse', command=self.open_browse_dialogue)
        button.grid(column=1, row=0, sticky='news')

    def open_browse_dialogue(self):
        if self.last_path == '':
            initialpath = os.path.expanduser('~')
        else:
            initialpath = self.last_path

        path = tk.filedialog.askopenfilename(initialdir=initialpath)
        self.last_path = path
        self.text_variable.set(path)

    def get_value(self):
        return self.text_variable.get()


class LabelEntryFolderBrowse(tk.LabelFrame):
    text_variable = None
    last_path = ''
    callback_f = None

    def __init__(self, label, master=None, callback=None):
        super().__init__()
        tk.LabelFrame.__init__(self, master, text=label)

        self.callback_f = callback
        self.text_variable = tk.StringVar()
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=1)

        entry = tk.Entry(self, textvariable=self.text_variable)
        entry.grid(column=0, row=0, sticky='news')

        button = tk.Button(self, text='Browse', command=self.open_browse_dialogue)
        button.grid(column=1, row=0, sticky='news')

    def open_browse_dialogue(self):
        if self.last_path == '':
            initialpath = os.path.expanduser('~')
        else:
            initialpath = self.last_path

        path = tk.filedialog.askdirectory(initialdir=initialpath)
        self.last_path = path
        self.text_variable.set(path)
        if self.callback_f is not None:
            self.callback_f(self.last_path)

    def get_value(self):
        return self.text_variable.get()


class LabelEntryText(tk.LabelFrame):
    text_variable = None
    entry = None

    def __init__(self, label, master=None):
        tk.LabelFrame.__init__(self, master, text=label)
        self.text_variable = tk.StringVar()
        self.rowconfigure(0, weight=1)

        self.entry = tk.Entry(self, textvariable=self.text_variable)
        self.entry.grid(column=0, row=0, sticky='news')

    def get_value(self):
        return self.text_variable.get()

    def enable(self):
        self.entry.config(state='normal')

    def disable(self):
        self.entry.config(state='disabled')


class LabelEntryInt(tk.LabelFrame):
    text_variable = None
    entry = None

    def __init__(self, label, master=None, initial_value=0):
        tk.LabelFrame.__init__(self, master, text=label)
        self.text_variable = tk.StringVar()
        self.text_variable.set(str(initial_value))
        self.columnconfigure(0, weight=1)
        vcmd = (self.register(validate_int))

        self.entry = tk.Entry(self, textvariable=self.text_variable, validate='all',
                              validatecommand=(vcmd, '%P'))
        self.entry.grid(column=0, row=0, sticky='news', padx=5, pady=5)

    def get_value(self):
        return int(self.text_variable.get())

    def set_value(self, value):
        self.text_variable.set(str(value))

    def enable(self):
        self.entry.config(state='normal')

    def disable(self):
        self.entry.config(state='disabled')


class LabelEntryFloat(tk.LabelFrame):
    text_variable = None
    entry = None

    def __init__(self, label, master=None, initial_value=0.0):
        tk.LabelFrame.__init__(self, master, text=label)
        self.text_variable = tk.StringVar()
        self.text_variable.set(str(initial_value))
        self.columnconfigure(0, weight=1)
        vcmd = (self.register(validate_float))

        self.entry = tk.Entry(self, textvariable=self.text_variable, validate='all',
                              validatecommand=(vcmd, '%P'))
        self.entry.grid(column=0, row=0, sticky='news')

    def enable(self):
        self.entry.config(state='normal')

    def disable(self):
        self.entry.config(state='disabled')

    def get_value(self):
        return float(self.text_variable.get())

    def set_value(self, value):
        self.text_variable.set(str(value))


class Console(tk.LabelFrame):
    console_listbox = None
    console_scrollbar = None

    def __init__(self, master=None, text='Console'):
        super().__init__()
        tk.LabelFrame.__init__(self, master, text=text)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.init_ui()

    def init_ui(self):
        self.console_listbox = tk.Listbox(self, bg='black', fg='green', highlightcolor='black',
                                          selectbackground='green', activestyle=tk.NONE)
        self.console_scrollbar = tk.Scrollbar(self.console_listbox)
        self.console_listbox.config(yscrollcommand=self.console_scrollbar.set)
        self.console_scrollbar.config(command=self.console_listbox.yview)
        self.console_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.console_listbox.pack(expand=True, fill=tk.BOTH)

    def write_info(self, text):
        self.console_listbox.insert(tk.END, 'INFO: ' + text)
        self.console_listbox.yview_moveto(1)

    def write_error(self, text):
        self.console_listbox.insert(tk.END, 'ERROR: ' + text)
        self.console_listbox.yview_moveto(1)


class ListboxWithControls(tk.Frame):
    listbox = None
    up_cmd = None
    down_cmd = None
    add_cmd = None
    remove_cmd = None
    clear_cmd = None
    process_cmd = None
    item_selected_cmd = None

    def __init__(self, master=None, title='', up_cmd=None, down_cmd=None, add_cmd=None, remove_cmd=None, clear_cmd=None,
                 process_cmd=None, item_selected_cmd=None):
        super().__init__()
        tk.Frame.__init__(self, master)

        self.up_cmd = up_cmd
        self.down_cmd = down_cmd
        self.add_cmd = add_cmd
        self.remove_cmd = remove_cmd
        self.clear_cmd = clear_cmd
        self.process_cmd = process_cmd
        self.item_selected_cmd = item_selected_cmd

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        main_frame = tk.Frame(self) if (title == '') else tk.LabelFrame(self, text=title)
        main_frame.grid(column=0, row=0, sticky='news')
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)

        self.listbox = tk.Listbox(main_frame, selectmode=tk.SINGLE)
        self.listbox.grid(column=0, row=0, sticky='news')

        button_frame = tk.Frame(main_frame)
        button_frame.grid(column=0, row=1, sticky='news')

        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(2, weight=1)
        button_frame.rowconfigure(0, weight=1)
        button_frame.rowconfigure(1, weight=1)

        if self.up_cmd is not None:
            up_button = tk.Button(button_frame, text='UP', command=self.up_cmd)
            up_button.grid(column=0, row=0, sticky='news')

        if self.down_cmd is not None:
            down_button = tk.Button(button_frame, text='DOWN', command=self.down_cmd)
            down_button.grid(column=0, row=1, sticky='news')

        if self.add_cmd is not None:
            add_button = tk.Button(button_frame, text='ADD', command=self.add_cmd)
            add_button.grid(column=1, row=0, sticky='news')

        if self.remove_cmd is not None:
            remove_button = tk.Button(button_frame, text='REMOVE', command=self.remove_cmd)
            remove_button.grid(column=1, row=1, sticky='news')

        if self.clear_cmd is not None:
            clear_button = tk.Button(button_frame, text='CLEAR', command=self.clear_cmd)
            clear_button.grid(column=2, row=0, sticky='news')

        if self.process_cmd is not None:
            process_button = tk.Button(button_frame, text='PROCESS', command=self.process_cmd)
            process_button.grid(column=2, row=1, sticky='news')

        if self.item_selected_cmd is not None:
            self.listbox.bind('<<ListboxSelect>>', self.item_selected_cmd)

    def update(self, data=None):
        if data is None:
            data = []
        self.listbox.delete(0, tk.END)
        for i in data:
            self.listbox.insert(tk.END, i)

    def get_selected_item(self):
        return self.listbox.get(self.listbox.curselection())


class ComboboxWithDetails(tk.Frame):
    combobox = None
    console = None
    current_selected_item = None
    item_list = None
    get_item_details_frame_cmd = None
    details_frame = None
    current_frame = None

    def __init__(self, master=None, text='', console=None, item_list=None, get_item_details_frame_cmd=None):
        super().__init__()
        tk.Frame.__init__(self, master)
        self.console = console
        self.item_list = item_list
        self.get_item_details_frame_cmd = get_item_details_frame_cmd
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.current_selected_item = tk.StringVar()
        self.current_selected_item.set(self.item_list[0])

        self.combobox = ttk.Combobox(self, textvariable=self.current_selected_item)
        self.combobox['values'] = self.item_list
        self.combobox['state'] = 'readonly'
        self.combobox.bind('<<ComboboxSelected>>', self.set_details_frame)
        self.combobox.grid(column=0, row=0, sticky='news')

        self.details_frame = tk.Frame(self) if (text == '') else tk.LabelFrame(self, text=text)
        self.details_frame.grid(column=0, row=1, sticky='news')

        self.set_details_frame(self.current_selected_item.get())

        return

    def set_details_frame(self, event):
        new_frame = self.get_item_details_frame_cmd(self.details_frame, self.current_selected_item.get())

        if self.current_frame is not None:
            self.current_frame.destroy()

        self.current_frame = new_frame
        self.current_frame.grid(column=0, row=0, sticky='news', padx=5, pady=5)

        return

    def get_details_data(self):
        return
