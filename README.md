# 终身教育平台自动刷课

⚠️⚠️⚠️
目前仍在开发中，项目有诸多bug，能用，但有很多问题
⚠️⚠️⚠️

## 课程ID配置说明

代码内预置16课程ID, 若要手动添加课程ID, 请按照以下步骤操作：

### 手动获取课程ID
1. 在浏览器中打开目标课程页面
2. 复制地址栏中的课程链接
3. 按以下格式提取课程ID：

**地址格式**：
```
https://le.ouchn.cn/courseDetails/[课程ID]/
```

**示例**：
```bash
# 单层级课程地址
课程链接: https://le.ouchn.cn/courseDetails/4784ff5f-8dc4-11ee-bd5f-fa163ea9b0ea
课程ID: 4784ff5f-8dc4-11ee-bd5f-fa163ea9b0ea

# 多层级课程地址
课程链接: https://le.ouchn.cn/courseDetails/4784ff5f-8dc4-11ee-bd5f-fa163ea9b0ea/a84sf5f-8dc4-11ee-bd5f-fa163ea410af
课程ID: 4784ff5f-8dc4-11ee-bd5f-fa163ea9b0ea
```

## 环境配置与使用指南

### Windows
```powershell
# 创建虚拟环境
python -m venv .venv

# 激活环境
.venv\Scripts\activate

# 安装依赖（使用阿里云镜像）
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple

# 运行程序
python main.py
```