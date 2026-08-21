from datetime import datetime, date, timedelta
from sqlalchemy import func
from extensions import db
from models.expense import Expense
from models.income import Income
from models.budget import Budget
from models.goal import Goal
from models.account import Account


def get_first_day_of_month(dt, offset_months=0):
    """
    Returns date object for the 1st day of the month offset_months ago (0 = current, 1 = previous month, etc.)
    """
    year = dt.year
    month = dt.month - offset_months
    while month <= 0:
        month += 12
        year -= 1
    return date(year, month, 1)


def get_last_day_of_month(dt_start):
    """
    Returns the last day of the month for a given 1st-of-month date.
    """
    if dt_start.month == 12:
        next_month = date(dt_start.year + 1, 1, 1)
    else:
        next_month = date(dt_start.year, dt_start.month + 1, 1)
    return next_month - timedelta(days=1)


def get_spending_analysis(user_id):
    """
    Analyzes spending patterns for the given user using actual DB records.
    Returns structured data for financial metrics, category breakdown,
    month-over-month comparison, budget status, and rule-based insights.
    """
    today = date.today()

    # 1. Total Income & Total Expenses
    incomes = Income.query.filter_by(user_id=user_id).all()
    expenses = Expense.query.filter_by(user_id=user_id).all()
    goals = Goal.query.filter_by(user_id=user_id).all()

    total_income = sum(inc.amount for inc in incomes)
    total_expenses = sum(exp.amount for exp in expenses)
    total_savings = total_income - total_expenses

    # 2. Category Breakdown
    category_totals = {}
    for exp in expenses:
        category_totals[exp.category] = category_totals.get(exp.category, 0.0) + exp.amount

    sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
    categories = [item[0] for item in sorted_categories]
    amounts = [float(item[1]) for item in sorted_categories]

    highest_spending_category = None
    highest_spending_amount = 0.0
    highest_spending_percentage = 0.0

    if sorted_categories and total_expenses > 0:
        highest_spending_category = sorted_categories[0][0]
        highest_spending_amount = sorted_categories[0][1]
        highest_spending_percentage = round((highest_spending_amount / total_expenses) * 100, 1)

    # 3. Current Month vs Previous Month Spending
    first_day_current_month = get_first_day_of_month(today, 0)
    first_day_prev_month = get_first_day_of_month(today, 1)
    last_day_prev_month = get_last_day_of_month(first_day_prev_month)

    current_month_expenses = sum(
        exp.amount for exp in expenses
        if exp.expense_date and exp.expense_date >= first_day_current_month
    )

    prev_month_expenses = sum(
        exp.amount for exp in expenses
        if exp.expense_date and first_day_prev_month <= exp.expense_date <= last_day_prev_month
    )

    # Percentage change
    spending_change_pct = 0.0
    if prev_month_expenses > 0:
        spending_change_pct = round(((current_month_expenses - prev_month_expenses) / prev_month_expenses) * 100, 1)
    elif current_month_expenses > 0 and prev_month_expenses == 0:
        spending_change_pct = 100.0

    # Category level changes (Current vs Prev month)
    category_prev_month = {}
    category_curr_month = {}
    for exp in expenses:
        if exp.expense_date:
            if first_day_prev_month <= exp.expense_date <= last_day_prev_month:
                category_prev_month[exp.category] = category_prev_month.get(exp.category, 0.0) + exp.amount
            elif exp.expense_date >= first_day_current_month:
                category_curr_month[exp.category] = category_curr_month.get(exp.category, 0.0) + exp.amount

    increased_categories = []
    for cat, curr_amt in category_curr_month.items():
        prev_amt = category_prev_month.get(cat, 0.0)
        if curr_amt > prev_amt:
            diff = curr_amt - prev_amt
            increased_categories.append({
                "category": cat,
                "curr_amt": curr_amt,
                "prev_amt": prev_amt,
                "diff": diff
            })

    # 4. Budget Status
    active_budget = Budget.query.filter_by(user_id=user_id).order_by(Budget.created_at.desc()).first()
    monthly_budget_amount = active_budget.monthly_budget if active_budget else 0.0
    remaining_budget = monthly_budget_amount - total_expenses if monthly_budget_amount > 0 else 0.0

    budget_used_pct = 0.0
    if monthly_budget_amount > 0:
        budget_used_pct = round((total_expenses / monthly_budget_amount) * 100, 1)

    is_over_budget = (monthly_budget_amount > 0 and total_expenses > monthly_budget_amount)
    over_budget_amount = max(0.0, total_expenses - monthly_budget_amount)

    # 5. Rule-Based Insights Generation (Explainable AI Engine)
    insights = []

    if highest_spending_category:
        insights.append(
            f"{highest_spending_category} is your highest spending category at ₹{highest_spending_amount:,.0f} ({highest_spending_percentage}% of total expenses)."
        )

    if prev_month_expenses > 0:
        if spending_change_pct > 0:
            insights.append(
                f"Your overall monthly spending increased by {spending_change_pct}% compared with last month."
            )
        elif spending_change_pct < 0:
            insights.append(
                f"Great job! Your monthly spending decreased by {abs(spending_change_pct)}% compared with last month."
            )
        else:
            insights.append("Your monthly spending is equal to last month's spending.")
    elif current_month_expenses > 0:
        insights.append(f"Current month spending is ₹{current_month_expenses:,.0f}.")

    for inc_cat in increased_categories[:2]:
        insights.append(
            f"{inc_cat['category']} spending increased compared with last month (₹{inc_cat['curr_amt']:,.0f} vs ₹{inc_cat['prev_amt']:,.0f})."
        )

    if monthly_budget_amount > 0:
        if is_over_budget:
            insights.append(
                f"You have exceeded your monthly budget by ₹{over_budget_amount:,.0f} ({budget_used_pct}% used)."
            )
        else:
            insights.append(
                f"You have used {budget_used_pct}% of your monthly budget (₹{total_expenses:,.0f} / ₹{monthly_budget_amount:,.0f})."
            )

    if total_income > 0:
        savings_rate = round((total_savings / total_income) * 100, 1)
        if savings_rate > 0:
            insights.append(f"Your net savings rate is {savings_rate}% of your total income.")
        elif savings_rate < 0:
            insights.append("Warning: Your total expenses exceed your total income!")

    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "total_savings": total_savings,
        "categories": categories,
        "amounts": amounts,
        "category_totals": category_totals,
        "highest_spending_category": highest_spending_category,
        "highest_spending_amount": highest_spending_amount,
        "highest_spending_percentage": highest_spending_percentage,
        "current_month_expenses": current_month_expenses,
        "prev_month_expenses": prev_month_expenses,
        "spending_change_pct": spending_change_pct,
        "increased_categories": increased_categories,
        "monthly_budget_amount": monthly_budget_amount,
        "remaining_budget": remaining_budget,
        "budget_used_pct": budget_used_pct,
        "is_over_budget": is_over_budget,
        "over_budget_amount": over_budget_amount,
        "insights": insights,
        "active_budget": active_budget
    }


