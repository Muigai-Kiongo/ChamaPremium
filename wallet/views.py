from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .forms import DepositForm, WithdrawForm, SendMoneyForm, PayChamaForm, TransactionFilterForm
from .models import Wallet, Transaction


def wallet_view(request):
    wallet, created = Wallet.objects.get_or_create(
        user=request.user,
        defaults={'phone_number': '', 'balance': 0}
    )

    context = {'wallet': wallet}
    return render(request, 'wallet/wallet_dashboard.html', context)

def deposit_view(request):
    if request.user.is_superuser:
        try:
            wallet = request.user.wallet
        except Wallet.DoesNotExist:
            messages.error(request, 'Wallet not found')
            return redirect('wallet:wallet_dashboard')

    
    if request.method == 'POST':
        form = DepositForm(request.POST)
        
        if form.is_valid():
            amount = form.cleaned_data['amount']
            phone_number = form.cleaned_data['phone_number']
            
            transaction = Transaction.objects.create(
                wallet=wallet,
                type='deposit',
                amount=amount,
                description=f'Deposit from M-Pesa {phone_number}',
                status='pending'
            )
            
            messages.info(request, 'M-Pesa payment integration pending. STK push will be sent to your phone.')
            
            return redirect('transaction_history')
        
        else:
            messages.error(request, 'Fix errors below')
    
    else:
        form = DepositForm()
    
    context = {'form': form, 'wallet': wallet}
    return render(request, 'wallet/deposit.html', context)



def withdraw_view(request):
    try:
        wallet = request.user.wallet
    except Wallet.DoesNotExist:
        messages.error(request, 'Wallet not found')
        return redirect('wallet_dashboard')
    
    if request.method == 'POST':
        form = WithdrawForm(request.POST, wallet=wallet)
        
        if form.is_valid():
            amount = form.cleaned_data['amount']
            phone_number = form.cleaned_data['phone_number']
            
            if wallet.balance < amount:
                messages.error(request, f'Insufficient balance. Your balance is {wallet.balance}')
                context = {'form': form, 'wallet': wallet}
                return render(request, 'wallet/withdraw.html', context)
            
            wallet.balance -= amount
            wallet.save()
            
            transaction = Transaction.objects.create(
                wallet=wallet,
                type='withdrawal',
                amount=amount,
                description=f'Withdrawal to M-Pesa {phone_number}',
                status='completed'
            )
            
            messages.success(request, f'Withdrawal of {amount} successful!')
            return redirect('transaction_history')
        
        else:
            messages.error(request, 'Fix errors below')
    
    else:
        form = WithdrawForm(wallet=wallet)
    
    context = {'form': form, 'wallet': wallet}
    return render(request, 'wallet/withdraw.html', context)



def send_money_view(request):
    try:
        wallet = request.user.wallet
    except Wallet.DoesNotExist:
        messages.error(request, 'Wallet not found')
        return redirect('wallet_dashboard')
    
    if request.method == 'POST':
        form = SendMoneyForm(request.POST, wallet=wallet)
        
        if form.is_valid():
            recipient_phone = form.cleaned_data['recipient_phone']
            amount = form.cleaned_data['amount']
            description = form.cleaned_data.get('description', '')
            
            try:
                recipient_wallet = Wallet.objects.get(phone_number=recipient_phone)
            except Wallet.DoesNotExist:
                messages.error(request, 'Recipient wallet not found')
                context = {'form': form, 'wallet': wallet}
                return render(request, 'wallet/send_money.html', context)
            
            if recipient_wallet == wallet:
                messages.error(request, 'Cannot send money to yourself')
                context = {'form': form, 'wallet': wallet}
                return render(request, 'wallet/send_money.html', context)
            
            if wallet.balance < amount:
                messages.error(request, f'Insufficient balance. Your balance is {wallet.balance}')
                context = {'form': form, 'wallet': wallet}
                return render(request, 'wallet/send_money.html', context)
            
            wallet.balance -= amount
            wallet.save()
            
            recipient_wallet.balance += amount
            recipient_wallet.save()
            
            Transaction.objects.create(
                wallet=wallet,
                type='withdrawal',
                amount=amount,
                description=f'Sent to {recipient_wallet.user.username} - {description}',
                status='completed'
            )
            
            Transaction.objects.create(
                wallet=recipient_wallet,
                type='deposit',
                amount=amount,
                description=f'Received from {wallet.user.username} - {description}',
                status='completed'
            )
            
            messages.success(request, f'Successfully sent {amount} to {recipient_wallet.user.username}')
            return redirect('transaction_history')
        
        else:
            messages.error(request, 'Fix errors below')
    
    else:
        form = SendMoneyForm(wallet=wallet)
    
    context = {'form': form, 'wallet': wallet}
    return render(request, 'wallet/send_money.html', context)



def pay_chama_view(request):
    try:
        wallet = request.user.wallet
    except Wallet.DoesNotExist:
        messages.error(request, 'Wallet not found')
        return redirect('wallet_dashboard')
    
    if request.method == 'POST':
        form = PayChamaForm(request.POST, wallet=wallet)
        
        if form.is_valid():
            amount = form.cleaned_data['amount']
            description = form.cleaned_data.get('description', '')
            
            if wallet.balance < amount:
                messages.error(request, f'Insufficient balance. Your balance is {wallet.balance}')
                context = {'form': form, 'wallet': wallet}
                return render(request, 'wallet/pay_chama.html', context)
            
            wallet.balance -= amount
            wallet.save()
            
            transaction = Transaction.objects.create(
                wallet=wallet,
                type='chama_payment',
                amount=amount,
                description=description if description else 'Chama contribution payment',
                status='completed'
            )
            
            messages.success(request, f'Chama payment of {amount} successful!')
            return redirect('transaction_history')
        
        else:
            messages.error(request, 'Fix errors below')
    
    else:
        form = PayChamaForm(wallet=wallet)
    
    context = {'form': form, 'wallet': wallet}
    return render(request, 'wallet/pay_chama.html', context)



def transaction_history_view(request):
    try:
        wallet = request.user.wallet
    except Wallet.DoesNotExist:
        messages.error(request, 'Wallet not found')
        return redirect('wallet_dashboard')
    
    transactions = Transaction.objects.filter(wallet=wallet)
    
    form = TransactionFilterForm(request.GET)
    
    if form.is_valid():
        transaction_type = form.cleaned_data.get('transaction_type')
        status = form.cleaned_data.get('status')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')
        
        if transaction_type:
            transactions = transactions.filter(type=transaction_type)
        
        if status:
            transactions = transactions.filter(status=status)
        
        if date_from:
            transactions = transactions.filter(created_at__gte=date_from)
        
        if date_to:
            transactions = transactions.filter(created_at__lte=date_to)
    
    context = {
        'form': form,
        'wallet': wallet,
        'transactions': transactions
    }
    return render(request, 'wallet/transaction_history.html', context)