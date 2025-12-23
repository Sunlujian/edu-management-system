import os
import sys
from app import create_app

# 获取项目根目录
project_root = os.path.dirname(os.path.abspath(__file__))
app_root = os.path.join(project_root, 'app')

print("=== 路径诊断 ===")
print(f"1. 项目根目录: {project_root}")
print(f"2. app目录: {app_root}")

# 检查模板目录
templates_dir = os.path.join(app_root, 'templates')
print(f"3. 模板目录: {templates_dir}")
print(f"4. 模板目录存在: {os.path.exists(templates_dir)}")

# 检查模板文件
if os.path.exists(templates_dir):
    templates_to_check = [
        'common/base.html',
        'common/index.html',
        'common/login.html',
        'common/register.html'
    ]
    
    print("\n5. 模板文件检查:")
    for template in templates_to_check:
        full_path = os.path.join(templates_dir, template)
        exists = os.path.exists(full_path)
        print(f"   {template}: {'✓ 存在' if exists else '✗ 不存在'}")
        if exists:
            print(f"     路径: {full_path}")

# 创建Flask应用测试
print("\n=== Flask应用测试 ===")
os.chdir(project_root)  # 切换到项目根目录
app = create_app()

print(f"6. Flask模板文件夹: {app.template_folder}")
print(f"7. Flask模板文件夹绝对路径: {os.path.abspath(app.template_folder)}")
print(f"8. 绝对路径存在: {os.path.exists(os.path.abspath(app.template_folder))}")

# 测试渲染
from flask import render_template_string
try:
    with app.app_context():
        result = render_template_string("<h1>Test</h1>")
        print("9. 模板引擎测试: ✓ 正常")
except Exception as e:
    print(f"9. 模板引擎测试: ✗ 异常 - {e}")