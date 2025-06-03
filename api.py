import random
from loguru import logger
from requests import Session
from time import sleep

class MicroCourse:
    def __init__(self, session: Session, course_id, module_id, course_name, thread_id=None):
        self.session = session
        self.course_id = course_id
        self.module_id = module_id
        self.course_name = course_name
        self.api_base_url = "https://le.ouchn.cn/api"
        self.micro_course_base_url = f"""
        {self.api_base_url}/Completion/Course/
        {self.course_id}/Module/Video/
        {self.module_id}/Session
        """.replace(" ", "").replace("\n", "").strip()
        if thread_id:
            self.thread_id = f"Thread-{thread_id}:"
        else:
            self.thread_id = ""

    def check_request_status(self, response, success_message = None):
        request_details = {
            "http_status_code": response.status_code,
            "request_url": response.url,
            "request_method": response.request.method,
            "course_name": self.course_name,
            "course_id": self.course_id,
            "response_data": response.json()
        }
        if request_details["http_status_code"] == 200:
            if success_message:
               logger.success(success_message)
            return request_details
        else:
            logger.error(f"{self.thread_id} api请求出错!\n{request_details}")
            raise Exception(request_details)

    def get_micro_course_info(self):
        url = f"{self.micro_course_base_url}/Start?Origin=ouchn"
        data = {
            "CourseId": self.course_id,
            "ModuleId": self.module_id,
            "ModuleType": "Video",
            "Origin": "ouchn"
        }
        response = self.session.post(url=url, json=data)
        request_details = self.check_request_status(
            response=response,
            success_message=f"成功获取微课 {self.course_name} 信息"
        )['response_data']['Data']
        self.session_id = request_details['SessionId']
        self.study_duration = request_details['StudyDuration']
        self.micro_course_duration = request_details['MicroCourseDuration']
        self.study_percentage = self.study_duration / self.micro_course_duration * 100
        return {
            "study_duration": self.study_duration,
            "micro_course_duration": self.micro_course_duration,
            "study_percentage": self.study_percentage
        }

    def process_micro_course(self, interrupt_data):
        url = f"{self.micro_course_base_url}/Process"
        data = {
            "CourseId": self.course_id,
            "ModuleId": self.module_id,
            "SessionId": self.session_id,
            "InterruptData": interrupt_data,
            "ModuleType": "Video",
            "Origin": "ouchn"
        }
        response = self.session.post(url=url, json=data)
        self.check_request_status(
            response=response,
            success_message=f"{self.thread_id} 成功上报视频时间戳: {interrupt_data}"
        )

    def end_micro_course(self, interrupt_data):
        url = f"{self.micro_course_base_url}/End"
        data = {
            "CourseId": self.course_id,
            "ModuleId": self.module_id,
            "SessionId": self.session_id,
            "InterruptData": interrupt_data,
            "ModuleType": "Video",
            "Origin": "ouchn"
        }
        response = self.session.post(url=url, json=data)
        self.check_request_status(response)

    def student_micro_course(self):
        url = f"{self.api_base_url}/StudentCourse/{self.course_id}"
        data = {"CourseId": self.course_id}
        response = self.session.post(url=url, json=data)
        self.check_request_status(
            response=response,
            success_message=f"{self.thread_id} 微课 {self.course_name} 学习记录上报成功"
        )

    def run(self):
        try:
            init_time = random.uniform(1, 5)
            logger.info(f"{self.thread_id} 微课 {self.course_name} 刷课线程初始化")
            logger.info(f"{self.thread_id} 微课 {self.course_name} 刷课线程在 {init_time:.1f}s 后启动")
            logger.info(f"{self.thread_id} 微课 {self.course_name} 的 CourseId 为 {self.course_id}")
            logger.info(f"{self.thread_id} 微课 {self.course_name} 的 ModuleId 为 {self.module_id}")
            self.get_micro_course_info()
            self.student_micro_course()
            sleep(init_time)    #避免频繁调用api高并发被服务器阻断,别问为什么加回来了
            for i in range(((self.micro_course_duration - self.study_duration) // 20) + 1):
                logger.info(f"{self.thread_id} 正在准备微课 {self.course_name} 信息")
                self.get_micro_course_info()
                logger.info(f"{self.thread_id} 微课 {self.course_name} 已学习 {self.study_percentage:.2f}%")
                interrupt_data = i * 20
                if interrupt_data > self.micro_course_duration:
                    interrupt_data = self.micro_course_duration
                wait_time = random.uniform(10, 11)
                logger.info(f"{self.thread_id} 微课 {self.course_name} 等待时间戳上报冷却 {wait_time:.1f}s")
                sleep(wait_time)
                logger.info(f"{self.thread_id} 微课 {self.course_name} 当前 SessionId 为 {self.session_id}")
                logger.info(f"{self.thread_id} 开始上报观看微课 {self.course_name}")
                self.process_micro_course(str(interrupt_data))
                logger.info(f"{self.thread_id} 开始刷新 SessionId")
                self.end_micro_course(str(interrupt_data))
            self.get_micro_course_info()
            logger.success("====================================================")
            logger.success(f"{self.thread_id} {self.course_name} 完成进度 {self.study_percentage:.1f}%")
            logger.success("====================================================")
        except Exception as e:
            logger.error(f"{self.thread_id} 微课 {self.course_name} 刷课线程运行出错")
            raise e