from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.models import Student, Course, Assignment, Selection, Department
from app.forms import CourseSelectionForm

bp = Blueprint('student', __name__, url_prefix='/student')

@bp.before_request
@login_required
def restrict_to_student():
    if current_user.role != 'student':
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('main.index'))

# ==================== 学生仪表盘 ====================
@bp.route('/dashboard')
def dashboard():
    """学生仪表盘"""
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        flash('学生信息不存在', 'danger')
        return redirect(url_for('auth.logout'))
    
    # 获取学生的选课记录
    selections = Selection.query.filter_by(student_id=student.student_id).all()
    
    # 统计信息
    stats = {
        'total_courses': len(selections),
        'completed_courses': len([s for s in selections if s.total_grade is not None]),
        'total_credits': sum(s.assignment.course.credits or 0 for s in selections if s.total_grade and s.total_grade >= 60),
        'gpa': calculate_gpa(selections)
    }
    
    # 获取当前学期的课程
    current_assignments = Assignment.query.filter(
        Assignment.academic_year == '2023-2024',
        Assignment.semester == '1'
    ).all()
    
    return render_template('student/dashboard.html', 
                          student=student, 
                          stats=stats, 
                          selections=selections,
                          current_assignments=current_assignments)

def calculate_gpa(selections):
    """计算GPA"""
    graded_courses = [s for s in selections if s.total_grade is not None]
    if not graded_courses:
        return 0.0
    
    total_points = 0
    total_credits = 0
    
    for selection in graded_courses:
        credits = selection.assignment.course.credits or 0
        grade = selection.total_grade
        
        # 转换为绩点（4.0制）
        if grade >= 90:
            points = 4.0
        elif grade >= 80:
            points = 3.0
        elif grade >= 70:
            points = 2.0
        elif grade >= 60:
            points = 1.0
        else:
            points = 0.0
            
        total_points += points * credits
        total_credits += credits
    
    return round(total_points / total_credits, 2) if total_credits > 0 else 0.0

# ==================== 查询个人信息 ====================
@bp.route('/profile')
def profile():
    """查询个人信息"""
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        flash('学生信息不存在', 'danger')
        return redirect(url_for('auth.logout'))
    
    return render_template('student/profile.html', student=student)

# ==================== 查询可选课程 ====================
@bp.route('/courses')
def courses():
    """查询可选课程"""
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        flash('学生信息不存在', 'danger')
        return redirect(url_for('auth.logout'))
    
    # 获取所有教学任务
    assignments = Assignment.query.order_by(
        Assignment.academic_year.desc(), 
        Assignment.semester.desc()
    ).all()
    
    # 修复：通过 Selection 表查询已选课程
    selected_assignments = Selection.query.filter_by(student_id=student.student_id).all()
    selected_course_ids = [s.assignment_id for s in selected_assignments]
    
    return render_template('student/courses.html', 
                          student=student, 
                          assignments=assignments,
                          selected_course_ids=selected_course_ids)

# ==================== 进行选课操作 ====================
@bp.route('/courses/select', methods=['GET', 'POST'])
def select_courses():
    """选课操作"""
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        flash('学生信息不存在', 'danger')
        return redirect(url_for('auth.logout'))
    
    # 获取学生已选课程的assignment_id
    selected_ids = [s.assignment_id for s in Selection.query.filter_by(
        student_id=student.student_id
    ).all()]
    
    # 获取所有课程
    all_assignments = Assignment.query.all()
    
    # 获取可选课程（排除已选和已满的课程）
    available_assignments = []
    for assignment in all_assignments:
        if assignment.assignment_id in selected_ids:
            continue
        
        # 检查课程是否已满
        if assignment.enrollment_limit and len(assignment.selections) >= assignment.enrollment_limit:
            continue
            
        available_assignments.append(assignment)
    
    if request.method == 'POST':
        assignment_id = request.form.get('assignment_id')
        if not assignment_id:
            flash('请选择课程', 'danger')
            return redirect(url_for('student.select_courses'))
        
        assignment = Assignment.query.get(assignment_id)
        if not assignment:
            flash('课程不存在', 'danger')
            return redirect(url_for('student.select_courses'))
        
        # 检查是否已选
        existing_selection = Selection.query.filter_by(
            student_id=student.student_id,
            assignment_id=assignment_id
        ).first()
        
        if existing_selection:
            flash('您已经选择了该课程', 'warning')
            return redirect(url_for('student.select_courses'))
        
        # 检查课程是否已满
        if assignment.enrollment_limit and len(assignment.selections) >= assignment.enrollment_limit:
            flash('该课程已满员，无法选择', 'danger')
            return redirect(url_for('student.select_courses'))
        
        # 创建选课记录
        selection = Selection(
            student_id=student.student_id,
            assignment_id=assignment_id,
            selection_time=datetime.utcnow()
        )
        
        try:
            db.session.add(selection)
            db.session.commit()
            flash(f'成功选择课程：{assignment.course.course_name}', 'success')
            return redirect(url_for('student.my_courses'))
        except Exception as e:
            db.session.rollback()
            flash(f'选课失败：{str(e)}', 'danger')
    
    return render_template('student/select_courses.html', 
                          student=student, 
                          assignments=available_assignments)

