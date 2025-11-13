from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
from forms import LoginForm, RegisterForm

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.query(User).filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash("Вход выполнен", "success")
            next_page = request.args.get('next') or url_for('main.contracts')
            return redirect(next_page)
        flash("Неверные учётные данные", "danger")
    return render_template('login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Выход выполнен", "info")
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    # регистрация доступна только админам
    if not current_user.is_admin:
        flash("Нет доступа", "danger")
        return redirect(url_for('main.contracts'))
    form = RegisterForm()
    if form.validate_on_submit():
        existing = db.session.query(User).filter_by(username=form.username.data).first()
        if existing:
            flash("Пользователь с таким именем уже существует", "danger")
            return render_template('register.html', form=form)
        user = User(username=form.username.data,
                    password=generate_password_hash(form.password.data),
                    is_admin=bool(form.is_admin.data))
        db.session.add(user)
        db.session.commit()
        flash("Пользователь создан", "success")
        return redirect(url_for('auth.users'))
    return render_template('register.html', form=form)

@auth_bp.route('/users')
@login_required
def users():
    # только админ видит список пользователей
    if not current_user.is_admin:
        flash("Нет доступа", "danger")
        return redirect(url_for('main.contracts'))
    users = db.session.query(User).order_by(User.created_at.desc()).all()
    return render_template('users.html', users=users)

@auth_bp.route('/delete_user/<int:uid>', methods=['POST'])
@login_required
def delete_user(uid):
    if not current_user.is_admin:
        flash("Нет доступа", "danger")
        return redirect(url_for('auth.users'))
    user = db.session.get(User, uid)
    if not user:
        flash("Пользователь не найден", "danger")
        return redirect(url_for('auth.users'))
    if user.id == current_user.id:
        flash("Нельзя удалить себя", "danger")
        return redirect(url_for('auth.users'))
    db.session.delete(user)
    db.session.commit()
    flash("Пользователь удалён", "success")
    return redirect(url_for('auth.users'))