import os
import time
from loguru import logger
from time import sleep
from traceback import print_exc
from concurrent.futures import ThreadPoolExecutor, as_completed
from api import MicroCourse
from config import Config
from utils import load, clone_session, check_micro_course_progress

VERSION  = "1.1"
LOG_DIR = "./logs"
MAX_RETRY = 3
START_TIME = time.strftime("%Y-%m-%d", time.localtime())
if not os.path.exists(LOG_DIR):
    os.mkdir(LOG_DIR)
LOG_FILE_NAME = os.path.join(LOG_DIR, f"{START_TIME}.log")
logger.add(LOG_FILE_NAME, rotation="5 MB", level="DEBUG")


def main():
    try:
        RUN_TIME = time.strftime("%Y-%m-%d", time.localtime())
        ERROR_LOG_FILE_NAME = os.path.join(LOG_DIR, f"{RUN_TIME}_error.log")
        cfg = Config()
        cfg.load_config()
        config = load()
        with ThreadPoolExecutor(max_workers=config['max_workers']) as executor:
            futures = [
                executor.submit(
                    lambda c=course, idx=idx: MicroCourse(
                        clone_session(cfg.session),
                        c['course_id'],
                        c['module_id'],
                        c['course_name'],
                        idx + 1
                    ).run(),
                )
                for idx, course in enumerate(config['courses'])
            ]
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error("线程执行出错")
                    raise e
        if not check_micro_course_progress():
            logger.error("仍有微课未刷完,尝试重新启动程序!")
            raise Exception("微课未刷完,重新启动程序")
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except Exception as e:
        logger.warning("捕获到程序运行异常！")
        logger.info("正在尝试保存报错日志...")
        try:
            with open(ERROR_LOG_FILE_NAME, "w", encoding="utf-8") as f:
                print_exc(file=f)
            logger.success("错误日志保存成功")
        except Exception as inner_e:
            logger.error(f"保存错误日志失败: {inner_e}")
        finally:
            raise e

if __name__ == "__main__":
    try:
        logger.info("程序开源地址: https://github.com/ChinoKou/fuck_le_ouchn")
        logger.info(f"当前程序版本: {VERSION}")
        retries = 0
        while True:
            try:
                if retries > 0:
                    logger.warning(f"第 {retries} 次重启程序!")
                main()
                break
            except KeyboardInterrupt:
                logger.info("已手动退出")
                break
            except Exception as e:
                if retries >= MAX_RETRY:
                    logger.error("重试次数过多,若有bug,请提交issue!")
                    break
                logger.info(f"将在10s后重新启动({retries + 1}/{MAX_RETRY})...")
                sleep(10)
                retries += 1
        logger.info("将在10s后退出程序...")
        sleep(10)
    except KeyboardInterrupt:
        logger.info("用户强制终止")