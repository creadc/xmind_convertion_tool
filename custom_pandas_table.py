from tkinter import Entry, StringVar

import pandas as pd
from pandastable import Table
from common import *


class CustomPandasTable(Table):
    def __init__(self, parent, dataframe):
        self.df = dataframe
        self.parent = parent

        # 初始化 Tooltip
        self.tooltip = None
        self.tooltip_label = None

        # 初始化当前行列
        self.edit_row = None
        self.edit_col = None

        Table.__init__(self, parent, dataframe=self.df, editable=True, maxcellwidth=1500)

        # 绑定鼠标移动事件
        self.bind("<Motion>", self.on_hover)    # 悬浮提示
        self.bind("<Leave>", self.on_leave)     # 离开表格时去掉提示

        # 监听编辑事件
        self.bind("<Double-Button-1>", self.on_edit_start)  # 开始编辑
        self.bind("<FocusOut>", self.on_edit_end)  # 失去焦点时退出编辑
        self.bind("<Return>", self.on_edit_end)  # 回车时退出编辑

        # 记录是否处于编辑状态
        self.editing = False

    def set_style(self):
        # 设置table样式
        self.setRowHeight(40)
        self.autoResizeColumns()

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

    def on_leave(self, event):
        """鼠标移出表格时隐藏 Tooltip"""
        self.hide_tooltip()

    def show_tooltip(self, event, text):
        """显示悬浮提示"""
        if self.tooltip is None:
            # 只创建一次 Tooltip
            self.tooltip = ttk.Toplevel(self)
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

    def destroy(self):
        """重写销毁方法，确保 Tooltip 也被销毁"""
        if self.tooltip:
            self.tooltip.destroy()
        super().destroy()

# 自定义实现的动态调整table列宽度，有点问题，不用了
    # def customAdjustColumnWidths(self):
    #     # 先测量所有列的原始宽度
    #     num_cols = self.table.model.getColumnCount()
    #     original_widths = []
    #     for col in range(num_cols):
    #         colname = self.table.model.getColumnName(col)
    #         # 测量列头宽度
    #         header_width, _ = util.getTextLength(colname, self.table.maxcellwidth, font=self.table.thefont)
    #         # 测量数据中最长条目的宽度（这里生成一个模拟文本）
    #         l = self.table.model.getlongestEntry(col)
    #         sample_text = "X" * (l + 1)
    #         data_width, _ = util.getTextLength(sample_text, self.table.maxcellwidth, font=self.table.thefont)
    #         # 取两者中的较大值
    #         original_widths.append(max(header_width, data_width))
    #
    #     # 根据容器当前宽度计算 cap（a 值）
    #     container_width = self.config_container.winfo_width() or self.table.width
    #     cap = self.compute_cap(original_widths, container_width)
    #
    #     # 对每一列，最终宽度 = min(原始宽度, cap)
    #     for col in range(num_cols):
    #         colname = self.table.model.getColumnName(col)
    #         self.table.columnwidths[colname] = min(original_widths[col], cap)
    #
    #     # 重新计算总宽度和 scrollregion，避免右侧额外空白
    #     self.tablewidth = sum(self.table.columnwidths.values())
    #     self.table.configure(scrollregion=(0, 0, self.tablewidth, self.table.rowheight * self.table.model.getRowCount()))
    #     self.table.redraw()
    #
    # def compute_cap(self, widths, container_width):
    #     """
    #     根据每列原始宽度和容器总宽度，计算出一个上限（cap）值，使得
    #     对每一列采用 min(原始宽度, cap) 后，总宽度恰好等于容器宽度。
    #
    #     算法思路：
    #       1. 将所有原始宽度按从小到大排序。
    #       2. 依次累计较小的宽度，并计算剩余宽度平均分配到剩下的列上的候选值 candidate。
    #       3. 当遇到某个列宽大于 candidate 时，就认为 candidate 为 cap。
    #       4. 如果所有列宽都小于候选值，则 cap 取所有列宽中的最大值。
    #     """
    #     sorted_widths = sorted(widths)
    #     total = 0
    #     n = len(sorted_widths)
    #     cap = None
    #     for i, w in enumerate(sorted_widths):
    #         candidate = (container_width - total) / (n - i)
    #         if w <= candidate:
    #             total += w
    #         else:
    #             cap = candidate
    #             break
    #     if cap is None:
    #         cap = max(widths)
    #     return cap
