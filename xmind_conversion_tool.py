import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from xmind_analyze import TestCaseManager
import pandas as pd
from pandastable import Table
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)


class XMindToExcelApp:
    def __init__(self, root):
        self.xmind_path = None      # xmind地址
        self.scenario_main = None   # 功能场景
        self.scenario_sub = None    # 功能场景
        self.effect_version = None  # 影响版本
        self.case_level = None      # 用例级别
        self.case_type = None       # 用例类型
        self.tags = None            # 标签
        self.link_type = None       # 链接类型
        self.link_issue = None      # 链接的问题

        self.test_cases = []
        self.table_frame = None
        self.table = None

        self.create_widgets()

    def create_widgets(self):
        """创建 UI 界面"""
        self.root = root
        self.root.title("xmind转换工具")
        self.root.geometry("1200x1000")  # 增大窗口默认尺寸
        self.root.resizable(True, True)  # 允许调整窗口大小
        self.root.configure(bg="#f5f5f5")  # 背景颜色

        # XMind 文件选择
        tk.Label(root, text="xmind文件位置").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.xmind_path = tk.StringVar()
        self.xmind_entry = tk.Entry(root, textvariable=self.xmind_path, width=50)
        self.xmind_entry.grid(row=0, column=1, padx=10, pady=10)
        tk.Button(root, text="选择本地文件", command=self.select_xmind_file).grid(row=0, column=2, padx=10, pady=10)

        # 功能场景
        tk.Label(root, text="功能场景").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.scenario_main = ttk.Combobox(root, values=["模块A", "模块B", "模块C"], state="readonly")
        self.scenario_main.grid(row=1, column=1, padx=10, pady=10, sticky="w")
        self.scenario_main.bind("<<ComboboxSelected>>", self.update_scenarios)
        self.scenario_sub = ttk.Combobox(root, state="readonly")
        self.scenario_sub.grid(row=1, column=2, padx=0, pady=10, sticky="w")

        # 影响版本
        tk.Label(root, text="影响版本").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.effect_version = ttk.Combobox(root, values=["4.1", "4.2"], state="readonly")
        self.effect_version.set("4.2")
        self.effect_version.grid(row=2, column=1, padx=10, pady=10, sticky="w")

        # 用例级别
        tk.Label(root, text="用例级别").grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.case_level = ttk.Combobox(root, values=["未分级", "1", "2", "3", "4"], state="readonly")
        self.case_level.set("未分级")
        self.case_level.grid(row=3, column=1, padx=10, pady=10, sticky="w")

        # 用例类型
        tk.Label(root, text="用例类型").grid(row=4, column=0, padx=10, pady=10, sticky="w")
        self.case_type = ttk.Combobox(root, values=["无", "常规用例", "冒烟用例", "发散用例", "门槛用例"],
                                      state="readonly")
        self.case_type.set("无")
        self.case_type.grid(row=4, column=1, padx=10, pady=10, sticky="w")

        # 标签
        tk.Label(root, text="标签").grid(row=5, column=0, padx=10, pady=10, sticky="w")
        self.tags = tk.Entry(root, width=50)
        self.tags.grid(row=5, column=1, padx=10, pady=10, sticky="w")

        # 链接类型
        tk.Label(root, text="链接类型").grid(row=6, column=0, padx=10, pady=10, sticky="w")
        self.link_type = ttk.Combobox(root, values=["关联的任务"], state="readonly")
        self.link_type.set("关联的任务")
        self.link_type.grid(row=6, column=1, padx=10, pady=10, sticky="w")
        # 问题
        tk.Label(root, text="问题").grid(row=6, column=2, padx=10, pady=10, sticky="w")
        self.link_issue = tk.Entry(root, width=20)
        self.link_issue.grid(row=6, column=3, padx=10, pady=10, sticky="w")

        # Preview Button
        tk.Button(root, text="预览", command=self.preview_test_cases).grid(row=7, column=0, columnspan=4, pady=20)

    def select_xmind_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("XMind Files", "*.xmind")])
        if file_path:
            self.xmind_path.set(file_path)

    def update_scenarios(self, event):
        # Simulated linked dropdown data, adjust based on real data
        if self.scenario_main.get() == "模块A":
            self.scenario_sub["values"] = ["子场景1A", "子场景2A"]
        elif self.scenario_main.get() == "模块B":
            self.scenario_sub["values"] = ["子场景1B", "子场景2B"]
        else:
            self.scenario_sub["values"] = ["子场景1C", "子场景2C"]
        self.scenario_sub.set("")

    def preview_test_cases(self):
        if not self.xmind_path.get() or not self.scenario_main.get() or not self.effect_version.get():
            messagebox.showerror("错误", "请确保xmind文件位置、功能场景和影响版本已填写！")
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
        self.table_frame.grid(row=8, column=0, columnspan=4, pady=10, sticky="nsew")

        # 基本字段和附加信息
        additional_data = {
            "功能场景": self.scenario_main.get(),
            "影响版本": self.effect_version.get(),
            "用例级别": self.case_level.get(),
            "用例类型": self.case_type.get(),
            "标签": self.tags.get(),
        }

        # 构造 DataFrame
        df = pd.DataFrame(self.test_cases, columns=["用例名称", "测试步骤", "预期结果", "测试数据"])
        for key, value in additional_data.items():
            df[key] = value

        # 仅在用例名称非空的行展示附加字段
        df.loc[df["用例名称"].isnull(), additional_data.keys()] = None

        # 使用 pandastable 展示
        self.table = Table(self.table_frame, dataframe=df, editable=True, width=1000, height=500)
        self.table.show()

        # 添加操作按钮
        tk.Button(self.root, text="生成Excel", command=self.generate_excel).grid(row=10, column=0, columnspan=2, pady=10)
        tk.Button(self.root, text="一键上传", command=self.upload_to_jira).grid(row=10, column=2, columnspan=2, pady=10)

    def generate_excel(self):
        # try:
            df = self.table.model.df
            file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
            if not file_path:
                return

            df.to_excel(file_path, index=False)
            messagebox.showinfo("成功", "Excel文件生成成功！")
        # except Exception as e:
        #     messagebox.showerror("错误", f"生成Excel失败: {e}")

    def upload_to_jira(self):
        messagebox.showinfo("提示", "一键上传功能暂未实现！")


if __name__ == "__main__":
    root = tk.Tk()
    app = XMindToExcelApp(root)
    root.mainloop()
