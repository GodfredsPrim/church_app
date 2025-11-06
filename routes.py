from flask import render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from flask_socketio import emit
from app import app, socketio
from models import db, User, Attendance, Offering, Member, Fund, Contribution, MonthlyBudget
from datetime import date, datetime
from dateutil.relativedelta import relativedelta  # pip install python-dateutil if needed

# ------------------------------------------------------------------
# DASHBOARD – Now with monthly totals
# ------------------------------------------------------------------
@app.route('/')
@login_required
def dashboard():
    today = date.today()
    services = ['Sunday', 'Monday', 'Thursday']

    att_data = {}
    off_data = {}
    monthly_att = {}
    monthly_off = {}

    # Today's data
    for s in services:
        att = Attendance.query.filter_by(service_date=today, service_type=s).first()
        off = Offering.query.filter_by(service_date=today, service_type=s).first()

        total_att = 0
        if att:
            total_att = (att.adults_men + att.adults_women +
                         att.youth_gents + att.youth_ladies +
                         att.children_boys + att.children_girls +
                         att.visitors_male + att.visitors_female)

        total_off = 0.0
        if off:
            total_off = off.first_offering + off.second_offering

        att_data[s] = total_att
        off_data[s] = round(total_off, 2)

    # Monthly totals (this month)
    current_month = today.strftime('%Y-%m')
    for s in services:
        month_att = db.session.query(db.func.sum(
            Attendance.adults_men + Attendance.adults_women +
            Attendance.youth_gents + Attendance.youth_ladies +
            Attendance.children_boys + Attendance.children_girls +
            Attendance.visitors_male + Attendance.visitors_female
        )).filter(
            db.func.strftime('%Y-%m', Attendance.service_date) == current_month,
            Attendance.service_type == s
        ).scalar() or 0

        month_off = db.session.query(db.func.sum(Offering.first_offering + Offering.second_offering)).filter(
            db.func.strftime('%Y-%m', Offering.service_date) == current_month,
            Offering.service_type == s
        ).scalar() or 0.0

        monthly_att[s] = month_att
        monthly_off[s] = round(month_off, 2)

    return render_template('dashboard.html',
                           attendance=att_data, offering=off_data,
                           monthly_att=monthly_att, monthly_off=monthly_off,
                           today_str=datetime.today().strftime('%B %d, %Y'))  # Formatted date

# ------------------------------------------------------------------
# LOGIN / LOGOUT (unchanged)
# ------------------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out', 'info')
    return redirect(url_for('login'))

# ------------------------------------------------------------------
# ATTENDANCE (unchanged, safe increment)
# ------------------------------------------------------------------
@app.route('/attendance', methods=['GET', 'POST'])
@login_required
def attendance():
    if request.method == 'POST':
        svc = request.form['service_type']
        today = date.today()

        rec = Attendance.query.filter_by(service_date=today, service_type=svc).first()
        if not rec:
            rec = Attendance(service_date=today, service_type=svc)
            db.session.add(rec)

        rec.adults_men       = (rec.adults_men or 0)       + int(request.form.get('adults_men', 0))
        rec.adults_women     = (rec.adults_women or 0)     + int(request.form.get('adults_women', 0))
        rec.youth_gents      = (rec.youth_gents or 0)      + int(request.form.get('youth_gents', 0))
        rec.youth_ladies     = (rec.youth_ladies or 0)     + int(request.form.get('youth_ladies', 0))
        rec.children_boys    = (rec.children_boys or 0)    + int(request.form.get('children_boys', 0))
        rec.children_girls   = (rec.children_girls or 0)   + int(request.form.get('children_girls', 0))
        rec.visitors_male    = (rec.visitors_male or 0)    + int(request.form.get('visitors_male', 0))
        rec.visitors_female  = (rec.visitors_female or 0)  + int(request.form.get('visitors_female', 0))

        db.session.commit()

        total = sum([
            rec.adults_men, rec.adults_women, rec.youth_gents, rec.youth_ladies,
            rec.children_boys, rec.children_girls, rec.visitors_male, rec.visitors_female
        ])

        socketio.emit('attendance_update', {'service': svc, 'total': total})
        flash(f'{svc} attendance saved', 'success')
        return redirect(url_for('dashboard'))

    return render_template('attendance.html')


# ------------------------------------------------------------------
# OFFERINGS (unchanged, safe increment)
# ------------------------------------------------------------------
@app.route('/offerings', methods=['GET', 'POST'])
@login_required
def offerings():
    if request.method == 'POST':
        svc = request.form['service_type']
        amt = float(request.form['amount'])
        today = date.today()

        rec = Offering.query.filter_by(service_date=today, service_type=svc).first()
        if not rec:
            rec = Offering(service_date=today, service_type=svc)
            db.session.add(rec)

        if svc == 'Sunday':
            typ = request.form.get('offering_type')
            if typ == 'first':
                rec.first_offering = (rec.first_offering or 0.0) + amt
            else:
                rec.second_offering = (rec.second_offering or 0.0) + amt
        else:
            rec.first_offering = (rec.first_offering or 0.0) + amt

        db.session.commit()

        total = rec.first_offering + rec.second_offering
        socketio.emit('offering_update', {'service': svc, 'total': round(total, 2)})
        flash(f'{svc} offering saved', 'success')
        return redirect(url_for('dashboard'))

    return render_template('offerings.html')

