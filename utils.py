import json

def save(data: dict):
    with open("config.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(data, indent=4, ensure_ascii=False))
    return

def load() -> dict:
    with open("config.json", "r", encoding="UTF-8") as f:
        data = json.loads(f.read())
    return data

def prompt(data):
    import inquirer
    return inquirer.prompt(data)

def get_course_info(session, course_id):
    if course_id == "":
        raise ValueError("课程ID不能为空")
    response = session.get(url=f"https://le.ouchn.cn/api/Course/{course_id}/MicroCourse/Details")
    if response.status_code == 500:
        raise ValueError("课程ID错误")
    return response.json()['Data']