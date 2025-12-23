from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.models import Teacher, Assignment, Selection, Student, Course, User
from app.forms import GradeForm

bp = Blueprint('teacher', __name__, url_prefix='/teacher')

@bp.before_request
@login_required
def restrict_to_teacher():
    if current_user.role != 'teacher':
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('main.index'))

# ==================== 教师仪表盘 ====================
@bp.route('/dashboard')
def dashboard():
    """教师仪表盘"""
    # 获取当前教师
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    if not teacher:
        flash('教师信息不存在', 'danger')
        return redirect(url_for('auth.logout'))
    
    # 获取教师的授课任务
    assignments = Assignment.query.filter_by(teacher_id=teacher.teacher_id).all()
    
    # 统计信息
    stats = {
        'total_courses': len(assignments),
        'total_students': sum(len(assignment.selections) for assignment in assignments),
        'ongoing_courses': len([a for a in assignments if a.academic_year == '2023-2024'])
    }
    
    return render_template('teacher/dashboard.html', 
                          teacher=teacher, 
                          stats=stats, 
                          assignments=assignments)

# ==================== 查询个人信息 ====================
@bp.route('/profile')
def profile():
    """查询个人信息"""
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    if not teacher:
        flash('教师信息不存在', 'danger')
        return redirect(url_for('auth.logout'))
    
    return render_template('teacher/profile.html', teacher=teacher)

# ==================== 查询教学任务 ====================
@bp.route('/courses')
def courses():
    """查询教学任务"""
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    if not teacher:
        flash('教师信息不存在', 'danger')
        return redirect(url_for('auth.logout'))
    
    assignments = Assignment.query.filter_by(teacher_id=teacher.teacher_id)\
                                 .order_by(Assignment.academic_year.desc(), 
                                          Assignment.semester.desc()).all()
    
    return render_template('teacher/courses.html', teacher=teacher, assignments=assignments)

@bp.route('/courses/<int:assignment_id>')
def course_detail(assignment_id):
    """课程详情"""
    assignment = Assignment.query.get_or_404(assignment_id)
    
    # 检查是否是自己的课程
    if assignment.teacher.user_id != current_user.id:
        flash('您没有权限查看此课程', 'danger')
        return redirect(url_for('teacher.courses'))
    
    # 修复：添加JOIN语句
    selections = Selection.query.filter_by(assignment_id=assignment_id)\
                               .join(Student, Selection.student_id == Student.student_id)\
                               .order_by(Student.name).all()
    
    return render_template('teacher/course_detail.html', 
                          assignment=assignment, 
                          selections=selections)

# ==================== 录入/修改所授课程成绩 ====================
@bp.route('/grades')
def grades():
    """成绩管理首页"""
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    if not teacher:
        flash('教师信息不存在', 'danger')
        return redirect(url_for('auth.logout'))
    
    assignments = Assignment.query.filter_by(teacher_id=teacher.teacher_id)\
                                 .order_by(Assignment.academic_year.desc(), 
                                          Assignment.semester.desc()).all()
    
    return render_template('teacher/grades.html', teacher=teacher, assignments=assignments)

