from Common import *
from configparser import ConfigParser
from jira_helper import JiraHelper
from xmind_conversion import XMindConvertionApp


class JiraLoginApp:
    def __init__(self, root):
        self.root = root
        self.jira_helper = JiraHelper()
        self.style = None
        self.login_frame = None

        self.field_data = None
        self.fail_times = 0

        # 从配置文件中获取用户名和密码
        self.config = ConfigParser()
        self.config.read("config.ini")
        self.jira_username_var = ttk.StringVar(value=self.config.get('jira', 'username', fallback=''))
        self.jira_password_var = ttk.StringVar(value=self.config.get('jira', 'password', fallback=''))

        # 样式初始化
        init_style(self.root)
        # 显示登录窗口
        self.create_login_widgets()

    def create_login_widgets(self):
        """创建登录界面"""
        # 配置主窗口的行和列权重
        init_grid(self.root, 2, 1)

        # 提示文字
        ttk.Label(self.root, text="使用jira用户名密码登录", font=('Consolas', 9), foreground='grey', anchor='center').grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # 登录主界面
        self.login_frame = ttk.Frame(self.root)
        self.login_frame.grid(row=1, column=0, sticky="nsew")

        # 配置Frame的行和列权重
        init_grid(self.login_frame, 3, 2)

        # 用户名
        ttk.Label(self.login_frame, text="用户名:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.username_entry = ttk.Entry(self.login_frame, textvariable=self.jira_username_var)
        self.username_entry.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        # 密码
        ttk.Label(self.login_frame, text="密码:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.password_entry = ttk.Entry(self.login_frame, textvariable=self.jira_password_var, show="*")
        self.password_entry.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        # 登录按钮
        ttk.Button(self.login_frame, text="登录", command=self.handle_login_button).grid(row=2, column=0, columnspan=2, pady=20)

        root.place_window_center()

        # 如果用户名和密码存在，直接登录
        a = self.jira_username_var.get()
        if self.jira_username_var.get() != "" and self.jira_password_var.get() != "":
            self.login(self.jira_username_var.get(), self.jira_password_var.get())
        else:
            self.fail_times += 1

    def handle_login_button(self):
        """处理登录按钮点击事件"""
        username = self.jira_username_var.get()
        password = self.jira_password_var.get()
        self.login(username, password)

    def login(self, username, password):
        """尝试登录 JIRA"""
        if not username or not password:
            show_messagebox(self.root, "error", "用户名或密码不能为空！")
            return

        # 显示连接 JIRA 的弹窗
        popup = create_popup("正在连接到 JIRA 服务器，请稍候...\n")

        try:
            # 登录
            res = self.jira_helper.login(username, password)
            if res:
                if self.fail_times != 0:
                    self.config["jira"] = {"username": username, "password": password}
                    with open("config.ini", "w") as config_file:
                        self.config.write(config_file)
            else:
                # 登录失败
                destroy_popup(popup)
                self.fail_times += 1
                show_messagebox(self.root, "error", "登录失败，请检查用户名和密码！")
                return
        except Exception as e:
            destroy_popup(popup)
            show_messagebox(self.root, "error", f"连接 JIRA 服务器失败：{e}")

        update_popup(popup, "正在初始化，请稍候...\n")
        # 获取 JIRA 字段信息
        try:
            # 获取新建用例时需要的基本信息
            self.field_data = self.jira_helper.get_field_data()
            destroy_popup(popup)
            if not self.field_data:
                # 获取 JIRA 字段信息失败
                show_messagebox(self.root, "error", "获取 JIRA 字段信息失败！")
        except Exception as e:
            destroy_popup(popup)
            show_messagebox(self.root, "error", f"获取jira字段信息异常：{e}")

        # 进入主界面
        self.open_main_app()

    def open_main_app(self):
        """加载主界面"""
        # 清空根窗口中的所有部件
        for widget in self.root.winfo_children():
            widget.destroy()

        # 修改窗口标题和尺寸
        self.root.title("xmind转换工具")
        self.place_window_center()  # 设置窗口位置
        # 创建主界面
        XMindConvertionApp(self.root, self.jira_helper, self.field_data)

    def place_window_center(self):
        self.root.update_idletasks()

        # 获取屏幕尺寸
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # 直接使用设置的窗口大小
        window_width = 2000
        window_height = 1000

        # 计算居中位置
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        # 重新设置窗口位置
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")


if __name__ == "__main__":
    root = ttk.Window(title="登录", themename=theme, size=(600, 300))
    JiraLoginApp(root)
    root.mainloop()
