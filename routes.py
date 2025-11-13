from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import current_user, login_required
from datetime import datetime, date

from models import db, Contract, Service, ExtraService, ContractHistory
from forms import ContractForm, ServiceForm, PaymentForm, ExtraServiceForm

main_bp = Blueprint('main', __name__)

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
    return render_template('contracts.html', contracts=contracts)

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
    return render_template('archived_contracts.html', contracts=contracts)

@main_bp.route('/contract/<int:cid>', methods=['GET', 'POST'])
@login_required
def contract_detail(cid):
    contract = Contract.query.get_or_404(cid)
    service_form = ServiceForm()
    payment_form = PaymentForm()
    extra_service_form = ExtraServiceForm()

    services = Service.query.filter_by(contract_id=contract.id).order_by(Service.date.desc()).all()
    extra_services = ExtraService.query.filter_by(contract_id=contract.id).order_by(ExtraService.date.desc()).all()

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
                quantity=service_form.quantity.data or 0.0,
                price_per_unit=service_form.price_per_unit.data or 0.0,
                total=(service_form.quantity.data or 0.0) * (service_form.price_per_unit.data or 0.0),
            )
            contract.amount_earned = (contract.amount_earned or 0.0) + (new_service.total or 0.0)
            db.session.add(new_service)
            db.session.add(ContractHistory(
                contract_id=contract.id,
                action=f"Добавлена услуга: {new_service.description}, сумма {new_service.total:.2f}",
                actor=current_user.username,
                date=svc_dt
            ))
            db.session.commit()
            flash("Услуга добавлена", "success")
            return redirect(url_for('main.contract_detail', cid=cid))

        elif form_name == 'payment' and payment_form.validate_on_submit():
            pay_date = payment_form.date.data
            pay_dt = datetime.combine(pay_date, datetime.min.time()) if isinstance(pay_date, date) else datetime.utcnow()
            amount = payment_form.amount_paid.data or 0.0
            contract.amount_paid = (contract.amount_paid or 0.0) + amount
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
                price=extra_service_form.price.data or 0.0,
                total=extra_service_form.total.data or 0.0,
            )
            contract.amount_earned = (contract.amount_earned or 0.0) + (new_ex.total or 0.0)
            db.session.add(new_ex)
            db.session.add(ContractHistory(
                contract_id=contract.id,
                action=f"Добавлена доп. услуга: {new_ex.description}, сумма {new_ex.total:.2f}",
                actor=current_user.username,
                date=ex_dt
            ))
            db.session.commit()
            flash("Доп. услуга добавлена", "success")
            return redirect(url_for('main.contract_detail', cid=cid))

    return render_template('contract_detail.html',
                           contract=contract,
                           services=services,
                           extra_services=extra_services,
                           service_form=service_form,
                           payment_form=payment_form,
                           extra_service_form=extra_service_form)


