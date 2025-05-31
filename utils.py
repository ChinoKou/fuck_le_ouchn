def save(config):
    import json
    with open("config.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(config, indent=4, ensure_ascii=False))
    return

def load():
    import json
    with open("config.json", "r", encoding="UTF-8") as f:
        return json.loads(f.read())

def prompt(data):
    import inquirer
    return inquirer.prompt(data)

def get_micro_course_info(session, course_id):
    from api import MicroCourse
    if course_id == "":
        raise ValueError("课程ID不能为空")
    response = session.get(url=f"https://le.ouchn.cn/api/Course/{course_id}/MicroCourse/Details")
    if response.status_code == 500:
        raise ValueError("课程ID错误")
    elif response.status_code == 200:
        response = response.json()['Data']
        course_info = {}
        course_info['course_name'] = response['Name']
        course_info['course_id'] = course_id
        course_info['module_id'] = response['Modules'][0]['Id']
        study_info = MicroCourse(
            session,
            course_id,
            course_info['module_id'],
            course_info['course_name']
        ).get_micro_course_info()
        for key in study_info.keys():
            course_info[key] = study_info[key]
    else:
        raise
    return course_info

def get_web_driver():
    from loguru import logger
    from selenium import webdriver
    from requests.exceptions import ConnectionError
    from webdrivermanager_cn import ChromeDriverManagerAliMirror
    from webdrivermanager_cn import GeckodriverManagerAliMirror
    from webdriver_manager.microsoft import EdgeChromiumDriverManager
    from selenium.common.exceptions import WebDriverException
    from selenium.webdriver.edge.service import Service as EdgeService
    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.webdriver.firefox.service import Service as FirefoxService

    web_drivers = [
        ('Chrome', webdriver.Chrome, ChromeService),
        ('Firefox', webdriver.Firefox, FirefoxService),
        ('Edge', webdriver.Edge, EdgeService)
    ]
    driver_managers = {
        'Chrome': ChromeDriverManagerAliMirror,
        'Firefox': GeckodriverManagerAliMirror,
        'Edge': EdgeChromiumDriverManager
    }
    for name, driver_class, service_class in web_drivers:
        try:
            logger.info(f"尝试调用 {name}")
            driver_options = {
                'Chrome': webdriver.ChromeOptions,
                'Firefox': webdriver.FirefoxOptions,
                'Edge': webdriver.EdgeOptions
            }[name]()
            common_options = [
                '--log-level=3',
                '--disable-dev-shm-usage',
                '--disable-logging',
                '--no-sandbox',
                '--disable-gpu'
            ]
            for option in common_options:
                driver_options.add_argument(option)
            if name != 'Firefox':
                driver_options.add_experimental_option('excludeSwitches', ['enable-logging'])
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