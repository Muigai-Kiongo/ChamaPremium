from django import forms
from django.contrib.auth.models import User
from .models import (
    MemberProfile, LoanProduct, LoanApplication, 
    Loan, LoanRepayment, TableBankingLoan, TableBankingRound, Contribution
)
from decimal import Decimal


class CheckEligibilityForm(forms.Form):
    """Form for checking loan eligibility"""
    loan_product = forms.ModelChoiceField(
        queryset=LoanProduct.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Select Loan Product',
        empty_label='-- Choose a loan product --'
    )
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter desired loan amount',
            'step': '0.01'
        }),
        label='Loan Amount'
    )


class LoanApplicationForm(forms.ModelForm):
    """Form for applying for a loan"""
    
    class Meta:
        model = LoanApplication
        fields = ['loan_product', 'amount_requested', 'purpose', 'repayment_period']
        widgets = {
            'loan_product': forms.Select(attrs={'class': 'form-control'}),
            'amount_requested': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter amount',
                'step': '0.01'
            }),
            'purpose': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Explain why you need this loan',
                'rows': 4
            }),
            'repayment_period': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'loan_product': 'Loan Product',
            'amount_requested': 'Amount Requested',
            'purpose': 'Loan Purpose',
            'repayment_period': 'Repayment Period (Months)',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['loan_product'].queryset = LoanProduct.objects.filter(is_active=True)
        self.fields['loan_product'].empty_label = '-- Select Loan Product --'

    def clean_amount_requested(self):
        amount = self.cleaned_data.get('amount_requested')
        loan_product = self.cleaned_data.get('loan_product')
        
        if loan_product:
            if amount < loan_product.min_amount:
                raise forms.ValidationError(
                    f'Minimum amount for this product is {loan_product.min_amount}'
                )
            if amount > loan_product.max_amount:
                raise forms.ValidationError(
                    f'Maximum amount for this product is {loan_product.max_amount}'
                )
        return amount

    def clean(self):
        cleaned_data = super().clean()
        loan_product = cleaned_data.get('loan_product')
        repayment_period = cleaned_data.get('repayment_period')
        
        if loan_product and repayment_period:
            available_periods = loan_product.repayment_periods
            if repayment_period not in available_periods:
                raise forms.ValidationError(
                    f'Invalid repayment period. Available periods: {available_periods}'
                )
        
        return cleaned_data



class LoanPaymentForm(forms.Form):
    """Form for making loan repayment"""
    PAYMENT_METHOD_CHOICES = [
        ('mpesa', 'M-Pesa'),
        ('wallet', 'Wallet'),
        ('cash', 'Cash'),
    ]
    
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter payment amount',
            'step': '0.01'
        }),
        label='Payment Amount'
    )
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHOD_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Payment Method'
    )
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '254712345678'
        }),
        label='M-Pesa Phone Number',
        help_text='Required for M-Pesa payments'
    )

    def __init__(self, *args, **kwargs):
        self.loan = kwargs.pop('loan', None)
        super().__init__(*args, **kwargs)

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if self.loan and amount > self.loan.balance_remaining:
            raise forms.ValidationError(
                f'Payment amount exceeds balance. Balance remaining: {self.loan.balance_remaining}'
            )
        return amount

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        phone_number = cleaned_data.get('phone_number')
        
        if payment_method == 'mpesa' and not phone_number:
            raise forms.ValidationError('Phone number is required for M-Pesa payments')
        
        return cleaned_data


class LoanCalculatorForm(forms.Form):
    """Form for loan calculator"""
    principal = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter loan amount',
            'step': '0.01'
        }),
        label='Loan Amount'
    )
    interest_rate = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter interest rate',
            'step': '0.01'
        }),
        label='Interest Rate (%)'
    )
    repayment_period = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Number of months'
        }),
        label='Repayment Period (Months)'
    )


class TableBankingApplicationForm(forms.ModelForm):
    """Form for applying for table banking loan"""
    
    class Meta:
        model = TableBankingLoan
        fields = ['amount_borrowed']
        widgets = {
            'amount_borrowed': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter amount to borrow',
                'step': '0.01'
            }),
        }
        labels = {
            'amount_borrowed': 'Amount to Borrow',
        }

    def __init__(self, *args, **kwargs):
        self.round = kwargs.pop('round', None)
        super().__init__(*args, **kwargs)

    def clean_amount_borrowed(self):
        amount = self.cleaned_data.get('amount_borrowed')
        
        if self.round:
            available = self.round.total_pool - self.round.amount_lent
            if amount > available:
                raise forms.ValidationError(
                    f'Amount exceeds available pool. Available: {available}'
                )
        return amount


class ContributionPaymentForm(forms.Form):
    """Form for paying monthly contribution"""
    PAYMENT_METHOD_CHOICES = [
        ('mpesa', 'M-Pesa'),
        ('wallet', 'Wallet'),
        ('cash', 'Cash'),
    ]
    
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter contribution amount',
            'step': '0.01'
        }),
        label='Contribution Amount'
    )
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHOD_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Payment Method'
    )
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '254712345678'
        }),
        label='M-Pesa Phone Number',
        help_text='Required for M-Pesa payments'
    )

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        phone_number = cleaned_data.get('phone_number')