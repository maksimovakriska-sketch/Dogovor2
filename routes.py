from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import current_user, login_required
from datetime import datetime, date

from models import db, Contract, Service, ExtraService, ContractHistory
from forms import ContractForm, ServiceForm, PaymentForm, ExtraServiceForm

main_bp = Blueprint('main', __name__)

def to_float(value):
    """Безопасно привести к float: поддерживает Decimal, None, int, float, str."""
    try:
        if value is None:
            return 0.0
        return float(value)
    except Exception:
        try:
            return float(str(value))
        except Exception:
            return 0.0

@main_bp.route('/')
def index():
    return redirect(url_for('main.contracts'))

@main_bp.route('/contracts')
@login_required
def contracts():
    sort_by = request.args.get('sort_by', 'date')
    order = request.args.get('order', 'desc')

    q = Contract.query.filter_by(archived=False, parent_id=None)
    if sort_by == 'date':
        q = q.order_by(Contract.contract_date.desc() if order != 'asc' else Contract.contract_date.asc())
    else:
        q = q.order_by(Contract.contract_date.desc())

    contracts = q.all()

    # Подсчёт оплачено по доп. соглашениям и флага наличия доп. соглашений
    extra_paid_map = {}
    has_children_map = {}
    for c in contracts:
        children = Contract.query.filter_by(parent_id=c.id).all()
        extra_paid = sum(to_float(ch.amount_paid) for ch in children)
        extra_paid_map[c.id] = extra_paid
        has_children_map[c.id] = len(children) > 0

    return render_template('contracts.html', contracts=contracts, extra_paid_map=extra_paid_map, has_children_map=has_children_map)

@main_bp.route('/contracts/archived')
@login_required
def contracts_archived():
    sort_by = request.args.get('sort_by', 'date')
    order = request.args.get('order', 'desc')

    q = Contract.query.filter_by(archived=True, parent_id=None)
    if sort_by == 'date':
        q = q.order_by(Contract.contract_date.desc() if order != 'asc' else Contract.contract_date.asc())
    else:
        q = q.order_by(Contract.contract_date.desc())

    contracts = q.all()

    extra_paid_map = {}
    has_children_map = {}
    for c in contracts:
        children = Contract.query.filter_by(parent_id=c.id).all()
        extra_paid = sum(to_float(ch.amount_paid) for ch in children)
        extra_paid_map[c.id] = extra_paid
        has_children_map[c.id] = len(children) > 0

    return render_template('archived_contracts.html', contracts=contracts, extra_paid_map=extra_paid_map, has_children_map=has_children_map)

