import random
from tqdm import tqdm
from loguru import logger
from time import sleep

class MicroCourse:
    def __init__(self, session, course_id, module_id, course_name, thread_id=None):
        self.session = session
        self.course_id = course_id
        self.module_id = module_id
        self.course_name = course_name
        self.thread_id = f"Thread-{thread_id}:"

    def get_micro_course_info(self):
        url = f"https://le.ouchn.cn/api/Completion/Course/{self.course_id}/Module/Video/{self.module_id}/Session/Start?Origin=ouchn"
        data = {
            "CourseId": self.course_id,
            "ModuleId": self.module_id,
            "ModuleType": "Video",
            "Origin": "ouchn"
        }
        response = self.session.post(url=url, json=data)
        if response.status_code == 200:
            logger.success(f"成功获取微课 {self.course_name} 信息")
        response = response.json()
        self.session_id = response['Data']['SessionId']
        self.study_duration = response['Data']['StudyDuration']
        self.micro_course_duration = response['Data']['MicroCourseDuration']
        self.study_percentage = self.study_duration / self.micro_course_duration * 100
        return {
            "study_duration": self.study_duration,
            "micro_course_duration": self.micro_course_duration,
            "study_percentage": self.study_percentage
        }

    def process_micro_course(self, interrupt_data):
        url = f"https://le.ouchn.cn/api/Completion/Course/{self.course_id}/Module/Video/{self.module_id}/Session/Process"
        data = {
            "CourseId": self.course_id,
            "ModuleId": self.module_id,
            "SessionId": self.session_id,
            "InterruptData": interrupt_data,
            "ModuleType": "Video",
            "Origin": "ouchn"
        }
        response = self.session.post(url=url, json=data)
        status_code = response.status_code
        response = response.json()
        if status_code == 200:
            logger.success(f"{self.thread_id} 成功上报视频时间戳: {interrupt_data}")
            pass
        else:
            logger.error(f"{self.thread_id} 上报视频时间戳失败: Http {status_code} error")
            logger.error(f"{self.thread_id} status_code: {response['status']}")
            logger.error(f"{self.thread_id} message: {response['title']}")
            logger.error(f"{self.thread_id} errors: {response['errors']['$']}")
            raise Exception(f"{self.thread_id} {self.course_name} - {self.course_id} - "+
                            f"上报视频时间戳失败:\n{status_code} {response['title']}")

    def end_micro_course(self, interrupt_data):
        url = f"https://le.ouchn.cn/api/Completion/Course/{self.course_id}/Module/Video/{self.module_id}/Session/End"
        data = {
            "CourseId": self.course_id,
            "ModuleId": self.module_id,
            "SessionId": self.session_id,
            "InterruptData": interrupt_data,
            "ModuleType": "Video",
            "Origin": "ouchn"
        }
        response = self.session.post(url=url, json=data)
        if response.status_code == 200:
            pass
        else:
            raise

    def student_micro_course(self):
        url = f"https://le.ouchn.cn/api/StudentCourse/{self.course_id}"
        data = {"CourseId": self.course_id}
        response = self.session.post(url=url, json=data)
        if response.status_code == 200:
            logger.success(f"{self.thread_id} 微课 {self.course_name} 学习记录上报成功")
        else:
            raise

    def run(self):
        try:
            init_time = random.randint(1, 2)
            logger.info(f"{self.thread_id} 微课 {self.course_name} 刷课线程初始化")
            logger.info(f"{self.thread_id} 微课 {self.course_name} 将在 {init_time:.1f}s 后开刷")
            logger.info(f"{self.thread_id} 微课 {self.course_name} 的 CourseId 为 {self.course_id}")
            logger.info(f"{self.thread_id} 微课 {self.course_name} 的 ModuleId 为 {self.module_id}")
            self.get_micro_course_info()
            self.student_micro_course()
            self.last_study_duration = self.study_duration
            sleep(init_time)
            for i in range(((self.micro_course_duration - self.study_duration) // 20) + 1):
                logger.info(f"{self.thread_id} 正在准备微课 {self.course_name} 信息")
                self.get_micro_course_info()
                logger.info(f"{self.thread_id} 微课 {self.course_name} 已学习 {self.study_percentage:.2f}%")
                self.last_study_duration = self.study_duration
                interrupt_data = i * 20
                if interrupt_data > self.micro_course_duration:
                    interrupt_data = self.micro_course_duration
                wait_time = random.randint(10, 11)
                logger.info(f"{self.thread_id} 微课 {self.course_name} 等待时间戳上报冷却 {wait_time}s")
                sleep(wait_time)
                logger.info(f"{self.thread_id} 微课 {self.course_name} 当前 SessionId 为 {self.session_id}")
                logger.info(f"{self.thread_id} 开始上报观看微课 {self.course_name}")
                self.process_micro_course(str(interrupt_data))
                logger.info(f"{self.thread_id} 开始刷新 SessionId")
                self.end_micro_course(str(interrupt_data))
            logger.success(f"{self.thread_id} {self.course_name} 完成进度 {self.study_percentage:.1f}%")
        except Exception as e:
            logger.error(f"{self.thread_id} 微课 {self.course_name} 运行出错")
            raise e