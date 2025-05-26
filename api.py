import time
import random
from loguru import logger
from tqdm import tqdm

class MicroCourse:
    def __init__(self, session, CourseId, ModuleId, CourseName):
        self.session = session
        self.CourseId = CourseId
        self.ModuleId = ModuleId
        self.CourseName = CourseName

    def GetMicroCourseInfo(self):
        url = f"https://le.ouchn.cn/api/Completion/Course/{self.CourseId}/Module/Video/{self.ModuleId}/Session/Start?Origin=ouchn"
        data = {
            "CourseId": self.CourseId,
            "ModuleId": self.ModuleId,
            "ModuleType": "Video",
            "Origin": "ouchn"
        }
        response = self.session.post(url=url, json=data).json()
        self.SessionId = response['Data']['SessionId']
        self.StudyDuration = response['Data']['StudyDuration']
        self.MicroCourseDuration = response['Data']['MicroCourseDuration']
        return {
            "StudyDuration": self.StudyDuration,
            "MicroCourseDuration": self.MicroCourseDuration,
            "StudyPercentage": self.StudyDuration / self.MicroCourseDuration * 100
        }

    def ProcessMicroCourse(self, InterruptData):
        url = f"https://le.ouchn.cn/api/Completion/Course/{self.CourseId}/Module/Video/{self.ModuleId}/Session/Process"
        data = {
            "CourseId": self.CourseId,
            "ModuleId": self.ModuleId,
            "SessionId": self.SessionId,
            "InterruptData": InterruptData,
            "ModuleType": "Video",
            "Origin": "ouchn"
        }
        response = self.session.post(url=url, json=data)
        if response.status_code == 200:
            # logger.success(f"成功上报视频时间戳: {InterruptData}")
            pass
        else:
            logger.error(f"上报视频时间戳失败: Http {response.status_code} error")
            response = response.json()
            logger.error(f"status_code: {response['status']}")
            logger.error(f"message: {response['title']}")
            logger.error(f"errors: {response['errors']['$']}")

    def EndMicroCourse(self, InterruptData):
        url = f"https://le.ouchn.cn/api/Completion/Course/{self.CourseId}/Module/Video/{self.ModuleId}/Session/End"
        data = {
            "CourseId": self.CourseId,
            "ModuleId": self.ModuleId,
            "SessionId": self.SessionId,
            "InterruptData": InterruptData,
            "ModuleType": "Video",
            "Origin": "ouchn"
        }
        response = self.session.post(url, json=data)
        if response.status_code == 200:
            pass
        else:
            raise

    def run(self):
        self.GetMicroCourseInfo()
        self.LastStudyDuration = self.StudyDuration
        with tqdm(total=self.MicroCourseDuration - self.StudyDuration, desc=f"当前刷课: {self.CourseName}", unit="秒") as pbar:
            for i in range(((self.MicroCourseDuration - self.StudyDuration) // 20) + 1):
                self.GetMicroCourseInfo()
                Duration = self.StudyDuration - self.LastStudyDuration
                if Duration > 10:
                    pbar.update(Duration)
                self.LastStudyDuration = self.StudyDuration
                InterruptData = i * 20
                if InterruptData > self.MicroCourseDuration:
                    InterruptData = self.MicroCourseDuration
                if self.StudyDuration == self.MicroCourseDuration:
                    logger.success(f"完成")
                    break
                time.sleep(random.randint(10, 11))
                self.ProcessMicroCourse(str(InterruptData))
                self.EndMicroCourse(str(InterruptData))