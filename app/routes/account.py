from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.forms import ChangePasswordForm

bp = Blueprint('account', __name__, url_prefix='/account')

@bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """修改密码"""
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        # 验证当前密码
        if not current_user.check_password(form.current_password.data):
            flash('当前密码错误', 'danger')
            return render_template('account/change_password.html', form=form)
        
        # 更新密码
        current_user.set_password(form.new_password.data)
        db.session.commit()
        
        flash('密码修改成功，请重新登录', 'success')
        return redirect(url_for('auth.logout'))
    
    return render_template('account/change_password.html', form=form)