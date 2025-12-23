import os
import shutil

# 项目路径
project_root = r"D:\python_codes\edu_management_system"
app_templates = os.path.join(project_root, "app", "templates")
root_templates = os.path.join(project_root, "templates")

print("修复模板路径问题...")
print(f"1. 当前app模板路径: {app_templates}")
print(f"2. Flask查找路径: {root_templates}")

# 方法1：创建符号链接
if not os.path.exists(root_templates):
    try:
        os.symlink(app_templates, root_templates, target_is_directory=True)
        print("✓ 已创建符号链接")
    except:
        # 方法2：复制文件
        shutil.copytree(app_templates, root_templates)
        print("✓ 已复制模板文件夹")
else:
    print("✓ templates文件夹已存在")

# 验证
if os.path.exists(root_templates):
    print(f"✓ 模板文件夹现在存在: {root_templates}")
else:
    print("✗ 修复失败")