@main_bp.route('/contract/<int:cid>', methods=['GET', 'POST'])
@login_required
def contract_detail(cid):
    contract = db.session.get(Contract, cid)
    if not contract:
        abort(404)

    service_form = ServiceForm()
    payment_form = PaymentForm()
    extra_service_form = ExtraServiceForm()

    services_q = Service.query.filter_by(contract_id=contract.id).order_by(Service.date.desc()).all()
    extra_services_q = ExtraService.query.filter_by(contract_id=contract.id).order_by(ExtraService.date.desc()).all()

    history = ContractHistory.query.filter_by(contract_id=contract.id).order_by(ContractHistory.date.desc()).all()

    if request.method == "POST":
        form_name = request.form.get('form_name')

        if form_name == 'service' and service_form.validate_on_submit():
            svc_date = service_form.date.data
            svc_dt = datetime.combine(svc_date, datetime.min.time()) if isinstance(svc_date, date) else datetime.utcnow()
            new_service = Service(
                contract_id=contract.id,
                date=svc_dt,
                description=service_form.description.data,
                unit=service_form.unit.data,
                quantity=to_float(service_form.quantity.data),
                price_per_unit=to_float(service_form.price_per_unit.data),
                total=to_float(service_form.quantity.data) * to_float(service_form.price_per_unit.data),
            )
            contract.amount_earned = to_float(contract.amount_earned) + to_float(new_service.total)
            db.session.add(new_service)
            db.session.add(ContractHistory(
                contract_id=contract.id,
                action=f"Добавлена услуга: {new_service.description}, сумма {to_float(new_service.total):.2f}",
                actor=current_user.username,
                date=svc_dt
            ))
            db.session.commit()
            flash("Услуга добавлена", "success")
            return redirect(url_for('main.contract_detail', cid=cid))

        elif form_name == 'payment' and payment_form.validate_on_submit():
            pay_date = payment_form.date.data
            pay_dt = datetime.combine(pay_date, datetime.min.time()) if isinstance(pay_date, date) else datetime.utcnow()
            amount = to_float(payment_form.amount_paid.data)
            contract.amount_paid = to_float(contract.amount_paid) + amount
            db.session.add(ContractHistory(
                contract_id=contract.id,
                action=f"Добавлена оплата {amount:.2f}",
                actor=current_user.username,
                date=pay_dt
            ))
            db.session.commit()
            flash("Оплата засчитана", "success")
            return redirect(url_for('main.contract_detail', cid=cid))

        elif form_name == 'extra_service' and extra_service_form.validate_on_submit():
            ex_date = extra_service_form.date.data
            ex_dt = datetime.combine(ex_date, datetime.min.time()) if isinstance(ex_date, date) else datetime.utcnow()
            new_ex = ExtraService(
                contract_id=contract.id,
                date=ex_dt,
                description=extra_service_form.description.data,
                price=to_float(extra_service_form.price.data),
                total=to_float(extra_service_form.total.data),
            )
            contract.amount_earned = to_float(contract.amount_earned) + to_float(new_ex.total)
            db.session.add(new_ex)
            db.session.add(ContractHistory(
                contract_id=contract.id,
                action=f"Добавлена доп. услуга: {new_ex.description}, сумма {to_float(new_ex.total):.2f}",
                actor=current_user.username,
                date=ex_dt
            ))
            db.session.commit()
            flash("Доп. услуга добавлена", "success")
            return redirect(url_for('main.contract_detail', cid=cid))

    subs = Contract.query.filter_by(parent_id=contract.id).order_by(Contract.contract_date.desc()).all()

    combined_services = []
    for s in services_q:
        combined_services.append({
            'date': s.date,
            'date_display': s.date.strftime('%d.%m.%Y') if s.date else '-',
            'description': s.description,
            'total': to_float(s.total),
            'is_extra': False,
            'id': getattr(s, 'id', None)
        })
    for ex in extra_services_q:
        combined_services.append({
            'date': ex.date,
            'date_display': ex.date.strftime('%d.%m.%Y') if ex.date else '-',
            'description': ex.description,
            'total': to_float(ex.total),
            'is_extra': True,
            'id': getattr(ex, 'id', None)
        })
    combined_services.sort(key=lambda x: x['date'] or datetime.min, reverse=True)

    return render_template('contract_detail.html',
                           contract=contract,
                           services=combined_services,
                           extra_services=extra_services_q,
                           subs=subs,
                           service_form=service_form,
                           payment_form=payment_form,
                           extra_service_form=extra_service_form,
                           history=history)


