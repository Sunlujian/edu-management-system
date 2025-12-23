from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, DateField, TextAreaField, IntegerField, FloatField, DateTimeField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, NumberRange, ValidationError
from app.models import User
from datetime import datetime, date

class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(min=3, max=20)])
    password = PasswordField('密码', validators=[DataRequired()])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登录')

class RegistrationForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('邮箱', validators=[DataRequired(), Email()])
    password = PasswordField('密码', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('确认密码', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('注册')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('该用户名已被使用')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('该邮箱已被注册')

class StudentForm(FlaskForm):
    student_id = StringField('学号', validators=[DataRequired(), Length(max=20)])
    name = StringField('姓名', validators=[DataRequired(), Length(max=20)])
    gender = SelectField('性别', choices=[('', '请选择'), ('男', '男'), ('女', '女')], validators=[Optional()])
    birth_date = DateField('出生日期', format='%Y-%m-%d', validators=[Optional()])
    enrollment_date = DateField('入学时间', format='%Y-%m-%d', validators=[DataRequired()])
    dept_id = SelectField('所在系部', coerce=str, validators=[DataRequired()])
    status = SelectField('状态', choices=[('在籍', '在籍'), ('毕业', '毕业'), ('休学', '休学'), ('退学', '退学')], default='在籍')
    submit = SubmitField('保存')

class TeacherForm(FlaskForm):
    teacher_id = StringField('工号', validators=[DataRequired(), Length(max=20)])
    name = StringField('姓名', validators=[DataRequired(), Length(max=20)])
    gender = SelectField('性别', choices=[('', '请选择'), ('男', '男'), ('女', '女')], validators=[Optional()])
    birth_date = DateField('出生日期', format='%Y-%m-%d', validators=[Optional()])
    hire_date = DateField('入职时间', format='%Y-%m-%d', validators=[DataRequired()])
    dept_id = SelectField('所在系部', coerce=str, validators=[DataRequired()])
    title = StringField('职称', validators=[Optional(), Length(max=20)])
    specialty = StringField('专业方向', validators=[Optional(), Length(max=100)])
    submit = SubmitField('保存')

class DepartmentForm(FlaskForm):
    dept_id = StringField('系号', validators=[DataRequired(), Length(max=20)])
    dept_name = StringField('系名称', validators=[DataRequired(), Length(max=50)])
    dean_id = SelectField('系主任', coerce=str, validators=[Optional()])
    phone = StringField('联系电话', validators=[Optional(), Length(max=20)])
    description = TextAreaField('系简介', validators=[Optional()])
    submit = SubmitField('保存')

class CourseForm(FlaskForm):
    course_id = StringField('课程号', validators=[DataRequired(), Length(max=20)])
    course_name = StringField('课程名称', validators=[DataRequired(), Length(max=100)])
    course_type = SelectField('课程性质', choices=[('必修', '必修'), ('选修', '选修')], default='必修')
    hours = IntegerField('学时', validators=[Optional(), NumberRange(min=0)])
    credits = FloatField('学分', validators=[Optional(), NumberRange(min=0)])
    description = TextAreaField('课程描述', validators=[Optional()])
    submit = SubmitField('保存')

class AssignmentForm(FlaskForm):
    course_id = SelectField('课程', coerce=str, validators=[DataRequired()])
    teacher_id = SelectField('授课教师', coerce=str, validators=[DataRequired()])
    academic_year = StringField('学年', validators=[DataRequired(), Length(max=20)])
    semester = SelectField('学期', choices=[('1', '第一学期'), ('2', '第二学期'), ('3', '夏季学期')], validators=[DataRequired()])
    class_time = StringField('上课时间', validators=[Optional(), Length(max=100)])
    location = StringField('上课地点', validators=[Optional(), Length(max=100)])
    exam_time = StringField('考试时间', validators=[Optional()])
    enrollment_limit = IntegerField('选课人数上限', validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField('保存')

class GradeForm(FlaskForm):
    usual_grade = FloatField('平时成绩', validators=[
        Optional(),
        NumberRange(min=0, max=100, message='成绩必须在0-100之间')
    ])
    
    final_grade = FloatField('期末成绩', validators=[
        Optional(),
        NumberRange(min=0, max=100, message='成绩必须在0-100之间')
    ])
    
    submit = SubmitField('保存成绩')


class CourseSelectionForm(FlaskForm):
    """课程选课表单"""
    assignment_id = SelectField('选择课程', coerce=int, validators=[DataRequired()])
    submit = SubmitField('确认选课')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('当前密码', validators=[DataRequired()])
    new_password = PasswordField('新密码', validators=[DataRequired(), Length(min=6, message='密码至少6位')])
    confirm_password = PasswordField('确认新密码', validators=[DataRequired(), EqualTo('new_password', message='两次输入的密码不一致')])
    submit = SubmitField('修改密码')

class ResetPasswordForm(FlaskForm):
    new_password = PasswordField('新密码', validators=[DataRequired(), Length(min=6, message='密码至少6位')])
    confirm_password = PasswordField('确认新密码', validators=[DataRequired(), EqualTo('new_password', message='两次输入的密码不一致')])
    submit = SubmitField('重置密码')