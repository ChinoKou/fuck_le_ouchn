import os
import json
import httpx
from loguru import logger


class HttpClient:
    def __init__(self):
        from config import Config
        cfg = Config()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" +
            " (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0"
        }
        if "token" in cfg.get_value(["cookies"]):
            headers["Authorization"] = f"Bearer {cfg.get_value(["cookies", "token"])}"
            headers["Cookie"] = "; ".join([f"{k}={v}" for k, v in cfg.get_value(["cookies"]).items()])
        self.client = httpx.Client(http2=True)
        if cfg.get_value(["debug"]):
            self.client = httpx.Client(http2=True, verify=False)
        self.client.headers = headers

    def check_response(self, response: httpx.Response, data=None, json_data=None, params=None):
        request_details = {
            "http_status_code": response.status_code,
            "request_url": response.url,
            "request_method": response.request.method,
        }
        if data:
            request_details["request_data"] = data
        elif json_data:
            request_details["request_json_data"] = json_data
        elif params:
            request_details["request_params"] = params
        request_details["response_body"] = response.text
        if request_details["http_status_code"] == 200:
            return True
        else:
            logger.debug(f"请求出错!\n{request_details}")
            return False

    def post(self, url, data=None, json_data=None, params=None, retry_times=3):
        try:
            response = self.client.post(url, data=data, json=json_data, params=params)
            status = self.check_response(response, data, json_data, params)
            return response, status
        except (
            httpx.ConnectTimeout,
            httpx.ConnectError,
            httpx.TimeoutException,
            httpx.ReadError,
            httpx.ReadTimeout,
            httpx.ConnectError,
            httpx.RemoteProtocolError,
            httpx.LocalProtocolError,
            json.decoder.JSONDecodeError
        ) as e:
            logger.error(e)
            logger.error("网络连接超时 / JSON解析错误")
            if retry_times <= 0:
                raise e
            logger.info("请求重试")
            return self.post(url, data, json_data, params, retry_times-1)
        except Exception as e:
            raise e

    def get(self, url, params=None, retry_times=3):
        try:
            response = self.client.get(url, params=params)
            status = self.check_response(response, params=params)
            return response, status
        except (
            httpx.ConnectTimeout,
            httpx.ConnectError,
            httpx.TimeoutException,
            httpx.ReadError,
            httpx.ReadTimeout,
            httpx.ConnectError,
            httpx.RemoteProtocolError,
            httpx.LocalProtocolError,
            json.decoder.JSONDecodeError
        ) as e:
            logger.error(e)
            logger.error("网络连接超时 / JSON解析错误")
            if retry_times <= 0:
                raise e
            logger.info("请求重试")
            return self.post(url, params, retry_times-1)
        except Exception as e:
            raise e

def prompt(data):
    import inquirer
    data = inquirer.prompt(data)
    if data is None:
        raise KeyboardInterrupt
    return data

