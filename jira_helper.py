import json
import re

import requests
import logging
from bs4 import BeautifulSoup
from atlassian import Jira


class JiraHelper:
    def __init__(self):
        self.jira = Jira(url='https://work.fineres.com/')
        self.base_url = "https://work.fineres.com"
        self.token = None
        self.user = ''
        self.headers = {
            "content-Type": "application/json"
        }
        # field_map存储field的name和fieldId的对照表{"优先级":"priority"}
        self.field_map = {}
        self.project = "ET"
        self.issuetype = "测试"

    def login(self, username, password):
        """登录"""
        try:
            response = requests.post(
                f"{self.base_url}/rest/auth/1/session",
                headers=self.headers,
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
                self.token = session['value']
                cookie = session['name'] + "=" + session['value']
                self.headers['cookie'] = self.__add_cookie(self.headers.get('cookie'), cookie)
                logging.info("JIRA 登录成功")
                self.jira = Jira(url=self.base_url, username=username, password=password)
                return True
        except Exception as e:
            logging.error(f"JIRA 登录接口异常: {e}")
            raise e

    def get_field_data(self):
        """获取新建用例时需要的字段信息，包括功能场景、测试用例来源、用例级别、用例类型"""
        try:
            data = {'pid': '14400'}
            headers = self.headers.copy()
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
            response = requests.post(
                f"{self.base_url}/secure/QuickCreateIssue!default.jspa?decorator=none",
                headers=headers,
                data=data,
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

    def create_case(self, row):
        """创建用例"""
        # 生成功能场景
        scenario = row['功能场景']
        parts = scenario.split("-")
        if len(parts) == 1 or (len(parts) == 2 and parts[1] == '无'):
            scenario = {"value": parts[0]}
        elif len(parts) == 2 and parts[1] != '无':
            # 如果有两个元素
            scenario = {"value": parts[0], "child": {"value": parts[1]}}
        else:
            # 如果不符合要求，返回错误信息
            logging.error(f"功能场景有误：{scenario}")
            return False
        data = {
            "fields": {
                "project": {"key": self.project},
                "issuetype": {"name": self.issuetype},
                "summary": row['用例名称（主题）'],
                "customfield_10809": scenario,
                "versions": [{"name": row['影响版本']}],
                "customfield_10545": {"value": row['测试用例来源']},
                "customfield_11300": {"value": row['用例级别']}
            }
        }
        if row['用例类型'] and row['用例类型'] != '无':
            data["fields"]["customfield_10546"] = {"value": row['用例类型']}
        if row['标签']:
            labels = row['标签'].split(",")
            data["fields"]["labels"] = labels
        print(f"创建用例请求：{data}")
        try:
            response = requests.post(
                f"{self.base_url}/rest/api/2/issue",
                headers=self.headers,
                json=data,
            )
            # 新建失败
            if response.status_code not in [200, 201]:
                logging.error(f"创建用例失败，具体报错为: {response.text}")
                return False
            # 新建成功
            res = json.loads(response.text)
            return res
        except Exception as e:
            logging.error(f"创建用例异常: {e}")
            raise e

    def add_test_step(self, issue_id, step, data, result, headers):
        data = {"step": step, "data": data, "result": result, "customFieldValues": {}}
        print(f"添加测试步骤：{data}")
        try:
            response = requests.post(self.base_url + "/rest/zephyr/latest/teststep/" + issue_id, headers=headers, json=data)
            if response.status_code != 200:
                logging.error(f"添加测试步骤失败，详情为: {response.text}")
                return False
            return True
        except Exception as e:
            logging.error(f"添加测试结果异常：{e}")
            raise e

    def add_link_issue(self, issue_id, link_id, link_type):
        json = {
            "type": {
                "id": str(link_type)
            },
            "inwardIssue": {
                "key": str(issue_id)
            },
            "outwardIssue": {
                "key": str(link_id)
            }
        }
        print(f"添加关联任务：{json}")
        try:
            self.jira.create_issue_link(json)
        except Exception as e:
            logging.error(f"添加关联任务失败：{e}")
            raise e

    def collect_issue_info(self, issue_key):
        """获取用例的信息"""
        info = IssueInfo()
        try:
            response = requests.get(self.base_url + "/browse/" + issue_key, headers=self.headers)
            if response.status_code != 200:
                logging.error(f"获取用例的信息失败: {issue_key}")
                return info
            if response.headers.get('Set-Cookie'):
                self.headers['cookie'] = self.__add_cookie(self.headers.get('cookie'), response.headers.get('Set-Cookie')[
                                                                                           :response.headers.get(
                                                                                               'Set-Cookie').rfind(
                                                                                               ";")])
            info.zEncKeyFld = re.findall('zEncKeyFld = "(.*?)"', response.text)[0].lower()
            info.zEncKeyVal = re.findall('zEncKeyVal = "(.*?)"', response.text)[0]
            info.issue_key = issue_key
            issue = self.jira.issue(issue_key)
            info.issue_id = issue['id']
            info.title = issue['fields']['summary']
            return info
        except Exception as e:
            logging.error(f"获取用例信息异常：{e}")
            raise e

    def upload_test_cases(self, df, conf, status_callback=None):
        issue_count = 0  # 已创建用例数目
        step_count = 0  # 添加用例的步骤
        issue_id = ''
        issue_key = ''
        headers = self.headers

        for _, row in df.iterrows():
            case_name = row['用例名称（主题）']
            if case_name:  # 如果用例名称不为空，创建新用例
                try:
                    res = self.create_case(row)
                    # res = {'id': '1339911', 'key': 'ET-3490'}
                    if res:
                        issue_id = res['id']
                        issue_key = res['key']
                        issue_count += 1
                        step_count = 0
                        status_callback(f"\n创建用例 {issue_key} 成功")
                    else:
                        status_callback(f"创建第{issue_count + 1}个用例失败，用例名称为'{case_name}'!!!")
                        return False
                except Exception as e:
                    logging.error(f"创建第{issue_count + 1}个用例异常，用例名称为'{case_name}',错误信息：{e}")
                    status_callback(f"创建第{issue_count + 1}个用例异常，用例名称为'{case_name}'!!!")
                    return False

                # 收集用例信息
                try:
                    info = self.collect_issue_info(issue_key)
                    if info.issue_id != "":
                        headers[info.zEncKeyFld] = info.zEncKeyVal
                except Exception as e:
                    logging.info(f"获取用例【{issue_key}】信息异常，错误信息：{e}")
                    status_callback(f"获取用例【{issue_key}】信息异常!!!")

                # 关联任务（若有）
                if conf["link_issue"]:
                    link_issue = conf["link_issue"]
                    try:
                        self.add_link_issue(issue_key, link_issue, "11600")
                        status_callback(f"关联 {link_issue} 与 {issue_key} 成功")
                    except Exception as e:
                        logging.error(f"关联 {link_issue} 与 {issue_key} 异常：{e}")
                        status_callback(f"关联 {link_issue} 与 {issue_key} 异常!!!")
                        return False

            # 添加步骤
            try:
                res = self.add_test_step(issue_id, row["测试步骤"], row["测试数据"], row["预期结果"], headers)
                if res:
                    step_count += 1
                    status_callback(f"{issue_key} 添加第 {step_count} 个步骤成功")
                else:
                    status_callback(f"{issue_key} 添加第 {step_count} 个步骤时失败!!!")
                    return False
            except Exception as e:
                logging.error(f"{issue_key} 添加第 {step_count} 个步骤时异常：{e}")
                status_callback(f"{issue_key} 添加第 {step_count} 个步骤时异常!!!")
                return False
        return True

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


class IssueInfo:
    """测试用例信息"""

    def __init__(self):
        self.issue_key = ""
        self.issue_id = ""
        self.zEncKeyFld = ""
        self.zEncKeyVal = ""
        self.title = ""
