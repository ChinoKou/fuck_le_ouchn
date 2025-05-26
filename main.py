from loguru import logger
from config import Config
from requests import Session
from traceback import print_exc
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils import load
from api import MicroCourse

def clone_session(original):
    new = Session()
    new.headers.update(original.headers.copy())
    return new

def main():
    cfg = Config()
    cfg.run()
    config = load()
    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = [
            executor.submit(
                lambda c=course: MicroCourse(
                    clone_session(cfg.session),
                    c['CourseId'],
                    c['ModuleId'],
                    c['Name']
                ).run(),
            )
            for course in config['courses']
        ]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logger.error("线程执行出错")
                raise e

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("已手动退出")
    except Exception as e:
        logger.warning("捕获到程序运行异常！")
        logger.info("正在尝试保存报错文件...")
        try:
            with open("latestErrorLog.log", "w", encoding="utf-8") as f:
                print_exc(file=f)
        except Exception as inner_e:
            logger.error(f"保存错误日志失败: {inner_e}")