def get_web_driver():
    from config import Config
    from selenium import webdriver
    from requests.exceptions import ConnectionError
    from webdrivermanager_cn import ChromeDriverManagerAliMirror
    from webdrivermanager_cn import GeckodriverManagerAliMirror
    from webdriver_manager.microsoft import EdgeChromiumDriverManager
    from selenium.common.exceptions import WebDriverException
    from selenium.webdriver.edge.service import Service as EdgeService
    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.webdriver.firefox.service import Service as FirefoxService

    logger.info("若是初次运行可能耗时较长")
    cfg = Config()
    browser_paths = {
        "Chrome": [
            os.path.join(os.getenv("PROGRAMFILES"), "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(os.getenv("LOCALAPPDATA"), "Google", "Chrome", "Application", "chrome.exe")
        ],
        "Edge": [
            os.path.join(os.getenv("PROGRAMFILES"), "Microsoft", "Edge", "Application", "msedge.exe"),
            os.path.join(os.getenv("PROGRAMFILES(X86)", ""), "Microsoft", "Edge", "Application", "msedge.exe"),
            os.path.join(os.getenv("LOCALAPPDATA"), "Microsoft", "Edge", "Application", "msedge.exe")
        ],
        "Firefox": [
            os.path.join(os.getenv("PROGRAMFILES"), "Mozilla Firefox", "firefox.exe"),
            os.path.join(os.getenv("LOCALAPPDATA"), "Mozilla Firefox", "firefox.exe")
        ]
    }
    browser_check = {
        "Chrome": lambda: any(os.path.exists(p) for p in browser_paths["Chrome"]),
        "Edge": lambda: any(os.path.exists(p) for p in browser_paths["Edge"]),
        "Firefox": lambda: any(os.path.exists(p) for p in browser_paths["Firefox"])
    }
    web_drivers = [
        ("Chrome", webdriver.Chrome, ChromeService),
        ("Firefox", webdriver.Firefox, FirefoxService),
        ("Edge", webdriver.Edge, EdgeService)
    ]
    driver_managers = {
        "Chrome": ChromeDriverManagerAliMirror,
        "Firefox": GeckodriverManagerAliMirror,
        "Edge": EdgeChromiumDriverManager
    }
    for name, driver_class, service_class in web_drivers:
        if not browser_check[name]() and cfg.get_value(["use_browser_check"]) == True:
            logger.warning(f"{name} 浏览器未安装，跳过初始化")
            continue
        try:
            logger.info(f"尝试调用 {name}")
            driver_options = {
                "Chrome": webdriver.ChromeOptions,
                "Firefox": webdriver.FirefoxOptions,
                "Edge": webdriver.EdgeOptions
            }[name]()
            common_options = [
                "--log-level=3",
                "--disable-dev-shm-usage",
                "--disable-logging",
                "--no-sandbox",
                "--disable-gpu"
            ]
            for option in common_options:
                driver_options.add_argument(option)
            if name != "Firefox":
                driver_options.add_experimental_option("excludeSwitches", ["enable-logging"])
            if name == "Edge":
                driver = driver_class(
                    service=service_class(driver_managers[name](
                        url="https://msedgedriver.microsoft.com/",
                        latest_release_url="https://msedgedriver.microsoft.com/LATEST_RELEASE"
                    ).install()),
                    options=driver_options
                )
            else:
                driver = driver_class(
                    service=service_class(driver_managers[name]().install()),
                    options=driver_options
                )
            logger.success(f"调用浏览器 {name}")
            return driver
        except (WebDriverException, ValueError, ConnectionError) as e:
            logger.warning(f"{name} 驱动初始化失败")
            continue
        except Exception as e:
            raise e
    logger.error("未找到可用的浏览器驱动")
    raise RuntimeError("未找到可用的浏览器驱动")

def get_logger(debug=False):
    from sys import stderr
    from time import strftime, localtime
    LOG_DIR = "./logs"
    START_TIME = strftime("%Y-%m-%d", localtime())
    if not os.path.exists(LOG_DIR):
        os.mkdir(LOG_DIR)
    LOG_FILE_NAME = os.path.join(LOG_DIR, f"{START_TIME}.log")
    logger.remove()
    if not debug:
        logger.add(
            stderr, level="INFO",
            format="<green>{time:MM-DD HH:mm:ss}</green> | <level>{level:<8}</level> | <level>{message}</level>"
        )
    else:
        logger.add(
            stderr, level="DEBUG",
            format="<green>{time:MM-DD HH:mm:ss}</green> | <level>{level:<8}</level> | <level>{message}</level>"
        )
    logger.add(
        LOG_FILE_NAME, rotation="5 MB", level="DEBUG",
        format="<green>{time:MM-DD HH:mm:ss}</green> | <level>{level:<8}</level> | <level>{message}</level>"
    )

if __name__ == "__main__":
    get_logger()
    logger.info("info")
    logger.debug("debug")