@bp.route('/grades/<int:assignment_id>', methods=['GET', 'POST'])
def grade_management(assignment_id):
    """成绩录入/修改"""
    assignment = Assignment.query.get_or_404(assignment_id)
    
    # 检查是否是自己的课程
    if assignment.teacher.user_id != current_user.id:
        flash('您没有权限管理此课程成绩', 'danger')
        return redirect(url_for('teacher.grades'))
    
    # 修复：添加JOIN语句
    selections = Selection.query.filter_by(assignment_id=assignment_id)\
                               .join(Student, Selection.student_id == Student.student_id)\
                               .order_by(Student.name).all()
    
    if request.method == 'POST':
        try:
            for selection in selections:
                usual_key = f'usual_grade_{selection.selection_id}'
                final_key = f'final_grade_{selection.selection_id}'
                
                if usual_key in request.form and request.form[usual_key]:
                    selection.usual_grade = float(request.form[usual_key])
                
                if final_key in request.form and request.form[final_key]:
                    selection.final_grade = float(request.form[final_key])
                
                selection.grade_time = datetime.utcnow()
            
            db.session.commit()
            flash('成绩保存成功', 'success')
            return redirect(url_for('teacher.grade_management', assignment_id=assignment_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'保存失败: {str(e)}', 'danger')
    
    return render_template('teacher/grade_management.html', 
                          assignment=assignment, 
                          selections=selections)

@bp.route('/grades/<int:selection_id>/edit', methods=['GET', 'POST'])
def edit_grade(selection_id):
    """单个学生成绩编辑"""
    selection = Selection.query.get_or_404(selection_id)
    assignment = selection.assignment
    
    # 检查是否是自己的课程
    if assignment.teacher.user_id != current_user.id:
        flash('您没有权限修改此成绩', 'danger')
        return redirect(url_for('teacher.grades'))
    
    form = GradeForm(obj=selection)
    
    if form.validate_on_submit():
        form.populate_obj(selection)
        selection.grade_time = datetime.utcnow()
        
        try:
            db.session.commit()
            flash('成绩更新成功', 'success')
            return redirect(url_for('teacher.grade_management', 
                                   assignment_id=assignment.assignment_id))
        except Exception as e:
            db.session.rollback()
            flash(f'更新失败: {str(e)}', 'danger')
    
    return render_template('teacher/edit_grade.html', 
                          form=form, 
                          selection=selection, 
                          assignment=assignment)

# ==================== 查询所授课程学生名单 ====================
@bp.route('/students')
def students():
    """学生名单查询"""
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    if not teacher:
        flash('教师信息不存在', 'danger')
        return redirect(url_for('auth.logout'))
    
    assignments = Assignment.query.filter_by(teacher_id=teacher.teacher_id).all()
    
    # 修复：通过查询获取学生列表
    all_students = []
    for assignment in assignments:
        # 获取该课程的所有选课记录
        selections = Selection.query.filter_by(assignment_id=assignment.assignment_id)\
                                   .join(Student, Selection.student_id == Student.student_id)\
                                   .order_by(Student.name).all()
        
        for selection in selections:
            student_info = {
                'student': selection.student,
                'assignment': assignment,
                'selection': selection
            }
            all_students.append(student_info)
    
    return render_template('teacher/students.html', 
                          teacher=teacher, 
                          all_students=all_students, 
                          assignments=assignments)

@bp.route('/students/<string:student_id>')
def student_detail(student_id):
    """学生详情"""
    student = Student.query.get_or_404(student_id)
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    
    if not teacher:
        flash('教师信息不存在', 'danger')
        return redirect(url_for('auth.logout'))
    
    # 修复：添加JOIN语句
    selections = Selection.query.join(Assignment)\
                               .filter(Assignment.teacher_id == teacher.teacher_id,
                                      Selection.student_id == student_id)\
                               .join(Student, Selection.student_id == Student.student_id)\
                               .order_by(Assignment.academic_year.desc(), 
                                        Assignment.semester.desc()).all()
    
    return render_template('teacher/student_detail.html', 
                          student=student, 
                          selections=selections)

# ==================== API接口 ====================
@bp.route('/api/my_courses')
def api_my_courses():
    """我的课程API"""
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    if not teacher:
        return jsonify([])
    
    assignments = Assignment.query.filter_by(teacher_id=teacher.teacher_id).all()
    result = []
    
    for assignment in assignments:
        result.append({
            'assignment_id': assignment.assignment_id,
            'course_name': assignment.course.course_name,
            'academic_year': assignment.academic_year,
            'semester': assignment.semester,
            'student_count': len(assignment.selections)
        })
    
    return jsonify(result)

@bp.route('/api/course/<int:assignment_id>/grades')
def api_course_grades(assignment_id):
    """课程成绩API"""
    assignment = Assignment.query.get_or_404(assignment_id)
    
    # 检查权限
    if assignment.teacher.user_id != current_user.id:
        return jsonify({'error': '无权限'}), 403
    
    # 修复：添加JOIN语句
    selections = Selection.query.filter_by(assignment_id=assignment_id)\
                               .join(Student, Selection.student_id == Student.student_id)\
                               .order_by(Student.name).all()
    result = []
    
    for selection in selections:
        result.append({
            'student_id': selection.student_id,
            'student_name': selection.student.name,
            'usual_grade': selection.usual_grade,
            'final_grade': selection.final_grade,
            'total_grade': selection.total_grade
        })
    
    return jsonify(result)