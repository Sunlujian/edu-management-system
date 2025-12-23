import os
import sys
from app import create_app
from dotenv import load_dotenv

# 确保在项目根目录
project_root = os.path.dirname(os.path.abspath(__file__))
os.chdir(project_root)

load_dotenv()
config_name = os.getenv('FLASK_CONFIG') or 'default'
app = create_app(config_name)

if __name__ == '__main__':
    print(f"工作目录: {os.getcwd()}")
    print(f"模板文件夹: {app.template_folder}")
    app.run(debug=True, host='0.0.0.0', port=5000)