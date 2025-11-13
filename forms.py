from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DecimalField, DateField, SubmitField, HiddenField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Optional, NumberRange, EqualTo, Length, Email

class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=1, max=150)])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

class RegisterForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=1, max=150)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=255)])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Повторите пароль', validators=[DataRequired(), EqualTo('password', message='Пароли должны совпадать')])
    # Поле для создания администратора (если хотите разрешать ставить при регистрации)
    # Если не хотите показывать это поле обычным пользователям — удалите из шаблона register.html или
    # контролируйте отображение на стороне шаблона (только для админов).
    is_admin = BooleanField('Сделать администратором')
    submit = SubmitField('Зарегистрироваться')

class ContractForm(FlaskForm):
    contract_date = DateField('Дата договора', validators=[DataRequired()])
    contract_number = StringField('Номер договора', validators=[DataRequired()])
    contractor = StringField('Контрагент', validators=[Optional()])
    main_or_additional = SelectField('Тип', choices=[('Основной', 'Основной'), ('Доп соглашение', 'Доп соглашение')], validators=[DataRequired()])
    parent_contract = SelectField('Основной договор (для доп.)', coerce=int, choices=[], validators=[Optional()])
    extra_type = SelectField('Тип доп. соглашения', choices=[('', '— (нет) —'), ('add_amount', 'Доп. сумма'), ('termination', 'Досрочное расторжение')], validators=[Optional()])
    payment_type = SelectField('Вид оплаты', choices=[('', '— (нет) —'), ('по факту', 'по факту'), ('предоплата', 'предоплата')], validators=[Optional()])
    # Сумма по договору (для основного и для доп. соглашения теперь используется это поле)
    amount_total = DecimalField('Сумма по договору', places=2, validators=[Optional(), NumberRange(min=0)])
    amount_paid = DecimalField('Оплачено', places=2, validators=[Optional(), NumberRange(min=0)])
    status = SelectField('Статус', choices=[('в работе', 'в работе'), ('исполнен', 'исполнен'), ('расторгнут', 'расторгнут')], validators=[DataRequired()])
    submit = SubmitField('Сохранить')

class ServiceForm(FlaskForm):
    date = DateField('Дата', validators=[DataRequired()])
    description = StringField('Описание', validators=[DataRequired()])
    unit = StringField('Ед. изм.', validators=[Optional()])
    quantity = DecimalField('Количество', places=2, validators=[Optional(), NumberRange(min=0)])
    price_per_unit = DecimalField('Цена за ед.', places=2, validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField('Добавить')

class PaymentForm(FlaskForm):
    date = DateField('Дата оплаты', validators=[Optional()])
    amount_paid = DecimalField('Сумма', places=2, validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Зачесть')

class ExtraServiceForm(FlaskForm):
    date = DateField('Дата', validators=[Optional()])
    description = StringField('Описание', validators=[DataRequired()])
    price = DecimalField('Цена', places=2, validators=[Optional(), NumberRange(min=0)])
    total = DecimalField('Сумма', places=2, validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField('Добавить')