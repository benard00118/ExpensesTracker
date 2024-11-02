# expense_tracker/urls.py (project-level URLs)
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),  # Include core app URLs
    path('accounts/', include('django.contrib.auth.urls')),  # Django auth URLs
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# core/urls.py (app-level URLs)
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Transactions
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions/add/', views.add_transaction, name='add_transaction'),
    path('transactions/<int:pk>/edit/', views.edit_transaction, name='edit_transaction'),
    path('transactions/<int:pk>/delete/', views.delete_transaction, name='delete_transaction'),
    
    # Accounts
    path('accounts/', views.account_list, name='account_list'),
    path('accounts/add/', views.add_account, name='add_account'),
    path('accounts/<int:account_id>/', views.account_summary, name='account_summary'),
    path('accounts/<int:pk>/edit/', views.edit_account, name='edit_account'),
    path('accounts/<int:pk>/delete/', views.delete_account, name='delete_account'),
    
    # Categories
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.add_category, name='add_category'),
    path('categories/<int:category_id>/analysis/', views.category_analysis, name='category_analysis'),
    path('categories/<int:pk>/edit/', views.edit_category, name='edit_category'),
    path('categories/<int:pk>/delete/', views.delete_category, name='delete_category'),
    
    # Budgets
    path('budgets/', views.budget_list, name='budget_list'),
    path('budgets/add/', views.add_budget, name='add_budget'),
    path('budgets/<int:pk>/edit/', views.edit_budget, name='edit_budget'),
    path('budgets/<int:pk>/delete/', views.delete_budget, name='delete_budget'),
    
    # Goals
    path('goals/', views.goal_list, name='goal_list'),
    path('goals/add/', views.add_goal, name='add_goal'),
    path('goals/<int:pk>/edit/', views.edit_goal, name='edit_goal'),
    path('goals/<int:pk>/delete/', views.delete_goal, name='delete_goal'),
    
    # Reports and Analysis
    path('reports/', views.report_list, name='report_list'),
    path('reports/expense-summary/', views.expense_summary, name='expense_summary'),
    path('reports/income-summary/', views.income_summary, name='income_summary'),
    path('reports/cash-flow/', views.cash_flow, name='cash_flow'),
    
    # API endpoints for AJAX requests
    path('api/transactions/chart-data/', views.transaction_chart_data, name='transaction_chart_data'),
    path('api/categories/chart-data/', views.category_chart_data, name='category_chart_data'),
    path('api/budget/progress/', views.budget_progress_data, name='budget_progress_data'),
    
    # User Profile and Settings
    path('profile/', views.user_profile, name='user_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('settings/', views.user_settings, name='user_settings'),
    
    # Export functionality
    path('export/transactions/', views.export_transactions, name='export_transactions'),
    path('export/report/<str:report_type>/', views.export_report, name='export_report'),
]   