def get_monthly_spending_trend(user_id, num_months=6):
    """
    Generates historical 6-month Income, Expense, and Savings trends for the logged-in user.
    Uses actual DB records, grouped by calendar month.
    """
    today = date.today()

    month_list = []
    for i in range(num_months - 1, -1, -1):
        month_start = get_first_day_of_month(today, i)
        month_end = get_last_day_of_month(month_start)
        month_label = month_start.strftime("%b %Y")

        month_list.append({
            "label": month_label,
            "start": month_start,
            "end": month_end
        })

    incomes = Income.query.filter_by(user_id=user_id).all()
    expenses = Expense.query.filter_by(user_id=user_id).all()

    trend_labels = []
    income_data = []
    expense_data = []
    savings_data = []
    table_rows = []

    for item in month_list:
        m_start = item["start"]
        m_end = item["end"]

        m_income = sum(
            inc.amount for inc in incomes
            if inc.income_date and m_start <= inc.income_date <= m_end
        )

        m_expense = sum(
            exp.amount for exp in expenses
            if exp.expense_date and m_start <= exp.expense_date <= m_end
        )

        m_savings = m_income - m_expense

        trend_labels.append(item["label"])
        income_data.append(float(m_income))
        expense_data.append(float(m_expense))
        savings_data.append(float(m_savings))

        table_rows.append({
            "month": item["label"],
            "income": m_income,
            "expenses": m_expense,
            "savings": m_savings
        })

    return {
        "labels": trend_labels,
        "income": income_data,
        "expenses": expense_data,
        "savings": savings_data,
        "table_rows": table_rows
    }


