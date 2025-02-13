#coding=utf-8
from common import *
from pandastable import Table,util


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

    def autoResizeColumns(self):
        """自动调整列宽以适应容器宽度"""
        self.adjustColumnWidths()
        self.redraw()

    def adjustColumnWidths(self, limit=None):
        """根据容器宽度动态调整列宽"""
        table_width = self.winfo_width()
        if table_width <= 1:
            return

        # 计算每列的原始宽度
        self.columnwidths = {}
        widths = []
        cols = self.model.getColumnCount()
        for col in range(cols):
            colname = self.model.getColumnName(col)
            l = self.model.getlongestEntry(col)
            txt = 'X' * (l + 1)
            tw, _ = util.getTextLength(txt, self.maxcellwidth, font=self.thefont)
            tw = max(tw, self.cellwidth)  # 确保不小于最小宽度
            tw = min(tw, self.maxcellwidth)  # 确保不超过最大限制
            self.columnwidths[colname] = tw
            widths.append(tw)

        sum_width = sum(widths)
        sum_total = table_width

        # 根据总宽度调整策略
        if sum_width > sum_total:
            # 计算cap阈值
            sorted_widths = sorted(widths)
            n = len(sorted_widths)
            sum_so_far = 0
            cap = sum_total  # 初始值

            for k in range(n):
                remaining = n - k
                candidate_cap = (sum_total - sum_so_far) / remaining
                if sorted_widths[k] <= candidate_cap:
                    sum_so_far += sorted_widths[k]
                else:
                    cap = candidate_cap
                    break
            else:
                cap = sorted_widths[-1] if n > 0 else 0

            # 应用阈值调整列宽
            for col in range(cols):
                colname = self.model.getColumnName(col)
                self.columnwidths[colname] = min(widths[col], cap)

        elif sum_width < sum_total:
            # 扩展列宽以填充剩余空间
            delta = sum_total - sum_width
            num_cols = cols
            avg_inc = delta / num_cols

            for col in range(num_cols):
                colname = self.model.getColumnName(col)
                new_width = widths[col] + avg_inc
                new_width = min(new_width, self.maxcellwidth)
                new_width = max(new_width, self.cellwidth)
                self.columnwidths[colname] = new_width
