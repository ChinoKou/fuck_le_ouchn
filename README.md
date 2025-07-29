# 终身教育平台自动刷课

## 注意事项
电脑需要安装Chrome Edge Firefox其中一个浏览器  

## 运行
### 运行可执行文件

可前往 [release](https://github.com/ChinoKou/fuck_le_ouchn/releases/latest) 下载可执行文件  
或者前往 [镜像](https://chinokou.cn/download/ouchn.exe) 下载 (可能更新不及时,大陆可直连)  

### 运行源代码
```powershell
# Windows python 3.12+环境测试通过,其他没测试
# 克隆代码
git clone https://github.com/ChinoKou/fuck_le_ouchn.git

# 进入项目目录
cd fuck_le_ouchn

# 创建虚拟环境
python -m venv .venv

# 激活环境
.venv\Scripts\activate

# 更新pip
python -m pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple

# 安装依赖（使用阿里云镜像）
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple

# 运行程序
python main.py
```