def get_advanced_spending_patterns(user_id):
    """
    Computes advanced spending pattern analytics:
    1. Monthly Spending Trend (Last 6 Months)
    2. Category Analysis (Last 3 Months)
    3. Weekly Spending Pattern (Current Month)
    4. Month vs Previous Month Comparison
    5. Spending Anomalies Detected (Explainable Rule-Based Engine)
    """
    today = date.today()
    expenses = Expense.query.filter_by(user_id=user_id).all()

    # -------------------------------------------------------------
    # 1. MONTHLY SPENDING TREND (LAST 6 MONTHS)
    # -------------------------------------------------------------
    month_6_labels = []
    month_6_amounts = []
    has_6m_data = False

    for i in range(5, -1, -1):
        m_start = get_first_day_of_month(today, i)
        m_end = get_last_day_of_month(m_start)
        m_label = m_start.strftime("%B")
        m_total = sum(
            exp.amount for exp in expenses
            if exp.expense_date and m_start <= exp.expense_date <= m_end
        )
        month_6_labels.append(m_label)
        month_6_amounts.append(float(m_total))
        if m_total > 0:
            has_6m_data = True

    monthly_trend_6m = {
        "labels": month_6_labels,
        "amounts": month_6_amounts,
        "has_data": has_6m_data
    }

    # -------------------------------------------------------------
    # 2. CATEGORY ANALYSIS (LAST 3 MONTHS)
    # -------------------------------------------------------------
    m3_labels = []
    m3_ranges = []
    for i in range(2, -1, -1):
        m_start = get_first_day_of_month(today, i)
        m_end = get_last_day_of_month(m_start)
        m3_labels.append(m_start.strftime("%B"))
        m3_ranges.append((m_start, m_end))

    cat_3m_data = {}
    total_3m_spending = 0.0

    for exp in expenses:
        if exp.expense_date and m3_ranges[0][0] <= exp.expense_date <= m3_ranges[2][1]:
            cat = exp.category
            if cat not in cat_3m_data:
                cat_3m_data[cat] = [0.0, 0.0, 0.0]
            
            for idx, (m_start, m_end) in enumerate(m3_ranges):
                if m_start <= exp.expense_date <= m_end:
                    cat_3m_data[cat][idx] += exp.amount
            total_3m_spending += exp.amount

    sorted_cat_3m = sorted(
        cat_3m_data.items(),
        key=lambda x: sum(x[1]),
        reverse=True
    )

    cat_3m_names = [item[0] for item in sorted_cat_3m]
    cat_3m_totals = [float(sum(item[1])) for item in sorted_cat_3m]
    has_3m_data = len(sorted_cat_3m) > 0 and total_3m_spending > 0

    category_analysis_3m = {
        "month_labels": m3_labels,
        "categories": cat_3m_names,
        "category_totals": cat_3m_totals,
        "cat_data_by_month": {item[0]: [float(v) for v in item[1]] for item in sorted_cat_3m},
        "total_3m_spending": float(total_3m_spending),
        "has_data": has_3m_data
    }

    # -------------------------------------------------------------
    # 3. WEEKLY SPENDING PATTERN (CURRENT MONTH)
    # -------------------------------------------------------------
    curr_m_start = get_first_day_of_month(today, 0)
    curr_m_end = get_last_day_of_month(curr_m_start)

    curr_month_expenses = [
        exp for exp in expenses
        if exp.expense_date and curr_m_start <= exp.expense_date <= curr_m_end
    ]

    week_labels = ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5"]
    week_totals = [0.0, 0.0, 0.0, 0.0, 0.0]

    for exp in curr_month_expenses:
        day = exp.expense_date.day
        if 1 <= day <= 7:
            week_totals[0] += exp.amount
        elif 8 <= day <= 14:
            week_totals[1] += exp.amount
        elif 15 <= day <= 21:
            week_totals[2] += exp.amount
        elif 22 <= day <= 28:
            week_totals[3] += exp.amount
        elif day >= 29:
            week_totals[4] += exp.amount

    highest_week = None
    has_weekly_data = any(w > 0 for w in week_totals)

    if has_weekly_data:
        max_idx = week_totals.index(max(week_totals))
        highest_week = {
            "week": week_labels[max_idx],
            "amount": float(week_totals[max_idx])
        }

    weekly_pattern = {
        "labels": week_labels,
        "amounts": [float(w) for w in week_totals],
        "highest_week": highest_week,
        "has_data": has_weekly_data
    }

    # -------------------------------------------------------------
    # 4. MONTH VS PREVIOUS MONTH COMPARISON
    # -------------------------------------------------------------
    prev_m_start = get_first_day_of_month(today, 1)
    prev_m_end = get_last_day_of_month(prev_m_start)

    prev_month_expenses = [
        exp for exp in expenses
        if exp.expense_date and prev_m_start <= exp.expense_date <= prev_m_end
    ]

    curr_total = sum(exp.amount for exp in curr_month_expenses)
    prev_total = sum(exp.amount for exp in prev_month_expenses)
    curr_count = len(curr_month_expenses)
    prev_count = len(prev_month_expenses)

    change_amount = curr_total - prev_total
    has_prev_data = prev_total > 0

    if has_prev_data:
        pct_change = round(((curr_total - prev_total) / prev_total) * 100, 1)
    else:
        pct_change = 0.0

    month_vs_prev = {
        "curr_total": float(curr_total),
        "prev_total": float(prev_total),
        "curr_count": curr_count,
        "prev_count": prev_count,
        "change_amount": float(change_amount),
        "pct_change": pct_change,
        "has_prev_data": has_prev_data
    }

    # -------------------------------------------------------------
    # 5. SPENDING ANOMALIES DETECTED (EXPLAINABLE RULE-BASED ENGINE)
    # -------------------------------------------------------------
    anomalies = []

    # Rule 1: Transaction significantly higher than normal (2.5x overall transaction avg)
    if len(expenses) >= 3:
        avg_txn_amt = sum(exp.amount for exp in expenses) / len(expenses)
        for exp in curr_month_expenses:
            if exp.amount >= 2.5 * avg_txn_amt and avg_txn_amt > 0:
                anomalies.append(
                    f"A ₹{exp.amount:,.0f} {exp.category} transaction ('{exp.title}') is significantly above your normal transaction average (₹{avg_txn_amt:,.0f})."
                )

    # Rule 2: Category spending significantly higher than its 3-month average (> 1.5x avg)
    if has_3m_data:
        for cat, monthly_vals in cat_3m_data.items():
            curr_cat_val = monthly_vals[2]
            prev_2m_avg = (monthly_vals[0] + monthly_vals[1]) / 2.0 if (monthly_vals[0] + monthly_vals[1]) > 0 else 0.0
            if prev_2m_avg > 0 and curr_cat_val >= 1.5 * prev_2m_avg:
                spike_pct = round(((curr_cat_val - prev_2m_avg) / prev_2m_avg) * 100, 1)
                anomalies.append(
                    f"{cat} spending (₹{curr_cat_val:,.0f}) is {spike_pct}% higher than its recent average (₹{prev_2m_avg:,.0f})."
                )

    # Rule 3: Current month total spending significantly higher than previous month (> 1.3x prev month)
    if has_prev_data and curr_total >= 1.3 * prev_total:
        anomalies.append(
            f"Current month spending (₹{curr_total:,.0f}) is {pct_change}% higher than previous month (₹{prev_total:,.0f})."
        )

    # Rule 4: High spending concentration in one category (>= 40% of current month)
    if curr_total > 0:
        cat_curr_totals = {}
        for exp in curr_month_expenses:
            cat_curr_totals[exp.category] = cat_curr_totals.get(exp.category, 0.0) + exp.amount

        for cat, amt in cat_curr_totals.items():
            pct = (amt / curr_total) * 100
            if pct >= 40.0:
                anomalies.append(
                    f"{cat} spending accounts for {pct:.1f}% of your total expenses this month (₹{amt:,.0f} out of ₹{curr_total:,.0f})."
                )

    seen_anomalies = set()
    unique_anomalies = []
    for a in anomalies:
        if a not in seen_anomalies:
            seen_anomalies.add(a)
            unique_anomalies.append(a)

    return {
        "monthly_trend_6m": monthly_trend_6m,
        "category_analysis_3m": category_analysis_3m,
        "weekly_pattern": weekly_pattern,
        "month_vs_prev": month_vs_prev,
        "anomalies": unique_anomalies
    }


