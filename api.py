import random
import inquirer
from loguru import logger
from time import sleep
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import Config
from utils import *


class MicroCourse:
    def __init__(self, course_id, module_id, course_name):
        self.client = HttpClient()
        self.course_id = course_id
        self.module_id = module_id
        self.course_name = course_name
        self.api_base_url = "https://le.ouchn.cn/api"
        self.micro_course_base_url = f"""
        {self.api_base_url}/Completion/Course/
        {self.course_id}/Module/Video/
        {self.module_id}/Session
        """.replace(" ", "").replace("\n", "").strip()

    def start_micro_course(self):
        url = f"{self.micro_course_base_url}/Start"
        req_body = {
            "CourseId": self.course_id,
            "ModuleId": self.module_id,
            "ModuleType": "Video",
            "Origin": "ouchn"
        }
        params = {
            "Origin": "ouchn"
        }
        response, status = self.client.post(url=url, json_data=req_body, params=params)
        if not status:
            logger.error("获取课程学习信息失败")
            raise
        response = response.json()
        response_data = response.get("Data")
        self.session_id = response_data.get("SessionId")
        self.study_duration = response_data.get("StudyDuration")
        self.micro_course_duration = response_data.get("MicroCourseDuration")
        self.study_percentage = self.study_duration / self.micro_course_duration * 100

    def process_micro_course(self, interrupt_data):
        url = f"{self.micro_course_base_url}/Process"
        req_body = {
            "CourseId": self.course_id,
            "ModuleId": self.module_id,
            "SessionId": self.session_id,
            "InterruptData": interrupt_data,
            "ModuleType": "Video",
            "Origin": "ouchn"
        }
        _, status = self.client.post(url=url, json_data=req_body)
        if not status:
            logger.error("上报进度失败")
            raise
        logger.debug(f"微课 {self.course_name} 成功上报视频时间戳: {interrupt_data}")

    def end_micro_course(self, interrupt_data):
        url = f"{self.micro_course_base_url}/End"
        req_body = {
            "CourseId": self.course_id,
            "ModuleId": self.module_id,
            "SessionId": self.session_id,
            "InterruptData": interrupt_data,
            "ModuleType": "Video",
            "Origin": "ouchn"
        }
        _, status = self.client.post(url=url, json_data=req_body)
        if not status:
            logger.error("提交微课进度失败")
            raise

    def run(self):
        try:
            from tqdm import tqdm
            init_time = random.uniform(1, 3)
            logger.info(f"微课 {self.course_name} 刷课线程将在 {2 * init_time:.1f}s 后启动")
            logger.debug(f"微课 {self.course_name} 的 CourseId 为 {self.course_id}")
            logger.debug(f"微课 {self.course_name} 的 ModuleId 为 {self.module_id}")
            OuchnUtils().student_micro_course(self.course_id, self.course_name)
            sleep(init_time)
            self.start_micro_course()
            sleep(init_time)
            with tqdm(total=self.micro_course_duration - self.study_duration, desc=f"当前刷课: {self.course_name}", unit="秒") as pbar:
                for i in range(((self.micro_course_duration - self.study_duration) // 20) + 1):
                    logger.debug(f"正在准备微课 {self.course_name} 信息")
                    self.start_micro_course()
                    if self.study_percentage >= 100:
                        break
                    interrupt_data = i * 20
                    if interrupt_data > self.micro_course_duration:
                        interrupt_data = self.micro_course_duration
                    wait_time = random.uniform(10, 11)
                    logger.debug(f"微课 {self.course_name} 等待时间戳上报冷却 {wait_time:.1f}s")
                    sleep(wait_time)
                    logger.debug(f"微课 {self.course_name} 当前 SessionId 为 {self.session_id}")
                    logger.debug(f"开始上报观看微课 {self.course_name}")
                    self.process_micro_course(str(interrupt_data))
                    pbar.update(interrupt_data)
                    logger.debug(f"开始刷新 SessionId")
                    self.end_micro_course(str(interrupt_data))
                self.start_micro_course()
                logger.success("====================================================")
                logger.success(f"{self.course_name} 已刷完")
                logger.success("====================================================")
        except Exception as e:
            logger.error(f"微课 {self.course_name} 刷课线程运行出错")
            raise e


class Login:
    def to_login(self):
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions
        from selenium.common.exceptions import WebDriverException
        cfg = Config()
        while True:
            try:
                driver = get_web_driver()
            except RuntimeError as e:
                use_browser_check = not prompt([
                    inquirer.Confirm(
                        name="confirm",
                        message="是否要取消浏览器安装检查? (可能修复无法调用浏览器,但会导致启动浏览器较慢)"
                    )
                ])["confirm"]
                cfg.update(["use_browser_check"], use_browser_check)
                continue
            else:
                break
        driver.get("https://le.ouchn.cn/")
        try:
            button = WebDriverWait(driver, 10).until(
                expected_conditions.element_to_be_clickable((By.CLASS_NAME, "login-btn"))
            )
            button.click()
            cookie_dict = {}
            while True:
                logger.debug("正在等待登录...")
                cookies = driver.get_cookies()
                for cookie in cookies:
                    cookie_dict[cookie['name']] = cookie['value']
                if "token" in cookie_dict:
                    cookie_dict = {cookie["name"]: cookie["value"] for cookie in cookies}
                    cfg.update(["cookies"], cookie_dict)
                    break
                else:
                    sleep(0.5)
                    continue
        except (AttributeError, ConnectionResetError, WebDriverException):
            logger.error("浏览器窗口被关闭！")
            self.to_login()
        except Exception as e:
            raise e
        finally:
            driver.quit()

    def try_login(self):
        while True:
            response, status = HttpClient().get("https://passport.le.ouchn.cn/localApi/UserInfo")
            if status:
                break
            self.to_login()
        response = response.json()
        response_data = response.get("Data")
        name = response_data.get("Name")
        nick_name = response_data.get("Nickname")
        logger.success(f"登录态已确认, 名字 - {name}, 昵称 - {nick_name}")


class OuchnUtils:
    def __init__(self):
        self.cfg = Config()
        self.base_url = "https://le.ouchn.cn/api"
        self.course_list_cache = {}

    def student_micro_course(self, course_id, course_name):
        url = f"{self.base_url}/StudentCourse/{course_id}"
        req_body = {
            "CourseId": course_id
        }
        _, status = HttpClient().post(url=url, json_data=req_body)
        if not status:
            logger.error(f"微课 {course_name} 学习记录上报失败")
            raise
        logger.debug(f"微课 {course_name} 学习记录上报成功")

    def get_micro_course_info(self, course_id):
        response, status = HttpClient().get(f"{self.base_url}/Course/{course_id}/MicroCourse/Details")
        if not status:
            logger.error("获取微课信息失败")
            return {}
        response = response.json()
        response_data = response.get("Data")
        micro_info = {
            "course_name": response_data.get("Name"),
            "module_list": {}
        }
        for module in response_data.get("Modules"):
            micro_info.get("module_list")[module["Id"]] = {
                "module_name": module.get("Title")
            }
        return micro_info

    def auto_fetch_course_id(self):
        url = f"{self.base_url}/Completion/Course/Paging"
        params = {
            "PageNum": 1,
            "PageSize": 10
        }
        response, status = HttpClient().get(url, params=params)
        if not status:
            logger.error("获取学习记录失败")
            return []
        logger.success("获取学习记录成功")
        course_id_list = []
        response = response.json()
        response_data = response["Data"]
        for course_info in response_data.get("PageListInfos"):
            if course_info.get("CompletionStatus") == "NotAttempted":
                _course_info = self.micro_course_cache(course_info.get("CourseId"))
                logger.info(f"已添加微课: {_course_info.get("course_name")}, 共 {len(_course_info.get("module_list"))} 集")
                course_id_list.append(course_info.get("CourseId"))
        logger.info("已添加尚未学习完成的微课")
        return course_id_list

    def get_study_info(self, course_id, module_id, course_name):
        micro_course = MicroCourse(course_id, module_id, course_name)
        micro_course.start_micro_course()
        study_info = {
            "study_duration": micro_course.study_duration,
            "micro_course_duration": micro_course.micro_course_duration,
            "study_percentage": micro_course.study_percentage
        }
        return study_info

    def check_micro_course_progress(self):
        logger.info("正在检查微课完成进度")
        def check_module_progress(course_id, course_info, module_id, module_info):
            study_info = self.get_study_info(course_id, module_id, module_info.get("module_name"))
            study_percentage_str = f"{study_info.get('study_percentage'):.2f}%"
            if study_info.get("study_percentage") >= 100:
                logger.info(
                    f"{study_percentage_str:<8} | " +
                    f"微课 '{course_info.get('course_name')}' " +
                    f"章节 '{module_info.get('module_name')}' 已刷完, 从配置文件剔除"
                )
                return None
            else:
                logger.info(
                    f"{study_percentage_str:<8} | " +
                    f"微课 '{course_info.get('course_name')}' " +
                    f"章节 '{module_info.get('module_name')}'"
                )
                return {module_id: module_info}
        tasks = []
        for course_id, course_info in self.cfg.get_value(["course_list"]).items():
            for module_id, module_info in course_info.get("module_list").items():
                tasks.append((course_id, course_info, module_id, module_info))
        completed_modules = {}
        with ThreadPoolExecutor(max_workers=self.cfg.get_value(["max_workers"])) as executor:
            future_to_task = {
                executor.submit(check_module_progress, *task): task 
                for task in tasks
            }
            for future in as_completed(future_to_task):
                result = future.result()
                if result is not None:
                    task = future_to_task[future]
                    course_id = task[0]
                    course_info = task[1]
                    
                    if course_id not in completed_modules:
                        completed_modules[course_id] = {
                            "course_name": course_info.get("course_name"),
                            "module_list": {}
                        }
                    completed_modules[course_id]["module_list"].update(result)
        self.cfg.update(["course_list"], completed_modules)
        if len(self.cfg.get_value(["course_list"])) == 0:
            logger.success("所有微课已刷完")
            return True
        else:
            return False

    def micro_course_cache(self, course_id):
        course_info = {}
        for id in self.course_list_cache.keys():
            if course_id == id:
                course_info = self.course_list_cache[id]
        if course_info != {}:
            return course_info
        self.course_list_cache[course_id] = self.get_micro_course_info(course_id)
        return self.micro_course_cache(course_id)

    def micro_course_config(self):
        course_id_list = []
        self.cfg.update(["course_list"], {})
        choices = prompt([
            inquirer.Checkbox(
                name="choice",
                message="请选择以何种方式配置刷课信息 (按空格键选择, 可多选, 回车键确定)",
                choices=["从个人中心-学习记录自动获取", "手动输入课程链接"]
            )
        ])["choice"]
        for choice in choices:
            if choice == "从个人中心-学习记录自动获取":
                course_id_list.extend(self.auto_fetch_course_id())
            elif choice == "手动输入课程链接":
                course_id_list.extend(self.manual_input_course_id())
        for course_id in course_id_list:
            self.cfg.update(["course_list", course_id], self.micro_course_cache(course_id))
        logger.success("微课保存成功")
        self.check_micro_course_progress()

    def manual_input_course_id(self):
        try:
            course_id_list = []
            while True:
                course_link = prompt([
                    inquirer.Text(
                        name="course_link",
                        message="请输入微课链接 (不输入直接回车即退出输入)"
                    )
                ])["course_link"]
                if course_link == "":
                    break
                course_id = course_link.split("/")[4]
                try:
                    course_info = self.micro_course_cache(course_id)
                    course_id_list.append(course_id)
                    logger.info(f"已添加微课: {course_info.get("course_name")}, 共 {len(course_info.get("module_list"))} 集")
                except ValueError:
                    logger.error("微课不存在, 请重新输入微课链接")
        except KeyboardInterrupt:
                logger.info("用户强制终止微课输入")
        return course_id_list

    def confirm_config(self):
        if len(self.cfg.get_value(["course_list"])) > 0:
            def fetch_study_info(course_id, course_info, module_id, module_info):
                study_info = self.get_study_info(course_id, module_id, module_info.get("module_name"))
                return {
                    'course_name': course_info.get("course_name"),
                    'module_name': module_info.get("module_name"),
                    'study_percentage': study_info["study_percentage"]
                }
            tasks = []
            total_modules = 0
            for course_id, course_info in self.cfg.get_value(["course_list"]).items():
                course_module_count = len(course_info.get("module_list", {}))
                total_modules += course_module_count
                for module_id, module_info in course_info.get("module_list").items():
                    tasks.append((course_id, course_info, module_id, module_info))
            with ThreadPoolExecutor(max_workers=self.cfg.get_value(["max_workers"])) as executor:
                future_to_task = {
                    executor.submit(fetch_study_info, *task): task 
                    for task in tasks
                }
                for future in as_completed(future_to_task):
                    result = future.result()
                    format_str = f"{result['study_percentage']:.2f}%"
                    logger.info(
                        f"{format_str:<8} | " +
                        f"微课 '{result['course_name']}' " +
                        f"章节 '{result['module_name']}'"
                    )
            logger.info(f"当前需刷 {total_modules} 节课")
        else:
            return False
        logger.info(f"当前最大刷课线程数: {self.cfg.get_value(['max_workers'])}\n")
        return True

    def relogin(self):
        self.cfg.update(["cookies"], {})
        Login().try_login()