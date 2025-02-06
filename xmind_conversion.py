import logging
import pandas as pd
import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
from tkinter import filedialog
from xmind_analyze import TestCaseManager
from pandastable import Table
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
        self.table_frame = None
        self.table = None

        self.log_frame = None
        self.log_text = None
        self.status_box = None

        # 解析 JIRA 字段信息
        self.parse_field_data(field_data)
        self.create_widgets()

    def create_widgets(self):
        """创建 UI 界面"""
        # 配置区域
        self.config_frame = ttk.Frame(self.root)
        self.config_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        ttk.Label(self.config_frame, text="xmind文件位置").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.xmind_path = ttk.StringVar()
        self.xmind_path_widget = ttk.Entry(self.config_frame, textvariable=self.xmind_path, width=50)
        self.xmind_path_widget.grid(row=0, column=1, columnspan=3, padx=5, pady=5, sticky="w")
        ttk.Button(self.config_frame, text="选择本地文件", command=self.select_xmind_file).grid(row=0, column=4, padx=5,
                                                                                               pady=5)

        ttk.Label(self.config_frame, text="功能场景").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.scenario_main_widget = ttk.Combobox(self.config_frame, values=self.scenario_main, state="readonly")
        self.scenario_main_widget.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.scenario_main_widget.bind("<<ComboboxSelected>>", self.update_scenarios)
        self.scenario_sub_widget = ttk.Combobox(self.config_frame, state="readonly")
        self.scenario_sub_widget.grid(row=1, column=2, columnspan=2, padx=0, pady=5, sticky="w")

        ttk.Label(self.config_frame, text="影响版本").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.effect_version_widget = ttk.Combobox(self.config_frame, values=self.effect_version, state="readonly")
        self.effect_version_widget.set("4.2")
        self.effect_version_widget.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(self.config_frame, text="用例来源").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.case_source_widget = ttk.Combobox(self.config_frame, values=self.case_source, state="readonly")
        self.case_source_widget.set("测试规划")
        self.case_source_widget.grid(row=3, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(self.config_frame, text="用例级别").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.case_level_widget = ttk.Combobox(self.config_frame, values=self.case_level, state="readonly")
        self.case_level_widget.set("3")
        self.case_level_widget.grid(row=4, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(self.config_frame, text="用例类型").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.case_type_widget = ttk.Combobox(self.config_frame, values=self.case_type, state="readonly")
        self.case_type_widget.grid(row=5, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(self.config_frame, text="标签").grid(row=6, column=0, padx=5, pady=5, sticky="w")
        self.tags_widget = ttk.Entry(self.config_frame, width=20)
        self.tags_widget.grid(row=6, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(self.config_frame, text="链接类型").grid(row=7, column=0, padx=5, pady=5, sticky="w")
        self.link_type_widget = ttk.Combobox(self.config_frame, values=["关联的任务"], state="readonly")
        self.link_type_widget.set("关联的任务")
        self.link_type_widget.grid(row=7, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(self.config_frame, text="问题").grid(row=7, column=2, padx=5, pady=5, sticky="w")
        self.link_issue_widget = ttk.Entry(self.config_frame, width=20)
        self.link_issue_widget.grid(row=7, column=3, padx=5, pady=5, sticky="w")

        ttk.Button(self.config_frame, text="预览", command=self.preview_test_cases).grid(row=8, column=0, columnspan=2,
                                                                                        pady=5)

        # 默认隐藏的按钮和区域
        self.generate_excel_btn = ttk.Button(self.config_frame, text="生成Excel", command=self.generate_excel)
        self.generate_excel_btn.grid(row=8, column=2, columnspan=2, pady=5)
        self.upload_btn = ttk.Button(self.config_frame, text="一键上传", command=self.upload_to_jira)
        self.upload_btn.grid(row=8, column=4, columnspan=2, pady=5)

        self.generate_excel_btn.grid_remove()
        self.upload_btn.grid_remove()

        # 表格区域（默认隐藏）
        self.create_table()
        self.table_frame.grid_remove()

        # 日志区域（默认隐藏）
        self.create_log_frame()
        self.log_frame.grid_remove()

    def create_table(self):
        self.table_frame = ttk.Frame(self.root)
        self.table_frame.grid(row=1, column=0, columnspan=7, pady=5, sticky="nsew")

    def create_log_frame(self):
        self.log_frame = ttk.Frame(self.root)
        self.log_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        self.log_text = ttk.Text(self.log_frame, height=10, width=70)
        self.log_text.pack(side=ttk.LEFT, fill=ttk.BOTH, expand=True)
        self.log_scrollbar = ttk.Scrollbar(self.log_frame, orient=ttk.VERTICAL)
        self.log_scrollbar.pack(side=ttk.RIGHT, fill=ttk.Y)
        self.log_text.config(yscrollcommand=self.log_scrollbar.set)
        self.log_scrollbar.config(command=self.log_text.yview)

    def preview_test_cases(self):
        if not self.verify_input():
            return

        try:
            manager = TestCaseManager(xmind_file=self.xmind_path.get(), output_dir="")
            manager.load_xmind()
            manager.parse_test_cases()
            self.test_cases = manager.test_cases

            self.root.geometry("1500x1000")
            self.show_preview_table()
            self.generate_excel_btn.grid()  # 显示生成Excel按钮
            self.upload_btn.grid()  # 显示一键上传按钮
            self.log_frame.grid()  # 显示日志区域

        except Exception as e:
            logging.error(e)
            Messagebox.show_error("错误", f"预览失败: {e}\n")

    def show_preview_table(self):
        self.table_frame.grid()  # 显示表格区域
        if self.table_frame:
            self.table_frame.destroy()
        self.create_table()

        additional_data = {
            "影响版本": self.effect_version_widget.get(),
            "功能场景": f"{self.scenario_main_widget.get()}-{self.scenario_sub_widget.get()}" if self.scenario_sub_widget.get() else self.scenario_main_widget.get(),
            "测试用例来源": self.case_source_widget.get(),
            "用例级别": self.case_level_widget.get(),
            "用例类型": self.case_type_widget.get(),
            "标签": self.tags_widget.get(),
        }

        df = pd.DataFrame(self.test_cases, columns=["用例名称（主题）", "测试步骤", "预期结果", "测试数据"])
        for key, value in additional_data.items():
            df[key] = value

        df.loc[df["用例名称（主题）"].isnull(), additional_data.keys()] = None

        self.table = Table(self.table_frame, dataframe=df, editable=True, width=1000, height=500)
        self.table.show()

    def upload_to_jira(self):
        result = Messagebox.yesno("确定要上传用例到 JIRA 吗？")
        if result == '确认':
            df = self.table.model.df
            self.update_status("开始上传用例到 JIRA...")
            result = self.jira_helper.upload_test_cases(df, self.update_status)
            if result:
                self.update_status("所有用例已成功上传到 JIRA！")
            else:
                self.update_status("部分用例上传到 JIRA 失败，请查看日志！")

    def update_status(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert(ttk.END, message + "\n")
        self.log_text.config(state="disabled")
        self.log_text.see(ttk.END)
        self.log_text.update_idletasks()

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
            self.xmind_path_widget.delete(0, ttk.END)
            self.xmind_path_widget.insert(0, file_path)

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
                Messagebox.show_error(f"请确保{field_name}已填写！\n")
                return False
        return True

    def generate_excel(self):
        try:
            df = self.table.model.df
            file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
            if not file_path:
                return

            df.to_excel(file_path, index=False)
            self.update_status("生成EXCEL成功")
        except Exception as e:
            self.update_status("生成EXCEL失败")
