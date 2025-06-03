import os
import time
from loguru import logger
from config import Config
from requests import Session
from time import sleep
from traceback import print_exc
from concurrent.futures import ThreadPoolExecutor, as_completed
from api import MicroCourse
from utils import load

LOG_DIR = "./logs"
START_TIME = time.strftime("%Y-%m-%d", time.localtime())

if not os.path.exists(LOG_DIR):
    os.mkdir(LOG_DIR)

LOG_FILE_NAME = os.path.join(LOG_DIR, f"{START_TIME}.log")
ERROR_LOG_FILE_NAME = os.path.join(LOG_DIR, f"{START_TIME}_error.log")
logger.add(LOG_FILE_NAME, rotation="5 MB", level="DEBUG")


def clone_session(original):
    new = Session()
    new.headers.update(original.headers.copy())
    return new

def main():
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

if __name__ == "__main__":
    try:
        logger.info("程序开源地址: https://github.com/ChinoKou/fuck_le_ouchn")
        main()
    except KeyboardInterrupt:
        logger.info("已手动退出")
    except Exception as e:
        logger.warning("捕获到程序运行异常！")
        logger.info("正在尝试保存报错文件...")
        try:
            with open(ERROR_LOG_FILE_NAME, "w", encoding="utf-8") as f:
                print_exc(file=f)
        except Exception as inner_e:
            logger.error(f"保存错误日志失败: {inner_e}")
    finally:
        logger.info("将在10s后退出程序...")
        sleep(10)