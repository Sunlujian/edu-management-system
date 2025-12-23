from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.Enum('admin', 'teacher', 'student'), nullable=False, default='student')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    teacher_profile = db.relationship('Teacher', backref='user', uselist=False, cascade='all, delete-orphan')
    student_profile = db.relationship('Student', backref='user', uselist=False, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Department(db.Model):
    __tablename__ = 'department'
    dept_id = db.Column(db.String(20), primary_key=True)
    dept_name = db.Column(db.String(50), nullable=False, index=True)
    dean_id = db.Column(db.String(20), db.ForeignKey('teacher.teacher_id'), nullable=True)
    phone = db.Column(db.String(20))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 明确指定外键关系
    dean = db.relationship('Teacher', foreign_keys=[dean_id], backref='dean_of_department')
    teachers = db.relationship('Teacher', 
                              back_populates='department', 
                              cascade='all, delete-orphan',
                              foreign_keys='Teacher.dept_id')
    students = db.relationship('Student', 
                              back_populates='department', 
                              cascade='all, delete-orphan',
                              foreign_keys='Student.dept_id')
    
    def __repr__(self):
        return f'<Department {self.dept_name}>'

class Teacher(db.Model):
    __tablename__ = 'teacher'
    teacher_id = db.Column(db.String(20), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=True)
    name = db.Column(db.String(20), nullable=False, index=True)
    gender = db.Column(db.Enum('男', '女'))
    birth_date = db.Column(db.Date)
    hire_date = db.Column(db.Date, nullable=False)
    dept_id = db.Column(db.String(20), db.ForeignKey('department.dept_id'), nullable=False)
    title = db.Column(db.String(20))
    specialty = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    assignments = db.relationship('Assignment', back_populates='teacher', cascade='all, delete-orphan')
    department = db.relationship('Department', 
                                back_populates='teachers', 
                                foreign_keys=[dept_id])
    
    def __repr__(self):
        return f'<Teacher {self.name}>'

class Student(db.Model):
    __tablename__ = 'student'
    student_id = db.Column(db.String(20), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=True)
    name = db.Column(db.String(20), nullable=False, index=True)
    gender = db.Column(db.Enum('男', '女'))
    birth_date = db.Column(db.Date)
    enrollment_date = db.Column(db.Date, nullable=False)
    dept_id = db.Column(db.String(20), db.ForeignKey('department.dept_id'), nullable=False)
    status = db.Column(db.Enum('在籍', '毕业', '休学', '退学'), default='在籍')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    selections = db.relationship('Selection', 
                                back_populates='student', 
                                cascade='all, delete-orphan',
                                lazy='dynamic')
    department = db.relationship('Department', 
                                back_populates='students', 
                                foreign_keys=[dept_id])
    
    def __repr__(self):
        return f'<Student {self.name}>'

class Course(db.Model):
    __tablename__ = 'course'
    course_id = db.Column(db.String(20), primary_key=True)
    course_name = db.Column(db.String(100), nullable=False, index=True)
    course_type = db.Column(db.Enum('必修', '选修'), default='必修')
    hours = db.Column(db.Integer, default=0)
    credits = db.Column(db.Float, default=0.0)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    assignments = db.relationship('Assignment', 
                                 back_populates='course', 
                                 cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Course {self.course_name}>'

class Assignment(db.Model):
    __tablename__ = 'assignment'
    assignment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    course_id = db.Column(db.String(20), db.ForeignKey('course.course_id'), nullable=False)
    teacher_id = db.Column(db.String(20), db.ForeignKey('teacher.teacher_id'), nullable=False)
    academic_year = db.Column(db.String(20), nullable=False, index=True)
    semester = db.Column(db.String(10), nullable=False, index=True)
    class_time = db.Column(db.String(100))
    location = db.Column(db.String(100))
    exam_time = db.Column(db.DateTime)
    enrollment_limit = db.Column(db.Integer, default=0)
    current_enrollment = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('course_id', 'teacher_id', 'academic_year', 'semester', 
                          name='uq_assignment_course_teacher_year_semester'),
    )
    
    course = db.relationship('Course', 
                            back_populates='assignments',
                            foreign_keys=[course_id])
    teacher = db.relationship('Teacher', 
                             back_populates='assignments',
                             foreign_keys=[teacher_id])
    selections = db.relationship('Selection', 
                                back_populates='assignment', 
                                cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Assignment {self.assignment_id}>'

class Selection(db.Model):
    __tablename__ = 'selection'
    selection_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.String(20), db.ForeignKey('student.student_id'), nullable=False)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.assignment_id'), nullable=False)
    usual_grade = db.Column(db.Float)
    final_grade = db.Column(db.Float)
    selection_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    grade_time = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('student_id', 'assignment_id', name='uq_selection_student_assignment'),
    )
    
    student = db.relationship('Student', 
                             back_populates='selections',
                             foreign_keys=[student_id])
    assignment = db.relationship('Assignment', 
                                back_populates='selections',
                                foreign_keys=[assignment_id])
    
    @property
    def total_grade(self):
        if self.usual_grade is None and self.final_grade is None:
            return None
        elif self.usual_grade is None:
            return self.final_grade
        elif self.final_grade is None:
            return self.usual_grade
        else:
            return round(self.usual_grade * 0.3 + self.final_grade * 0.7, 2)
    
    def __repr__(self):
        return f'<Selection {self.selection_id}>'