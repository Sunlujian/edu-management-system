from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse
from app import db
from app.models import User
from app.forms import LoginForm, RegistrationForm, ChangePasswordForm

bp = Blueprint('auth', __name__)

# ================= 登录 =================
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user is None or not user.check_password(form.password.data):
            flash('用户名或密码错误', 'danger')
            return redirect(url_for('auth.login'))

        login_user(user, remember=form.remember_me.data)

        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.dashboard')

        flash('登录成功！', 'success')
        return redirect(next_page)

    return render_template('common/login.html', form=form)


# ================= 注册（禁用） =================
@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    flash('系统暂不开放公共注册，请联系管理员创建账号', 'info')
    return redirect(url_for('auth.login'))


# ================= 退出 =================
@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('您已成功退出系统', 'info')
    return redirect(url_for('main.index'))


# ================= 修改密码（新增） =================
@bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()

    if form.validate_on_submit():
        # 校验当前密码
        if not current_user.check_password(form.current_password.data):
            flash('当前密码错误', 'danger')
            return render_template('common/change_password.html', form=form)

        # 更新密码
        current_user.set_password(form.new_password.data)
        db.session.commit()

        flash('密码修改成功，请重新登录', 'success')
        return redirect(url_for('auth.logout'))

    return render_template('common/change_password.html', form=form)