@main_bp.route('/contract_new', methods=['GET', 'POST'])
@main_bp.route('/contract_edit/<int:cid>', methods=['GET', 'POST'])
@login_required
def contract_edit(cid=None):
    # Список только номеров основных договоров
    main_contracts = Contract.query.filter_by(parent_id=None).order_by(Contract.contract_date.desc()).all()
    choices = [(0, "— (нет) —")]
    for c in main_contracts:
        if cid and c.id == cid:
            continue
        choices.append((c.id, f"{c.contract_number}"))

    contract = Contract.query.get(cid) if cid else None
    if cid and not contract:
        flash("Договор не найден", "danger")
        return redirect(url_for('main.contracts'))
    if cid and not current_user.is_admin and contract.user_id != current_user.id:
        flash("Нет доступа", "danger")
        return redirect(url_for('main.contracts'))

    form = ContractForm(obj=contract)
    form.parent_contract.choices = choices

    # Сохраняем старые значения для корректировки родителя при редактировании
    orig_parent_id = contract.parent_id if contract else None
    orig_extra_type = contract.extra_type if contract else None
    orig_extra_amount = contract.extra_amount if contract else None
    orig_amount_paid = contract.amount_paid if contract else None

    if request.method == 'GET' and contract:
        form.parent_contract.data = contract.parent_id or 0
        form.extra_type.data = contract.extra_type or ""
        form.extra_amount.data = contract.extra_amount
        form.amount_total.data = contract.amount_total
        form.amount_paid.data = contract.amount_paid

    if form.validate_on_submit():
        is_extra = (form.main_or_additional.data == "Доп соглашение")
        parent_id = form.parent_contract.data if form.parent_contract.data else None
        extra_type = form.extra_type.data or None
        extra_amount = form.extra_amount.data if form.extra_amount.data else None
        amount_paid_input = form.amount_paid.data if form.amount_paid.data else 0.0

        # Валидации
        if is_extra and not parent_id:
            flash("Для доп. соглашения выберите основной договор", "danger")
            return render_template('edit_contract.html', form=form, contract=contract)
        if is_extra and extra_type == "add_amount" and (extra_amount is None or extra_amount <= 0):
            flash("Для доп. соглашения типа 'Доп. сумма' укажите корректную сумму", "danger")
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
            contract.amount_total = form.amount_total.data or 0.0
            contract.amount_paid = form.amount_paid.data or 0.0
            contract.status = form.status.data

            # Если ранее был связан с каким-то parent и был add_amount — откатим вклад в старого родителя (и сумму, и оплачено)
            if orig_parent_id and orig_extra_type == "add_amount":
                old_parent = Contract.query.get(orig_parent_id)
                if old_parent:
                    old_parent.amount_total = max(0.0, (old_parent.amount_total or 0.0) - (orig_extra_amount or 0.0))
                    if orig_amount_paid:
                        old_parent.amount_paid = max(0.0, (old_parent.amount_paid or 0.0) - (orig_amount_paid or 0.0))
                    db.session.add(ContractHistory(
                        contract_id=old_parent.id,
                        action=f"Откат участия доп. соглашения #{contract.id}: -{orig_extra_amount or 0:.2f}, оплачено откат: -{orig_amount_paid or 0:.2f}",
                        actor=current_user.username
                    ))

            # Применяем новые значения (если теперь договор — доп. соглашение)
            if is_extra:
                contract.parent_id = parent_id
                contract.extra_type = extra_type
                contract.extra_amount = extra_amount
                # Если новый тип add_amount — применяем вклад в родителя
                if extra_type == "add_amount" and parent_id:
                    parent = Contract.query.get(parent_id)
                    if parent:
                        parent.amount_total = (parent.amount_total or 0.0) + (extra_amount or 0.0)
                        if amount_paid_input:
                            parent.amount_paid = (parent.amount_paid or 0.0) + amount_paid_input
                        db.session.add(ContractHistory(
                            contract_id=parent.id,
                            action=f"К договору добавлено/обновлено доп. соглашение #{contract.id}: +{extra_amount or 0:.2f}",
                            actor=current_user.username
                        ))
                        if amount_paid_input:
                            db.session.add(ContractHistory(
                                contract_id=parent.id,
                                action=f"Оплачено по доп. соглашению #{contract.id}: +{amount_paid_input:.2f}",
                                actor=current_user.username
                            ))
            else:
                # если теперь основной — очистим доп. поля
                contract.parent_id = None
                contract.extra_type = None
                contract.extra_amount = None

            db.session.add(ContractHistory(
                contract_id=contract.id,
                action="Изменение договора",
                actor=current_user.username
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
                amount_total=form.amount_total.data or 0.0,
                amount_paid=form.amount_paid.data or 0.0,
                status=form.status.data,
                user_id=current_user.id
            )
            if is_extra:
                new_contract.parent_id = parent_id
                new_contract.extra_type = extra_type
                new_contract.extra_amount = extra_amount

            db.session.add(new_contract)
            db.session.commit()

            # Если доп. соглашение типа add_amount — применяем его вклад в parent (и оплачено если указано)
            if is_extra and new_contract.extra_type == "add_amount" and new_contract.parent_id:
                parent = Contract.query.get(new_contract.parent_id)
                if parent:
                    parent.amount_total = (parent.amount_total or 0.0) + (new_contract.extra_amount or 0.0)
                    if new_contract.amount_paid:
                        parent.amount_paid = (parent.amount_paid or 0.0) + (new_contract.amount_paid or 0.0)
                        db.session.add(ContractHistory(
                            contract_id=parent.id,
                            action=f"Оплачено по доп. соглашению #{new_contract.id}: +{new_contract.amount_paid:.2f}",
                            actor=current_user.username
                        ))
                    db.session.add(ContractHistory(
                        contract_id=parent.id,
                        action=f"К договору добавлено доп. соглашение #{new_contract.id}: +{new_contract.extra_amount or 0:.2f}",
                        actor=current_user.username
                    ))
                    db.session.commit()

            # Если доп. соглашение — досрочное расторжение
            if is_extra and new_contract.extra_type == "termination" and new_contract.parent_id:
                parent = Contract.query.get(new_contract.parent_id)
                if parent:
                    parent.status = "расторгнут"
                    db.session.add(ContractHistory(
                        contract_id=parent.id,
                        action=f"К договору добавлено доп. соглашение #{new_contract.id}: досрочное расторжение",
                        actor=current_user.username
                    ))
                    db.session.commit()

            flash("Договор создан", "success")
            return redirect(url_for('main.contracts'))

    return render_template('edit_contract.html', form=form, contract=contract)


@main_bp.route('/contract_delete/<int:cid>', methods=['POST'])
@login_required
def contract_delete(cid):
    contract = Contract.query.get_or_404(cid)
    if not current_user.is_admin:
        flash("Нет доступа", "danger")
        return redirect(url_for('main.contracts'))

    # If this is an extra that affected parent, revert its effect (both total and paid)
    if contract.parent_id:
        parent = Contract.query.get(contract.parent_id)
        if parent:
            if contract.extra_type == 'add_amount' and contract.extra_amount:
                parent.amount_total = max(0.0, (parent.amount_total or 0.0) - (contract.extra_amount or 0.0))
                db.session.add(ContractHistory(
                    contract_id=parent.id,
                    action=f"Откат доп. суммы при удалении доп. соглашения #{contract.id}: -{contract.extra_amount:.2f}",
                    actor=current_user.username
                ))
            if contract.extra_type == 'add_amount' and contract.amount_paid:
                parent.amount_paid = max(0.0, (parent.amount_paid or 0.0) - (contract.amount_paid or 0.0))
                db.session.add(ContractHistory(
                    contract_id=parent.id,
                    action=f"Откат оплаты при удалении доп. соглашения #{contract.id}: -{contract.amount_paid:.2f}",
                    actor=current_user.username
                ))
            if contract.extra_type == 'termination':
                db.session.add(ContractHistory(
                    contract_id=parent.id,
                    action=f"Удалено доп. соглашение #{contract.id} типа 'досрочное расторжение' — проверьте статус основного договора вручную",
                    actor=current_user.username
                ))

    db.session.add(ContractHistory(
        contract_id=contract.id,
        action="Договор удалён",
        actor=current_user.username
    ))
    db.session.delete(contract)
    db.session.commit()
    flash("Договор удалён", "success")
    return redirect(url_for('main.contracts'))

@main_bp.route('/contract_archive/<int:cid>', methods=['POST'])
@login_required
def contract_archive(cid):
    contract = Contract.query.get_or_404(cid)
    if not current_user.is_admin:
        flash("Нет доступа", "danger")
        return redirect(url_for('main.contracts'))
    contract.archived = True
    db.session.add(ContractHistory(
        contract_id=contract.id,
        action="Договор архивирован",
        actor=current_user.username
    ))
    db.session.commit()
    flash("Договор перемещён в архив", "success")
    return redirect(url_for('main.contracts'))

@main_bp.route('/contract_unarchive/<int:cid>', methods=['POST'])
@login_required
def contract_unarchive(cid):
    contract = Contract.query.get_or_404(cid)
    if not current_user.is_admin:
        flash("Нет доступа", "danger")
        return redirect(url_for('main.contracts_archived'))
    contract.archived = False
    db.session.add(ContractHistory(
        contract_id=contract.id,
        action="Договор восстановлен из архива",
        actor=current_user.username
    ))
    db.session.commit()
    flash("Договор восстановлен из архива", "success")
    return redirect(url_for('main.contracts_archived'))

# Service edit/delete and extra_service edit/delete (POST for deletes)
@main_bp.route('/service_edit/<int:sid>', methods=['GET', 'POST'])
@login_required
def service_edit(sid):
    svc = Service.query.get_or_404(sid)
    contract = Contract.query.get_or_404(svc.contract_id)
    if not current_user.is_admin and contract.user_id != current_user.id:
        flash("Нет доступа", "danger")
        return redirect(url_for('main.contract_detail', cid=contract.id))
    form = ServiceForm(obj=svc)
    if request.method == 'GET' and svc.date:
        form.date.data = svc.date.date()
    if form.validate_on_submit():
        old_total = svc.total or 0.0
        svc_date = form.date.data
        svc_dt = datetime.combine(svc_date, datetime.min.time()) if isinstance(svc_date, date) else datetime.utcnow()
        svc.date = svc_dt
        svc.description = form.description.data
        svc.unit = form.unit.data
        svc.quantity = form.quantity.data or 0.0
        svc.price_per_unit = form.price_per_unit.data or 0.0
        svc.total = (svc.quantity or 0.0) * (svc.price_per_unit or 0.0)
        delta = (svc.total or 0.0) - old_total
        contract.amount_earned = (contract.amount_earned or 0.0) + delta
        db.session.add(ContractHistory(
            contract_id=contract.id,
            action=f"Изменена услуга: {svc.description}, новая сумма {svc.total:.2f}, изменение {delta:+.2f}",
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
    svc = Service.query.get_or_404(sid)
    contract = Contract.query.get_or_404(svc.contract_id)
    if not current_user.is_admin and contract.user_id != current_user.id:
        flash("Нет доступа", "danger")
        return redirect(url_for('main.contract_detail', cid=contract.id))
    contract.amount_earned = max(0.0, (contract.amount_earned or 0.0) - (svc.total or 0.0))
    db.session.add(ContractHistory(
        contract_id=contract.id,
        action=f"Удалена услуга: {svc.description}, сумма {svc.total:.2f}",
        actor=current_user.username
    ))
    db.session.delete(svc)
    db.session.commit()
    flash("Услуга удалена", "success")
    return redirect(url_for('main.contract_detail', cid=contract.id))

@main_bp.route('/extra_service_edit/<int:eid>', methods=['GET', 'POST'])
@login_required
def extra_service_edit(eid):
    ex = ExtraService.query.get_or_404(eid)
    contract = Contract.query.get_or_404(ex.contract_id)
    if not current_user.is_admin and contract.user_id != current_user.id:
        flash("Нет доступа", "danger")
        return redirect(url_for('main.contract_detail', cid=contract.id))
    form = ExtraServiceForm(obj=ex)
    if request.method == 'GET' and ex.date:
        form.date.data = ex.date.date()
    if form.validate_on_submit():
        old_total = ex.total or 0.0
        ex_date = form.date.data
        ex_dt = datetime.combine(ex_date, datetime.min.time()) if isinstance(ex_date, date) else datetime.utcnow()
        ex.date = ex_dt
        ex.description = form.description.data
        ex.price = form.price.data or 0.0
        ex.total = form.total.data or 0.0
        delta = (ex.total or 0.0) - old_total
        contract.amount_earned = (contract.amount_earned or 0.0) + delta
        db.session.add(ContractHistory(
            contract_id=contract.id,
            action=f"Изменена доп. услуга: {ex.description}, новая сумма {ex.total:.2f}, изменение {delta:+.2f}",
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
    ex = ExtraService.query.get_or_404(eid)
    contract = Contract.query.get_or_404(ex.contract_id)
    if not current_user.is_admin and contract.user_id != current_user.id:
        flash("Нет доступа", "danger")
        return redirect(url_for('main.contract_detail', cid=contract.id))
    contract.amount_earned = max(0.0, (contract.amount_earned or 0.0) - (ex.total or 0.0))
    db.session.add(ContractHistory(
        contract_id=contract.id,
        action=f"Удалена доп. услуга: {ex.description}, сумма {ex.total:.2f}",
        actor=current_user.username
    ))
    db.session.delete(ex)
    db.session.commit()
    flash("Доп. услуга удалена", "success")
    return redirect(url_for('main.contract_detail', cid=contract.id))

@main_bp.route('/contract_history/<int:cid>')
@login_required
def contract_history(cid):
    contract = Contract.query.get_or_404(cid)
    history = ContractHistory.query.filter_by(contract_id=contract.id).order_by(ContractHistory.date.desc()).all()
    return render_template("history.html", history=history, contract=contract)