def get_rebuilt_analytics_data(user_id):
    """
    Calculates data for the rebuilt Analytics Dashboard:
    1. Top 4 KPI Cards:
       - Monthly Savings (current month income - expenses, savings %, MoM comparison)
       - Avg Monthly Expenses (average expenses across active expense months)
       - Projected Month-End Balance (Formula: Total Accounts Balance)
       - Active Goals (count of 'In Progress' goals, progress summary)
    2. Spending Pattern Analysis (Doughnut chart categories, total spent, highest spending cat)
    3. Cash Flow Trend (Last 6 Months line chart)
    4. Budget Recommendations (Rule-based explainable recommendations)
    5. AI Insights (Rule-based explainable insights)
    """
    today = date.today()
    incomes = Income.query.filter_by(user_id=user_id).all()
    expenses = Expense.query.filter_by(user_id=user_id).all()
    accounts = Account.query.filter_by(user_id=user_id).all()
    goals = Goal.query.filter_by(user_id=user_id).all()
    budget = Budget.query.filter_by(user_id=user_id).order_by(Budget.created_at.desc()).first()

    # 1. Current & Previous Month Dates
    first_day_curr = get_first_day_of_month(today, 0)
    first_day_prev = get_first_day_of_month(today, 1)
    last_day_prev = get_last_day_of_month(first_day_prev)

    # Current Month Income & Expenses
    curr_m_income = sum(i.amount for i in incomes if i.income_date and i.income_date >= first_day_curr)
    curr_m_expense = sum(e.amount for e in expenses if e.expense_date and e.expense_date >= first_day_curr)
    curr_m_savings = curr_m_income - curr_m_expense
    savings_pct = round((curr_m_savings / curr_m_income) * 100, 1) if curr_m_income > 0 else 0.0

    # Previous Month Expenses for MoM comparison
    prev_m_expense = sum(e.amount for e in expenses if e.expense_date and first_day_prev <= e.expense_date <= last_day_prev)
    prev_m_income = sum(i.amount for i in incomes if i.income_date and first_day_prev <= i.income_date <= last_day_prev)

    has_prev_data = prev_m_expense > 0 or prev_m_income > 0
    mom_expense_change_pct = 0.0
    if prev_m_expense > 0:
        mom_expense_change_pct = round(((curr_m_expense - prev_m_expense) / prev_m_expense) * 100, 1)

    # 2. Avg Monthly Expenses
    expense_months = set()
    for e in expenses:
        if e.expense_date:
            expense_months.add((e.expense_date.year, e.expense_date.month))

    num_active_months = max(1, len(expense_months))
    total_all_expenses = sum(e.amount for e in expenses)
    avg_monthly_expenses = round(total_all_expenses / num_active_months, 0)

    # 3. Projected Month-End Balance
    # Formula Documentation:
    # Total Accounts Balance represents current real bank/savings balances.
    # Projected Month-End Balance = Total Accounts Balance.
    total_accounts_balance = sum(acc.balance for acc in accounts)
    projected_month_end_balance = total_accounts_balance

    # 4. Active Goals
    active_goals = [g for g in goals if g.status == "In Progress"]
    active_goals_count = len(active_goals)

    # 5. Budget Recommendations (Rule-Based & Explainable)
    budget_recommendations = []
    monthly_budget_amount = budget.monthly_budget if budget else 0.0
    budget_used_pct = round((curr_m_expense / monthly_budget_amount) * 100, 1) if monthly_budget_amount > 0 else 0.0

    if budget:
        if budget_used_pct > 100:
            budget_recommendations.append(
                f"High Budget Utilization: You have exceeded your monthly budget (₹{curr_m_expense:,.0f} spent out of ₹{monthly_budget_amount:,.0f}). Consider pausing non-essential expenses."
            )
        elif budget_used_pct >= 75:
            budget_recommendations.append(
                f"Budget Caution: You have utilized {budget_used_pct}% of your monthly budget. Keep an eye on remaining funds (₹{monthly_budget_amount - curr_m_expense:,.0f} left)."
            )
        else:
            budget_recommendations.append(
                f"Budget Discipline: Good progress! You have used {budget_used_pct}% of your ₹{monthly_budget_amount:,.0f} budget so far."
            )
    else:
        budget_recommendations.append(
            "Set Up a Monthly Budget: Create a monthly budget to set spending caps and improve your savings discipline."
        )

    category_totals = {}
    for exp in expenses:
        category_totals[exp.category] = category_totals.get(exp.category, 0.0) + exp.amount

    sorted_cats = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
    if sorted_cats and total_all_expenses > 0:
        top_cat, top_amt = sorted_cats[0]
        top_pct = round((top_amt / total_all_expenses) * 100, 1)
        if top_pct >= 35.0:
            budget_recommendations.append(
                f"Category Recommendation: {top_cat} accounts for {top_pct}% of your total expenses (₹{top_amt:,.0f}). Consider capping {top_cat} expenses to increase net savings."
            )

    if curr_m_savings > 0:
        budget_recommendations.append(
            f"Savings Allocation: You have saved ₹{curr_m_savings:,.0f} this month ({savings_pct}% of income). Allocating 50% toward active goals will accelerate completion."
        )

    # 6. AI Insights (Rule-Based & Explainable)
    ai_insights = []
    if sorted_cats and total_all_expenses > 0:
        ai_insights.append(
            f"Top Category: {sorted_cats[0][0]} is your largest expense category at ₹{sorted_cats[0][1]:,.0f} ({round(sorted_cats[0][1]/total_all_expenses*100, 1)}% of total)."
        )

    if prev_m_expense > 0:
        if mom_expense_change_pct > 0:
            ai_insights.append(
                f"Spending Trajectory: Monthly expenses increased by {mom_expense_change_pct}% compared with previous month (₹{curr_m_expense:,.0f} vs ₹{prev_m_expense:,.0f})."
            )
        elif mom_expense_change_pct < 0:
            ai_insights.append(
                f"Spending Trajectory: Excellent! Monthly expenses reduced by {abs(mom_expense_change_pct)}% compared with previous month."
            )
    elif curr_m_expense > 0:
        ai_insights.append(f"Current Month Spending: Total recorded expenses for this month stand at ₹{curr_m_expense:,.0f}.")

    if active_goals:
        top_goal = active_goals[0]
        g_prog = round((top_goal.current_amount / top_goal.target_amount) * 100, 1) if top_goal.target_amount > 0 else 0.0
        ai_insights.append(
            f"Goal Progress: '{top_goal.goal_name}' is currently {g_prog}% achieved (₹{top_goal.current_amount:,.0f} of ₹{top_goal.target_amount:,.0f})."
        )

    if curr_m_income > 0:
        ai_insights.append(
            f"Income & Savings Balance: Net monthly savings rate is currently {savings_pct}% of total income."
        )

    return {
        "curr_m_savings": curr_m_savings,
        "savings_pct": savings_pct,
        "curr_m_income": curr_m_income,
        "curr_m_expense": curr_m_expense,
        "prev_m_expense": prev_m_expense,
        "has_prev_data": has_prev_data,
        "mom_expense_change_pct": mom_expense_change_pct,
        "avg_monthly_expenses": avg_monthly_expenses,
        "projected_month_end_balance": projected_month_end_balance,
        "total_accounts_balance": total_accounts_balance,
        "active_goals_count": active_goals_count,
        "active_goals": active_goals,
        "budget_recommendations": budget_recommendations,
        "ai_insights": ai_insights
    }