@main_bp.route('/contract_new', methods=['GET', 'POST'])
@main_bp.route('/contract_edit/<int:cid>', methods=['GET', 'POST'])
@login_required
def contract_edit(cid=None):
    # … (логика создания/редактирования договоров — без изменений) …
   def contract_edit(cid=None):
    # Список только номеров основных договоров
    main_contracts = Contract.query.filter_by(parent_id=None).order_by(Contract.contract_date.desc()).all()
    choices = [(0, "— (нет) —")]
    for c in main_contracts:
        if cid and c.id == cid:
            continue
        choices.append((c.id, f"{c.contract_number}"))

    contract = db.session.get(Contract, cid) if cid else None
    if cid and not contract:
        flash("Договор не найден", "danger")
        return redirect(url_for('main.contracts'))
    if cid and not current_user.is_admin and contract and contract.user_id != current_user.id:
        flash("Нет доступа", "danger")
        return redirect(url_for('main.contracts'))

    form = ContractForm(obj=contract)
    form.parent_contract.choices = choices

    # Сохраняем старые значения для корректировки родителя при редактировании
    orig_parent_id = contract.parent_id if contract else None
    orig_extra_type = contract.extra_type if contract else None
    # previously extra amount could be stored in extra_amount field; now extras may use amount_total as the "add amount"
    if contract and orig_extra_type == "add_amount":
        orig_extra_amount = contract.extra_amount if (contract.extra_amount is not None) else contract.amount_total
    else:
        orig_extra_amount = contract.extra_amount if contract else None
    orig_amount_paid = contract.amount_paid if contract else None

    if request.method == 'GET' and contract:
        form.parent_contract.data = contract.parent_id or 0
        form.extra_type.data = contract.extra_type or ""
        # populate amount_total/amount_paid for form
        form.amount_total.data = contract.amount_total
        form.amount_paid.data = contract.amount_paid

    if form.validate_on_submit():
        is_extra = (form.main_or_additional.data == "Доп соглашение")
        parent_id = form.parent_contract.data if form.parent_contract.data else None
        extra_type = form.extra_type.data or None
        # For add_amount extra agreements, the amount is taken from amount_total
        extra_amount_from_amount_total = to_float(form.amount_total.data) if form.amount_total.data is not None else None
        amount_paid_input = to_float(form.amount_paid.data) if form.amount_paid.data is not None else 0.0

        # Валидации
        if is_extra and not parent_id:
            flash("Для доп. соглашения выберите основной договор", "danger")
            return render_template('edit_contract.html', form=form, contract=contract)
        if is_extra and extra_type == "add_amount" and (extra_amount_from_amount_total is None or extra_amount_from_amount_total <= 0):
            flash("Для доп. соглашения типа 'Доп. сумма' укажите корректную сумму (поле 'Сумма по договору')", "danger")
            return render_template('edit_contract.html', form=form, contract=contract)
        if is_extra and extra_type == "add_amount" and not form.payment_type.data:
            flash("Для доп. соглашения типа 'Доп. сумма' выберите вид оплаты", "danger")
            return render_template('edit_contract.html', form=form, contract=contract)
        if not is_extra and (form.amount_total.data is None):
            flash("Для основного договора укажите сумму по договору", "danger")
            return render_template('edit_contract.html', form=form, contract=contract)

        if contract:
            # Update existing contract
            contract.contract_date = form.contract_date.data
            contract.contract_number = form.contract_number.data
            contract.contractor = form.contractor.data
            contract.main_or_additional = form.main_or_additional.data
            contract.payment_type = form.payment_type.data
            contract.amount_total = to_float(form.amount_total.data)
            contract.amount_paid = to_float(form.amount_paid.data)
            contract.status = form.status.data

            # Если ранее был связан с каким-то parent и был add_amount — откатим вклад в старого родителя (и сумму, и оплачено)
            if orig_parent_id and orig_extra_type == "add_amount":
                old_parent = db.session.get(Contract, orig_parent_id)
                if old_parent:
                    old_parent.amount_total = max(0.0, to_float(old_parent.amount_total) - to_float(orig_extra_amount))
                    if orig_amount_paid:
                        old_parent.amount_paid = max(0.0, to_float(old_parent.amount_paid) - to_float(orig_amount_paid))
                    db.session.add(ContractHistory(
                        contract_id=old_parent.id,
                        action=f"Откат участия доп. соглашения №{contract.contract_number}: -{to_float(orig_extra_amount):.2f}, оплачено откат: -{to_float(orig_amount_paid):.2f}",
                        actor=current_user.username,
                        date=datetime.utcnow()
                    ))

            # Применяем новые значения (если теперь договор — доп. соглашение)
            if is_extra:
                contract.parent_id = parent_id
                contract.extra_type = extra_type
                # Keep legacy extra_amount clear, amount_total used for add_amount
                contract.extra_amount = None
                if extra_type == "add_amount" and parent_id:
                    parent = db.session.get(Contract, parent_id)
                    if parent:
                        parent.amount_total = to_float(parent.amount_total) + to_float(contract.amount_total)
                        if amount_paid_input:
                            parent.amount_paid = to_float(parent.amount_paid) + amount_paid_input
                        db.session.add(ContractHistory(
                            contract_id=parent.id,
                            action=f"К договору добавлено/обновлено доп. соглашение №{contract.contract_number}: +{to_float(contract.amount_total):.2f}",
                            actor=current_user.username,
                            date=datetime.utcnow()
                        ))
                        if amount_paid_input:
                            db.session.add(ContractHistory(
                                contract_id=parent.id,
                                action=f"Оплачено по доп. соглашению №{contract.contract_number}: +{amount_paid_input:.2f}",
                                actor=current_user.username,
                                date=datetime.utcnow()
                            ))
            else:
                # если теперь основной — очистим доп. поля
                contract.parent_id = None
                contract.extra_type = None
                contract.extra_amount = None

            db.session.add(ContractHistory(
                contract_id=contract.id,
                action="Изменение договора",
                actor=current_user.username,
                date=datetime.utcnow()
            ))
            db.session.commit()
            flash("Изменения сохранены", "success")
            return redirect(url_for('main.contracts'))

        else:
            # Create new contract (main or extra)
            new_contract = Contract(
                contract_date=form.contract_date.data,
                contract_number=form.contract_number.data,
                contractor=form.contractor.data,
                main_or_additional=form.main_or_additional.data,
                payment_type=form.payment_type.data,
                amount_total=to_float(form.amount_total.data),
                amount_paid=to_float(form.amount_paid.data),
                status=form.status.data,
                user_id=current_user.id
            )
            if is_extra:
                new_contract.parent_id = parent_id
                new_contract.extra_type = extra_type
                new_contract.extra_amount = None

            db.session.add(new_contract)
            db.session.commit()

            # Если доп. соглашение типа add_amount — применяем его вклад в parent (и оплачено если указано)
            if is_extra and new_contract.extra_type == "add_amount" and new_contract.parent_id:
                parent = db.session.get(Contract, new_contract.parent_id)
                if parent:
                    parent.amount_total = to_float(parent.amount_total) + to_float(new_contract.amount_total)
                    if new_contract.amount_paid:
                        parent.amount_paid = to_float(parent.amount_paid) + to_float(new_contract.amount_paid)
                        db.session.add(ContractHistory(
                            contract_id=parent.id,
                            action=f"Оплачено по доп. соглашению №{new_contract.contract_number}: +{to_float(new_contract.amount_paid):.2f}",
                            actor=current_user.username,
                            date=datetime.utcnow()
                        ))
                    db.session.add(ContractHistory(
                        contract_id=parent.id,
                        action=f"К договору добавлено доп. соглашение №{new_contract.contract_number}: +{to_float(new_contract.amount_total):.2f}",
                        actor=current_user.username,
                        date=datetime.utcnow()
                    ))
                    db.session.commit()

            # Если доп. соглашение — досрочное расторжение
            if is_extra and new_contract.extra_type == "termination" and new_contract.parent_id:
                parent = db.session.get(Contract, new_contract.parent_id)
                if parent:
                    parent.status = "расторгнут"
                    db.session.add(ContractHistory(
                        contract_id=parent.id,
                        action=f"К договору добавлено доп. соглашение №{new_contract.contract_number}: досрочное расторжение",
                        actor=current_user.username,
                        date=datetime.utcnow()
                    ))
                    db.session.commit()

            flash("Договор создан", "success")
            return redirect(url_for('main.contracts'))

    return render_template('edit_contract.html', form=form, contract=contract)
    pass


