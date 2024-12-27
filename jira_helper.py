import requests
import logging
import traceback
import json
from bs4 import BeautifulSoup


class JiraHelper:
    def __init__(self):
        self.base_url = "https://work.fineres.com"
        self.token = None
        self.user = ''
        self.__headers = {
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

    def login(self, username, password):
        try:
            response = requests.post(
                f"{self.base_url}/rest/auth/1/session",
                headers=self.__headers,
                json={"username": username, "password": password},
                timeout=10
            )
            if response.status_code != 200:
                logging.error(f"JIRA 登录失败: {response.text}")
                return False
            else:
                self.user = username
                # 保存认证信息
                session = response.json()['session']
                cookie = session['name'] + "=" + session['value']
                self.__headers['cookie'] = self.__add_cookie(self.__headers.get('cookie'), cookie)
                logging.info("JIRA 登录成功")
                return True
        except Exception as e:
            logging.error(f"JIRA 登录接口异常: {e}")
            raise e

    def get_field_data(self):
        """获取新建用例时需要的字段信息，包括功能场景、测试用例来源、用例级别、用例类型"""
        try:
            response = requests.post(
                # 这里URL要加上某个ET用例的issueId，才能把默认页面转到ET项目，才能获取到ET对应的用例值
                f"{self.base_url}/secure/QuickCreateIssue!default.jspa?decorator=none&issueId=1323216",
                headers=self.__headers,
                timeout=10
            )
            if response.status_code != 200:
                logging.error(f"获取 JIRA 字段信息失败: {response.text}")
                return None
            # 解析字段信息
            data = response.json()
            field_data = {}
            for field in data.get('fields', []):
                label = field['label']
                edit_html = field['editHtml']
                soup = BeautifulSoup(edit_html, 'html.parser')

                if label == '影响版本':
                    options = soup.find_all('option')
                    field_data[label] = [option.text.strip() for option in options]

                elif label in ['测试用例来源', '用例级别', '用例类型']:
                    options = soup.find('select').find_all('option')
                    field_data[label] = [option.text.strip() for option in options]

                elif label == '功能场景':
                    # 解析第一个select（父场景）
                    parent_select = soup.find_all('select')[0]
                    parent_options = parent_select.find_all('option')
                    parent_scenarios = {option['value']: option.text.strip() for option in parent_options}

                    # 解析第二个select（子场景）
                    child_select = soup.find_all('select')[1]
                    child_options = child_select.find_all('option')
                    scenario_dict = {}

                    for option in child_options:
                        text = option.text.strip()
                        class_list = option.get('class', [])
                        if isinstance(class_list, list) and class_list:
                            parent_key = class_list[-1].split('-')[-1]
                            if parent_key in parent_scenarios:
                                if parent_scenarios[parent_key] not in scenario_dict:
                                    scenario_dict[parent_scenarios[parent_key]] = []
                                scenario_dict[parent_scenarios[parent_key]].append(text)

                    # 构建最终的父子场景结构
                    field_data[label] = scenario_dict
            return field_data
        except Exception as e:
            logging.error(f"获取 JIRA 字段信息异常: {e}")
            raise e

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

    @staticmethod
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