import logging

import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox

theme = 'litera'  # 主题
common_font = 'Consolas'  # 通用字体
common_font_size = 12  # 通用字体大小


def init_style(root):
    style = ttk.Style()
    root.option_add("*Font", (common_font, common_font_size))  # 全局设置字体
    style.configure('TButton', font=(common_font, common_font_size))  # 设置Button的字体

    style.configure("Custom.TNotebook", tabmargins=[2, 5, 2, 0])  # 调整整体样式
    style.configure("Custom.TNotebook.Tab", font=("Arial", 12), padding=[10, 5])  # 调整标签样式
    style.map("Custom.TNotebook.Tab", background=[("selected", "blue"), ("!selected", "white")])

def init_grid(frame, row, col):
    """初始化布局"""
    for i in range(row):
        frame.grid_rowconfigure(i, weight=1)
    for i in range(col):
        frame.grid_columnconfigure(i, weight=1)


def create_popup(text):
    """创建弹窗"""
    popup = ttk.Window(title="JIRA 登录", themename=theme)
    ttk.Label(popup, text=text, font=(common_font, common_font_size)).grid()
    popup.place_window_center()
    popup.update()
    return popup


def update_popup(popup, text):
    """更新弹窗内容"""
    for widget in popup.winfo_children():
        if isinstance(widget, ttk.Label):
            widget.config(text=text)
    popup.place_window_center()
    popup.update()


def destroy_popup(popup):
    """销毁弹窗"""
    if popup.winfo_exists():
        popup.destroy()


def show_messagebox(root, msg_type, message):
    """显示弹窗"""
    pos = (
        int(root.winfo_rootx() + 0.5 * root.winfo_width()) - 150,
        int(root.winfo_rooty() + 0.33 * root.winfo_height())
    )
    if msg_type == "info":
        return Messagebox.show_info(message, position=pos)
    elif msg_type == "error":
        return Messagebox.show_error(message, position=pos)
    elif msg_type == "yesno":
        return Messagebox.yesno(message, position=pos)
    else:
        logging.error("非法弹窗类型")
