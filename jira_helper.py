import requests
import logging


class JiraHelper:
    def __init__(self, username, password):
        self.base_url = "https://work.fineres.com"
        self.username = username
        self.password = password
        self.headers = {
            "content-Type": "application/json"
        }
        # issuetype_map存储issuetype的name和id的对照表{"测试":"123"}
        self.issuetype_map = {}
        # project_map存储project的name和key的对照表{"质量管理":"QA"}
        self.project_map = {}
        # field_map存储field的name和fieldId的对照表{"优先级":"priority"}
        self.field_map = {}
        self.project = None
        self.issuetype = None

    def __add_cookie(cookie_old, cookie_add):
        r"""添加cookie.

        :param cookie_old: 旧cookie, :class: `str`.
        :param cookie_add: 要添加的cookie, :class:`str`.
        :return: cookie: 组合的新cookie, :class:`str`.
        """
        if not cookie_old:
            return cookie_add
        else:
            return cookie_old + "; " + cookie_add

    def login(self):
        try:
            response = requests.post(
                f"{self.base_url}/rest/auth/1/session",
                headers=self.headers,
                json={"username": self.username, "password": self.password},
                timeout=5
            )
            if response.status_code == 200:
                self.headers['cookie'] = self.__add_cookie(self.__headers.get('cookie'), cookie)
                self.token = response.cookies["JSESSIONID"]
                logging.info("JIRA 登录成功")
                return True
            else:
                logging.error(f"JIRA 登录失败: {response.text}")
                return False
        except Exception as e:
            logging.error(f"JIRA 登录异常: {e}")
            return False

    def upload_test_cases(self, df):
        for _, row in df.iterrows():
            response = requests.post(
                f"{self.base_url}/rest/api/2/issue",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "fields": {
                        "project": {"key": "PROJECT_KEY"},
                        "summary": row["用例名称"],
                        "description": row["测试步骤"],
                        "issuetype": {"name": "Test Case"},
                    }
                },
            )
            if response.status_code != 201:
                raise Exception(f"上传失败: {response.text}")
