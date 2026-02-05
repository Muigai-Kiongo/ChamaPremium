from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
from .forms import (
    CheckEligibilityForm, LoanApplicationForm,  LoanPaymentForm, LoanCalculatorForm,
    TableBankingApplicationForm, ContributionPaymentForm
)
from .models import (
    MemberProfile, LoanProduct, LoanApplication,
    Loan, LoanRepayment, TableBankingLoan, TableBankingRound, Contribution
)


from django.db.models import Sum, Count, Q
from datetime import datetime, timedelta

def loan_view(request):
    return render(request, 'lending/loan.html')




def dashboard_view(request):
    user = request.user
    
    # Get or create member profile
    try:
        member_profile = user.member_profile
    except MemberProfile.DoesNotExist:
        member_profile = MemberProfile.objects.create(
            user=user,
            member_since=user.date_joined.date()
        )
    
    # Get active loans
    active_loans = Loan.objects.filter(
        borrower=user,
        status='active'
    )
    print(f"this are the active loans {active_loans}")
    # Get recent loan repayments (last 5)
    recent_payments = LoanRepayment.objects.filter(
        loan__borrower=user
    ).select_related('loan').order_by('-payment_date')[:5]
    
    # Get recent contributions (last 5)
    recent_contributions = Contribution.objects.filter(
        user=user
    ).order_by('-payment_date')[:5]
    
    # Get pending loan applications
    pending_applications = LoanApplication.objects.filter(
        applicant=user,
        status='pending'
    ).count()
    
    # Calculate total loan balance
    total_loan_balance = active_loans.aggregate(
        total=Sum('balance_remaining')
    )['total'] or 0
    
    # Calculate total contributions
    total_contributions = member_profile.total_contributions
    
    # Get upcoming payment (next due date)
    upcoming_payment = active_loans.filter(
        next_due_date__isnull=False
    ).order_by('next_due_date').first()
    
    # Calculate wallet balance (if you have a wallet model)
    try:
        wallet_balance = user.wallet.balance
    except:
        wallet_balance = 0
    
        # Stats for dashboard cards
    context = {
        'member_profile': member_profile,
        'active_loans': active_loans,
        'recent_payments': recent_payments,
        'recent_contributions': recent_contributions,
        'upcoming_payment': upcoming_payment,
        'wallet_balance': wallet_balance,
        'active_loan_count': active_loans.count(),
        'total_contributions': total_contributions,
        'credit_score': member_profile.credit_score,
    }
    
    return render(request, 'lending/dashboard.html', context)

def check_eligibility_view(request):
    if request.method == 'POST':
        form = CheckEligibilityForm(request.POST)
        
        if form.is_valid():
            loan_product = form.cleaned_data['loan_product']
            amount = form.cleaned_data['amount']
            
            if not request.user.is_authenticated:
                messages.error(request, 'Please log in to check eligibility.')
                return redirect('check_eligibility')

            try:
                member_profile = request.user.member_profile
            except MemberProfile.DoesNotExist:
                messages.error(request, 'Member profile not found.')
                return redirect('check_eligibility')

            
            is_eligible = True
            reasons = []
            
            if amount < loan_product.min_amount:
                is_eligible = False
                reasons.append(f'Amount below minimum of {loan_product.min_amount}')
            
            if amount > loan_product.max_amount:
                is_eligible = False
                reasons.append(f'Amount exceeds maximum of {loan_product.max_amount}')
            
            if member_profile.credit_score < loan_product.min_credit_score:
                is_eligible = False
                reasons.append(f'Credit score {member_profile.credit_score} below required {loan_product.min_credit_score}')
            
            if not member_profile.is_qualified:
                is_eligible = False
                reasons.append('Member not qualified')
            
            if not loan_product.is_active:
                is_eligible = False
                reasons.append('Loan product inactive')
            
            context = {
                'form': form,
                'is_eligible': is_eligible,
                'loan_product': loan_product,
                'amount': amount,
                'reasons': reasons,
                'member_profile': member_profile,
            }
            
            if is_eligible:
                messages.success(request, f'Eligible for {loan_product.name} of {amount}!')
            else:
                messages.error(request, 'Not eligible')
            
            return render(request, 'lending/check_eligibility.html', context)
        
        else:
            messages.error(request, 'Fix errors below')
    
    else:
        form = CheckEligibilityForm()
    
    context = {'form': form}
    return render(request, 'lending/check_eligibility.html', context)



