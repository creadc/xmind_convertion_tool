#coding=utf-8
import logging
import threading
import tkinter as tk

from common import *
from pandas import DataFrame as pd
from tkinter import filedialog
from xmind_analyze import TestCaseManager
from custom_pandas_table import CustomPandasTable
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)


class XMindConvertionApp:
    def __init__(self, root, jira_helper, field_data):
        self.root = root

        self.jira_helper = jira_helper

        self.xmind_path = None  # xmind地址
        self.scenario = None  # 功能场景
        self.scenario_main = None  # 父功能场景
        self.scenario_sub = None  # 子功能场景
        self.effect_version = None  # 影响版本
        self.case_source = None  # 用例来源
        self.case_level = None  # 用例级别
        self.case_type = None  # 用例类型
        self.tags = None  # 标签
        self.link_type = None  # 链接类型
        self.link_issue = None  # 链接的问题
        self.test_cases = []

        self.config_frame = None  # 配置区域
        self.table_frame = None  # 表格区域
        self.log_frame = None  # 日志区域
        self.table = None
        self.log_text = None
        self.status_box = None
        self.scenario_main_all = []
        self.scenario_sub_all = []
        self.scenario_filter_delay = 300
        self.scenario_popup_max_rows = 12
        self._scenario_main_filter_job = None
        self._scenario_sub_filter_job = None
        self.scenario_popup = None
        self.scenario_listbox = None
        self.scenario_scrollbar = None
        self.active_scenario_widget = None
        self.scenario_main_ime_active = False
        self.scenario_sub_ime_active = False

        # 解析 JIRA 字段信息
        self.parse_field_data(field_data)
        self.create_widgets()

    def create_widgets(self):
        """创建 UI 界面"""
        # 创建 Notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        # 配置行列权重
        init_grid(self.root, 1, 1)

        # 创建 Tabs
        self.config_frame = ttk.Frame(self.notebook)
        self.table_frame = ttk.Frame(self.notebook)
        self.log_frame = ttk.Frame(self.notebook)

        self.notebook.add(self.config_frame, text="配置")

        # 配置区域
        self.init_config_frame()

        # 表格区域
        self.init_table_frame()

        # 日志区域
        self.init_log_frame()

    def init_config_frame(self):
        self.config_container = ttk.Frame(self.config_frame)
        self.config_container.grid(row=0, column=0, sticky="nsew")

        ttk.Label(self.config_container, text="xmind文件位置*").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.xmind_path = ttk.StringVar()
        self.xmind_path_widget = ttk.Entry(self.config_container, textvariable=self.xmind_path, width=45)
        self.xmind_path_widget.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky="w")
        ttk.Button(self.config_container, text="选择本地文件", command=self.select_xmind_file).grid(row=0, column=3, pady=5, sticky="w")

        ttk.Label(self.config_container, text="功能场景*").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.scenario_main_all = list(self.scenario_main)
        self.scenario_sub_all = []
        self.scenario_main_widget = ttk.Combobox(self.config_container, values=self.scenario_main_all, state="normal")
        self.scenario_main_widget.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.scenario_main_widget.bind("<<ComboboxSelected>>", self.update_scenarios)
        self.scenario_main_widget.bind("<KeyRelease>", self.on_scenario_main_typing, add="+")
        self.scenario_main_widget.bind("<ButtonPress-1>", self.on_scenario_combobox_click, add="+")
        self.scenario_main_widget.bind("<Down>", self.on_scenario_arrow_down, add="+")
        self.scenario_main_widget.bind("<Escape>", self.hide_scenario_popup, add="+")
        self.scenario_main_widget.bind("<<TkStartIMEMarkedText>>", self.on_scenario_main_ime_start, add="+")
        self.scenario_main_widget.bind("<<TkEndIMEMarkedText>>", self.on_scenario_main_ime_end, add="+")
        self.scenario_sub_widget = ttk.Combobox(self.config_container, state="normal")
        self.scenario_sub_widget.grid(row=1, column=2, columnspan=2, padx=0, pady=5, sticky="w")
        self.scenario_sub_widget.bind("<KeyRelease>", self.on_scenario_sub_typing, add="+")
        self.scenario_sub_widget.bind("<ButtonPress-1>", self.on_scenario_combobox_click, add="+")
        self.scenario_sub_widget.bind("<Down>", self.on_scenario_arrow_down, add="+")
        self.scenario_sub_widget.bind("<Escape>", self.hide_scenario_popup, add="+")
        self.scenario_sub_widget.bind("<<TkStartIMEMarkedText>>", self.on_scenario_sub_ime_start, add="+")
        self.scenario_sub_widget.bind("<<TkEndIMEMarkedText>>", self.on_scenario_sub_ime_end, add="+")
        self.root.bind_all("<ButtonPress-1>", self.on_global_mouse_down, add="+")
        self.root.bind("<FocusOut>", self.on_root_focus_out, add="+")

        ttk.Label(self.config_container, text="影响版本*").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.effect_version_widget = ttk.Combobox(self.config_container, values=self.effect_version, state="readonly")
        self.effect_version_widget.set(self.effect_version[-1])
        self.effect_version_widget.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(self.config_container, text="用例级别*").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.case_level_widget = ttk.Combobox(self.config_container, values=self.case_level, state="readonly")
        self.case_level_widget.set(self.case_level[1])
        self.case_level_widget.grid(row=3, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(self.config_container, text="用例来源").grid(row=4, column=0, padx=5, pady=5, sticky="e")
        self.case_source_widget = ttk.Combobox(self.config_container, values=self.case_source, state="readonly")
        self.case_source_widget.set(self.case_source[1])
        self.case_source_widget.grid(row=4, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(self.config_container, text="用例类型").grid(row=5, column=0, padx=5, pady=5, sticky="e")
        self.case_type_widget = ttk.Combobox(self.config_container, values=self.case_type, state="readonly")
        self.case_type_widget.set(self.case_type[0])
        self.case_type_widget.grid(row=5, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(self.config_container, text="链接类型和任务链接").grid(row=6, column=0, padx=5, pady=5, sticky="e")
        self.link_type_widget = ttk.Combobox(self.config_container, values=["关联的任务"], state="readonly")
        self.link_type_widget.set("关联的任务")
        self.link_type_widget.grid(row=6, column=1, padx=5, pady=5, sticky="w")
        self.link_issue_widget = ttk.Entry(self.config_container, width=20)
        self.link_issue_widget.grid(row=6, column=2, padx=0, pady=5, sticky="w")
        ttk.Label(self.config_container, text="任务链接形如FDL-xxxx", style="Tip.TLabel").grid(row=6, column=3, padx=5, pady=5, sticky="w")

        ttk.Label(self.config_container, text="标签").grid(row=7, column=0, padx=5, pady=5, sticky="e")
        self.tags_widget = ttk.Entry(self.config_container, width=21)
        self.tags_widget.grid(row=7, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(self.config_container, text="多个标签用英文逗号隔开", style="Tip.TLabel").grid(row=7, column=2, padx=5, pady=5, sticky="w")

        ttk.Button(self.config_frame, text="预览", command=self.preview_test_cases).grid(row=1, column=0, pady=30)

        init_grid(self.config_container, 8, 0)
        self.config_container.grid_columnconfigure(0, weight=1)
        self.config_container.grid_columnconfigure(4, weight=1)

        init_grid(self.config_frame, 1, 1)
        self.config_frame.grid_rowconfigure(1, weight=2)

    def init_table_frame(self):
        init_grid(self.table_frame, 1, 2)
        self.table_container = ttk.Frame(self.table_frame)
        self.table_container.grid(row=0, column=0, columnspan=3, sticky="nsew")
        self.generate_excel_btn = ttk.Button(self.table_frame, text="生成Excel", command=self.generate_excel)
        self.generate_excel_btn.grid(row=1, column=0, pady=5)
        self.upload_btn = ttk.Button(self.table_frame, text="一键上传", command=self.upload_to_jira)
        self.upload_btn.grid(row=1, column=1, pady=5)

    def init_log_frame(self):
        init_grid(self.log_frame, 1, 1)
        self.log_text = ttk.Text(self.log_frame, height=10, width=70)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        self.log_scrollbar = ttk.Scrollbar(self.log_frame, orient="vertical", command=self.log_text.yview)
        self.log_scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.config(yscrollcommand=self.log_scrollbar.set)

    def preview_test_cases(self):
        if not self.verify_input():
            return
        try:
            manager = TestCaseManager(xmind_file=self.xmind_path.get(), output_dir="")
            manager.load_xmind()
            manager.parse_test_cases()
            self.test_cases = manager.test_cases
            self.show_preview_table()
        except Exception as e:
            logging.error(e)
            show_messagebox(self.root, "error", f"预览失败: {e}")

    def show_preview_table(self):
        clean_widget(self.table_container)

        additional_data = {
            "影响版本": self.effect_version_widget.get(),
            "功能场景": f"{self.scenario_main_widget.get()}-{self.scenario_sub_widget.get()}" if self.scenario_sub_widget.get() else self.scenario_main_widget.get(),
            "测试用例来源": self.case_source_widget.get(),
            "用例级别": self.case_level_widget.get(),
            "用例类型": self.case_type_widget.get(),
            "标签": self.tags_widget.get(),
        }
        df = pd(self.test_cases, columns=["用例名称（主题）", "测试步骤", "预期结果", "测试数据"])
        for key, value in additional_data.items():
            df[key] = value
        df.loc[df["用例名称（主题）"].isnull(), additional_data.keys()] = None

        self.table = CustomPandasTable(self.table_container, df)
        # 显示表格
        self.table.grid(row=0, column=0, sticky="nsew")
        self.table.show()
        # 设置表格样式
        self.table.set_style()

        self.notebook.add(self.table_frame, text="表格")
        self.notebook.select(1)

    def generate_excel(self):
        try:
            df = self.table.model.df
            file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
            if not file_path:
                return
            df.to_excel(file_path, index=False)
            show_messagebox(self.root, "info", "生成EXCEL成功！")
        except Exception as e:
            logging.error(e)
            show_messagebox(self.root, "error", f"生成EXCEL失败！{e}")

    def upload_to_jira(self):
        a = show_messagebox(self.root, "yesno", "确定要上传用例到 JIRA 吗？")
        if a == '确认' or a.lower() == 'yes':
            self.notebook.add(self.log_frame, text="日志")
            self.notebook.select(2)

            # 如果之前有日志，加个换行符区分
            if self.log_text.get("1.0", ttk.END).strip():
                self.update_status("\n")

            # 禁用上传按钮防止重复操作
            self.upload_btn.config(state="disabled")

            self.progress_bar = ttk.Progressbar(self.log_frame, orient="horizontal", length=400, mode="determinate")
            self.progress_bar.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
            self.progress_bar["value"] = 0

            # 启动上传线程
            upload_thread = threading.Thread(
                target=self._run_upload_in_thread,
                daemon=True
            )
            upload_thread.start()

    def _run_upload_in_thread(self):
        """在后台线程中执行上传操作"""
        try:
            # 获取数据
            df = self.table.model.df
            conf = {
                "link_type": self.link_type_widget.get(),
                "link_issue": self.link_issue_widget.get()
            }

            # 创建线程安全的回调函数
            def safe_callback(message, level="normal"):
                self.root.after(0, lambda: self.update_status(message, level))

            # 创建进度更新函数
            def progress_callback(current, total):
                percent = int((current / total) * 100)
                self.root.after(0, lambda: self.progress_bar.configure(value=percent))
                self.root.after(0, lambda: self.progress_bar.update())

            # 通知开始
            safe_callback("开始上传用例到 JIRA...")

            # 执行上传
            result = self.jira_helper.upload_test_cases(
                df,
                conf,
                status_callback=safe_callback,
                progress_callback=progress_callback
            )

            # 显示最终结果
            if result:
                safe_callback("\n所有用例已成功上传到 JIRA！")
            else:
                safe_callback("\n部分用例上传到 JIRA 失败，请查看日志!!!", "error")

        except Exception as e:
            self.root.after(0, lambda: self.update_status(f"上传过程中发生错误: {str(e)}", "error"))
            logging.exception("上传过程中发生异常")
        finally:
            # 重新启用按钮
            self.root.after(0, lambda: self.upload_btn.config(state="normal"))
            # 隐藏进度条
            self.root.after(0, lambda: self.progress_bar.grid_remove())

    def update_status(self, message, level="normal"):
        self.log_text.config(state="normal")
        self.insert_text(message + "\n", level)
        self.log_text.config(state="disabled")
        self.log_text.see(ttk.END)
        self.log_text.update_idletasks()

    def insert_text(self, message, level):
        color = "black"
        if level == "error":
            color = "red"
        # 配置标签的字体颜色
        self.log_text.tag_configure(level, foreground=color)
        # 插入文本并应用标签
        self.log_text.insert(ttk.END, message, level)

    def parse_field_data(self, field_data):
        if not isinstance(field_data, dict):
            raise ValueError("JIRA 字段信息为空或格式错误")

        required_keys = ["功能场景", "影响版本", "测试用例来源", "用例级别", "用例类型"]
        missing_keys = [key for key in required_keys if key not in field_data]
        if missing_keys:
            raise KeyError(f"JIRA 字段信息缺少必要字段: {', '.join(missing_keys)}")

        self.scenario = field_data["功能场景"]
        self.scenario_main = list(field_data["功能场景"].keys())
        self.effect_version = field_data["影响版本"]
        self.case_source = field_data["测试用例来源"]
        self.case_level = field_data["用例级别"]
        self.case_type = field_data["用例类型"]

    def select_xmind_file(self):
        """选择xmind文件"""
        file_path = filedialog.askopenfilename(filetypes=[("XMind Files", "*.xmind")])
        if file_path:
            self.xmind_path.set(file_path)

    def update_scenarios(self, event):
        """更新子功能场景"""
        selected_main = self.scenario_main_widget.get().strip()
        self.scenario_sub_all = list(self.scenario.get(selected_main, []))
        self.scenario_sub_widget["values"] = self.scenario_sub_all
        self.scenario_sub_widget.set("")

    def on_scenario_combobox_click(self, event):
        widget = event.widget
        self._focus_scenario_widget(widget)
        self.show_scenario_popup(widget)
        return "break"

    def on_scenario_arrow_down(self, event):
        self._focus_scenario_widget(event.widget)
        self.show_scenario_popup(event.widget)
        return "break"

    def on_scenario_main_typing(self, event):
        self.active_scenario_widget = self.scenario_main_widget
        if self.scenario_main_ime_active:
            return
        self._schedule_scenario_filter(is_main=True)

    def on_scenario_sub_typing(self, event):
        self.active_scenario_widget = self.scenario_sub_widget
        if self.scenario_sub_ime_active:
            return
        self._schedule_scenario_filter(is_main=False)

    def on_scenario_main_ime_start(self, event):
        self.scenario_main_ime_active = True

    def on_scenario_main_ime_end(self, event):
        self.scenario_main_ime_active = False
        self.active_scenario_widget = self.scenario_main_widget
        self._schedule_scenario_filter(is_main=True)

    def on_scenario_sub_ime_start(self, event):
        self.scenario_sub_ime_active = True

    def on_scenario_sub_ime_end(self, event):
        self.scenario_sub_ime_active = False
        self.active_scenario_widget = self.scenario_sub_widget
        self._schedule_scenario_filter(is_main=False)

    def _schedule_scenario_filter(self, is_main):
        job_attr = "_scenario_main_filter_job" if is_main else "_scenario_sub_filter_job"
        callback = self._apply_main_scenario_filter if is_main else self._apply_sub_scenario_filter
        job = getattr(self, job_attr)
        if job:
            self.root.after_cancel(job)
        setattr(self, job_attr, self.root.after(self.scenario_filter_delay, callback))

    def _apply_main_scenario_filter(self):
        self._scenario_main_filter_job = None
        keyword = self.scenario_main_widget.get().strip().lower()
        if keyword:
            filtered = [item for item in self.scenario_main_all if keyword in item.lower()]
        else:
            filtered = self.scenario_main_all
        self.scenario_main_widget["values"] = filtered

        selected_main = self.scenario_main_widget.get().strip()
        self.scenario_sub_all = list(self.scenario.get(selected_main, []))
        self.scenario_sub_widget["values"] = self.scenario_sub_all
        if selected_main not in self.scenario:
            self.scenario_sub_widget.set("")

        self._focus_scenario_widget(self.scenario_main_widget)
        if self.active_scenario_widget == self.scenario_main_widget:
            self.show_scenario_popup(self.scenario_main_widget)

    def _apply_sub_scenario_filter(self):
        self._scenario_sub_filter_job = None
        keyword = self.scenario_sub_widget.get().strip().lower()
        if not self.scenario_sub_all:
            selected_main = self.scenario_main_widget.get().strip()
            self.scenario_sub_all = list(self.scenario.get(selected_main, []))

        if keyword:
            filtered = [item for item in self.scenario_sub_all if keyword in item.lower()]
        else:
            filtered = self.scenario_sub_all
        self.scenario_sub_widget["values"] = filtered

        self._focus_scenario_widget(self.scenario_sub_widget)
        if self.active_scenario_widget == self.scenario_sub_widget:
            self.show_scenario_popup(self.scenario_sub_widget)

    def _focus_scenario_widget(self, widget):
        widget.focus_force()
        widget.icursor(len(widget.get()))

    def _ensure_scenario_popup(self):
        if self.scenario_popup and self.scenario_popup.winfo_exists():
            return

        self.scenario_popup = tk.Toplevel(self.root)
        self.scenario_popup.withdraw()
        self.scenario_popup.overrideredirect(True)
        self.scenario_popup.transient(self.root)
        self.scenario_popup.configure(borderwidth=1, relief="solid", background="white")

        popup_body = tk.Frame(self.scenario_popup, borderwidth=0, highlightthickness=0, background="white")
        popup_body.pack(fill="both", expand=True)

        self.scenario_listbox = tk.Listbox(
            popup_body,
            activestyle="none",
            borderwidth=0,
            exportselection=False,
            highlightthickness=0,
            relief="flat",
        )
        self.scenario_scrollbar = tk.Scrollbar(popup_body, orient="vertical", command=self.scenario_listbox.yview)
        self.scenario_listbox.configure(yscrollcommand=self.scenario_scrollbar.set)
        self.scenario_listbox.pack(side="left", fill="both", expand=True)
        self.scenario_listbox.bind("<Motion>", self.on_scenario_listbox_hover)
        self.scenario_listbox.bind("<Leave>", self.on_scenario_listbox_leave)
        self.scenario_listbox.bind("<ButtonRelease-1>", self.on_scenario_listbox_select)

    def _get_filtered_scenario_values(self, widget):
        keyword = widget.get().strip().lower()
        source = self.scenario_main_all if widget == self.scenario_main_widget else self.scenario_sub_all
        if keyword:
            return [item for item in source if keyword in item.lower()]
        return list(source)

    def show_scenario_popup(self, widget):
        self._ensure_scenario_popup()
        self.active_scenario_widget = widget
        values = self._get_filtered_scenario_values(widget)
        self.scenario_listbox.delete(0, tk.END)
        for item in values:
            self.scenario_listbox.insert(tk.END, item)
        self.scenario_listbox.yview_moveto(0)

        height = min(max(len(values), 1), self.scenario_popup_max_rows)
        self.scenario_listbox.configure(height=height)
        if len(values) > self.scenario_popup_max_rows:
            if not self.scenario_scrollbar.winfo_ismapped():
                self.scenario_scrollbar.pack(side="right", fill="y")
        elif self.scenario_scrollbar.winfo_ismapped():
            self.scenario_scrollbar.pack_forget()

        self.root.update_idletasks()
        x = widget.winfo_rootx()
        y = widget.winfo_rooty() + widget.winfo_height()
        width = max(widget.winfo_width(), self.scenario_popup.winfo_reqwidth())
        popup_height = self.scenario_popup.winfo_reqheight()
        self.scenario_popup.geometry(f"{width}x{popup_height}+{x}+{y}")
        self.scenario_popup.deiconify()
        self.scenario_popup.lift()
        self._focus_scenario_widget(widget)

        if values:
            self.scenario_listbox.selection_clear(0, tk.END)
            self.scenario_listbox.selection_set(0)
            self.scenario_listbox.activate(0)

    def hide_scenario_popup(self, event=None):
        if self.scenario_popup and self.scenario_popup.winfo_exists():
            self.scenario_popup.withdraw()
        if event and getattr(event, "widget", None) in (self.scenario_main_widget, self.scenario_sub_widget):
            return "break"

    def on_global_mouse_down(self, event):
        if not self.scenario_popup or not self.scenario_popup.winfo_exists():
            return

        widget = event.widget
        if widget in (self.scenario_main_widget, self.scenario_sub_widget, self.scenario_listbox):
            return

        parent = getattr(widget, "master", None)
        if parent == self.scenario_popup:
            return

        self.hide_scenario_popup()

    def on_root_focus_out(self, event):
        self.root.after_idle(self._hide_popup_if_app_inactive)

    def _hide_popup_if_app_inactive(self):
        if not self.scenario_popup or not self.scenario_popup.winfo_exists():
            return

        try:
            focus_widget_name = str(self.root.tk.call("focus"))
        except tk.TclError:
            self.hide_scenario_popup()
            return

        if not focus_widget_name:
            self.hide_scenario_popup()
            return

        # ttk.Combobox opens an internal popdown window that tkinter cannot
        # always resolve back to a widget instance. Treat it as an external
        # focus target for this popup and close safely.
        if "popdown" in focus_widget_name:
            self.hide_scenario_popup()
            return

        try:
            focus_widget = self.root.nametowidget(focus_widget_name)
        except KeyError:
            self.hide_scenario_popup()
            return

        if focus_widget.winfo_toplevel() != self.root:
            self.hide_scenario_popup()

    def on_scenario_listbox_hover(self, event):
        if self.scenario_listbox.size() == 0:
            return

        index = self.scenario_listbox.nearest(event.y)
        self.scenario_listbox.selection_clear(0, tk.END)
        self.scenario_listbox.selection_set(index)
        self.scenario_listbox.activate(index)

    def on_scenario_listbox_leave(self, event):
        if self.scenario_listbox.size() == 0:
            return

        current = self.scenario_listbox.index(tk.ACTIVE)
        self.scenario_listbox.selection_clear(0, tk.END)
        self.scenario_listbox.selection_set(current)

    def on_scenario_listbox_select(self, event):
        if not self.active_scenario_widget or not self.scenario_listbox.curselection():
            return

        value = self.scenario_listbox.get(self.scenario_listbox.curselection()[0])
        self.active_scenario_widget.set(value)
        self._focus_scenario_widget(self.active_scenario_widget)
        if self.active_scenario_widget == self.scenario_main_widget:
            self.update_scenarios(None)
        self.hide_scenario_popup()

    def verify_input(self):
        fields = [
            (self.xmind_path_widget.get(), "xmind文件位置"),
            (self.scenario_main_widget.get(), "功能场景"),
            (self.effect_version_widget.get(), "影响版本"),
            (self.case_level_widget.get(), "用例级别"),
        ]
        for value, field_name in fields:
            if not value:
                show_messagebox(self.root, "error", f"请确保{field_name}已填写！")
                return False
        return True
