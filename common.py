import logging

import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox

theme = 'litera'  # 主题
common_font = 'Consolas'  # 通用字体
small_font_size = 9     # 小号字体
common_font_size = 12   # 通用字体
big_font_size = 15      # 大号字体


def init_style(root):
    style = ttk.Style()
    root.option_add("*Font", (common_font, common_font_size))  # 全局设置字体
    style.configure('TButton', font=(common_font, common_font_size))  # 设置Button的字体
    style.configure("Red.TLabel", font=(common_font, common_font_size), foreground="red")
    style.configure("Tip.TLabel", font=(common_font, common_font_size), foreground="grey")

    # 设置 Notebook 整体背景色
    style.configure("TNotebook", background="white", borderwidth=0)
    style.configure("TNotebook.Tab", font=(common_font, big_font_size), background="white")
    style.map("TNotebook.Tab", background=[("selected", "#4582EC")], foreground=[("selected", "white")])


def init_grid(frame, row, col):
    """初始化布局"""
    for i in range(row):
        frame.grid_rowconfigure(i, weight=1)
    for i in range(col):
        frame.grid_columnconfigure(i, weight=1)


def clean_widget(root):
    """清除组件"""
    for widget in root.winfo_children():
        widget.destroy()


def clean_grid(root):
    for i in range(root.grid_size()[1]):
        root.grid_rowconfigure(i, weight=0)
    for j in range(root.grid_size()[0]):
        root.grid_columnconfigure(j, weight=0)


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
