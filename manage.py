import os
import click
from datetime import date
from app import create_app, db
from app.models import User, Department, Teacher, Student, Course

app = create_app()

@click.group()
def cli():
    """教务管理系统管理工具"""
    pass

@cli.command()
def init():
    """初始化数据库"""
    with app.app_context():
        click.echo("正在创建数据库表...")
        db.create_all()
        click.echo("数据库表创建完成！")
        
        dept = Department(
            dept_id='CS001',
            dept_name='计算机科学与技术系',
            phone='010-62780000'
        )
        db.session.add(dept)
        db.session.commit()
        click.echo("创建默认系部: 计算机科学与技术系")

@cli.command()
@click.option('--username', prompt=True, help='管理员用户名')
@click.option('--email', prompt=True, help='管理员邮箱')
@click.password_option(help='管理员密码')
def create_admin(username, email, password):
    """创建管理员账户"""
    with app.app_context():
        admin = User(
            username=username,
            email=email,
            role='admin'
        )
        admin.set_password(password)
        
        db.session.add(admin)
        db.session.commit()
        click.echo(f"管理员 {username} 创建成功！")

@cli.command(name='sample-data')
def sample_data():
    """创建示例数据"""
    with app.app_context():
        click.echo("正在创建示例数据...")
        
        try:
            # 1. 系部
            dept = Department.query.get('CS001')
            if dept is None:
                dept = Department(
                    dept_id='CS001',
                    dept_name='计算机科学与技术系',
                    phone='010-62780000'
                )
                db.session.add(dept)
                click.echo("✓ 创建系部: CS001")
            else:
                click.echo("✓ 系部已存在: CS001")
            
            # 2. 教师
            teacher = Teacher.query.get('T001')
            if teacher is None:
                teacher = Teacher(
                    teacher_id='T001',
                    name='张教授',
                    gender='男',
                    hire_date=date(2010, 9, 1),
                    dept_id='CS001',
                    title='教授',
                    specialty='人工智能'
                )
                db.session.add(teacher)
                click.echo("✓ 创建教师: T001")
            else:
                click.echo("✓ 教师已存在: T001")
            
            # 3. 教师用户
            teacher_user = User.query.filter_by(username='T001').first()
            if teacher_user is None:
                teacher_user = User(
                    username='T001',
                    email='teacher001@university.edu',
                    role='teacher'
                )
                teacher_user.set_password('teacher123')
                teacher.user = teacher_user
                db.session.add(teacher_user)
                click.echo("✓ 创建教师用户: T001")
            else:
                click.echo("✓ 教师用户已存在: T001")
            
            # 4. 更新系主任
            dept.dean_id = 'T001'
            
            # 5. 学生
            student = Student.query.get('S2023001')
            if student is None:
                student = Student(
                    student_id='S2023001',
                    name='王小明',
                    gender='男',
                    enrollment_date=date(2023, 9, 1),
                    dept_id='CS001'
                )
                db.session.add(student)
                click.echo("✓ 创建学生: S2023001")
            else:
                click.echo("✓ 学生已存在: S2023001")
            
            # 6. 学生用户
            student_user = User.query.filter_by(username='S2023001').first()
            if student_user is None:
                student_user = User(
                    username='S2023001',
                    email='student001@university.edu',
                    role='student'
                )
                student_user.set_password('student123')
                student.user = student_user
                db.session.add(student_user)
                click.echo("✓ 创建学生用户: S2023001")
            else:
                click.echo("✓ 学生用户已存在: S2023001")
            
            # 7. 课程
            course = Course.query.get('CS101')
            if course is None:
                course = Course(
                    course_id='CS101',
                    course_name='数据结构',
                    course_type='必修',
                    hours=64,
                    credits=4.0
                )
                db.session.add(course)
                click.echo("✓ 创建课程: CS101")
            else:
                click.echo("✓ 课程已存在: CS101")
            
            db.session.commit()
            click.echo("\n🎉 示例数据处理完成！")
            click.echo("测试账号：")
            click.echo("  教师: T001 / teacher123")
            click.echo("  学生: S2023001 / student123")
            
        except Exception as e:
            db.session.rollback()
            click.echo(f"❌ 错误: {e}")

if __name__ == '__main__':
    cli()