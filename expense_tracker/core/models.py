
# Create your models here.
# core/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

# class User(AbstractUser):
#     """Extended User model"""
#     
#     
# In your core/models.py file or wherever core.User is defined
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    # Ensure unique related_name values to avoid conflicts with auth.User
    currency = models.CharField(max_length=3, default='USD')
    notifications_enabled = models.BooleanField(default=True)
    theme = models.CharField(max_length=10, default='light')
    language = models.CharField(max_length=2, default='en')
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_groups',  # Change this related_name
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions',  # Change this related_name
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions'
    )

class Account(models.Model):
    """Bank accounts, cash, credit cards etc."""
    ACCOUNT_TYPES = [
        ('CASH', 'Cash'),
        ('BANK', 'Bank Account'),
        ('CREDIT', 'Credit Card'),
        ('SAVINGS', 'Savings Account'),
        ('INVESTMENT', 'Investment Account'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='USD')
    is_default = models.BooleanField(default=False)
    icon = models.CharField(max_length=50, null=True, blank=True)
    color = models.CharField(max_length=7, null=True, blank=True)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_default', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_account_type_display()})"

class Category(models.Model):
    """Expense or income category."""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # Additional fields
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subcategories')
    color = models.CharField(max_length=7, null=True, blank=True)  # e.g., Hex color code
    category_type = models.CharField(max_length=50, null=True, blank=True)  # Optional for categorization type
    icon = models.CharField(max_length=50, null=True, blank=True)  # Optional for storing an icon name
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Transaction(models.Model):
    """Financial transactions"""
    TRANSACTION_TYPES = [
        ('EXPENSE', 'Expense'),
        ('INCOME', 'Income'),
        ('TRANSFER', 'Transfer'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.CharField(max_length=200)
    date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='COMPLETED')
    attachments = models.JSONField(null=True, blank=True)  # Store URLs as JSON array
    location = models.JSONField(null=True, blank=True)  # Store location data as JSON
    tags = models.JSONField(null=True, blank=True)  # Store tags as JSON array
    is_recurring = models.BooleanField(default=False)
    recurring = models.ForeignKey('RecurringTransaction', null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.description} ({self.amount})"

    def save(self, *args, **kwargs):
        # Update account balance on transaction save
        if self.transaction_type == 'EXPENSE':
            self.account.balance -= self.amount
        elif self.transaction_type == 'INCOME':
            self.account.balance += self.amount
        self.account.save()
        super().save(*args, **kwargs)

class RecurringTransaction(models.Model):
    """Recurring transactions setup"""
    FREQUENCY_CHOICES = [
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
        ('YEARLY', 'Yearly'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('PAUSED', 'Paused'),
        ('CANCELLED', 'Cancelled'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.CharField(max_length=200)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    last_processed = models.DateField(null=True)
    next_due = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Budget(models.Model):
    """Budget tracking"""
    PERIOD_CHOICES = [
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
        ('YEARLY', 'Yearly'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='budget_items'  # Changed to avoid clashes
    )
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    rollover = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Goal(models.Model):
    """Financial goals"""
    GOAL_TYPES = [
        ('SAVINGS', 'Savings'),
        ('DEBT_PAYMENT', 'Debt Payment'),
        ('INVESTMENT', 'Investment'),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
    ]
    
    STATUS_CHOICES = [
        ('IN_PROGRESS', 'In Progress'),
        ('ACHIEVED', 'Achieved'),
        ('FAILED', 'Failed'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=100)
    target_amount = models.DecimalField(max_digits=15, decimal_places=2)
    current_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    deadline = models.DateField(null=True, blank=True)
    goal_type = models.CharField(max_length=20, choices=GOAL_TYPES)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='IN_PROGRESS')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)