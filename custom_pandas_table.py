from tkinter import Entry, StringVar

import pandas as pd
from pandastable import Table
from common import *


class CustomPandasTable(Table):
    def __init__(self, parent, dataframe):
        self.df = dataframe

        # 初始化 Tooltip
        self.tooltip = None
        self.tooltip_label = None

        # 初始化当前行列
        self.edit_row = None
        self.edit_col = None

        Table.__init__(self, parent, dataframe=self.df, editable=True, maxcellwidth=1500)

        # 绑定鼠标移动事件（悬浮提示）
        self.bind("<Motion>", self.on_hover)

        # 监听编辑事件
        self.bind("<Double-Button-1>", self.on_edit_start)  # 开始编辑
        self.bind("<FocusOut>", self.on_edit_end)  # 失去焦点时退出编辑
        self.bind("<Return>", self.on_edit_end)  # 回车时退出编辑

        # 设置table样式
        self.setRowHeight(40)
        self.autoResizeColumns()
        self.redraw()

        # 记录是否处于编辑状态
        self.editing = False

    def on_hover(self, event):
        """鼠标悬浮时显示自定义提示"""
        if self.editing:  # 编辑状态下不显示 Tooltip
            self.hide_tooltip()
            return

        row = self.get_row_clicked(event)
        col = self.get_col_clicked(event)
        if row is None or col is None or row < 0 or col < 0:
            return

        try:
            tooltip_text = self.model.getValueAt(row, col)  # 获取当前单元格内容
        except IndexError:
            self.hide_tooltip()
            return

        if tooltip_text:
            self.show_tooltip(event, tooltip_text)
        else:
            self.hide_tooltip()

    def show_tooltip(self, event, text):
        """显示悬浮提示"""
        if self.tooltip is None:
            # 只创建一次 Tooltip
            self.tooltip = ttk.Toplevel(self.parentframe)
            self.tooltip.wm_overrideredirect(True)  # 去除窗口边框
            self.tooltip.config(bg="lightyellow")

            # 只创建一次 Label
            self.tooltip_label = ttk.Label(self.tooltip, background="lightyellow", relief="solid", borderwidth=1)
            self.tooltip_label.grid(row=0, column=0, padx=5, pady=3)

        # 更新 Tooltip 内容
        self.tooltip_label.config(text=text)

        # 设定 Tooltip 位置

        self.tooltip.wm_geometry(f"+{int(event.x_root + 10)}+{int(event.y_root + 10)}")
        self.tooltip.deiconify()

    def hide_tooltip(self):
        """关闭悬浮提示"""
        if self.tooltip:
            self.tooltip.withdraw()  # 隐藏窗口

    def on_edit_start(self, event):
        """双击单元格进入编辑模式,隐藏 Tooltip"""
        self.edit_row = self.get_row_clicked(event)
        self.edit_col = self.get_col_clicked(event)

        if self.edit_row is None or self.edit_col is None:
            return

        self.editing = True  # 标记为编辑状态
        self.hide_tooltip()  # 隐藏 Tooltip

        # **手动触发 PandasTable 的编辑逻辑**
        self.handle_double_click(event)

    def on_edit_end(self, event):
        """处理退出编辑状态逻辑（回车或失焦）"""
        if self.editing:
            self.editing = False  # 退出编辑状态
