import os
import inquirer
from time import sleep
from loguru import logger
from requests import Session
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support import expected_conditions as EC
from utils import load, save, prompt, get_micro_course_info, get_web_driver

class Config:
    def __init__(self):
        try:
            self.config = load()
            self.first_run = False
        except:
            self.first_run = True
            logger.info("配置文件不存在，正在创建...")
            save({})
            self.config = load()
        if "max_workers" not in self.config:
            self.config['max_workers'] = int(prompt([inquirer.Text(
                name="max_workers",
                message="请输入刷课最大线程数(默认16)",
                default=16,
                validate=lambda _, x: x.isdigit() or "请输入数字"
            )])['max_workers'])
        if "cookies" not in self.config:
            self.config["cookies"] = {}

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" +
            " (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0"
        }

        if "token" in self.config['cookies']:
            self.headers["Authorization"] = f"Bearer {self.config['cookies']['token']}"
            cookie_str = ""
            for cookie in self.config['cookies']:
                cookie_str += f"{cookie}={self.config['cookies'][cookie]}; "
            self.headers["Cookie"] = cookie_str

        self.session = Session()
        self.session.headers = self.headers

        self.courses_cache = []

    def to_login(self):
        driver = get_web_driver()
        driver.get("https://le.ouchn.cn/")
        try:
            button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "login-btn"))
            )
            button.click()

            while True:
                logger.info("正在等待登录...")
                cookies = driver.get_cookies()
                cookie_str = ""
                for cookie in cookies:
                    self.config['cookies'][cookie['name']] = cookie['value']
                    cookie_str += cookie['name'] + "=" + cookie['value'] + ";"
                if "token" in self.config['cookies']:
                    self.headers['Authorization'] = "Bearer " + self.config['cookies']['token']
                    self.headers['Cookie'] = cookie_str
                    self.session.headers = self.headers
                    save(self.config)
                    break
                else:
                    sleep(2)
                    continue
        except WebDriverException as e:
            raise e
        finally:
            driver.quit()

    def try_login(self):
        while True:
            response = self.session.get("https://passport.le.ouchn.cn/localApi/UserInfo")
            if response.status_code == 200:
                logger.success("登录成功")
                return True
            else:
                logger.warning("当前未登录或登录过期")
                self.config['cookies'] = {}
                save(self.config)
                self.__init__()
                self.to_login()

    def micro_course_cache(self, course_id):
        for course in self.courses_cache:
            if course_id == course['course_id']:
                return course
        self.courses_cache.append(get_micro_course_info(self.session, course_id))
        return self.micro_course_cache(course_id)

    def micro_course_config(self):
        DEFAULT_COURSES = (
            "f020ff29-b591-96cc-96c8-74f889692a42",
            "549d8e42-2fb8-f7b6-9067-4b1bd7a7b6f7",
            "3663c995-570c-89d9-1691-d8de33bce240",
            "a1311156-9648-f74e-d619-afee6656e242",
            "5e7a1b64-0346-4db9-aff3-e3b2bf8a13ff",
            "c8e0d104-9af8-4373-950b-d557eff5fa2e",
            "85724f6b-f94a-4eda-b876-b70520acb86c",
            "729b5cca-ef0c-4cca-a3b9-45f9970495c6",
            "baf8210e-c6cb-4438-88eb-96a17f3d4910",
            "7647e35f-2f67-4fc3-b77c-5f0ae24fd320",
            "a123cfc5-0901-4b19-aeb4-552e01dc3fba",
            "034bc10d-dce2-4b9a-9735-0cb914424f80",
            "8b78c32a-1409-4004-9062-145d553a81af",
            "3de288dc-55dc-43c6-904b-0688f628267f",
            "07832e0f-e752-4ab9-83d7-11ca1edf9ead",
            "cc74f1ec-4b12-4e54-b439-2718a03d6c89"
        )

        if "courses" not in self.config:
            self.config['courses'] = []
        if len(self.config['courses']) == 0 or self.config['courses'] == "null":
            try:
                logger.info("当前微课列表为空，可使用默认微课列表或输入微课链接")
                courses: list[str] = prompt([
                    inquirer.Checkbox(
                        name="courses",
                        message="目前可选默认微课 (按空格键选择, 回车键确定, 可不选直接回车)",
                        choices=[
                            f"""{
                            self.micro_course_cache(DEFAULT_COURSES[i])['course_name']} | {
                            DEFAULT_COURSES[i]} | {
                            self.micro_course_cache(DEFAULT_COURSES[i])['study_percentage']:.1f}%"""
                            for i in range(len(DEFAULT_COURSES))
                        ]
                    )
                ])['courses']
                course_id_list = []
                for course in courses:
                    course_id_list.append(course.split('|')[1].strip())
                if len(course_id_list) == 0:
                    logger.info("未选微课, 手动输入微课链接")
                    while True:
                        course_link = prompt([
                            inquirer.Text(
                                name="course_link",
                                message="请输入微课链接 (不输入直接回车即退出输入)"
                            )
                        ])["course_link"]
                        if course_link == "":
                            break
                        course_id = course_link.split('/')[4]
                        try:
                            self.micro_course_cache(course_id)
                            logger.info(f"已添加微课: {self.micro_course_cache(course_id)['course_name']}")
                            course_id_list.append(course_id)
                        except ValueError:
                            logger.error("微课不存在, 请重新输入微课链接")
            except TypeError:
                    logger.info("用户强制终止微课输入")
            try:
                for course_id in course_id_list:
                    if self.micro_course_cache(course_id)['study_percentage'] >= 100:
                        if prompt([
                            inquirer.Confirm(
                                name="confirm",
                                message=f"""
                                微课'{self.micro_course_cache(course_id)['course_name']}'
                                已刷完，是否仍需保存?
                                """.replace(" ", "").replace("\n", "").strip(),
                                default=False
                            )
                        ])['confirm'] == False:
                            logger.info(f"跳过微课 {self.micro_course_cache(course_id)['course_name']}")
                            continue
                    self.config['courses'].append(self.micro_course_cache(course_id))
                save(self.config)
                logger.success("微课保存成功")
            except Exception as e:
                logger.error("微课保存失败!")
                raise e
        else:
            logger.info("正在检查微课完成进度")
            new_courses = []
            for course in self.config['courses']:
                course_info = self.micro_course_cache(course['course_id'])
                if course_info['study_percentage'] >= 100:
                    logger.info(f"微课 {course_info['course_name']} 已刷完, 从配置文件剔除")
                    continue
                new_courses.append(course_info)
            self.config['courses'] = new_courses
            save(self.config)


    def load_config(self):
        if self.first_run == False:
            run_info = prompt([
                inquirer.List(
                    name="on_start",
                    message="选择要进行的操作(尽管保留登录信息仍可能需要重新登录)",
                    choices=[
                        "延续上次配置运行",
                        "保留登录信息重新配置",
                        "全新启动"
                    ],
                    default="延续上次配置运行"
                )
            ])['on_start']
            if run_info == "延续上次配置运行":
                logger.info("使用上次的配置文件")
                self.try_login()
                self.micro_course_config()
            elif run_info == "保留登录信息重新配置":
                self.try_login()
                logger.info("重新配置课程")
                self.config['courses'] = []
                self.micro_course_config()
                save(self.config)
            elif run_info == "全新启动":
                logger.info("全新启动")
                os.remove("config.json")
                Config().load_config()
        else:
            self.try_login()
            self.micro_course_config()