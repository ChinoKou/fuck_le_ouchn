import os
import time
import inquirer
from loguru import logger
from requests import Session
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from api import MicroCourse
from utils import load, save, prompt, getCourseInfo

class Config:
    def __init__(self):
        if not os.path.exists("config.json"):
            logger.info("配置文件不存在，正在创建...")
            save({})
        try:
            self.config = load()
        except:
            save({})
            self.config = load()
        if "cookies" not in self.config:
            self.config["cookies"] = {}

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0"
        }

        if "token" in self.config['cookies']:
            self.headers["Authorization"] = f"Bearer {self.config['cookies']['token']}"
            cookie_str = ""
            for cookie in self.config['cookies']:
                cookie_str += f"{cookie}={self.config['cookies'][cookie]}; "
            self.headers["Cookie"] = cookie_str

        self.session = Session()
        self.session.headers = self.headers

    def toLogin(self):
        edge_options = webdriver.EdgeOptions()
        edge_options.add_argument('--log-level=3')
        edge_options.add_argument('--disable-dev-shm-usage')
        edge_options.add_argument('--disable-logging')
        edge_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        driver = webdriver.Edge(options=edge_options)
        driver.get("https://le.ouchn.cn/")
        try:
            button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "login-btn")))
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
                    time.sleep(1)
                    continue
        except WebDriverException as e:
            raise e
        finally:
            driver.quit()

    def tryLogin(self):
        while True:
            response = self.session.get("https://passport.le.ouchn.cn/localApi/UserInfo")
            if response.status_code == 200:
                logger.success("登录成功")
                return True
            else:
                logger.warning("当前未登录")
                self.config['cookies'] = {}
                save(self.config)
                self.__init__()
                self.toLogin()

    def microCourseConfig(self):
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
            logger.info("当前课程列表为空，可使用默认课程列表或输入课程ID")
            courseList = prompt([
                inquirer.Checkbox(
                    name="courses",
                    message="目前可选默认课程 (按空格键选择，回车键确定)",
                    choices=[
                        f"{getCourseInfo(self.session, DEFAULT_COURSES[i])['Name']} | {DEFAULT_COURSES[i]} | {MicroCourse(self.session, DEFAULT_COURSES[i], getCourseInfo(self.session, DEFAULT_COURSES[i])['Modules'][0]['Id'], getCourseInfo(self.session, DEFAULT_COURSES[i])['Name']).GetMicroCourseInfo()['StudyPercentage']:.1f}%"for i in range(len(DEFAULT_COURSES))
                    ],
                )
            ])['courses']
            if len(courseList) == 0:
                while True:
                    course = prompt([
                        inquirer.Text(
                            name="courseId",
                            message="请输入课程ID (输入0终止输入)")
                    ])["courseId"]
                    if course == "0":
                        break
                    try:
                        getCourseInfo(self.session, course)
                        logger.info(f"已添加课程: {getCourseInfo(self.session, course)['Name']}")
                        courseList.append(f" |{course}| ")
                    except ValueError:
                        logger.error("课程不存在，请重新输入课程ID")
            try:
                for course in courseList:
                    self.config['courses'].append({"Name": getCourseInfo(self.session, course.split('|')[1].strip())['Name'], "CourseId": course.split('|')[1].strip(), "ModuleId": getCourseInfo(self.session, course.split('|')[1].strip())['Modules'][0]['Id'], "MicroCourseDuration": MicroCourse(self.session, course.split('|')[1].strip(), getCourseInfo(self.session, course.split('|')[1].strip())['Modules'][0]['Id'], getCourseInfo(self.session, course.split('|')[1].strip())).GetMicroCourseInfo()['MicroCourseDuration']})
                save(self.config)
                logger.success("课程保存成功")
            except Exception as e:
                logger.exception("课程保存失败!")
                raise e

    def run(self):
        try:
            self.tryLogin()
            self.microCourseConfig()
        except Exception as e:
            raise e
        finally:
            save(self.config)


if __name__ == "__main__":
    classconfig = Config()
    classconfig.run()