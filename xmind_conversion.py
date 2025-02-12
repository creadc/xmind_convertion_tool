#coding=utf-8
import logging
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
        self.scenario_main_widget = ttk.Combobox(self.config_container, values=self.scenario_main, state="readonly")
        self.scenario_main_widget.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.scenario_main_widget.bind("<<ComboboxSelected>>", self.update_scenarios)
        self.scenario_sub_widget = ttk.Combobox(self.config_container, state="readonly")
        self.scenario_sub_widget.grid(row=1, column=2, columnspan=2, padx=0, pady=5, sticky="w")

        ttk.Label(self.config_container, text="影响版本*").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.effect_version_widget = ttk.Combobox(self.config_container, values=self.effect_version, state="readonly")
        self.effect_version_widget.set(self.effect_version[-1])
        self.effect_version_widget.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(self.config_container, text="用例来源").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.case_source_widget = ttk.Combobox(self.config_container, values=self.case_source, state="readonly")
        self.case_source_widget.set(self.case_source[1])
        self.case_source_widget.grid(row=3, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(self.config_container, text="用例级别*").grid(row=4, column=0, padx=5, pady=5, sticky="e")
        self.case_level_widget = ttk.Combobox(self.config_container, values=self.case_level, state="readonly")
        self.case_level_widget.set(self.case_level[1])
        self.case_level_widget.grid(row=4, column=1, padx=5, pady=5, sticky="w")

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
        if show_messagebox(self.root, "yesno", "确定要上传用例到 JIRA 吗？") == '确认':
            self.notebook.add(self.log_frame, text="日志")
            self.notebook.select(2)

            # 如果之前有日志，加个换行符区分
            if self.log_text.get("1.0", ttk.END).strip():
                self.update_status("\n")

            df = self.table.model.df
            conf = {"link_type": self.link_type_widget.get(), "link_issue": self.link_issue_widget.get()}
            self.update_status("开始上传用例到 JIRA...")
            result = self.jira_helper.upload_test_cases(df, conf, self.update_status)
            if result:
                self.update_status("\n所有用例已成功上传到 JIRA！")
            else:
                self.update_status("\n部分用例上传到 JIRA 失败，请查看日志!!!", "error")

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
        self.scenario_sub_widget["values"] = self.scenario[self.scenario_main_widget.get()]
        self.scenario_sub_widget.set("")

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