# ------------------------------------------------------------------
# MEMBERS – List & Register
# ------------------------------------------------------------------
@app.route('/members', methods=['GET', 'POST'])
@login_required
def members():
    if request.method == 'POST':
        new_member = Member(
            name=request.form['name'],
            gender=request.form['gender'],
            age_group=request.form['age_group'],
            contact=request.form.get('contact', '')
        )
        db.session.add(new_member)
        db.session.commit()
        flash('Member registered successfully!', 'success')
        return redirect(url_for('members'))

    all_members = Member.query.all()
    return render_template('members.html', members=all_members)

# ------------------------------------------------------------------
# FUNDS – Create & List
# ------------------------------------------------------------------
@app.route('/funds', methods=['GET', 'POST'])
@login_required
def funds():
    if request.method == 'POST':
        new_fund = Fund(
            name=request.form['name'],
            description=request.form.get('description', '')
        )
        db.session.add(new_fund)
        db.session.commit()
        socketio.emit('fund_update', {'action': 'created', 'name': new_fund.name})  # Live update
        flash('Fund created!', 'success')
        return redirect(url_for('funds'))

    all_funds = Fund.query.all()
    return render_template('funds.html', funds=all_funds)

# ------------------------------------------------------------------
# CONTRIBUTIONS – Record
# ------------------------------------------------------------------
@app.route('/contributions', methods=['GET', 'POST'])
@login_required
def contributions():
    if request.method == 'POST':
        contrib = Contribution(
            fund_id=int(request.form['fund_id']),
            service_date=date.today(),
            service_type=request.form['service_type'],
            amount=float(request.form['amount']),
            member_id=request.form.get('member_id', type=int)
        )
        db.session.add(contrib)
        db.session.commit()

        total_fund = db.session.query(db.func.sum(Contribution.amount)).filter_by(fund_id=contrib.fund_id).scalar() or 0.0
        socketio.emit('contribution_update', {'fund': contrib.fund.name, 'total': round(total_fund, 2)})
        flash('Contribution recorded!', 'success')
        return redirect(url_for('contributions'))

    funds = Fund.query.all()
    members = Member.query.all()
    return render_template('contributions.html', funds=funds, members=members)

# ------------------------------------------------------------------
# BUDGET – Set & View Monthly
# ------------------------------------------------------------------
@app.route('/budget', methods=['GET', 'POST'])
@login_required
def budget():
    today = date.today()
    current_month = today.strftime('%Y-%m')

    if request.method == 'POST':
        for s in ['Sunday', 'Monday', 'Thursday']:
            budget = MonthlyBudget.query.filter_by(month_year=current_month, service_type=s).first()
            if not budget:
                budget = MonthlyBudget(month_year=current_month, service_type=s)
                db.session.add(budget)
            
            budget.target_attendance = int(request.form.get(f'target_att_{s}', 0))
            budget.target_offering = float(request.form.get(f'target_off_{s}', 0.0))
        
        db.session.commit()
        flash('Budgets updated!', 'success')
        return redirect(url_for('budget'))

    # Pre-calculate budget dict for template
    budget_dict = {}
    budgets = MonthlyBudget.query.filter_by(month_year=current_month).all()
    for s in ['Sunday', 'Monday', 'Thursday']:
        b = next((x for x in budgets if x.service_type == s), None)
        budget_dict[s] = {
            'target_attendance': b.target_attendance if b else 0,
            'target_offering': b.target_offering if b else 0.0
        }

    return render_template('budget.html', budget_dict=budget_dict, month=current_month)

# ------------------------------------------------------------------
# MONTHLY REPORTS
# ------------------------------------------------------------------
@app.route('/reports/monthly')
@login_required
def monthly_reports():
    today = date.today()
    month_start = today.replace(day=1)
    month_end = (month_start + relativedelta(months=1)) - relativedelta(days=1)  # End of month
    current_month = today.strftime('%Y-%m')

    services = ['Sunday', 'Monday', 'Thursday']
    report_data = {}

    for s in services:
        # Actuals
        att_actual = db.session.query(db.func.sum(
            Attendance.adults_men + Attendance.adults_women +
            Attendance.youth_gents + Attendance.youth_ladies +
            Attendance.children_boys + Attendance.children_girls +
            Attendance.visitors_male + Attendance.visitors_female
        )).filter(
            Attendance.service_date >= month_start,
            Attendance.service_date <= month_end,
            Attendance.service_type == s
        ).scalar() or 0

        off_actual = db.session.query(db.func.sum(Offering.first_offering + Offering.second_offering)).filter(
            Offering.service_date >= month_start,
            Offering.service_date <= month_end,
            Offering.service_type == s
        ).scalar() or 0.0

        # Budgets
        budget = MonthlyBudget.query.filter_by(month_year=current_month, service_type=s).first()
        att_target = budget.target_attendance if budget else 0
        off_target = budget.target_offering if budget else 0.0

        report_data[s] = {
            'att_actual': att_actual, 'att_target': att_target,
            'off_actual': round(off_actual, 2), 'off_target': round(off_target, 2)
        }

    return render_template('reports_monthly.html', report=report_data, month=current_month)

# ------------------------------------------------------------------
# SocketIO connect (unchanged)
# ------------------------------------------------------------------
@socketio.on('connect')
def on_connect():
    print('Client connected')