import os
import json
import inquirer
from loguru import logger
from utils import prompt


class Config:
    def __init__(self):
        self.config_version = "2.0.0"
        self.on_load()

    def on_load(self):
        if os.path.exists("ouchn_config.json"):
            self.load()
            logger.debug("配置文件加载成功")
            if self.config.get("version") != self.config_version:
                logger.warning("配置文件版本不匹配，建议使用 '恢复出厂设置' 重新配置")
        else:
            self.config = {}
            self.config["version"] = self.config_version
            self.config["max_workers"] = 16
            self.config["use_browser_check"] = True
            self.config["debug"] = False
            self.config["cookies"] = {}
            self.config["course_list"] = {}
            self.save()
            self.load()

    def load(self):
        with open("ouchn_config.json", "r", encoding="UTF-8") as f:
            self.config = json.loads(f.read())

    def save(self):
        with open("ouchn_config.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(self.config, indent=4, ensure_ascii=False))
        return

    def get_value(self, keys: list):
        data = self.config
        for key in keys:
            data = data.get(key)
        return data

    def update(self, keys: list, value):
        self.load()
        data = self.config
        for key in keys[:-1]:
            if key not in data or not isinstance(data[key], dict):
                data[key] = {}
            data = data[key]
        data[keys[-1]] = value
        self.save()
        self.load()

    def max_workers_config(self):
        logger.info(f"当前最大线程数：{self.get_value(["max_workers"])}")
        max_workers = int(prompt([inquirer.Text(
            name="max_workers",
            message="配置网络请求时最大线程数(默认16)",
            default=16,
            validate=lambda _, x: x.isdigit() or "请输入数字"
        )])["max_workers"])
        self.update(["max_workers"], max_workers)

    def reset(self):
        os.remove("ouchn_config.json")
        self.on_load()

if __name__ == "__main__":
    Config()
