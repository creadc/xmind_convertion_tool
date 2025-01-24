import pandas as pd
import tkinter as tk
from tkinter import filedialog, ttk, messagebox, font
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
        self.root.title("xmind转换工具")
        self.root.geometry("600x400")  # 调整窗口尺寸
        self.set_font()  # 设置字体

        # 配置区域
        self.config_frame = tk.Frame(self.root)
        self.config_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        tk.Label(self.config_frame, text="xmind文件位置").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.xmind_path = tk.StringVar()
        self.xmind_entry = tk.Entry(self.config_frame, textvariable=self.xmind_path, width=50)
        self.xmind_entry.grid(row=0, column=1, columnspan=3, padx=5, pady=5, sticky="w")
        tk.Button(self.config_frame, text="选择本地文件", command=self.select_xmind_file).grid(row=0, column=4, padx=5,
                                                                                               pady=5)

        tk.Label(self.config_frame, text="功能场景").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.scenario_main = ttk.Combobox(self.config_frame, values=self.scenario_main, state="readonly")
        self.scenario_main.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.scenario_main.bind("<<ComboboxSelected>>", self.update_scenarios)
        self.scenario_sub = ttk.Combobox(self.config_frame, state="readonly")
        self.scenario_sub.grid(row=1, column=2, columnspan=2, padx=0, pady=5, sticky="w")

        tk.Label(self.config_frame, text="影响版本").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.effect_version = ttk.Combobox(self.config_frame, values=self.effect_version, state="readonly")
        self.effect_version.set("4.2")
        self.effect_version.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        tk.Label(self.config_frame, text="用例来源").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.case_source = ttk.Combobox(self.config_frame, values=self.case_source, state="readonly")
        self.case_source.set("测试规划")
        self.case_source.grid(row=3, column=1, padx=5, pady=5, sticky="w")

        tk.Label(self.config_frame, text="用例级别").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.case_level = ttk.Combobox(self.config_frame, values=self.case_level, state="readonly")
        self.case_level.set("3")
        self.case_level.grid(row=4, column=1, padx=5, pady=5, sticky="w")

        tk.Label(self.config_frame, text="用例类型").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.case_type = ttk.Combobox(self.config_frame, values=self.case_type, state="readonly")
        self.case_type.grid(row=5, column=1, padx=5, pady=5, sticky="w")

        tk.Label(self.config_frame, text="标签").grid(row=6, column=0, padx=5, pady=5, sticky="w")
        self.tags = tk.Entry(self.config_frame, width=20)
        self.tags.grid(row=6, column=1, padx=5, pady=5, sticky="w")

        tk.Label(self.config_frame, text="链接类型").grid(row=7, column=0, padx=5, pady=5, sticky="w")
        self.link_type = ttk.Combobox(self.config_frame, values=["关联的任务"], state="readonly")
        self.link_type.set("关联的任务")
        self.link_type.grid(row=7, column=1, padx=5, pady=5, sticky="w")
        tk.Label(self.config_frame, text="问题").grid(row=7, column=2, padx=5, pady=5, sticky="w")
        self.link_issue = tk.Entry(self.config_frame, width=20)
        self.link_issue.grid(row=7, column=3, padx=5, pady=5, sticky="w")

        tk.Button(self.config_frame, text="预览", command=self.preview_test_cases).grid(row=8, column=0, columnspan=2,
                                                                                        pady=5)

        # 默认隐藏的按钮和区域
        self.generate_excel_btn = tk.Button(self.config_frame, text="生成Excel", command=self.generate_excel)
        self.generate_excel_btn.grid(row=8, column=2, columnspan=2, pady=5)
        self.upload_btn = tk.Button(self.config_frame, text="一键上传", command=self.upload_to_jira)
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
        self.table_frame = tk.Frame(self.root)
        self.table_frame.grid(row=1, column=0, columnspan=7, pady=5, sticky="nsew")

    def create_log_frame(self):
        self.log_frame = tk.Frame(self.root)
        self.log_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        self.log_text = tk.Text(self.log_frame, height=10, width=70)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.log_scrollbar = tk.Scrollbar(self.log_frame, orient=tk.VERTICAL)
        self.log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
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

            self.root.geometry("1100x1000")
            self.show_preview_table()
            self.generate_excel_btn.grid()  # 显示生成Excel按钮
            self.upload_btn.grid()  # 显示一键上传按钮
            self.log_frame.grid()  # 显示日志区域

        except Exception as e:
            messagebox.showerror("错误", f"预览失败: {e}")

    def show_preview_table(self):
        self.table_frame.grid()  # 显示表格区域
        if self.table_frame:
            self.table_frame.destroy()
        self.create_table()

        additional_data = {
            "影响版本": self.effect_version.get(),
            "功能场景": f"{self.scenario_main.get()}-{self.scenario_sub.get()}" if self.scenario_sub.get() else self.scenario_main.get(),
            "测试用例来源": self.case_source.get(),
            "用例级别": self.case_level.get(),
            "用例类型": self.case_type.get(),
            "标签": self.tags.get(),
        }

        df = pd.DataFrame(self.test_cases, columns=["用例名称（主题）", "测试步骤", "预期结果", "测试数据"])
        for key, value in additional_data.items():
            df[key] = value

        df.loc[df["用例名称（主题）"].isnull(), additional_data.keys()] = None

        self.table = Table(self.table_frame, dataframe=df, editable=True, width=1000, height=500)
        self.table.show()

    def upload_to_jira(self):
        if messagebox.askyesno("确认", "确定要上传用例到 JIRA 吗？"):
            df = self.table.model.df
            self.update_status("开始上传用例到 JIRA...")
            result = self.jira_helper.upload_test_cases(df, self.update_status)
            if result:
                self.update_status("所有用例已成功上传到 JIRA！")
            else:
                self.update_status("部分用例上传到 JIRA 失败，请查看日志！")

    def update_status(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.config(state="disabled")
        self.log_text.see(tk.END)
        self.log_text.update_idletasks()

    def parse_field_data(self, field_data):
        self.scenario = field_data["功能场景"]
        self.scenario_main = list(field_data["功能场景"].keys())
        self.effect_version = field_data["影响版本"]
        self.case_source = field_data["测试用例来源"]
        self.case_level = field_data["用例级别"]
        self.case_type = field_data["用例类型"]

    def set_font(self):
        # 全局设置默认字体
        default_font = font.nametofont("TkDefaultFont")
        default_font.configure(size=12)

        # 配置 ttk.Combobox 样式
        style = ttk.Style()
        style.configure("TCombobox", font=("微软雅黑", 12))  # 设置下拉框字体
        style.configure("TEntry", font=("微软雅黑", 12))  # 设置下拉框输入框字体

    def select_xmind_file(self):
        """选择xmind文件"""
        file_path = filedialog.askopenfilename(filetypes=[("XMind Files", "*.xmind")])
        if file_path:
            self.xmind_path.set(file_path)

    def update_scenarios(self, event):
        """更新子功能场景"""
        self.scenario_sub["values"] = self.scenario[self.scenario_main.get()]
        self.scenario_sub.set("")

    def verify_input(self):
        fields = [
            (self.xmind_path.get(), "xmind文件位置"),
            (self.scenario_main.get(), "功能场景"),
            (self.effect_version.get(), "影响版本"),
            (self.case_level.get(), "用例级别"),
        ]
        for value, field_name in fields:
            if not value:
                messagebox.showerror("错误", f"请确保{field_name}已填写！")
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
