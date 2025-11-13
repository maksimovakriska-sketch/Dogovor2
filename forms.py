from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, SelectField, BooleanField
from wtforms.fields import DateField
from wtforms.validators import DataRequired, Length, EqualTo, Optional

class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

class RegisterForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=4, max=25)])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Повторите пароль', validators=[DataRequired(), EqualTo('password')])
    is_admin = BooleanField('Админ?')
    submit = SubmitField('Зарегистрировать')

class ContractForm(FlaskForm):
    contract_date = DateField('Дата договора', validators=[DataRequired()], format='%Y-%m-%d')
    contract_number = StringField('Номер договора', validators=[DataRequired()])
    contractor = StringField('Контрагент', validators=[DataRequired()])
    main_or_additional = SelectField('Тип', choices=[("Основной договор", "Основной договор"), ("Доп соглашение", "Доп соглашение")])
    parent_contract = SelectField('К какому основному договору', coerce=int, choices=[], validators=[Optional()])
    extra_type = SelectField('Тип доп. соглашения', choices=[("", "—"), ("add_amount", "Доп. сумма"), ("termination", "Досрочное расторжение")], validators=[Optional()])
    extra_amount = FloatField('Сумма доп. выплаты', validators=[Optional()])
    payment_type = SelectField('Вид оплаты', choices=[("по факту", "По факту"), ("аванс", "Аванс")])
    amount_total = FloatField('Сумма по договору', validators=[Optional()])
    amount_paid = FloatField('Оплачено', validators=[Optional()])
    status = SelectField('Статус', choices=[("в работе", "В работе"), ("исполнен", "Исполнен"), ("расторгнут", "Расторгнут")])
    submit = SubmitField('Сохранить')

class ServiceForm(FlaskForm):
    date = DateField('Дата оказания', validators=[DataRequired()], format='%Y-%m-%d')
    description = StringField('Описание услуги', validators=[DataRequired()])
    unit = SelectField('Единица измерения', choices=[("час", "Час"), ("шт", "Штука")])
    quantity = FloatField('Количество', validators=[DataRequired()])
    price_per_unit = FloatField('Цена за единицу', validators=[DataRequired()])
    submit = SubmitField('Добавить услугу')

class ExtraServiceForm(FlaskForm):
    date = DateField('Дата доп. услуги', validators=[Optional()], format='%Y-%m-%d')
    description = StringField('Описание доп. услуги', validators=[DataRequired()])
    price = FloatField('Стоимость за услугу', validators=[DataRequired()])
    total = FloatField('Сумма услуги', validators=[DataRequired()])
    submit = SubmitField('Добавить доп. услугу')

class PaymentForm(FlaskForm):
    date = DateField('Дата оплаты', validators=[Optional()], format='%Y-%m-%d')
    amount_paid = FloatField('Сумма оплаты', validators=[DataRequired()])
    submit = SubmitField('Зачесть оплату')