@main_bp.route('/contract_delete/<int:cid>', methods=['POST'])
@login_required
def contract_delete(cid):
    contract = db.session.get(Contract, cid)
    if not contract:
        abort(404)
    if not current_user.is_admin and contract.user_id != current_user.id:
        flash("Нет доступа", "danger")
        return redirect(url_for('main.contracts'))

    try:
        # Если это доп. соглашение — нужно откатить влияние на родителя
        if contract.parent_id:
            parent = db.session.get(Contract, contract.parent_id)
            if parent:
                if contract.extra_type == 'add_amount' and contract.amount_total:
                    parent.amount_total = max(0.0, to_float(parent.amount_total) - to_float(contract.amount_total))
                    db.session.add(ContractHistory(
                        contract_id=parent.id,
                        action=f"Откат доп. суммы при удалении доп. соглашения №{contract.contract_number}: -{to_float(contract.amount_total):.2f}",
                        actor=current_user.username,
                        date=datetime.utcnow()
                    ))
                if contract.extra_type == 'add_amount' and contract.amount_paid:
                    parent.amount_paid = max(0.0, to_float(parent.amount_paid) - to_float(contract.amount_paid))
                    db.session.add(ContractHistory(
                        contract_id=parent.id,
                        action=f"Откат оплаты при удалении доп. соглашения №{contract.contract_number}: -{to_float(contract.amount_paid):.2f}",
                        actor=current_user.username,
                        date=datetime.utcnow()
                    ))
                if contract.extra_type == 'termination':
                    db.session.add(ContractHistory(
                        contract_id=parent.id,
                        action=f"Удалено доп. соглашение №{contract.contract_number} типа 'досрочное расторжение' — проверьте статус основного договора вручную",
                        actor=current_user.username,
                        date=datetime.utcnow()
                    ))

        # Удаляем все записи истории, которые принадлежат удаляемому договору,
        # чтобы избежать попыток SQLAlchemy/DB обнулить FK (и получить IntegrityError).
        db.session.query(ContractHistory).filter_by(contract_id=contract.id).delete(synchronize_session=False)

        # Удаляем сам договор
        db.session.delete(contract)
        db.session.commit()
        flash("Договор удалён", "success")
    except Exception as e:
        db.session.rollback()
        flash("Ошибка при удалении договора: " + str(e), "danger")
    return redirect(url_for('main.contracts'))

