import os
import sys
from app import create_app

app = create_app()

print("=== Flask应用诊断 ===")
print(f"1. 模板文件夹: {app.template_folder}")
print(f"2. 模板文件夹是否存在: {os.path.exists(app.template_folder)}")

# 检查常见模板
templates_to_check = [
    'common/base.html',
    'common/index.html', 
    'common/login.html',
    'common/register.html'
]

print("\n3. 模板文件检查:")
for template in templates_to_check:
    template_path = os.path.join(app.template_folder, template)
    exists = os.path.exists(template_path)
    print(f"   {template}: {'✓ 存在' if exists else '✗ 不存在'}")

print(f"\n4. Flask DEBUG模式: {app.debug}")
print(f"5. Flask SECRET_KEY已设置: {'✓' if app.config.get('SECRET_KEY') else '✗'}")