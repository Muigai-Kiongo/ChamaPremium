from django.contrib import admin
from .models import (
    MemberProfile, LoanProduct, LoanApplication, Loan, 
    LoanRepayment, RepaymentSchedule, TableBankingRound, 
    TableBankingLoan, Contribution
)


@admin.register(MemberProfile)
class MemberProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'credit_score', 'is_qualified', 'total_contributions', 'member_since']
    list_filter = ['is_qualified', 'member_since']
    search_fields = ['user__username']


@admin.register(LoanProduct)
class LoanProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'min_amount', 'max_amount', 'interest_rate', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']


@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = ['applicant', 'loan_product', 'amount_requested', 'status', 'applied_date']
    list_filter = ['status', 'applied_date']
    search_fields = ['applicant__username', 'loan_product__name']
    readonly_fields = ['applied_date']


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ['borrower', 'principal_amount', 'balance_remaining', 'status', 'disbursement_date']
    list_filter = ['status', 'disbursement_date']
    search_fields = ['borrower__username']
    readonly_fields = ['disbursement_date']


@admin.register(LoanRepayment)
class LoanRepaymentAdmin(admin.ModelAdmin):
    list_display = ['loan', 'amount_paid', 'payment_method', 'payment_date']
    list_filter = ['payment_method', 'payment_date']
    search_fields = ['loan__borrower__username']
    readonly_fields = ['payment_date']


@admin.register(RepaymentSchedule)
class RepaymentScheduleAdmin(admin.ModelAdmin):
    list_display = ['loan', 'installment_number', 'due_date', 'amount_due', 'status']
    list_filter = ['status', 'due_date']
    search_fields = ['loan__borrower__username']


@admin.register(TableBankingRound)
class TableBankingRoundAdmin(admin.ModelAdmin):
    list_display = ['round_number', 'round_date', 'total_pool', 'amount_lent', 'status']
    list_filter = ['status', 'round_date']


@admin.register(TableBankingLoan)
class TableBankingLoanAdmin(admin.ModelAdmin):
    list_display = ['borrower', 'round', 'amount_borrowed', 'amount_repaid', 'status', 'due_date']
    list_filter = ['status', 'due_date']
    search_fields = ['borrower__username']


@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = ['user', 'period', 'expected_amount', 'amount_paid', 'status', 'payment_date']
    list_filter = ['status', 'payment_method', 'payment_date']
    search_fields = ['user__username', 'period']
    readonly_fields = ['payment_date']