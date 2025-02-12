#coding=utf-8
import logging
from xmindparser import xmind_to_dict


def _is_test_step(title):
    """判断是否为测试步骤"""
    return len(title) > 2 and title[0].isdigit() and title[1] == '.' and ("check" in title.lower())


class TestCaseManager:
    def __init__(self, xmind_file, output_dir):
        self.xmind_file = xmind_file
        self.output_dir = output_dir

        self.data = None
        self.test_cases = []

        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def load_xmind(self):
        """加载xmind文件"""
        try:
            self.data = xmind_to_dict(self.xmind_file)
            logging.info("加载xmind文件完成")
        except Exception as e:
            logging.error(f"加载xmind文件错误: {e}")

    def parse_test_cases(self):
        """解析测试用例"""
        if not self.data:
            logging.error("没有可解析的用例")
            return

        root_topic = self.data[0]['topic']
        for child in root_topic.get('topics', []):
            module_name = child['title']
            if module_name not in ['交互', '功能', '性能']:
                logging.warning(f"未识别的模块: {module_name} 跳过解析")
                continue

            suffix = f"-{module_name}" if module_name in ['交互', '性能'] else ""
            self._parse_module(child, suffix)

    def _parse_module(self, module, suffix):
        """解析模块"""
        for scenario in module.get('topics', []):
            scenario_name = scenario['title']
            self._parse_scenario(scenario, scenario_name, suffix)

    def _parse_scenario(self, node, path, suffix):
        """拼接功能场景作为用例名"""
        for child in node.get('topics', []):
            title = child['title']
            if _is_test_step(title):
                self._parse_test_steps(node, path, suffix)
                break
            else:
                # 拼接用例名称
                self._parse_scenario(child, f"{path}-{title}", suffix)

    def _parse_test_steps(self, node, path, suffix):
        """解析测试步骤"""
        test_data = None
        steps = []
        is_new_test_data = True

        for child in node.get('topics', []):
            title = child['title']
            if _is_test_step(title):
                step = title
                expectation = child['topics'][0] if child.get('topics') else None
                # 预期结果为空时提示一下
                if expectation['title'] is None:
                    logging.warning(f"{path}{suffix} - 步骤 '{step}' 缺少预期结果")
                # 如果标明门槛，在标题行添加【门槛】
                threshold = expectation['topics'][0] if expectation.get('topics') else None
                if threshold and threshold['title'] and ("门槛" not in path):
                    path = f"【{threshold['title']}】{path}"
                # 只有测试数据更新时带上测试数据
                if is_new_test_data and test_data is not None:
                    steps.append((step, expectation['title'], test_data))
                    is_new_test_data = False
                else:
                    steps.append((step, expectation['title'], None))

            else:
                test_data = title
                is_new_test_data = True

        if not steps:
            logging.warning(f"{path}{suffix} 没有测试步骤")
        else:
            is_first_loop = True
            for step, expectation, data in steps:
                # 用例第一行带上用例名，后续不用带
                if is_first_loop:
                    self.test_cases.append([f"{path}{suffix}", step, expectation, data])
                    is_first_loop = False
                else:
                    self.test_cases.append([None, step, expectation, data])
