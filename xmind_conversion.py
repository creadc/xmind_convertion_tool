import configparser
import pandas as pd
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from xmind_analyze import TestCaseManager
from pandastable import Table
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)


class XMindConvertionApp:
    def __init__(self, root, jira_helper, field_data):
        self.root = root
        self.jira_helper = jira_helper

        self.xmind_path = None      # xmind地址
        self.scenario = None        # 功能场景
        self.scenario_main = None   # 父功能场景
        self.scenario_sub = None    # 子功能场景
        self.effect_version = None  # 影响版本
        self.case_source = None     # 用例来源
        self.case_level = None      # 用例级别
        self.case_type = None       # 用例类型
        self.tags = None            # 标签
        self.link_type = None       # 链接类型
        self.link_issue = None      # 链接的问题

        self.test_cases = []
        self.table_frame = None
        self.table = None

        # 解析 JIRA 字段信息
        self.parse_field_data(field_data)
        self.create_widgets()

    def create_widgets(self):
        """创建 UI 界面"""
        self.root.title("xmind转换工具")
        self.root.geometry("1100x1100")  # 增大窗口默认尺寸
        self.root.resizable(True, True)  # 允许调整窗口大小
        self.root.configure(bg="#f5f5f5")  # 背景颜色

        # XMind 文件选择
        tk.Label(self.root, text="xmind文件位置").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.xmind_path = tk.StringVar()
        self.xmind_entry = tk.Entry(self.root, textvariable=self.xmind_path, width=50)
        self.xmind_entry.grid(row=0, column=1, padx=10, pady=10)
        tk.Button(self.root, text="选择本地文件", command=self.select_xmind_file).grid(row=0, column=2, padx=10, pady=10)

        # 功能场景
        tk.Label(self.root, text="功能场景").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.scenario_main = ttk.Combobox(self.root, values=self.scenario_main, state="readonly")
        self.scenario_main.grid(row=1, column=1, padx=10, pady=10, sticky="w")
        self.scenario_main.bind("<<ComboboxSelected>>", self.update_scenarios)
        self.scenario_sub = ttk.Combobox(self.root, state="readonly")
        self.scenario_sub.grid(row=1, column=2, padx=0, pady=10, sticky="w")

        # 影响版本
        tk.Label(self.root, text="影响版本").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.effect_version = ttk.Combobox(self.root, values=self.effect_version, state="readonly")
        self.effect_version.set("4.2")
        self.effect_version.grid(row=2, column=1, padx=10, pady=10, sticky="w")

        # 用例来源
        tk.Label(self.root, text="用例来源").grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.case_source = ttk.Combobox(self.root, values=self.case_source, state="readonly")
        self.case_source.set("测试规划")
        self.case_source.grid(row=3, column=1, padx=10, pady=10, sticky="w")

        # 用例级别
        tk.Label(self.root, text="用例级别").grid(row=4, column=0, padx=10, pady=10, sticky="w")
        self.case_level = ttk.Combobox(self.root, values=self.case_level, state="readonly")
        self.case_level.set("3")
        self.case_level.grid(row=4, column=1, padx=10, pady=10, sticky="w")

        # 用例类型
        tk.Label(self.root, text="用例类型").grid(row=5, column=0, padx=10, pady=10, sticky="w")
        self.case_type = ttk.Combobox(self.root, values=self.case_type, state="readonly")
        self.case_type.grid(row=5, column=1, padx=10, pady=10, sticky="w")

        # 标签
        tk.Label(self.root, text="标签").grid(row=6, column=0, padx=10, pady=10, sticky="w")
        self.tags = tk.Entry(self.root, width=20)
        self.tags.grid(row=6, column=1, padx=10, pady=10, sticky="w")

        # 链接类型
        tk.Label(self.root, text="链接类型").grid(row=7, column=0, padx=10, pady=10, sticky="w")
        self.link_type = ttk.Combobox(self.root, values=["关联的任务"], state="readonly")
        self.link_type.set("关联的任务")
        self.link_type.grid(row=7, column=1, padx=10, pady=10, sticky="w")
        # 问题
        tk.Label(self.root, text="问题").grid(row=7, column=2, padx=10, pady=10, sticky="w")
        self.link_issue = tk.Entry(self.root, width=20)
        self.link_issue.grid(row=7, column=3, padx=10, pady=10, sticky="w")

        # Preview Button
        tk.Button(self.root, text="预览", command=self.preview_test_cases).grid(row=8, column=0, columnspan=4, pady=20)

    def parse_field_data(self, field_data):
        """初始化字段信息"""
        print(field_data)
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
        self.scenario_sub["values"] = self.scenario[self.scenario_main.get()]
        self.scenario_sub.set("")

    def verify_input(self):
        """校验"""
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

    def preview_test_cases(self):
        if not self.verify_input():
            return

        try:
            manager = TestCaseManager(xmind_file=self.xmind_path.get(), output_dir="")
            manager.load_xmind()
            manager.parse_test_cases()
            self.test_cases = manager.test_cases

            # Display preview
            self.show_preview_table()

        except Exception as e:
            messagebox.showerror("错误", f"预览失败: {e}")

    def show_preview_table(self):
        if self.table_frame:
            self.table_frame.destroy()

        self.table_frame = tk.Frame(self.root)
        self.table_frame.grid(row=9, column=0, columnspan=4, pady=10, sticky="nsew")

        # 附加信息
        a = self.scenario_sub.get()
        additional_data = {
            "影响版本": self.effect_version.get(),
            "功能场景": f"{self.scenario_main.get()}-{self.scenario_sub.get()}" if self.scenario_sub.get() else self.scenario_main.get(),
            "测试用例来源": self.case_source.get(),
            "用例级别": self.case_level.get(),
            "用例类型": self.case_type.get(),
            "标签": self.tags.get(),
        }

        # 构造 DataFrame
        df = pd.DataFrame(self.test_cases, columns=["用例名称（主题）", "测试步骤", "预期结果", "测试数据"])
        for key, value in additional_data.items():
            df[key] = value

        # 仅在用例名称非空的行展示附加字段
        df.loc[df["用例名称（主题）"].isnull(), additional_data.keys()] = None

        # 使用 pandastable 展示
        self.table = Table(self.table_frame, dataframe=df, editable=True, width=1000, height=500)
        self.table.show()

        # 添加操作按钮
        tk.Button(self.root, text="生成Excel", command=self.generate_excel).grid(row=10, column=0, columnspan=2, pady=10)
        tk.Button(self.root, text="一键上传", command=self.upload_to_jira).grid(row=10, column=2, columnspan=2, pady=10)

    def generate_excel(self):
        try:
            df = self.table.model.df
            file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
            if not file_path:
                return

            df.to_excel(file_path, index=False)
            messagebox.showinfo("成功", "Excel文件生成成功！")
        except Exception as e:
            messagebox.showerror("错误", f"生成Excel失败: {e}")

    def upload_to_jira(self):
        if messagebox.askyesno("确认", "确定要上传用例到 JIRA 吗？"):
            try:
                df = self.table.model.df
                result = self.jira_helper.upload_test_cases(df)
                if result:
                    messagebox.showinfo("成功", "用例成功上传到 JIRA！")
                else:
                    messagebox.showerror("错误", f"上传到 JIRA 失败，详情请看日志！")
            except Exception as e:
                messagebox.showerror("错误", f"上传到 JIRA 异常: {e}，详情请看日志！")