import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
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
        self.jira_username_var = ttk.StringVar(value=self.config.get('jira', 'username', fallback=''))
        self.jira_password_var = ttk.StringVar(value=self.config.get('jira', 'password', fallback=''))

        # 如果用户名和密码存在，直接登录
        # if self.jira_username_var.get() and self.jira_password_var.get():
        #     self.try_login(self.jira_username_var.get(), self.jira_password_var.get())

        # 如果登录失败或用户名密码为空，显示登录窗口
        self.create_login_widgets()

    def create_login_widgets(self):
        """创建登录界面"""
        ttk.Label(self.root, text="用户名:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.username_entry = ttk.Entry(self.root, textvariable=self.jira_username_var)
        self.username_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(self.root, text="密码:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.password_entry = ttk.Entry(self.root, textvariable=self.jira_password_var, show="*")
        self.password_entry.grid(row=1, column=1, padx=10, pady=10)

        ttk.Button(self.root, text="登录", command=self.handle_login_button).grid(row=2, column=0, columnspan=2, pady=20)

    def handle_login_button(self):
        """处理登录按钮点击事件"""
        username = self.jira_username_var.get()
        password = self.jira_password_var.get()
        self.try_login(username, password)

    def try_login(self, username, password):
        """尝试登录 JIRA"""
        if not username or not password:
            Messagebox.show_error("用户名或密码不能为空！")
            return

        # 显示连接 JIRA 的弹窗
        popup = self.create_popup("正在连接到 JIRA 服务器，请稍候...")

        try:
            # 登录
            if self.jira_helper.login(username, password):
                # 登录成功，保存用户名和密码到配置文件
                self.config["jira"] = {"username": username, "password": password}
                with open("config.ini", "w") as config_file:
                    self.config.write(config_file)
            else:
                # 登录失败
                self.destroy_popup(popup)
                Messagebox.show_error("登录失败，请检查用户名和密码！")
                return
        except Exception as e:
            self.destroy_popup(popup)
            Messagebox.show_error(f"连接 JIRA 服务器失败：{e}")

        self.update_popup(popup, "正在初始化，请稍候...")

        # 获取 JIRA 字段信息
        try:
            # 获取新建用例时需要的基本信息
            self.field_data = self.jira_helper.get_field_data()
            self.destroy_popup(popup)
            if not self.field_data:
                # 获取 JIRA 字段信息失败
                Messagebox.show_error("获取 JIRA 字段信息失败")
        except Exception as e:
            self.destroy_popup(popup)
            Messagebox.show_error(f"获取jira字段信息异常：{e}")

        # 解析 JIRA 字段信息,进入主界面
        self.open_main_app()

    def create_popup(self, text):
        """创建弹窗"""
        popup = ttk.Window(title="JIRA 登录", themename="litera", size=(400, 100))
        popup.place_window_center()
        ttk.Label(popup, text=text).grid()
        popup.update()
        return popup

    def update_popup(self, popup, text):
        """更新弹窗内容"""
        for widget in popup.winfo_children():
            widget.config(text=text)
        popup.update()

    def destroy_popup(self, popup):
        """销毁弹窗"""
        if popup.winfo_exists():
            popup.destroy()

    def open_main_app(self):
        """打开主界面"""
        self.root.destroy()  # 销毁登录窗口
        try:
            main_root = ttk.Window(title="xmind转换工具", themename="litera", size=(600, 600))
            main_root.place_window_center()
            XMindConvertionApp(main_root, self.jira_helper, self.field_data)
            main_root.mainloop()
        except Exception as e:
            Messagebox.show_error(f"打开主界面报错：{e}")


if __name__ == "__main__":
    root = ttk.Window(title="JIRA 登录", themename="litera", size=(500, 200))
    root.place_window_center()
    JiraLoginApp(root)
    root.mainloop()
