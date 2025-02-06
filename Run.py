import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
from configparser import ConfigParser
from jira_helper import JiraHelper
from xmind_conversion import XMindConvertionApp

common_font = 'Consolas'    # 通用字体
common_font_size = 12       # 通用字体大小


class JiraLoginApp:
    def __init__(self, root):
        self.root = root
        self.jira_helper = JiraHelper()
        self.style = None

        self.field_data = None
        self.fail_times = 0

        # 从配置文件中获取用户名和密码
        self.config = ConfigParser()
        self.config.read("config.ini")
        self.jira_username_var = ttk.StringVar(value=self.config.get('jira', 'username', fallback=''))
        self.jira_password_var = ttk.StringVar(value=self.config.get('jira', 'password', fallback=''))

        # 样式初始化
        self.init_style()
        # 显示登录窗口
        self.create_login_widgets()

    def init_style(self):
        self.style = ttk.Style()
        self.style.configure('TLabel', font=(common_font, common_font_size))  # 设置Label的字体
        self.style.configure('TEntry', font=(common_font, common_font_size))  # 设置Entry的字体
        self.style.configure('TButton', font=(common_font, common_font_size))  # 设置Button的字体

    def create_login_widgets(self):
        """创建登录界面"""
        # 配置主窗口的行和列权重
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # 提示文字
        ttk.Label(self.root, text="使用jira用户名密码登录", font=('Consolas', 9), foreground='grey', anchor='center').grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # 登录主界面
        login_frame = ttk.Frame(self.root)
        login_frame.grid(row=1, column=0, sticky="nsew")

        # 配置Frame的行和列权重
        login_frame.grid_rowconfigure(0, weight=1)
        login_frame.grid_rowconfigure(1, weight=1)
        login_frame.grid_rowconfigure(2, weight=1)
        login_frame.grid_columnconfigure(0, weight=1)
        login_frame.grid_columnconfigure(1, weight=1)

        # 用户名
        ttk.Label(login_frame, text="用户名:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.username_entry = ttk.Entry(login_frame, textvariable=self.jira_username_var, font=(common_font, common_font_size))
        self.username_entry.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        # 密码
        ttk.Label(login_frame, text="密码:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.password_entry = ttk.Entry(login_frame, textvariable=self.jira_password_var, font=(common_font, common_font_size), show="*")
        self.password_entry.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        # 登录按钮
        ttk.Button(login_frame, text="登录", command=self.handle_login_button).grid(row=2, column=0, columnspan=2, pady=20)

        root.place_window_center()

    def handle_login_button(self):
        """处理登录按钮点击事件"""
        username = self.jira_username_var.get()
        password = self.jira_password_var.get()
        self.login(username, password)

    def login(self, username, password):
        """尝试登录 JIRA"""
        if not username or not password:
            Messagebox.show_error("用户名或密码不能为空！\n")
            return

        # 显示连接 JIRA 的弹窗
        popup = self.create_popup("正在连接到 JIRA 服务器，请稍候...\n")

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
                self.destroy_popup(popup)
                self.fail_times += 1
                Messagebox.show_error("登录失败，请检查用户名和密码！\n")
                return
        except Exception as e:
            self.destroy_popup(popup)
            Messagebox.show_error(f"连接 JIRA 服务器失败：{e}\n")

        self.update_popup(popup, "正在初始化，请稍候...\n")

        # 获取 JIRA 字段信息
        try:
            # 获取新建用例时需要的基本信息
            self.field_data = self.jira_helper.get_field_data()
            self.destroy_popup(popup)
            if not self.field_data:
                # 获取 JIRA 字段信息失败
                Messagebox.show_error("获取 JIRA 字段信息失败\n")
        except Exception as e:
            self.destroy_popup(popup)
            Messagebox.show_error("错误", f"获取jira字段信息异常：{e}\n")

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
        self.root.update_idletasks()  # 确保 Tkinter 计算窗口大小

        # 获取屏幕尺寸
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # 直接使用设置的窗口大小
        window_width = 1200
        window_height = 1000

        # 计算居中位置
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        # 重新设置窗口位置
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

    def create_popup(self, text):
        """创建弹窗"""
        popup = ttk.Window(title="JIRA 登录", themename="litera")
        ttk.Label(popup, text=text, font=(common_font, common_font_size)).grid()
        popup.place_window_center()
        popup.update()
        return popup

    def update_popup(self, popup, text):
        """更新弹窗内容"""
        for widget in popup.winfo_children():
            if isinstance(widget, ttk.Label):
                widget.config(text=text)
        popup.place_window_center()
        popup.update()

    def destroy_popup(self, popup):
        """销毁弹窗"""
        if popup.winfo_exists():
            popup.destroy()


if __name__ == "__main__":
    root = ttk.Window(title="登录", themename="litera",size=(600, 300))
    JiraLoginApp(root)
    root.mainloop()
