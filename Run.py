import tkinter as tk
from tkinter import messagebox
from configparser import ConfigParser
from jira_helper import JiraHelper
from xmind_conversion import XMindConvertionApp


class JiraLoginApp:
    def __init__(self, root):
        self.root = root
        self.jira_helper = JiraHelper()
        self.field_data = None

        # 从配置文件中获取用户名和密码
        self.config = ConfigParser()
        self.config.read("config.ini")
        self.jira_username_var = tk.StringVar(value=self.config.get('jira', 'username', fallback=''))
        self.jira_password_var = tk.StringVar(value=self.config.get('jira', 'password', fallback=''))

        # 如果用户名和密码存在，直接登录
        if self.jira_username_var.get() and self.jira_password_var.get():
            self.try_login(self.jira_username_var.get(), self.jira_password_var.get())

        # 如果登录失败或用户名密码为空，显示登录窗口
        self.create_login_widgets()
        self.create_login_widgets()

    def create_login_widgets(self):
        """创建登录界面"""
        self.root.title("JIRA 登录")
        self.root.geometry("400x200")
        self.root.resizable(False, False)

        tk.Label(self.root, text="用户名:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.username_entry = tk.Entry(self.root, textvariable=self.jira_username_var)
        self.username_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(self.root, text="密码:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.password_entry = tk.Entry(self.root, textvariable=self.jira_password_var, show="*")
        self.password_entry.grid(row=1, column=1, padx=10, pady=10)

        tk.Button(self.root, text="登录", command=self.handle_login_button).grid(row=2, column=0, columnspan=2, pady=20)

    def handle_login_button(self):
        """处理登录按钮点击事件"""
        username = self.jira_username_var.get()
        password = self.jira_password_var.get()
        self.try_login(username, password)

    def try_login(self, username, password):
        """尝试登录 JIRA"""
        if not username or not password:
            messagebox.showerror("错误", "用户名或密码不能为空！")
            return

        # 显示连接 JIRA 的弹窗
        connecting_popup = self.create_popup("正在连接到 JIRA 服务器，请稍候...")

        try:
            # 登录
            if self.jira_helper.login(username, password):
                # 登录成功，保存用户名和密码到配置文件
                self.config["jira"] = {"username": username, "password": password}
                with open("config.ini", "w") as config_file:
                    self.config.write(config_file)
                self.destroy_popup(connecting_popup)
            else:
                # 登录失败
                self.destroy_popup(connecting_popup)
                messagebox.showerror("登录失败", "登录失败，请检查用户名和密码！")
        except Exception as e:
            self.destroy_popup(connecting_popup)
            messagebox.showerror("错误", f"连接 JIRA 服务器失败：{e}")
        init_popup = self.create_popup("正在初始化，请稍候...")

        # 获取 JIRA 字段信息
        try:
            # 获取新建用例时需要的基本信息
            self.field_data = self.jira_helper.get_field_data()
            self.destroy_popup(init_popup)
            if not self.field_data:
                # 获取 JIRA 字段信息失败
                messagebox.showerror("错误", f"获取 JIRA 字段信息失败")
        except Exception as e:
            self.destroy_popup(init_popup)
            messagebox.showerror("错误", f"获取jira字段信息异常：{e}")

        # 解析 JIRA 字段信息
        try:
            # 进入主界面
            self.open_main_app()
        except Exception as e:
            messagebox.showerror("错误", f"解析jira字段信息异常，请确保JIRA当前项目为ET")

    def create_popup(self, text):
        """创建弹窗"""
        popup = tk.Toplevel(self.root)
        popup.title("")
        popup.geometry("300x100")
        popup.resizable(False, False)
        popup.transient(self.root)  # 使弹窗附属于主窗口
        popup.grab_set()  # 阻止用户点击主窗口
        tk.Label(popup, text=text, padx=20, pady=20).pack()
        popup.update()  # 强制更新 UI
        return popup

    def destroy_popup(self, popup):
        """销毁弹窗"""
        if popup.winfo_exists():
            popup.destroy()

    def open_main_app(self):
        """打开主界面"""
        self.root.destroy()
        main_root = tk.Tk()
        XMindConvertionApp(main_root, self.jira_helper, self.field_data)
        main_root.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    JiraLoginApp(root)
    root.mainloop()
