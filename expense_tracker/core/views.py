from django.shortcuts import render

# Create your views here.
# core/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Account, Transaction, Category, Budget, Goal
from .forms import TransactionForm, BudgetForm, GoalForm  # We'll create these forms later

@login_required
def dashboard(request):
    """Main dashboard view showing overview of finances"""
    # Get current date and start of month
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    
    # Get account summaries
    accounts = Account.objects.filter(user=request.user, is_archived=False)
    total_balance = accounts.aggregate(total=Sum('balance'))['total'] or 0
    
    # Get monthly income and expenses
    monthly_transactions = Transaction.objects.filter(
        user=request.user,
        date__gte=start_of_month,
        date__lte=today
    )
    monthly_income = monthly_transactions.filter(
        transaction_type='INCOME'
    ).aggregate(total=Sum('amount'))['total'] or 0
    monthly_expenses = monthly_transactions.filter(
        transaction_type='EXPENSE'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Get expense distribution by category
    expense_by_category = monthly_transactions.filter(
        transaction_type='EXPENSE'
    ).values('category__name').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    # Get monthly trend (last 6 months)
    six_months_ago = today - timedelta(days=180)
    monthly_trend = Transaction.objects.filter(
        user=request.user,
        date__gte=six_months_ago
    ).values('date__month').annotate(
        expenses=Sum('amount', filter=models.Q(transaction_type='EXPENSE')),
        income=Sum('amount', filter=models.Q(transaction_type='INCOME'))
    ).order_by('date__month')
    
    # Get recent transactions
    recent_transactions = Transaction.objects.filter(
        user=request.user
    ).select_related('category', 'account').order_by('-date')[:5]
    
    # Get budget progress
    active_budgets = Budget.objects.filter(
        user=request.user,
        start_date__lte=today,
        end_date__gte=today
    ).select_related('category')
    
    for budget in active_budgets:
        current_spending = monthly_transactions.filter(
            category=budget.category,
            transaction_type='EXPENSE'
        ).aggregate(total=Sum('amount'))['total'] or 0
        budget.progress = (current_spending / budget.amount) * 100
        budget.remaining = budget.amount - current_spending

    context = {
        'total_balance': total_balance,
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'expense_by_category': expense_by_category,
        'monthly_trend': monthly_trend,
        'recent_transactions': recent_transactions,
        'active_budgets': active_budgets,
    }
    return render(request, 'core/dashboard.html', context)

@login_required
def transaction_list(request):
    """View for listing and filtering transactions"""
    transactions = Transaction.objects.filter(
        user=request.user
    ).select_related('category', 'account').order_by('-date')
    
    # Handle filtering
    category_id = request.GET.get('category')
    account_id = request.GET.get('account')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if category_id:
        transactions = transactions.filter(category_id=category_id)
    if account_id:
        transactions = transactions.filter(account_id=account_id)
    if date_from:
        transactions = transactions.filter(date__gte=date_from)
    if date_to:
        transactions = transactions.filter(date__lte=date_to)
    
    categories = Category.objects.filter(user=request.user)
    accounts = Account.objects.filter(user=request.user)
    
    context = {
        'transactions': transactions,
        'categories': categories,
        'accounts': accounts,
    }
    return render(request, 'core/transaction_list.html', context)

@login_required
def add_transaction(request):
    """View for adding new transactions"""
    if request.method == 'POST':
        form = TransactionForm(request.POST, user=request.user)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            messages.success(request, 'Transaction added successfully!')
            return redirect('transaction_list')
    else:
        form = TransactionForm(user=request.user)
    
    context = {'form': form}
    return render(request, 'core/transaction_form.html', context)

@login_required
def budget_list(request):
    """View for managing budgets"""
    budgets = Budget.objects.filter(user=request.user)
    
    if request.method == 'POST':
        form = BudgetForm(request.POST, user=request.user)
        if form.is_valid():
            budget = form.save(commit=False)
            budget.user = request.user
            budget.save()
            messages.success(request, 'Budget created successfully!')
            return redirect('budget_list')
    else:
        form = BudgetForm(user=request.user)
    
    context = {
        'budgets': budgets,
        'form': form,
    }
    return render(request, 'core/budget_list.html', context)

@login_required
def goal_list(request):
    """View for managing financial goals"""
    goals = Goal.objects.filter(user=request.user)
    
    if request.method == 'POST':
        form = GoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.save()
            messages.success(request, 'Goal created successfully!')
            return redirect('goal_list')
    else:
        form = GoalForm()
    
    context = {
        'goals': goals,
        'form': form,
    }
    return render(request, 'core/goal_list.html', context)

@login_required
def account_summary(request, account_id):
    """View for detailed account information"""
    account = get_object_or_404(Account, id=account_id, user=request.user)
    
    # Get transactions for this account
    transactions = Transaction.objects.filter(
        account=account
    ).select_related('category').order_by('-date')[:10]
    
    # Get monthly statistics
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    monthly_stats = Transaction.objects.filter(
        account=account,
        date__gte=start_of_month
    ).aggregate(
        income=Sum('amount', filter=models.Q(transaction_type='INCOME')),
        expenses=Sum('amount', filter=models.Q(transaction_type='EXPENSE'))
    )
    
    context = {
        'account': account,
        'transactions': transactions,
        'monthly_stats': monthly_stats,
    }
    return render(request, 'core/account_summary.html', context)

@login_required
def category_analysis(request, category_id):
    """View for analyzing spending by category"""
    category = get_object_or_404(Category, id=category_id, user=request.user)
    
    # Get date range (default to last 6 months)
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=180)
    
    # Get monthly spending for this category
    monthly_spending = Transaction.objects.filter(
        category=category,
        transaction_type='EXPENSE',
        date__gte=start_date,
        date__lte=end_date
    ).values('date__month').annotate(
        total=Sum('amount')
    ).order_by('date__month')
    
    # Get budget information if it exists
    budget = Budget.objects.filter(
        category=category,
        start_date__lte=end_date,
        end_date__gte=end_date
    ).first()
    
    context = {
        'category': category,
        'monthly_spending': monthly_spending,
        'budget': budget,
    }
    return render(request, 'core/category_analysis.html', context)
@login_required
def edit_transaction(request, pk):
    # Implementation needed
    pass

@login_required
def delete_transaction(request, pk):
    # Implementation needed
    pass

# ... (implement other view functions)