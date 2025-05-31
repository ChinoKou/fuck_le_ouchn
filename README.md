# 终身教育平台自动刷课

⚠️⚠️⚠️  
初版测试版可能存在微课未出现在个人中心的问题  
手动登录浏览器登录后点进微课即可  
最新版已修复此问题，未刷完的微课刷完后会正常出现  
⚠️⚠️⚠️

## 运行

可前往 [release](https://github.com/ChinoKou/fuck_le_ouchn/releases) 下载可执行文件  
或者前往镜像 [下载](https://chinokou.cn/download/ouchn.exe) (可能更新不及时)  

### 运行源代码
```powershell
# 克隆代码
git clone https://github.com/ChinoKou/fuck_le_ouchn.git

# 进入项目目录
cd fuck_le_ouchn

# 创建虚拟环境
python -m venv .venv

# 激活环境
.venv\Scripts\activate

# 安装依赖（使用阿里云镜像）
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple

# 运行程序
python main.py
```