def apply_loan_view(request):
    if request.method == 'POST':
        form = LoanApplicationForm(request.POST, user=request.user)
        
        if form.is_valid():
            loan_application = form.save(commit=False)
            loan_application.applicant = request.user
            loan_application.status = 'pending'
            loan_application.save()
            
            messages.success(request, 'Loan application submitted successfully!')
            return redirect('select_guarantors', application_id=loan_application.id)
        
        else:
            messages.error(request, 'Fix errors below')
    
    else:
        form = LoanApplicationForm(user=request.user)
    
    context = {'form': form}
    return render(request, 'lending/apply_loan.html', context)



def repay_loan_view(request, loan_id):
    loan = get_object_or_404(Loan, id=loan_id, borrower=request.user)
    
    if loan.status != 'active':
        messages.error(request, 'This loan is not active')
        return redirect('lending:my_loans')
    
    if request.method == 'POST':
        form = LoanPaymentForm(request.POST, loan=loan)
        
        if form.is_valid():
            amount = form.cleaned_data['amount']
            payment_method = form.cleaned_data['payment_method']
            phone_number = form.cleaned_data.get('phone_number')
            
            if payment_method == 'mpesa':
                messages.info(request, 'M-Pesa payment integration pending')
                return redirect('repay_loan', loan_id=loan.id)
            
            elif payment_method == 'wallet':
                try:
                    wallet = request.user.wallet
                    
                    if wallet.balance < amount:
                        messages.error(request, 'Insufficient wallet balance')
                        context = {'form': form, 'loan': loan}
                        return render(request, 'lending/repay_loan.html', context)
                    
                    wallet.balance -= amount
                    wallet.save()
                    
                    loan.amount_paid += amount
                    loan.balance_remaining -= amount
                    
                    if loan.balance_remaining <= 0:
                        loan.status = 'completed'
                    
                    loan.save()
                    
                    LoanRepayment.objects.create(
                        loan=loan,
                        amount_paid=amount,
                        payment_method=payment_method,
                        balance_after=loan.balance_remaining
                    )
                    
                    messages.success(request, f'Payment of {amount} successful. Balance remaining: {loan.balance_remaining}')
                    return redirect('my_loans')
                
                except Exception as e:
                    messages.error(request, f'Payment failed: {str(e)}')
            
            elif payment_method == 'cash':
                loan.amount_paid += amount
                loan.balance_remaining -= amount
                
                if loan.balance_remaining <= 0:
                    loan.status = 'completed'
                
                loan.save()
                
                LoanRepayment.objects.create(
                    loan=loan,
                    amount_paid=amount,
                    payment_method=payment_method,
                    balance_after=loan.balance_remaining
                )
                
                messages.success(request, f'Cash payment of {amount} recorded. Balance remaining: {loan.balance_remaining}')
                return redirect('my_loans')
        
        else:
            messages.error(request, 'Fix errors below')
    
    else:
        form = LoanPaymentForm(loan=loan)
    
    context = {'form': form, 'loan': loan}
    return render(request, 'lending/repay_loan.html', context)



def loan_calculator_view(request):
    calculation_result = None
    
    if request.method == 'POST':
        form = LoanCalculatorForm(request.POST)
        
        if form.is_valid():
            principal = form.cleaned_data['principal']
            interest_rate = form.cleaned_data['interest_rate']
            repayment_period = form.cleaned_data['repayment_period']
            
            monthly_rate = (interest_rate / 100) / 12
            
            if monthly_rate > 0:
                monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** repayment_period) / ((1 + monthly_rate) ** repayment_period - 1)
            else:
                monthly_payment = principal / repayment_period
            
            total_payable = monthly_payment * repayment_period
            total_interest = total_payable - principal
            
            calculation_result = {
                'principal': principal,
                'interest_rate': interest_rate,
                'repayment_period': repayment_period,
                'monthly_payment': round(monthly_payment, 2),
                'total_payable': round(total_payable, 2),
                'total_interest': round(total_interest, 2)
            }
        
        else:
            messages.error(request, 'Fix errors below')
    
    else:
        form = LoanCalculatorForm()
    
    context = {
        'form': form,
        'calculation_result': calculation_result
    }
    return render(request, 'lending/loan_calculator.html', context)



