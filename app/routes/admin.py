from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date
from sqlalchemy.exc import IntegrityError
from app import db
from app.models import User, Department, Teacher, Student, Course, Assignment, Selection
from app.forms import StudentForm, TeacherForm, DepartmentForm, CourseForm, AssignmentForm

bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.before_request
@login_required
def restrict_to_admin():
    if current_user.role != 'admin':
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('main.index'))

@bp.route('/')
@bp.route('/dashboard')
def dashboard():
    """管理员仪表盘"""
    stats = {
        'students': Student.query.count(),
        'teachers': Teacher.query.count(),
        'departments': Department.query.count(),
        'courses': Course.query.count(),
        'active_assignments': Assignment.query.count(),
        'selections': Selection.query.count(),
        'users': User.query.count()
    }
    return render_template('admin/dashboard.html', stats=stats)

# ==================== 学生管理 ====================
@bp.route('/students')
def students():
    """学生列表"""
    students = Student.query.order_by(Student.student_id).all()
    # 获取筛选参数
    dept_filter = request.args.get('dept', '')
    status_filter = request.args.get('status', '')
    search_query = request.args.get('search', '')
    
    # 构建查询
    query = Student.query
    
    if dept_filter:
        query = query.filter_by(dept_id=dept_filter)
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    if search_query:
        query = query.filter(
            db.or_(
                Student.student_id.ilike(f'%{search_query}%'),
                Student.name.ilike(f'%{search_query}%')
            )
        )
    
    students = query.order_by(Student.enrollment_date.desc()).all()
    departments = Department.query.order_by(Department.dept_name).all()
    
    return render_template('admin/students.html', 
                          students=students,
                          departments=departments,
                          dept_filter=dept_filter,
                          status_filter=status_filter,
                          search_query=search_query)
    


@bp.route('/students/add', methods=['GET', 'POST'])
def add_student():
    """添加学生（并创建用户账号）"""
    from app.forms import StudentForm
    from app.models import User
    from werkzeug.security import generate_password_hash
    
    form = StudentForm()
    
    # 动态加载系部选择
    departments = Department.query.order_by(Department.dept_id).all()
    form.dept_id.choices = [('', '请选择系部')] + [(d.dept_id, f"{d.dept_id} - {d.dept_name}") for d in departments]
    
    if form.validate_on_submit():
        # 检查学号是否已存在
        if Student.query.filter_by(student_id=form.student_id.data).first():
            flash('该学号已存在', 'danger')
            return render_template('admin/student_form.html', form=form, title='添加学生')
        
        # 1. 创建用户账号
        username = form.student_id.data
        email = f"{username}@school.edu"  # 生成默认邮箱
        default_password = '123456'  # 默认密码
        
        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            flash(f'用户名 {username} 已存在', 'danger')
            return render_template('admin/student_form.html', form=form, title='添加学生')
        
        # 创建用户
        user = User(
            username=username,
            email=email,
            role='student',
            is_active=True
        )
        user.set_password(default_password)
        
        # 2. 创建学生
        student = Student(
            student_id=form.student_id.data,
            name=form.name.data,
            gender=form.gender.data or None,
            birth_date=form.birth_date.data,
            enrollment_date=form.enrollment_date.data,
            dept_id=form.dept_id.data,
            status=form.status.data
        )
        
        try:
            # 先保存用户，获取user_id
            db.session.add(user)
            db.session.flush()  # 获取user.id但不提交
            
            # 关联用户和学生
            student.user_id = user.id
            
            db.session.add(student)
            db.session.commit()
            
            flash(f'学生 {student.name} 添加成功！初始账号：{username}，密码：{default_password}', 'success')
            return redirect(url_for('admin.students'))
        except Exception as e:
            db.session.rollback()
            flash(f'添加失败: {str(e)}', 'danger')
    
    return render_template('admin/student_form.html', form=form, title='添加学生')