@main_bp.route('/contract_archive/<int:cid>', methods=['POST'])
@login_required
def contract_archive(cid):
    contract = db.session.get(Contract, cid)
    if not contract:
        abort(404)
    if not current_user.is_admin:
        flash("Нет доступа", "danger")
        return redirect(url_for('main.contracts'))
    contract.archived = True
    db.session.add(ContractHistory(
        contract_id=contract.id,
        action="Договор архивирован",
        actor=current_user.username,
        date=datetime.utcnow()
    ))
    db.session.commit()
    flash("Договор перемещён в архив", "success")
    return redirect(url_for('main.contracts'))


@main_bp.route('/contract_unarchive/<int:cid>', methods=['POST'])
@login_required
def contract_unarchive(cid):
    contract = db.session.get(Contract, cid)
    if not contract:
        abort(404)
    if not current_user.is_admin:
        flash("Нет доступа", "danger")
        return redirect(url_for('main.contracts_archived'))
    contract.archived = False
    db.session.add(ContractHistory(
        contract_id=contract.id,
        action="Договор восстановлен из архива",
        actor=current_user.username,
        date=datetime.utcnow()
    ))
    db.session.commit()
    flash("Договор восстановлен из архива", "success")
    return redirect(url_for('main.contracts_archived'))


# Service edit/delete and extra_service edit/delete (POST for deletes)
@main_bp.route('/service_edit/<int:sid>', methods=['GET', 'POST'])
@login_required
def service_edit(sid):
    svc = db.session.get(Service, sid)
    if not svc:
        abort(404)
    contract = db.session.get(Contract, svc.contract_id)
    if not contract:
        abort(404)
    if not current_user.is_admin and contract.user_id != current_user.id:
        flash("Нет доступа", "danger")
        return redirect(url_for('main.contract_detail', cid=contract.id))
    form = ServiceForm(obj=svc)
    if request.method == 'GET' and svc.date:
        form.date.data = svc.date.date()
    if form.validate_on_submit():
        old_total = to_float(svc.total)
        svc_date = form.date.data
        svc_dt = datetime.combine(svc_date, datetime.min.time()) if isinstance(svc_date, date) else datetime.utcnow()
        svc.date = svc_dt
        svc.description = form.description.data
        svc.unit = form.unit.data
        svc.quantity = to_float(form.quantity.data)
        svc.price_per_unit = to_float(form.price_per_unit.data)
        svc.total = to_float(svc.quantity) * to_float(svc.price_per_unit)
        delta = to_float(svc.total) - old_total
        contract.amount_earned = to_float(contract.amount_earned) + delta
        db.session.add(ContractHistory(
            contract_id=contract.id,
            action=f"Изменена услуга: {svc.description}, новая сумма {to_float(svc.total):.2f}, изменение {delta:+.2f}",
            actor=current_user.username,
            date=svc_dt
        ))
        db.session.commit()
        flash("Услуга обновлена", "success")
        return redirect(url_for('main.contract_detail', cid=contract.id))
    return render_template('service_edit.html', form=form, service=svc, contract=contract)


