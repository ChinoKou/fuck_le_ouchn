import inquirer
from loguru import logger
from time import sleep
from sys import exit
from traceback import format_exc
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import Config
from api import *

VERSION  = "2.0"

def main():
    while True:
        cfg = Config()
        Login().try_login()
        ouchn_utils = OuchnUtils()
        menu_choices = ["配置刷课信息", "开始刷课", "配置最大线程数", "重新登录", "清理刷完课程", "恢复出厂设置", "退出"]
        if cfg.get_value(["debug"]):
            menu_choices.append("输出debug日志")
        try:
            func_choice = prompt([
                inquirer.List(
                    name="menu",
                    message="主菜单,请选择接下来的操作",
                    choices=menu_choices
                )
            ])["menu"]
            if func_choice == "配置刷课信息":
                if not ouchn_utils.confirm_config():
                    ouchn_utils.micro_course_config()
                elif prompt([
                    inquirer.Confirm(
                        name="confirm",
                        message="已存在以上刷课信息，是否要重新配置？",
                        default=True
                    )
                ])["confirm"]:
                    logger.info("重新配置刷课信息")
                    ouchn_utils.micro_course_config()
            elif func_choice == "开始刷课":
                if not ouchn_utils.confirm_config():
                    logger.warning("未配置刷课信息或刷课信息有误")
                    continue
                elif not prompt([
                    inquirer.Confirm(
                        name="confirm",
                        message="请确认是否以当前刷课配置启动刷课",
                        default=True
                    )
                ])["confirm"]:
                    continue
                logger.info("开始刷课")
                with ThreadPoolExecutor(max_workers=cfg.config["max_workers"]) as executor:
                    futures = [
                        executor.submit(
                            MicroCourse(course_id, module_id, module_info["module_name"]).run,
                        )
                        for course_id, course_info in cfg.get_value(["course_list"]).items()
                        for module_id, module_info in course_info["module_list"].items()
                    ]
                    for future in as_completed(futures):
                        try:
                            future.result()
                        except Exception as e:
                            logger.error("线程执行出错")
                            raise e
                ouchn_utils.check_micro_course_progress()
            elif func_choice == "配置最大线程数":
                logger.info("配置最大线程数")
                cfg.max_workers_config()
            elif func_choice == "重新登录":
                logger.info("正在重新登录")
                ouchn_utils.relogin()
            elif func_choice == "清理刷完课程":
                logger.info("清理刷完课程")
                ouchn_utils.check_micro_course_progress()
            elif func_choice == "恢复出厂设置":
                logger.info("恢复出厂设置")
                cfg.reset()
                return main()
            elif func_choice == "输出debug日志":
                get_logger(debug=True)
            elif func_choice == "退出":
                logger.info("退出")
                exit()
        except KeyboardInterrupt:
            continue
        except Exception as e:
            logger.error("捕获到程序运行异常！")
            logger.error(f"\n{format_exc()}")
            # logger.exception()
            break

if __name__ == "__main__":
    try:
        get_logger()
        logger.info("程序开源地址: https://github.com/ChinoKou/fuck_le_ouchn")
        logger.info(f"当前程序版本: {VERSION}")
        main()
        logger.info("将在10s后退出程序...")
        sleep(10)
    except KeyboardInterrupt:
        logger.info("用户强制终止")