@bp.route('/students/<student_id>/edit', methods=['GET', 'POST'])
def edit_student(student_id):
    """编辑学生信息"""
    student = Student.query.get_or_404(student_id)
    form = StudentForm(obj=student)
    
    departments = Department.query.order_by(Department.dept_id).all()
    form.dept_id.choices = [('', '请选择系部')] + [(d.dept_id, f"{d.dept_id} - {d.dept_name}") for d in departments]
    
    if form.validate_on_submit():
        # 检查学号是否被其他学生使用
        if student_id != form.student_id.data and Student.query.filter_by(student_id=form.student_id.data).first():
            flash('该学号已被其他学生使用', 'danger')
            return render_template('admin/student_form.html', form=form, title='编辑学生')
        
        form.populate_obj(student)
        student.updated_at = datetime.utcnow()
        
        try:
            db.session.commit()
            flash(f'学生信息更新成功', 'success')
            return redirect(url_for('admin.students'))
        except Exception as e:
            db.session.rollback()
            flash(f'更新失败: {str(e)}', 'danger')
    
    return render_template('admin/student_form.html', form=form, title='编辑学生')

@bp.route('/students/<student_id>/delete', methods=['POST'])
def delete_student(student_id):
    """删除学生"""
    student = Student.query.get_or_404(student_id)
    
    try:
        # 检查是否有选课记录
        if Selection.query.filter_by(student_id=student_id).first():
            flash('该学生有选课记录，无法删除', 'danger')
            return redirect(url_for('admin.students'))
        
        db.session.delete(student)
        db.session.commit()
        flash(f'学生 {student.name} 删除成功', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败: {str(e)}', 'danger')
    
    return redirect(url_for('admin.students'))

@bp.route('/students/<student_id>/detail')
def student_detail(student_id):
    """学生详情"""
    student = Student.query.get_or_404(student_id)
    selections = Selection.query.filter_by(student_id=student_id).all()
    return render_template('admin/student_detail.html', student=student, selections=selections)

# ==================== 教师管理 ====================
@bp.route('/teachers')
def teachers():
    """教师管理"""
    # 获取筛选参数
    dept_filter = request.args.get('dept', '')
    search_query = request.args.get('search', '')
    
    # 构建查询
    query = Teacher.query
    
    if dept_filter:
        query = query.filter_by(dept_id=dept_filter)
    
    if search_query:
        query = query.filter(
            db.or_(
                Teacher.teacher_id.ilike(f'%{search_query}%'),
                Teacher.name.ilike(f'%{search_query}%'),
                Teacher.title.ilike(f'%{search_query}%')
            )
        )
    
    teachers = query.order_by(Teacher.hire_date.desc()).all()
    departments = Department.query.order_by(Department.dept_name).all()
    
    return render_template('admin/teachers.html', 
                          teachers=teachers,
                          departments=departments,
                          dept_filter=dept_filter,
                          search_query=search_query)

@bp.route('/teachers/<string:teacher_id>')
def teacher_detail(teacher_id):
    """教师详情"""
    teacher = Teacher.query.get_or_404(teacher_id)
    
    # 获取该教师的教学任务
    assignments = Assignment.query.filter_by(teacher_id=teacher_id).all()
    
    # 统计信息
    stats = {
        'total_courses': len(assignments),
        'total_students': sum(len(assignment.selections) for assignment in assignments),
        'ongoing_courses': len([a for a in assignments if a.academic_year == '2023-2024'])
    }
    
    return render_template('admin/teacher_detail.html', 
                          teacher=teacher, 
                          assignments=assignments,
                          stats=stats)

@bp.route('/teachers/add', methods=['GET', 'POST'])
def add_teacher():
    """添加教师（并创建用户账号）"""
    from app.forms import TeacherForm
    from app.models import User
    from werkzeug.security import generate_password_hash
    
    form = TeacherForm()
    
    # 动态加载系部选择
    departments = Department.query.order_by(Department.dept_id).all()
    form.dept_id.choices = [('', '请选择系部')] + [(d.dept_id, f"{d.dept_id} - {d.dept_name}") for d in departments]
    
    if form.validate_on_submit():
        # 检查工号是否已存在
        if Teacher.query.filter_by(teacher_id=form.teacher_id.data).first():
            flash('该工号已存在', 'danger')
            return render_template('admin/teacher_form.html', form=form, title='添加教师')
        
        # 1. 创建用户账号
        username = form.teacher_id.data
        email = f"{username}@school.edu"  # 生成默认邮箱
        default_password = '123456'  # 默认密码
        
        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            flash(f'用户名 {username} 已存在', 'danger')
            return render_template('admin/teacher_form.html', form=form, title='添加教师')
        
        # 创建用户
        user = User(
            username=username,
            email=email,
            role='teacher',
            is_active=True
        )
        user.set_password(default_password)
        
        # 2. 创建教师
        teacher = Teacher(
            teacher_id=form.teacher_id.data,
            name=form.name.data,
            gender=form.gender.data or None,
            birth_date=form.birth_date.data,
            hire_date=form.hire_date.data,
            dept_id=form.dept_id.data,
            title=form.title.data,
            specialty=form.specialty.data
        )
        
        try:
            # 先保存用户，获取user_id
            db.session.add(user)
            db.session.flush()  # 获取user.id但不提交
            
            # 关联用户和教师
            teacher.user_id = user.id
            
            db.session.add(teacher)
            db.session.commit()
            
            flash(f'教师 {teacher.name} 添加成功！初始账号：{username}，密码：{default_password}', 'success')
            return redirect(url_for('admin.teachers'))
        except Exception as e:
            db.session.rollback()
            flash(f'添加失败: {str(e)}', 'danger')
    
    return render_template('admin/teacher_form.html', form=form, title='添加教师')

@bp.route('/teachers/<teacher_id>/edit', methods=['GET', 'POST'])
def edit_teacher(teacher_id):
    """编辑教师信息"""
    teacher = Teacher.query.get_or_404(teacher_id)
    form = TeacherForm(obj=teacher)
    
    departments = Department.query.order_by(Department.dept_id).all()
    form.dept_id.choices = [('', '请选择系部')] + [(d.dept_id, f"{d.dept_id} - {d.dept_name}") for d in departments]
    
    if form.validate_on_submit():
        if teacher_id != form.teacher_id.data and Teacher.query.filter_by(teacher_id=form.teacher_id.data).first():
            flash('该工号已被其他教师使用', 'danger')
            return render_template('admin/teacher_form.html', form=form, title='编辑教师')
        
        form.populate_obj(teacher)
        teacher.updated_at = datetime.utcnow()
        
        try:
            db.session.commit()
            flash('教师信息更新成功', 'success')
            return redirect(url_for('admin.teachers'))
        except Exception as e:
            db.session.rollback()
            flash(f'更新失败: {str(e)}', 'danger')
    
    return render_template('admin/teacher_form.html', form=form, title='编辑教师')

@bp.route('/teachers/<teacher_id>/delete', methods=['POST'])
def delete_teacher(teacher_id):
    """删除教师"""
    teacher = Teacher.query.get_or_404(teacher_id)
    
    try:
        # 检查是否有教学任务
        if Assignment.query.filter_by(teacher_id=teacher_id).first():
            flash('该教师有教学任务，无法删除', 'danger')
            return redirect(url_for('admin.teachers'))
        
        # 检查是否是系主任
        departments = Department.query.filter_by(dean_id=teacher_id).all()
        for dept in departments:
            dept.dean_id = None
        
        db.session.delete(teacher)
        db.session.commit()
        flash(f'教师 {teacher.name} 删除成功', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败: {str(e)}', 'danger')
    
    return redirect(url_for('admin.teachers'))

# ==================== 系部管理 ====================
@bp.route('/departments')
def departments():
    """系部列表"""
    departments = Department.query.order_by(Department.dept_id).all()
    return render_template('admin/departments.html', departments=departments)

@bp.route('/departments/add', methods=['GET', 'POST'])
def add_department():
    """添加系部"""
    form = DepartmentForm()
    
    teachers = Teacher.query.order_by(Teacher.name).all()
    form.dean_id.choices = [('', '请选择系主任')] + [(t.teacher_id, f"{t.teacher_id} - {t.name}") for t in teachers]
    
    if form.validate_on_submit():
        if Department.query.filter_by(dept_id=form.dept_id.data).first():
            flash('该系部编号已存在', 'danger')
            return render_template('admin/department_form.html', form=form, title='添加系部')
        
        department = Department(
            dept_id=form.dept_id.data,
            dept_name=form.dept_name.data,
            dean_id=form.dean_id.data or None,
            phone=form.phone.data,
            description=form.description.data
        )
        
        try:
            db.session.add(department)
            db.session.commit()
            flash(f'系部 {department.dept_name} 添加成功', 'success')
            return redirect(url_for('admin.departments'))
        except Exception as e:
            db.session.rollback()
            flash(f'添加失败: {str(e)}', 'danger')
    
    return render_template('admin/department_form.html', form=form, title='添加系部')

@bp.route('/departments/<dept_id>/edit', methods=['GET', 'POST'])
def edit_department(dept_id):
    """编辑系部信息"""
    department = Department.query.get_or_404(dept_id)
    form = DepartmentForm(obj=department)
    
    teachers = Teacher.query.order_by(Teacher.name).all()
    form.dean_id.choices = [('', '请选择系主任')] + [(t.teacher_id, f"{t.teacher_id} - {t.name}") for t in teachers]
    
    if form.validate_on_submit():
        if dept_id != form.dept_id.data and Department.query.filter_by(dept_id=form.dept_id.data).first():
            flash('该系部编号已存在', 'danger')
            return render_template('admin/department_form.html', form=form, title='编辑系部')
        
        form.populate_obj(department)
        department.updated_at = datetime.utcnow()
        
        try:
            db.session.commit()
            flash('系部信息更新成功', 'success')
            return redirect(url_for('admin.departments'))
        except Exception as e:
            db.session.rollback()
            flash(f'更新失败: {str(e)}', 'danger')
    
    return render_template('admin/department_form.html', form=form, title='编辑系部')

@bp.route('/departments/<dept_id>/delete', methods=['POST'])
def delete_department(dept_id):
    """删除系部"""
    department = Department.query.get_or_404(dept_id)
    
    try:
        # 检查是否有学生或教师
        if Student.query.filter_by(dept_id=dept_id).first() or Teacher.query.filter_by(dept_id=dept_id).first():
            flash('该系部下有学生或教师，无法删除', 'danger')
            return redirect(url_for('admin.departments'))
        
        db.session.delete(department)
        db.session.commit()
        flash(f'系部 {department.dept_name} 删除成功', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败: {str(e)}', 'danger')
    
    return redirect(url_for('admin.departments'))

# ==================== 课程管理 ====================
@bp.route('/courses')
def courses():
    """课程列表"""
    courses = Course.query.order_by(Course.course_id).all()
    return render_template('admin/courses.html', courses=courses)

@bp.route('/courses/add', methods=['GET', 'POST'])
def add_course():
    """添加课程"""
    form = CourseForm()
    
    if form.validate_on_submit():
        if Course.query.filter_by(course_id=form.course_id.data).first():
            flash('该课程编号已存在', 'danger')
            return render_template('admin/course_form.html', form=form, title='添加课程')
        
        course = Course(
            course_id=form.course_id.data,
            course_name=form.course_name.data,
            course_type=form.course_type.data,
            hours=form.hours.data,
            credits=form.credits.data,
            description=form.description.data
        )
        
        try:
            db.session.add(course)
            db.session.commit()
            flash(f'课程 {course.course_name} 添加成功', 'success')
            return redirect(url_for('admin.courses'))
        except Exception as e:
            db.session.rollback()
            flash(f'添加失败: {str(e)}', 'danger')
    
    return render_template('admin/course_form.html', form=form, title='添加课程')

@bp.route('/courses/<course_id>/edit', methods=['GET', 'POST'])
def edit_course(course_id):
    """编辑课程信息"""
    course = Course.query.get_or_404(course_id)
    form = CourseForm(obj=course)
    
    if form.validate_on_submit():
        if course_id != form.course_id.data and Course.query.filter_by(course_id=form.course_id.data).first():
            flash('该课程编号已存在', 'danger')
            return render_template('admin/course_form.html', form=form, title='编辑课程')
        
        form.populate_obj(course)
        course.updated_at = datetime.utcnow()
        
        try:
            db.session.commit()
            flash('课程信息更新成功', 'success')
            return redirect(url_for('admin.courses'))
        except Exception as e:
            db.session.rollback()
            flash(f'更新失败: {str(e)}', 'danger')
    
    return render_template('admin/course_form.html', form=form, title='编辑课程')

@bp.route('/courses/<course_id>/delete', methods=['POST'])
def delete_course(course_id):
    """删除课程"""
    course = Course.query.get_or_404(course_id)
    
    try:
        # 检查是否有教学任务
        if Assignment.query.filter_by(course_id=course_id).first():
            flash('该课程有教学任务，无法删除', 'danger')
            return redirect(url_for('admin.courses'))
        
        db.session.delete(course)
        db.session.commit()
        flash(f'课程 {course.course_name} 删除成功', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败: {str(e)}', 'danger')
    
    return redirect(url_for('admin.courses'))

# ==================== 教学任务管理 ====================
@bp.route('/assignments')
def assignments():
    """教学任务列表"""
    assignments = Assignment.query.order_by(
        Assignment.academic_year.desc(), 
        Assignment.semester.desc()
    ).all()
    return render_template('admin/assignments.html', assignments=assignments)

@bp.route('/assignments/add', methods=['GET', 'POST'])
def add_assignment():
    """添加教学任务"""
    form = AssignmentForm()
    
    # 动态加载选择项
    courses = Course.query.order_by(Course.course_name).all()
    teachers = Teacher.query.order_by(Teacher.name).all()
    
    form.course_id.choices = [('', '请选择课程')] + [(c.course_id, f"{c.course_id} - {c.course_name}") for c in courses]
    form.teacher_id.choices = [('', '请选择教师')] + [(t.teacher_id, f"{t.teacher_id} - {t.name}") for t in teachers]
    
    if form.validate_on_submit():
        # 检查是否已存在相同的教学任务
        existing = Assignment.query.filter_by(
            course_id=form.course_id.data,
            teacher_id=form.teacher_id.data,
            academic_year=form.academic_year.data,
            semester=form.semester.data
        ).first()
        
        if existing:
            flash('该教学任务已存在', 'danger')
            return render_template('admin/assignment_form.html', form=form, title='添加教学任务')
        
        assignment = Assignment(
            course_id=form.course_id.data,
            teacher_id=form.teacher_id.data,
            academic_year=form.academic_year.data,
            semester=form.semester.data,
            class_time=form.class_time.data,
            location=form.location.data,
            exam_time=form.exam_time.data,
            enrollment_limit=form.enrollment_limit.data or 0
        )
        
        try:
            db.session.add(assignment)
            db.session.commit()
            flash('教学任务添加成功', 'success')
            return redirect(url_for('admin.assignments'))
        except Exception as e:
            db.session.rollback()
            flash(f'添加失败: {str(e)}', 'danger')
    
    return render_template('admin/assignment_form.html', form=form, title='添加教学任务')

@bp.route('/assignments/<int:assignment_id>/delete', methods=['POST'])
def delete_assignment(assignment_id):
    """删除教学任务"""
    assignment = Assignment.query.get_or_404(assignment_id)
    
    try:
        # 检查是否有选课记录
        if Selection.query.filter_by(assignment_id=assignment_id).first():
            flash('该教学任务有选课记录，无法删除', 'danger')
            return redirect(url_for('admin.assignments'))
        
        db.session.delete(assignment)
        db.session.commit()
        flash('教学任务删除成功', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败: {str(e)}', 'danger')
    
    return redirect(url_for('admin.assignments'))

# ==================== 用户管理 ====================
@bp.route('/users')
def users():
    """用户管理"""
    # 获取筛选参数
    role_filter = request.args.get('role', '')
    search_query = request.args.get('search', '')
    
    # 构建查询
    query = User.query
    
    if role_filter:
        query = query.filter_by(role=role_filter)
    
    if search_query:
        query = query.filter(
            db.or_(
                User.username.ilike(f'%{search_query}%'),
                User.email.ilike(f'%{search_query}%')
            )
        )
    
    users = query.order_by(User.created_at.desc()).all()
    
    return render_template('admin/users.html', 
                          users=users,
                          role_filter=role_filter,
                          search_query=search_query)

@bp.route('/users/<int:user_id>/reset_password', methods=['GET', 'POST'])
def reset_user_password(user_id):
    """重置用户密码（管理员功能）"""
    user = User.query.get_or_404(user_id)
    
    from app.forms import ResetPasswordForm
    form = ResetPasswordForm()
    
    if form.validate_on_submit():
        user.set_password(form.new_password.data)
        db.session.commit()
        
        flash(f'用户 {user.username} 的密码已重置为: {form.new_password.data}', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/reset_password.html', form=form, user=user)

@bp.route('/users/<int:user_id>/toggle_active', methods=['POST'])
def toggle_user_active(user_id):
    """启用/禁用用户"""
    user = User.query.get_or_404(user_id)
    
    # 不能禁用自己
    if user.id == current_user.id:
        flash('不能禁用自己的账户', 'danger')
        return redirect(url_for('admin.users'))
    
    user.is_active = not user.is_active
    db.session.commit()
    
    status = '启用' if user.is_active else '禁用'
    flash(f'用户 {user.username} 已{status}', 'success')
    return redirect(url_for('admin.users'))

@bp.route('/users/<int:user_id>/delete', methods=['POST'])
def delete_user(user_id):
    """删除用户"""
    user = User.query.get_or_404(user_id)
    
    # 不能删除自己
    if user.id == current_user.id:
        flash('不能删除自己的账户', 'danger')
        return redirect(url_for('admin.users'))
    
    # 不能删除有关联的用户
    if user.teacher_profile or user.student_profile:
        flash('该用户有关联的教师或学生信息，无法删除', 'danger')
        return redirect(url_for('admin.users'))
    
    try:
        db.session.delete(user)
        db.session.commit()
        flash(f'用户 {user.username} 已删除', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败: {str(e)}', 'danger')
    
    return redirect(url_for('admin.users'))

# ==================== 数据统计 ====================
@bp.route('/statistics')
def statistics():
    """数据统计"""
    # 系部学生统计
    dept_stats = db.session.query(
        Department.dept_name,
        db.func.count(Student.student_id).label('student_count')
    ).join(Student, Department.dept_id == Student.dept_id, isouter=True)\
     .group_by(Department.dept_id, Department.dept_name).all()
    
    # 课程选课统计
    course_stats = db.session.query(
        Course.course_name,
        db.func.count(Selection.selection_id).label('selection_count')
    ).join(Assignment, Course.course_id == Assignment.course_id, isouter=True)\
     .join(Selection, Assignment.assignment_id == Selection.assignment_id, isouter=True)\
     .group_by(Course.course_id, Course.course_name).all()
    
    return render_template('admin/statistics.html', 
                          dept_stats=dept_stats, 
                          course_stats=course_stats)

# ==================== API接口 ====================
@bp.route('/api/students/count')
def api_students_count():
    """学生数量API"""
    count = Student.query.count()
    return jsonify({'count': count})

@bp.route('/api/teachers/count')
def api_teachers_count():
    """教师数量API"""
    count = Teacher.query.count()
    return jsonify({'count': count})

@bp.route('/api/departments/<dept_id>/teachers')
def api_department_teachers(dept_id):
    """获取系部教师API"""
    teachers = Teacher.query.filter_by(dept_id=dept_id).all()
    result = [{'teacher_id': t.teacher_id, 'name': t.name} for t in teachers]
    return jsonify(result)

# ==================== 系统设置 ====================
@bp.route('/settings')
def settings():
    """系统设置"""
    return render_template('admin/settings.html')

@bp.route('/settings/update', methods=['POST'])
def update_settings():
    """更新系统设置"""
    # 这里可以添加系统设置更新逻辑
    flash('系统设置已更新', 'success')
    return redirect(url_for('admin.settings'))

# ==================== 数据备份 ====================
@bp.route('/backup')
def backup():
    """数据备份"""
    # 这里可以添加数据备份逻辑
    flash('数据备份功能开发中', 'info')
    return redirect(url_for('admin.dashboard'))

@bp.route('/import')
def data_import():
    """数据导入"""
    flash('数据导入功能开发中', 'info')
    return redirect(url_for('admin.dashboard'))

@bp.route('/export')
def data_export():
    """数据导出"""
    flash('数据导出功能开发中', 'info')
    return redirect(url_for('admin.dashboard'))