def get_goal_expense_analytics(user_id):
    """
    Computes real Expense-to-Goal Analytics:
    1. Per Goal Expense Metrics (Total linked expenses, Count, Avg amount, Latest date)
    2. Goal vs Expense Visualizations (Goal-Linked Expenses by Goal, Goal-linked vs Regular Non-goal expenses)
    3. Monthly Goal-Linked Expense Trend (Last 6 Months)
    4. Smart Dashboard Goal-Expense metrics
    """
    today = date.today()
    goals = Goal.query.filter_by(user_id=user_id).all()
    all_expenses = Expense.query.filter_by(user_id=user_id).all()

    goal_analysis_list = []
    goal_names = []
    goal_linked_totals = []
    total_all_goal_linked = 0.0

    most_expensive_goal_name = "None"
    max_goal_expense_amt = -1.0
    latest_goal_expense_obj = None

    for g in goals:
        linked_exp = [e for e in all_expenses if e.goal_id == g.id]
        linked_exp.sort(key=lambda x: x.expense_date or date.min, reverse=True)

        total_amt = sum(e.amount for e in linked_exp)
        count_exp = len(linked_exp)
        avg_amt = round(total_amt / count_exp, 2) if count_exp > 0 else 0.0
        latest_date_str = linked_exp[0].expense_date.strftime("%d %b %Y") if count_exp > 0 and linked_exp[0].expense_date else "N/A"

        if count_exp > 0:
            if not latest_goal_expense_obj or (linked_exp[0].expense_date and linked_exp[0].expense_date > (latest_goal_expense_obj.expense_date or date.min)):
                latest_goal_expense_obj = linked_exp[0]

        if total_amt > max_goal_expense_amt and total_amt > 0:
            max_goal_expense_amt = total_amt
            most_expensive_goal_name = g.goal_name

        total_all_goal_linked += total_amt

        goal_analysis_list.append({
            "goal": g,
            "total_expenses": total_amt,
            "count_expenses": count_exp,
            "avg_expense": avg_amt,
            "latest_date": latest_date_str
        })

        if total_amt > 0 or len(goals) <= 5:
            goal_names.append(g.goal_name)
            goal_linked_totals.append(float(total_amt))

    total_all_expenses = sum(e.amount for e in all_expenses)
    total_regular_expenses = max(0.0, total_all_expenses - total_all_goal_linked)

    goals_with_expenses_count = sum(1 for item in goal_analysis_list if item["count_expenses"] > 0)

    # Monthly Goal-Linked Expense Trend (Last 6 Months)
    month_labels = []
    monthly_goal_expenses = []
    for i in range(5, -1, -1):
        m_start = get_first_day_of_month(today, i)
        m_end = get_last_day_of_month(m_start)
        m_label = m_start.strftime("%b %Y")
        
    first_day_curr = get_first_day_of_month(today, 0)
    first_day_prev = get_first_day_of_month(today, 1)
    last_day_prev = get_last_day_of_month(first_day_prev)

    # Current Month Income & Expenses
    curr_m_income = sum(i.amount for i in incomes if i.income_date and i.income_date >= first_day_curr)
    curr_m_expense = sum(e.amount for e in expenses if e.expense_date and e.expense_date >= first_day_curr)
    curr_m_savings = curr_m_income - curr_m_expense
    savings_pct = round((curr_m_savings / curr_m_income) * 100, 1) if curr_m_income > 0 else 0.0

    # Previous Month Expenses for MoM comparison
    prev_m_expense = sum(e.amount for e in expenses if e.expense_date and first_day_prev <= e.expense_date <= last_day_prev)
    prev_m_income = sum(i.amount for i in incomes if i.income_date and first_day_prev <= i.income_date <= last_day_prev)

    has_prev_data = prev_m_expense > 0 or prev_m_income > 0
    mom_expense_change_pct = 0.0
    if prev_m_expense > 0:
        mom_expense_change_pct = round(((curr_m_expense - prev_m_expense) / prev_m_expense) * 100, 1)

    # 2. Avg Monthly Expenses
    expense_months = set()
    for e in expenses:
        if e.expense_date:
            expense_months.add((e.expense_date.year, e.expense_date.month))

    num_active_months = max(1, len(expense_months))
    total_all_expenses = sum(e.amount for e in expenses)
    avg_monthly_expenses = round(total_all_expenses / num_active_months, 0)

    # 3. Projected Month-End Balance
    # Formula Documentation:
    # Total Accounts Balance represents current real bank/savings balances.
    # Projected Month-End Balance = Total Accounts Balance.
    total_accounts_balance = sum(acc.balance for acc in accounts)
    projected_month_end_balance = total_accounts_balance

    # 4. Active Goals
    active_goals = [g for g in goals if g.status == "In Progress"]
    active_goals_count = len(active_goals)

    # 5. Budget Recommendations (Rule-Based & Explainable)
    budget_recommendations = []
    monthly_budget_amount = budget.monthly_budget if budget else 0.0
    budget_used_pct = round((curr_m_expense / monthly_budget_amount) * 100, 1) if monthly_budget_amount > 0 else 0.0

    if budget:
        if budget_used_pct > 100:
            budget_recommendations.append(
                f"High Budget Utilization: You have exceeded your monthly budget (₹{curr_m_expense:,.0f} spent out of ₹{monthly_budget_amount:,.0f}). Consider pausing non-essential expenses."
            )
        elif budget_used_pct >= 75:
            budget_recommendations.append(
                f"Budget Caution: You have utilized {budget_used_pct}% of your monthly budget. Keep an eye on remaining funds (₹{monthly_budget_amount - curr_m_expense:,.0f} left)."
            )
        else:
            budget_recommendations.append(
                f"Budget Discipline: Good progress! You have used {budget_used_pct}% of your ₹{monthly_budget_amount:,.0f} budget so far."
            )
    else:
        budget_recommendations.append(
            "Set Up a Monthly Budget: Create a monthly budget to set spending caps and improve your savings discipline."
        )

    category_totals = {}
    for exp in expenses:
        category_totals[exp.category] = category_totals.get(exp.category, 0.0) + exp.amount

    sorted_cats = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
    if sorted_cats and total_all_expenses > 0:
        top_cat, top_amt = sorted_cats[0]
        top_pct = round((top_amt / total_all_expenses) * 100, 1)
        if top_pct >= 35.0:
            budget_recommendations.append(
                f"Category Recommendation: {top_cat} accounts for {top_pct}% of your total expenses (₹{top_amt:,.0f}). Consider capping {top_cat} expenses to increase net savings."
            )

    if curr_m_savings > 0:
        budget_recommendations.append(
            f"Savings Allocation: You have saved ₹{curr_m_savings:,.0f} this month ({savings_pct}% of income). Allocating 50% toward active goals will accelerate completion."
        )

    # 6. AI Insights (Rule-Based & Explainable)
    ai_insights = []
    if sorted_cats and total_all_expenses > 0:
        ai_insights.append(
            f"Top Category: {sorted_cats[0][0]} is your largest expense category at ₹{sorted_cats[0][1]:,.0f} ({round(sorted_cats[0][1]/total_all_expenses*100, 1)}% of total)."
        )

    if prev_m_expense > 0:
        if mom_expense_change_pct > 0:
            ai_insights.append(
                f"Spending Trajectory: Monthly expenses increased by {mom_expense_change_pct}% compared with previous month (₹{curr_m_expense:,.0f} vs ₹{prev_m_expense:,.0f})."
            )
        elif mom_expense_change_pct < 0:
            ai_insights.append(
                f"Spending Trajectory: Excellent! Monthly expenses reduced by {abs(mom_expense_change_pct)}% compared with previous month."
            )
    elif curr_m_expense > 0:
        ai_insights.append(f"Current Month Spending: Total recorded expenses for this month stand at ₹{curr_m_expense:,.0f}.")

    if active_goals:
        top_goal = active_goals[0]
        g_prog = round((top_goal.current_amount / top_goal.target_amount) * 100, 1) if top_goal.target_amount > 0 else 0.0
        ai_insights.append(
            f"Goal Progress: '{top_goal.goal_name}' is currently {g_prog}% achieved (₹{top_goal.current_amount:,.0f} of ₹{top_goal.target_amount:,.0f})."
        )

    if curr_m_income > 0:
        ai_insights.append(
            f"Income & Savings Balance: Net monthly savings rate is currently {savings_pct}% of total income."
        )

    return {
        "curr_m_savings": curr_m_savings,
        "savings_pct": savings_pct,
        "curr_m_income": curr_m_income,
        "curr_m_expense": curr_m_expense,
        "prev_m_expense": prev_m_expense,
        "has_prev_data": has_prev_data,
        "mom_expense_change_pct": mom_expense_change_pct,
        "avg_monthly_expenses": avg_monthly_expenses,
        "projected_month_end_balance": projected_month_end_balance,
        "total_accounts_balance": total_accounts_balance,
        "active_goals_count": active_goals_count,
        "active_goals": active_goals,
        "budget_recommendations": budget_recommendations,
        "ai_insights": ai_insights
    }