@main_bp.route('/service_delete/<int:sid>', methods=['POST'])
@login_required
def service_delete(sid):
    svc = db.session.get(Service, sid)
    if not svc:
        abort(404)
    contract = db.session.get(Contract, svc.contract_id)
    if not contract:
        abort(404)
    if not current_user.is_admin and contract.user_id != current_user.id:
        flash("Нет доступа", "danger")
        return redirect(url_for('main.contract_detail', cid=contract.id))
    contract.amount_earned = max(0.0, to_float(contract.amount_earned) - to_float(svc.total))
    db.session.add(ContractHistory(
        contract_id=contract.id,
        action=f"Удалена услуга: {svc.description}, сумма {to_float(svc.total):.2f}",
        actor=current_user.username,
        date=datetime.utcnow()
    ))
    db.session.delete(svc)
    db.session.commit()
    flash("Услуга удалена", "success")
    return redirect(url_for('main.contract_detail', cid=contract.id))


@main_bp.route('/extra_service_edit/<int:eid>', methods=['GET', 'POST'])
@login_required
def extra_service_edit(eid):
    ex = db.session.get(ExtraService, eid)
    if not ex:
        abort(404)
    contract = db.session.get(Contract, ex.contract_id)
    if not contract:
        abort(404)
    if not current_user.is_admin and contract.user_id != current_user.id:
        flash("Нет доступа", "danger")
        return redirect(url_for('main.contract_detail', cid=contract.id))
    form = ExtraServiceForm(obj=ex)
    if request.method == 'GET' and ex.date:
        form.date.data = ex.date.date()
    if form.validate_on_submit():
        old_total = to_float(ex.total)
        ex_date = form.date.data
        ex_dt = datetime.combine(ex_date, datetime.min.time()) if isinstance(ex_date, date) else datetime.utcnow()
        ex.date = ex_dt
        ex.description = form.description.data
        ex.price = to_float(form.price.data)
        ex.total = to_float(form.total.data)
        delta = to_float(ex.total) - old_total
        contract.amount_earned = to_float(contract.amount_earned) + delta
        db.session.add(ContractHistory(
            contract_id=contract.id,
            action=f"Изменена доп. услуга: {ex.description}, новая сумма {to_float(ex.total):.2f}, изменение {delta:+.2f}",
            actor=current_user.username,
            date=ex_dt
        ))
        db.session.commit()
        flash("Доп. услуга обновлена", "success")
        return redirect(url_for('main.contract_detail', cid=contract.id))
    return render_template('extra_service_edit.html', form=form, extra_service=ex, contract=contract)


@main_bp.route('/extra_service_delete/<int:eid>', methods=['POST'])
@login_required
def extra_service_delete(eid):
    ex = db.session.get(ExtraService, eid)
    if not ex:
        abort(404)
    contract = db.session.get(Contract, ex.contract_id)
    if not contract:
        abort(404)
    if not current_user.is_admin and contract.user_id != current_user.id:
        flash("Нет доступа", "danger")
        return redirect(url_for('main.contract_detail', cid=contract.id))
    contract.amount_earned = max(0.0, to_float(contract.amount_earned) - to_float(ex.total))
    db.session.add(ContractHistory(
        contract_id=contract.id,
        action=f"Удалена доп. услуга: {ex.description}, сумма {to_float(ex.total):.2f}",
        actor=current_user.username,
        date=datetime.utcnow()
    ))
    db.session.delete(ex)
    db.session.commit()
    flash("Доп. услуга удалена", "success")
    return redirect(url_for('main.contract_detail', cid=contract.id))


@main_bp.route('/contract_history/<int:cid>')
@login_required
def contract_history(cid):
    contract = db.session.get(Contract, cid)
    if not contract:
        abort(404)
    history = ContractHistory.query.filter_by(contract_id=contract.id).order_by(ContractHistory.date.desc()).all()
    return render_template("history.html", history=history, contract=contract)
# … остальной код (архивация/восстановление/работа с услугами и т.д.) без изменений …
# Поместите остальные обработчики из вашего текущего routes.py сюда (service_edit, service_delete, extra_service_edit, extra_service_delete, contract_history и т.д.).