def apply_table_banking_view(request):
    try:
        current_round = TableBankingRound.objects.filter(status='open').latest('round_number')
    except TableBankingRound.DoesNotExist:
        messages.error(request, 'No active table banking round')
        return redirect('lending:loan')
    
    if request.method == 'POST':
        form = TableBankingApplicationForm(request.POST, round=current_round)
        
        if form.is_valid():
            table_banking_loan = form.save(commit=False)
            table_banking_loan.round = current_round
            table_banking_loan.borrower = request.user
            table_banking_loan.due_date = timezone.now().date() + timedelta(days=30)
            table_banking_loan.status = 'active'
            table_banking_loan.save()
            
            current_round.amount_lent += table_banking_loan.amount_borrowed
            current_round.save()
            
            messages.success(request, f'Table banking loan of {table_banking_loan.amount_borrowed} approved!')
            return redirect('my_table_banking_loans')
        
        else:
            messages.error(request, 'Fix errors below')
    
    else:
        form = TableBankingApplicationForm(round=current_round)
    
    available_amount = current_round.total_pool - current_round.amount_lent
    
    context = {
        'form': form,
        'current_round': current_round,
        'available_amount': available_amount
    }
    return render(request, 'lending/apply_table_banking.html', context)



def pay_contribution_view(request):
    if request.method == 'POST':
        form = ContributionPaymentForm(request.POST)
        
        if form.is_valid():
            amount = form.cleaned_data['amount']
            payment_method = form.cleaned_data['payment_method']
            phone_number = form.cleaned_data.get('phone_number')
            
            current_period = timezone.now().strftime('%Y-%m')
            
            contribution, created = Contribution.objects.get_or_create(
                user=request.user,
                period=current_period,
                defaults={
                    'expected_amount': amount,
                    'amount_paid': 0,
                    'status': 'missed'
                }
            )
            
            if payment_method == 'mpesa':
                messages.info(request, 'M-Pesa payment integration pending')
                return redirect('pay_contribution')
            
            elif payment_method == 'wallet':
                try:
                    wallet = request.user.wallet
                    
                    if wallet.balance < amount:
                        messages.error(request, 'Insufficient wallet balance')
                        context = {'form': form}
                        return render(request, 'lending/pay_contribution.html', context)
                    
                    wallet.balance -= amount
                    wallet.save()
                    
                    contribution.amount_paid += amount
                    contribution.payment_date = timezone.now()
                    contribution.payment_method = payment_method
                    
                    if contribution.amount_paid >= contribution.expected_amount:
                        contribution.status = 'paid'
                    else:
                        contribution.status = 'partial'
                    
                    contribution.save()
                    
                    member_profile = request.user.member_profile
                    member_profile.total_contributions += amount
                    member_profile.save()
                    
                    messages.success(request, f'Contribution payment of {amount} successful!')
                    return redirect('my_contributions')
                
                except Exception as e:
                    messages.error(request, f'Payment failed: {str(e)}')
            
            elif payment_method == 'cash':
                contribution.amount_paid += amount
                contribution.payment_date = timezone.now()
                contribution.payment_method = payment_method
                
                if contribution.amount_paid >= contribution.expected_amount:
                    contribution.status = 'paid'
                else:
                    contribution.status = 'partial'
                
                contribution.save()
                
                member_profile = request.user.member_profile
                member_profile.total_contributions += amount
                member_profile.save()
                
                messages.success(request, f'Cash contribution of {amount} recorded!')
                return redirect('my_contributions')
        
        else:
            messages.error(request, 'Fix errors below')
    
    else:
        form = ContributionPaymentForm()
    
    context = {'form': form}
    return render(request, 'lending/pay_contribution.html', context)



# @login_required
def my_loans_view(request):
    """Display all loans for the current user"""
    
    # Get all loans for the user
    active_loans = Loan.objects.filter(
        borrower=request.user, 
        status='active'
    ).order_by('-disbursement_date')
    
    completed_loans = Loan.objects.filter(
        borrower=request.user, 
        status='completed'
    ).order_by('-disbursement_date')
    
    pending_applications = LoanApplication.objects.filter(
        applicant=request.user,
        status='pending'
    ).order_by('-applied_date')  # CHANGED: application_date → applied_date
    
    rejected_applications = LoanApplication.objects.filter(
        applicant=request.user,
        status='rejected'
    ).order_by('-applied_date')  # CHANGED: application_date → applied_date
    
    # Calculate totals
    total_active_balance = sum(loan.balance_remaining for loan in active_loans)
    total_borrowed = sum(loan.principal_amount for loan in active_loans) + sum(loan.principal_amount for loan in completed_loans)
    total_paid = sum(loan.amount_paid for loan in active_loans) + sum(loan.principal_amount for loan in completed_loans)
    
    context = {
        'active_loans': active_loans,
        'completed_loans': completed_loans,
        'pending_applications': pending_applications,
        'rejected_applications': rejected_applications,
        'total_active_balance': total_active_balance,
        'total_borrowed': total_borrowed,
        'total_paid': total_paid,
    }
    
    return render(request, 'lending/my_loans.html', context)