@bp.route('/courses/<int:assignment_id>/select', methods=['POST'])
def select_course(assignment_id):
    """快速选课"""
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        return jsonify({'success': False, 'message': '学生信息不存在'})
    
    assignment = Assignment.query.get(assignment_id)
    if not assignment:
        return jsonify({'success': False, 'message': '课程不存在'})
    
    # 检查是否已选
    existing_selection = Selection.query.filter_by(
        student_id=student.student_id,
        assignment_id=assignment_id
    ).first()
    
    if existing_selection:
        return jsonify({'success': False, 'message': '您已经选择了该课程'})
    
    # 检查课程是否已满
    if assignment.enrollment_limit and len(assignment.selections) >= assignment.enrollment_limit:
        return jsonify({'success': False, 'message': '该课程已满员'})
    
    # 创建选课记录
    selection = Selection(
        student_id=student.student_id,
        assignment_id=assignment_id,
        selection_time=datetime.utcnow()
    )
    
    try:
        db.session.add(selection)
        db.session.commit()
        return jsonify({
            'success': True, 
            'message': f'成功选择：{assignment.course.course_name}',
            'course_name': assignment.course.course_name
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'选课失败：{str(e)}'})

@bp.route('/courses/<int:selection_id>/drop', methods=['POST'])
def drop_course(selection_id):
    """退选课程"""
    selection = Selection.query.get_or_404(selection_id)
    student = Student.query.filter_by(user_id=current_user.id).first()
    
    if not student or selection.student_id != student.student_id:
        return jsonify({'success': False, 'message': '无权操作'})
    
    # 检查是否已录入成绩
    if selection.usual_grade is not None or selection.final_grade is not None:
        return jsonify({'success': False, 'message': '该课程已录入成绩，无法退选'})
    
    try:
        db.session.delete(selection)
        db.session.commit()
        return jsonify({'success': True, 'message': '退选成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'退选失败：{str(e)}'})

# ==================== 我的课程 ====================
@bp.route('/my_courses')
def my_courses():
    """我的课程"""
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        flash('学生信息不存在', 'danger')
        return redirect(url_for('auth.logout'))
    
    selections = Selection.query.filter_by(student_id=student.student_id).order_by(
        Selection.selection_time.desc()
    ).all()
    
    return render_template('student/my_courses.html', 
                          student=student, 
                          selections=selections)

# ==================== 查询个人成绩 ====================
@bp.route('/grades')
def grades():
    """查询个人成绩"""
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        flash('学生信息不存在', 'danger')
        return redirect(url_for('auth.logout'))
    
    # 修复排序错误
    selections = Selection.query.filter_by(student_id=student.student_id)\
                               .join(Assignment)\
                               .order_by(
                                   Assignment.academic_year.desc(),
                                   Assignment.semester.desc()
                               ).all()
    
    # 计算统计信息
    graded_selections = [s for s in selections if s.total_grade is not None]
    stats = {
        'total_courses': len(selections),
        'graded_courses': len(graded_selections),
        'passed_courses': len([s for s in graded_selections if s.total_grade >= 60]),
        'total_credits': sum(s.assignment.course.credits or 0 for s in graded_selections if s.total_grade >= 60),
        'gpa': calculate_gpa(selections)
    }
    
    return render_template('student/grades.html', 
                          student=student, 
                          selections=selections,
                          stats=stats)

# ==================== 成绩详情 ====================
@bp.route('/grades/<int:selection_id>')
def grade_detail(selection_id):
    """成绩详情"""
    selection = Selection.query.get_or_404(selection_id)
    student = Student.query.filter_by(user_id=current_user.id).first()
    
    if not student or selection.student_id != student.student_id:
        flash('无权查看此成绩', 'danger')
        return redirect(url_for('student.grades'))
    
    return render_template('student/grade_detail.html', 
                          selection=selection, 
                          student=student)

# ==================== API接口 ====================
@bp.route('/api/my_grades')
def api_my_grades():
    """我的成绩API"""
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        return jsonify([])
    
    selections = Selection.query.filter_by(student_id=student.student_id).all()
    result = []
    
    for selection in selections:
        if selection.total_grade is not None:
            result.append({
                'course_name': selection.assignment.course.course_name,
                'academic_year': selection.assignment.academic_year,
                'semester': selection.assignment.semester,
                'usual_grade': selection.usual_grade,
                'final_grade': selection.final_grade,
                'total_grade': selection.total_grade,
                'credits': selection.assignment.course.credits or 0
            })
    
    return jsonify(result)

@bp.route('/api/available_courses')
def api_available_courses():
    """可选课程API"""
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        return jsonify([])
    
    # 获取学生已选的课程ID
    selected_assignments = Selection.query.filter_by(student_id=student.student_id).all()
    selected_ids = [s.assignment_id for s in selected_assignments]
    
    # 获取所有课程
    all_assignments = Assignment.query.all()
    
    result = []
    for assignment in all_assignments:
        # 排除已选课程
        if assignment.assignment_id in selected_ids:
            continue
            
        # 检查是否已满
        is_full = assignment.enrollment_limit and len(assignment.selections) >= assignment.enrollment_limit
        
        result.append({
            'assignment_id': assignment.assignment_id,
            'course_name': assignment.course.course_name,
            'teacher_name': assignment.teacher.name,
            'academic_year': assignment.academic_year,
            'semester': assignment.semester,
            'class_time': assignment.class_time,
            'location': assignment.location,
            'current_enrollment': len(assignment.selections),
            'enrollment_limit': assignment.enrollment_limit,
            'is_full': is_full,
            'credits': assignment.course.credits or 0
        })
    
    return jsonify(result)