def get_goal_expense_analytics(user_id):
    """
    Computes real Expense-to-Goal Analytics:
    1. Per Goal Expense Metrics (Total linked expenses, Count, Avg amount, Latest date)
    2. Goal vs Expense Visualizations (Goal-Linked Expenses by Goal, Goal-linked vs Regular Non-goal expenses)
    3. Monthly Goal-Linked Expense Trend (Last 6 Months)
    4. Smart Dashboard Goal-Expense metrics
    """
    today = date.today()
    goals = Goal.query.filter_by(user_id=user_id).all()
    all_expenses = Expense.query.filter_by(user_id=user_id).all()

    goal_analysis_list = []
    goal_names = []
    goal_linked_totals = []
    total_all_goal_linked = 0.0

    most_expensive_goal_name = "None"
    max_goal_expense_amt = -1.0
    latest_goal_expense_obj = None

    for g in goals:
        linked_exp = [e for e in all_expenses if e.goal_id == g.id]
        linked_exp.sort(key=lambda x: x.expense_date or date.min, reverse=True)

        total_amt = sum(e.amount for e in linked_exp)
        count_exp = len(linked_exp)
        avg_amt = round(total_amt / count_exp, 2) if count_exp > 0 else 0.0
        latest_date_str = linked_exp[0].expense_date.strftime("%d %b %Y") if count_exp > 0 and linked_exp[0].expense_date else "N/A"

        if count_exp > 0:
            if not latest_goal_expense_obj or (linked_exp[0].expense_date and linked_exp[0].expense_date > (latest_goal_expense_obj.expense_date or date.min)):
                latest_goal_expense_obj = linked_exp[0]

        if total_amt > max_goal_expense_amt and total_amt > 0:
            max_goal_expense_amt = total_amt
            most_expensive_goal_name = g.goal_name

        total_all_goal_linked += total_amt

        goal_analysis_list.append({
            "goal": g,
            "total_expenses": total_amt,
            "count_expenses": count_exp,
            "avg_expense": avg_amt,
            "latest_date": latest_date_str
        })

        if total_amt > 0 or len(goals) <= 5:
            goal_names.append(g.goal_name)
            goal_linked_totals.append(float(total_amt))

    total_all_expenses = sum(e.amount for e in all_expenses)
    total_regular_expenses = max(0.0, total_all_expenses - total_all_goal_linked)

    goals_with_expenses_count = sum(1 for item in goal_analysis_list if item["count_expenses"] > 0)

    # Monthly Goal-Linked Expense Trend (Last 6 Months)
    month_labels = []
    monthly_goal_expenses = []
    for i in range(5, -1, -1):
        m_start = get_first_day_of_month(today, i)
        m_end = get_last_day_of_month(m_start)
        m_label = m_start.strftime("%b %Y")
        
        m_sum = sum(
            e.amount for e in all_expenses
            if e.goal_id and e.expense_date and m_start <= e.expense_date <= m_end
        )
        month_labels.append(m_label)
        monthly_goal_expenses.append(float(m_sum))

    return {
        "goal_analysis_list": goal_analysis_list,
        "goal_names": goal_names,
        "goal_linked_totals": goal_linked_totals,
        "total_all_goal_linked": float(total_all_goal_linked),
        "total_regular_expenses": float(total_regular_expenses),
        "total_all_expenses": float(total_all_expenses),
        "goals_with_expenses_count": goals_with_expenses_count,
        "most_expensive_goal_name": most_expensive_goal_name,
        "most_expensive_goal_amt": float(max_goal_expense_amt) if max_goal_expense_amt > 0 else 0.0,
        "latest_goal_expense": latest_goal_expense_obj,
        "monthly_trend_labels": month_labels,
        "monthly_trend_amounts": monthly_goal_expenses
    }


