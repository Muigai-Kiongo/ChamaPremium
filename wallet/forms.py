from django import forms
from django.contrib.auth.models import User
from .models import Wallet, Transaction


class DepositForm(forms.Form):
    """Form for depositing money from M-Pesa to wallet"""
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter amount',
            'step': '0.01'
        }),
        label='Amount to Deposit'
    )
    phone_number = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '254712345678'
        }),
        label='M-Pesa Phone Number',
        help_text='Format: 254XXXXXXXXX'
    )


class WithdrawForm(forms.Form):
    """Form for withdrawing money from wallet to M-Pesa"""
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter amount',
            'step': '0.01'
        }),
        label='Amount to Withdraw'
    )
    phone_number = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '254712345678'
        }),
        label='M-Pesa Phone Number',
        help_text='Format: 254XXXXXXXXX'
    )

    def __init__(self, *args, **kwargs):
        self.wallet = kwargs.pop('wallet', None)
        super().__init__(*args, **kwargs)

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if self.wallet and amount > self.wallet.balance:
            raise forms.ValidationError(
                f'Insufficient balance. Your balance is {self.wallet.balance}'
            )
        return amount


class SendMoneyForm(forms.Form):
    """Form for sending money to another chama member"""
    recipient_phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '254712345678'
        }),
        label='Recipient Phone Number',
        help_text='Enter the phone number of the chama member'
    )
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter amount',
            'step': '0.01'
        }),
        label='Amount to Send'
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Optional description',
            'rows': 3
        }),
        label='Description (Optional)'
    )

    def __init__(self, *args, **kwargs):
        self.wallet = kwargs.pop('wallet', None)
        super().__init__(*args, **kwargs)

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if self.wallet and amount > self.wallet.balance:
            raise forms.ValidationError(
                f'Insufficient balance. Your balance is {self.wallet.balance}'
            )
        return amount

    def clean_recipient_phone(self):
        phone = self.cleaned_data.get('recipient_phone')
        try:
            recipient_wallet = Wallet.objects.get(phone_number=phone)
            if self.wallet and recipient_wallet == self.wallet:
                raise forms.ValidationError("You cannot send money to yourself")
        except Wallet.DoesNotExist:
            raise forms.ValidationError("No wallet found with this phone number")
        return phone


class PayChamaForm(forms.Form):
    """Form for paying chama contribution from wallet"""
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter amount',
            'step': '0.01'
        }),
        label='Contribution Amount'
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'E.g., Monthly contribution for January 2024',
            'rows': 3
        }),
        label='Description (Optional)'
    )

    def __init__(self, *args, **kwargs):
        self.wallet = kwargs.pop('wallet', None)
        super().__init__(*args, **kwargs)

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if self.wallet and amount > self.wallet.balance:
            raise forms.ValidationError(
                f'Insufficient balance. Your balance is {self.wallet.balance}'
            )
        return amount


class TransactionFilterForm(forms.Form):
    """Form for filtering transaction history"""
    TRANSACTION_TYPE_CHOICES = [
        ('', 'All Transactions'),
        ('deposit', 'Deposits'),
        ('withdrawal', 'Withdrawals'),
        ('chama_payment', 'Chama Payments'),
    ]
    
    STATUS_CHOICES = [
        ('', 'All Status'),
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    transaction_type = forms.ChoiceField(
        choices=TRANSACTION_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Transaction Type'
    )
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Status'
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='From Date'
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='To Date'
    )