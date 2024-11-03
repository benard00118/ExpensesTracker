# core/forms.py
from django import forms
from .models import Transaction, Budget, Goal, Category, RecurringTransaction, Account

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['account', 'category', 'transaction_type', 'amount', 'date', 'description']
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Get the user from the kwargs
        super().__init__(*args, **kwargs)
        
        # Filter the account and category fields to show only the user's data
        if user:
            self.fields['account'].queryset = self.fields['account'].queryset.filter(user=user)
            self.fields['category'].queryset = self.fields['category'].queryset.filter(user=user)

        # Add custom labels and widgets if needed
        self.fields['date'].widget = forms.DateInput(attrs={'type': 'date'})
class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['category', 'amount', 'start_date', 'end_date']
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter the category field for the logged-in user
        if user:
            self.fields['category'].queryset = self.fields['category'].queryset.filter(user=user)
        
        # Set date widgets for a better user interface
        self.fields['start_date'].widget = forms.DateInput(attrs={'type': 'date'})
        self.fields['end_date'].widget = forms.DateInput(attrs={'type': 'date'})
class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ['name', 'target_amount', 'deadline', 'description']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['target_date'].widget = forms.DateInput(attrs={'type': 'date'})
class TransactionFilterForm(forms.Form):
    category = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label='Category',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    account = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label='Account',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='From'
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='To'
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['category'].queryset = Category.objects.filter(user=user)
            self.fields['account'].queryset = Account.objects.filter(user=user)
class BaseUserForm(forms.ModelForm):
    """A base form class to filter user-specific data"""
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.filter_user_data()
    
    def filter_user_data(self):
        """Override this method to filter user-specific fields in child forms"""
        pass
class RecurringTransactionForm(forms.ModelForm):
    class Meta:
        model = RecurringTransaction
        fields = ['account', 'category', 'amount', 'description', 'frequency', 'start_date', 'end_date', 'status']
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['account'].queryset = Account.objects.filter(user=user)
            self.fields['category'].queryset = Category.objects.filter(user=user)
        
        self.fields['start_date'].widget = forms.DateInput(attrs={'type': 'date'})
        self.fields['end_date'].widget = forms.DateInput(attrs={'type': 'date'})
class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'category_type', 'icon', 'color', 'parent']
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['parent'].queryset = Category.objects.filter(user=user, is_archived=False)
from django import forms
from .models import Account, User

class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['name', 'account_type', 'balance', 'currency', 'is_default', 'icon', 'color']
        widgets = {
            'color': forms.TextInput(attrs={'type': 'color'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Add any custom field attributes or validation
        self.fields['balance'].widget.attrs['step'] = '0.01'
        self.fields['is_default'].help_text = 'Make this your default account'
        
        # Optional: Add Bootstrap classes or other styling
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'
        self.fields['is_default'].widget.attrs['class'] = 'form-check-input'

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes or other styling
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'
            
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('This email address is already in use.')
        return email

class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['currency', 'language', 'theme', 'notifications_enabled']
        widgets = {
            'theme': forms.Select(choices=[
                ('light', 'Light'),
                ('dark', 'Dark'),
                ('system', 'System Default')
            ]),
            'language': forms.Select(choices=[
                ('en', 'English'),
                ('es', 'Spanish'),
                ('fr', 'French'),
                ('de', 'German')
            ])
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes
        for field in self.fields:
            if field != 'notifications_enabled':
                self.fields[field].widget.attrs['class'] = 'form-control'
            else:
                self.fields[field].widget.attrs['class'] = 'form-check-input'
        
        # Add currency choices - you might want to customize this list
        self.fields['currency'].widget = forms.Select(choices=[
            ('USD', 'US Dollar'),
            ('EUR', 'Euro'),
            ('GBP', 'British Pound'),
            ('JPY', 'Japanese Yen'),
            ('AUD', 'Australian Dollar'),
            ('CAD', 'Canadian Dollar')
        ])
        
        # Customize help text
        self.fields['notifications_enabled'].help_text = 'Receive email notifications for important updates'