def calculate_financial_health_score(user_id):
    """
    Dynamically calculates the Financial Health Score (0-100) based on 5 financial pillars:
    1. Net Savings Rate (25 pts)
    2. Budget Health & Utilization (25 pts)
    3. Goal Progress & Achievement (20 pts)
    4. Spending Pattern & Category Concentration (15 pts)
    5. Financial Risk & Unread Alerts (15 pts)
    """
    from models.alert import FinancialAlert

    incomes = Income.query.filter_by(user_id=user_id).all()
    expenses = Expense.query.filter_by(user_id=user_id).all()
    goals = Goal.query.filter_by(user_id=user_id).all()
    active_budget = Budget.query.filter_by(user_id=user_id).order_by(Budget.created_at.desc()).first()
    unread_alerts = FinancialAlert.query.filter_by(user_id=user_id, is_read=False).all()

    total_income = sum(inc.amount for inc in incomes)
    total_expenses = sum(exp.amount for exp in expenses)
    total_savings = total_income - total_expenses

    breakdown = []

    # 1. Net Savings Rate (Max 25 Pts)
    if total_income > 0:
        savings_rate = round((total_savings / total_income) * 100, 1)
        if savings_rate >= 30.0:
            savings_score = 25
            savings_note = f"Excellent net savings rate ({savings_rate}% of income)."
        elif savings_rate >= 20.0:
            savings_score = 20
            savings_note = f"Good net savings rate ({savings_rate}% of income)."
        elif savings_rate >= 10.0:
            savings_score = 15
            savings_note = f"Moderate net savings rate ({savings_rate}% of income)."
        elif savings_rate >= 0.0:
            savings_score = 10
            savings_note = f"Low net savings rate ({savings_rate}% of income)."
        else:
            savings_score = 0
            savings_note = f"Warning: Overspending detected (Net savings rate is {savings_rate}%)."
    else:
        if total_expenses > 0:
            savings_score = 0
            savings_note = "Expenses recorded without any income."
        else:
            savings_score = 15
            savings_note = "No income/expense records yet (Neutral balance)."

    breakdown.append({
        "pillar": "Net Savings",
        "score": savings_score,
        "max_score": 25,
        "note": savings_note
    })

    # 2. Budget Health (Max 25 Pts)
    if active_budget and active_budget.monthly_budget > 0:
        budget_limit = active_budget.monthly_budget
        budget_used_pct = round((total_expenses / budget_limit) * 100, 1)
        if budget_used_pct <= 70.0:
            budget_score = 25
            budget_note = f"Excellent budget utilization ({budget_used_pct}% used)."
        elif budget_used_pct <= 85.0:
            budget_score = 20
            budget_note = f"Good budget control ({budget_used_pct}% used)."
        elif budget_used_pct <= 100.0:
            budget_score = 12
            budget_note = f"Budget near limit ({budget_used_pct}% used)."
        elif budget_used_pct <= 120.0:
            budget_score = 5
            budget_note = f"Budget exceeded by {round(budget_used_pct - 100, 1)}%."
        else:
            budget_score = 0
            budget_note = f"Severe budget overrun ({budget_used_pct}% used)."
    else:
        budget_score = 15
        budget_note = "No active monthly budget set."

    breakdown.append({
        "pillar": "Budget Health",
        "score": budget_score,
        "max_score": 25,
        "note": budget_note
    })

    # 3. Goal Progress (Max 20 Pts)
    if goals:
        progresses = []
        for g in goals:
            p = (g.current_amount / g.target_amount * 100) if g.target_amount > 0 else 0.0
            progresses.append(min(100.0, p))
        avg_progress = round(sum(progresses) / len(progresses), 1)

        if avg_progress >= 75.0:
            goal_score = 20
            goal_note = f"High goal completion progress (Avg: {avg_progress}%)."
        elif avg_progress >= 50.0:
            goal_score = 16
            goal_note = f"Good goal progress (Avg: {avg_progress}%)."
        elif avg_progress >= 25.0:
            goal_score = 12
            goal_note = f"Moderate goal progress (Avg: {avg_progress}%)."
        elif avg_progress > 0.0:
            goal_score = 8
            goal_note = f"Early goal progress (Avg: {avg_progress}%)."
        else:
            goal_score = 5
            goal_note = "Goal progress has not started yet (0%)."
    else:
        goal_score = 10
        goal_note = "No financial goals created yet."

    breakdown.append({
        "pillar": "Goal Progress",
        "score": goal_score,
        "max_score": 20,
        "note": goal_note
    })

    # 4. Spending Pattern (Max 15 Pts)
    if total_expenses > 0:
        cat_totals = {}
        for e in expenses:
            cat_totals[e.category] = cat_totals.get(e.category, 0.0) + e.amount
        top_cat_amt = max(cat_totals.values())
        top_cat_name = [k for k, v in cat_totals.items() if v == top_cat_amt][0]
        top_cat_pct = round((top_cat_amt / total_expenses) * 100, 1)

        if top_cat_pct <= 30.0:
            spending_score = 15
            spending_note = f"Well-balanced category spending (Top: {top_cat_name} at {top_cat_pct}%)."
        elif top_cat_pct <= 45.0:
            spending_score = 12
            spending_note = f"Moderate category concentration ({top_cat_name} is {top_cat_pct}%)."
        elif top_cat_pct <= 60.0:
            spending_score = 7
            spending_note = f"High category concentration ({top_cat_name} is {top_cat_pct}%)."
        else:
            spending_score = 2
            spending_note = f"Heavy category overconcentration ({top_cat_name} is {top_cat_pct}%)."
    else:
        spending_score = 15
        spending_note = "No expense data recorded."

    breakdown.append({
        "pillar": "Spending Pattern",
        "score": spending_score,
        "max_score": 15,
        "note": spending_note
    })

    # 5. Financial Risk & Alerts (Max 15 Pts)
    danger_alerts = sum(1 for a in unread_alerts if a.severity == "danger")
    warning_alerts = sum(1 for a in unread_alerts if a.severity == "warning")

    deductions = (danger_alerts * 5) + (warning_alerts * 3)
    risk_score = max(0, 15 - deductions)

    if danger_alerts == 0 and warning_alerts == 0:
        risk_note = "No active warning or critical alerts."
    else:
        risk_note = f"Active risk alerts detected: {warning_alerts} warning(s), {danger_alerts} critical (-{deductions} pts)."

    breakdown.append({
        "pillar": "Financial Risk & Alerts",
        "score": risk_score,
        "max_score": 15,
        "note": risk_note
    })

    # -------------------------------------------------------------
    # POSITIVE FACTORS, AREAS FOR IMPROVEMENT & RECOMMENDATIONS
    # -------------------------------------------------------------
    positive_factors = []
    areas_for_improvement = []
    recommendations = []

    # Savings Pillar
    if savings_score >= 20:
        positive_factors.append(f"Strong Net Savings: {savings_note}")
    else:
        areas_for_improvement.append(f"Low Savings Margin: {savings_note}")
        recommendations.append("Increase your monthly savings margin by reviewing and reducing non-essential expenses.")

    # Budget Pillar
    if budget_score >= 20:
        positive_factors.append(f"Healthy Budget Control: {budget_note}")
    else:
        areas_for_improvement.append(f"Budget Utilization Concern: {budget_note}")
        recommendations.append("Review category caps and adjust your monthly budget limit to maintain buffer.")

    # Goal Pillar
    if goal_score >= 16:
        positive_factors.append(f"Solid Goal Progress: {goal_note}")
    else:
        areas_for_improvement.append(f"Slow Goal Advancement: {goal_note}")
        recommendations.append("Allocate a portion of net savings regularly toward active financial goals.")

    # Spending Pattern Pillar
    if spending_score >= 12:
        positive_factors.append(f"Balanced Spending Diversification: {spending_note}")
    else:
        areas_for_improvement.append(f"Category Spending Concentration: {spending_note}")
        recommendations.append("Set category caps on your highest spending category to balance monthly expenses.")

    # Risk & Alerts Pillar
    if risk_score == 15:
        positive_factors.append("Clean Financial Alert Status: Zero active warning or critical alerts.")
    else:
        areas_for_improvement.append(f"Unresolved Risk Alerts: {risk_note}")
        recommendations.append("Review and mark read active financial alerts on the Alert Dashboard.")

    total_health_score = savings_score + budget_score + goal_score + spending_score + risk_score

    if total_health_score >= 80:
        status_label = "Excellent"
        status_class = "excellent"
        summary_explanation = f"Your Financial Health Score is {total_health_score}/100. Excellent financial discipline across savings, budget, and goal tracking!"
    elif total_health_score >= 60:
        status_label = "Stable"
        status_class = "stable"
        summary_explanation = f"Your Financial Health Score is {total_health_score}/100. Stable overall finances. Small optimizations in budget control or goals will increase your score."
    elif total_health_score >= 40:
        status_label = "Needs Attention"
        status_class = "attention"
        summary_explanation = f"Your Financial Health Score is {total_health_score}/100. Financial management needs attention due to budget utilization, category concentration, or active alerts."
    else:
        status_label = "At Risk"
        status_class = "risk"
        summary_explanation = f"Your Financial Health Score is {total_health_score}/100. Financial status is at risk of strain due to high expenses, over-budget spending, or critical risk alerts."

    return {
        "score": total_health_score,
        "max_score": 100,
        "status_label": status_label,
        "status_class": status_class,
        "summary_explanation": summary_explanation,
        "breakdown": breakdown,
        "savings_score": savings_score,
        "budget_score": budget_score,
        "goal_score": goal_score,
        "spending_score": spending_score,
        "risk_score": risk_score,
        "positive_factors": positive_factors,
        "areas_for_improvement": areas_for_improvement,
        "recommendations": recommendations
    }
