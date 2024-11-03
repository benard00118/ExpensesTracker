from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Sum, Q,Count
from django.utils import timezone
from datetime import datetime, timedelta
import csv
import json
from .models import Account, Transaction, Category, Budget, Goal
from .forms import AccountForm, CategoryForm, UserProfileForm, UserSettingsForm ,GoalForm ,BudgetForm# Add these forms
from django.db.models.functions import TruncMonth

@login_required
def dashboard(request):
    # Get current date and first day of current month
    today = timezone.now().date()
    first_day_of_month = today.replace(day=1)
    
    # Account Summary
    accounts = Account.objects.filter(
        user=request.user,
        is_archived=False
    ).annotate(
        transaction_count=Count('transaction')
    )
    total_balance = accounts.aggregate(total=Sum('balance'))['total'] or 0
    
    # Monthly Summary
    monthly_transactions = Transaction.objects.filter(
        user=request.user,
        date__gte=first_day_of_month,
        date__lte=today
    )
    
    monthly_income = monthly_transactions.filter(
        transaction_type='INCOME'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    monthly_expenses = monthly_transactions.filter(
        transaction_type='EXPENSE'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Recent Transactions
    recent_transactions = Transaction.objects.filter(
        user=request.user
    ).select_related('account', 'category')[:5]
    
    # Budget Progress
    active_budgets = Budget.objects.filter(
        user=request.user,
        start_date__lte=today
    ).select_related('category')
    
    budget_progress = []
    for budget in active_budgets:
        spent = Transaction.objects.filter(
            user=request.user,
            category=budget.category,
            date__gte=budget.start_date,
            date__lte=today,
            transaction_type='EXPENSE'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        budget_progress.append({
            'budget': budget,
            'spent': spent,
            'remaining': budget.amount - spent,
            'percentage': (spent / budget.amount * 100) if budget.amount > 0 else 0
        })
    
    # Goals Progress
    active_goals = Goal.objects.filter(
        user=request.user,
        status='IN_PROGRESS'
    )
    
    # Spending by Category (Last 30 days)
    thirty_days_ago = today - timedelta(days=30)
    category_spending = Transaction.objects.filter(
        user=request.user,
        transaction_type='EXPENSE',
        date__gte=thirty_days_ago
    ).values('category__name').annotate(
        total=Sum('amount')
    ).order_by('-total')[:5]
    
    # Monthly Spending Trend (Last 6 months)
    six_months_ago = today - timedelta(days=180)
    monthly_trend = Transaction.objects.filter(
        user=request.user,
        date__gte=six_months_ago
    ).annotate(
        month=TruncMonth('date')
    ).values('month', 'transaction_type').annotate(
        total=Sum('amount')
    ).order_by('month')
    
    # Upcoming Recurring Transactions
    upcoming_recurring = Transaction.objects.filter(
        user=request.user,
        is_recurring=True,
        date__gt=today
    ).order_by('date')[:3]
    
    context = {
        'total_balance': total_balance,
        'accounts': accounts,
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'recent_transactions': recent_transactions,
        'budget_progress': budget_progress,
        'active_goals': active_goals,
        'category_spending': category_spending,
        'monthly_trend': monthly_trend,
        'upcoming_recurring': upcoming_recurring,
        'current_month': today.strftime('%B %Y'),
    }
    
    return render(request, 'core/dashboard.html', context)

@login_required
def account_list(request):
    """View for listing all accounts"""
    accounts = Account.objects.filter(user=request.user)
    total_balance = accounts.aggregate(total=Sum('balance'))['total'] or 0
    
    context = {
        'accounts': accounts,
        'total_balance': total_balance,
    }
    return render(request, 'core/account_list.html', context)

@login_required
def add_account(request):
    """View for adding a new account"""
    if request.method == 'POST':
        form = AccountForm(request.POST)
        if form.is_valid():
            account = form.save(commit=False)
            account.user = request.user
            account.save()
            messages.success(request, 'Account created successfully!')
            return redirect('core:account_list')
    else:
        form = AccountForm()
    
    return render(request, 'core/account_form.html', {'form': form})

@login_required
def edit_account(request, pk):
    """View for editing an existing account"""
    account = get_object_or_404(Account, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = AccountForm(request.POST, instance=account)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account updated successfully!')
            return redirect('core:account_list')
    else:
        form = AccountForm(instance=account)
    
    return render(request, 'core/account_form.html', {'form': form, 'account': account})

@login_required
def delete_account(request, pk):
    """View for deleting an account"""
    account = get_object_or_404(Account, pk=pk, user=request.user)
    
    if request.method == 'POST':
        account.delete()
        messages.success(request, 'Account deleted successfully!')
        return redirect('core:account_list')
    
    return render(request, 'core/account_confirm_delete.html', {'account': account})

@login_required
def category_list(request):
    """View for listing all categories"""
    categories = Category.objects.filter(user=request.user)
    context = {'categories': categories}
    return render(request, 'core/category_list.html', context)

@login_required
def add_category(request):
    """View for adding a new category"""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            messages.success(request, 'Category created successfully!')
            return redirect('core:category_list')
    else:
        form = CategoryForm()
    
    return render(request, 'core/category_form.html', {'form': form})

@login_required
def edit_category(request, pk):
    """View for editing an existing category"""
    category = get_object_or_404(Category, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully!')
            return redirect('core:category_list')
    else:
        form = CategoryForm(instance=category)
    
    return render(request, 'core/category_form.html', {'form': form, 'category': category})

@login_required
def delete_category(request, pk):
    """View for deleting a category"""
    category = get_object_or_404(Category, pk=pk, user=request.user)
    
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted successfully!')
        return redirect('core:category_list')
    
    return render(request, 'core/category_confirm_delete.html', {'category': category})

@login_required
def add_budget(request):
    """View for adding a new budget"""
    if request.method == 'POST':
        form = BudgetForm(request.POST, user=request.user)
        if form.is_valid():
            budget = form.save(commit=False)
            budget.user = request.user
            budget.save()
            messages.success(request, 'Budget created successfully!')
            return redirect('core:budget_list')
    else:
        form = BudgetForm(user=request.user)
    
    return render(request, 'core/budget_form.html', {'form': form})

@login_required
def edit_budget(request, pk):
    """View for editing an existing budget"""
    budget = get_object_or_404(Budget, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = BudgetForm(request.POST, instance=budget, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Budget updated successfully!')
            return redirect('core:budget_list')
    else:
        form = BudgetForm(instance=budget, user=request.user)
    
    return render(request, 'core/budget_form.html', {'form': form, 'budget': budget})

@login_required
def delete_budget(request, pk):
    """View for deleting a budget"""
    budget = get_object_or_404(Budget, pk=pk, user=request.user)
    
    if request.method == 'POST':
        budget.delete()
        messages.success(request, 'Budget deleted successfully!')
        return redirect('core:budget_list')
    
    return render(request, 'core/budget_confirm_delete.html', {'budget': budget})

@login_required
def add_goal(request):
    """View for adding a new financial goal"""
    if request.method == 'POST':
        form = GoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.save()
            messages.success(request, 'Goal created successfully!')
            return redirect('core:goal_list')
    else:
        form = GoalForm()
    
    return render(request, 'core/goal_form.html', {'form': form})

@login_required
def edit_goal(request, pk):
    """View for editing an existing goal"""
    goal = get_object_or_404(Goal, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = GoalForm(request.POST, instance=goal)
        if form.is_valid():
            form.save()
            messages.success(request, 'Goal updated successfully!')
            return redirect('core:goal_list')
    else:
        form = GoalForm(instance=goal)
    
    return render(request, 'core/goal_form.html', {'form': form, 'goal': goal})

@login_required
def delete_goal(request, pk):
    """View for deleting a goal"""
    goal = get_object_or_404(Goal, pk=pk, user=request.user)
    
    if request.method == 'POST':
        goal.delete()
        messages.success(request, 'Goal deleted successfully!')
        return redirect('core:goal_list')
    
    return render(request, 'core/goal_confirm_delete.html', {'goal': goal})

@login_required
def report_list(request):
    """View for listing available reports"""
    return render(request, 'core/report_list.html')

@login_required
def expense_summary(request):
    """View for expense summary report"""
    today = timezone.now().date()
    start_date = today - timedelta(days=30)
    
    expenses = Transaction.objects.filter(
        user=request.user,
        transaction_type='EXPENSE',
        date__gte=start_date
    ).values('category__name').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    context = {
        'expenses': expenses,
        'start_date': start_date,
        'end_date': today,
    }
    return render(request, 'core/expense_summary.html', context)

@login_required
def income_summary(request):
    """View for income summary report"""
    today = timezone.now().date()
    start_date = today - timedelta(days=30)
    
    income = Transaction.objects.filter(
        user=request.user,
        transaction_type='INCOME',
        date__gte=start_date
    ).values('category__name').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    context = {
        'income': income,
        'start_date': start_date,
        'end_date': today,
    }
    return render(request, 'core/income_summary.html', context)

@login_required
def cash_flow(request):
    """View for cash flow report"""
    today = timezone.now().date()
    start_date = today - timedelta(days=30)
    
    transactions = Transaction.objects.filter(
        user=request.user,
        date__gte=start_date
    ).values('date').annotate(
        income=Sum('amount', filter=Q(transaction_type='INCOME')),
        expenses=Sum('amount', filter=Q(transaction_type='EXPENSE'))
    ).order_by('date')
    
    context = {
        'transactions': transactions,
        'start_date': start_date,
        'end_date': today,
    }
    return render(request, 'core/cash_flow.html', context)

@login_required
def transaction_chart_data(request):
    """API endpoint for transaction chart data"""
    today = timezone.now().date()
    start_date = today - timedelta(days=30)
    
    data = Transaction.objects.filter(
        user=request.user,
        date__gte=start_date
    ).values('date').annotate(
        income=Sum('amount', filter=Q(transaction_type='INCOME')),
        expenses=Sum('amount', filter=Q(transaction_type='EXPENSE'))
    ).order_by('date')
    
    return JsonResponse(list(data), safe=False)

@login_required
def category_chart_data(request):
    """API endpoint for category chart data"""
    today = timezone.now().date()
    start_date = today - timedelta(days=30)
    
    data = Transaction.objects.filter(
        user=request.user,
        date__gte=start_date
    ).values('category__name').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    return JsonResponse(list(data), safe=False)

@login_required
def budget_progress_data(request):
    """API endpoint for budget progress data"""
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    
    budgets = Budget.objects.filter(
        user=request.user,
        start_date__lte=today,
        end_date__gte=today
    ).select_related('category')
    
    data = []
    for budget in budgets:
        spending = Transaction.objects.filter(
            user=request.user,
            category=budget.category,
            transaction_type='EXPENSE',
            date__gte=start_of_month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        data.append({
            'category': budget.category.name,
            'budget': float(budget.amount),
            'spent': float(spending),
            'remaining': float(budget.amount - spending)
        })
    
    return JsonResponse(data, safe=False)

@login_required
def user_profile(request):
    """View for user profile"""
    return render(request, 'core/user_profile.html')

@login_required
def edit_profile(request):
    """View for editing user profile"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('core:user_profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'core/edit_profile.html', {'form': form})

@login_required
def user_settings(request):
    """View for user settings"""
    if request.method == 'POST':
        form = UserSettingsForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Settings updated successfully!')
            return redirect('core:dashboard')
    else:
        form = UserSettingsForm(instance=request.user)
    
    return render(request, 'core/user_settings.html', {'form': form})

@login_required
def export_transactions(request):
    """View for exporting transactions to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Date', 'Category', 'Account', 'Type', 'Amount', 'Description'])
    
    transactions = Transaction.objects.filter(user=request.user).select_related(
        'category', 'account'
    ).order_by('-date')
    
    for transaction in transactions:
        writer.writerow([
            transaction.date,
            transaction.category.name,
            transaction.account.name,
            transaction.transaction_type,
            transaction.amount,
            transaction.description
        ])
    
    return response

@login_required
def export_report(request, report_type):
    """View for exporting various reports"""
    today = timezone.now().date()
    start_date = today - timedelta(days=30)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{report_type}_report.csv"'
    
    writer = csv.writer(response)
    
    if report_type == 'expense':
        writer.writerow(['Category', 'Total Expenses'])
        data = Transaction.objects.filter(
            user=request.user,
            transaction_type='EXPENSE',
            date__gte=start_date
        ).values('category__name').annotate(
            total=Sum('amount')
        ).order_by('-total')
        
        for item in data:
            writer.writerow([item['category__name'], item['total']])
            
    elif report_type == 'income':
        writer.writerow(['Category', 'Total Income'])
        data = Transaction.objects.filter(
            user=request.user,
            transaction_type='INCOME',
            date__gte=start_date
        ).values('category__name').annotate(
            total=Sum('amount')
        ).order_by('-total')
        
        for item in data:
            writer.writerow([item['category__name'], item['total']])