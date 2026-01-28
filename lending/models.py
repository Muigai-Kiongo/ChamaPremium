from django.db import models
from django.contrib.auth.models import User

class MemberProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='member_profile')
    total_contributions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    contributions_missed = models.IntegerField(default=0)
    meetings_attended = models.IntegerField(default=0)
    meetings_missed = models.IntegerField(default=0)
    credit_score = models.IntegerField(default=0)
    is_qualified = models.BooleanField(default=False)
    member_since = models.DateField()
    
    def __str__(self):
        return f"{self.user.username} - Credit Score: {self.credit_score}"
    
    class Meta:
        verbose_name = "Member Profile"
        verbose_name_plural = "Member Profiles"


class LoanProduct(models.Model):
    name = models.CharField(max_length=100)
    min_amount = models.DecimalField(max_digits=12, decimal_places=2)
    max_amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    repayment_periods = models.JSONField()
    guarantors_required = models.IntegerField(default=0)
    min_credit_score = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Loan Product"
        verbose_name_plural = "Loan Products"


class LoanApplication(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('disbursed', 'Disbursed'),
    ]
    
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loan_applications')
    loan_product = models.ForeignKey(LoanProduct, on_delete=models.CASCADE, related_name='applications')
    amount_requested = models.DecimalField(max_digits=12, decimal_places=2)
    amount_approved = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    purpose = models.TextField()
    repayment_period = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_date = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_applications')
    review_notes = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.applicant.username} - {self.loan_product.name} - {self.status}"
    
    class Meta:
        verbose_name = "Loan Application"
        verbose_name_plural = "Loan Applications"
        ordering = ['-applied_date']


class Guarantor(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    ]
    
    loan_application = models.ForeignKey(LoanApplication, on_delete=models.CASCADE, related_name='guarantors')
    guarantor_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='guarantees')
    amount_guaranteed = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    responded_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.guarantor_user.username} guarantees {self.amount_guaranteed}"
    
    class Meta:
        verbose_name = "Guarantor"
        verbose_name_plural = "Guarantors"


class Loan(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('defaulted', 'Defaulted'),
    ]
    
    loan_application = models.ForeignKey(LoanApplication, on_delete=models.CASCADE, related_name='loans')
    borrower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loans')
    principal_amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    total_payable = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance_remaining = models.DecimalField(max_digits=12, decimal_places=2)
    monthly_installment = models.DecimalField(max_digits=12, decimal_places=2)
    disbursement_date = models.DateField(null=True, blank=True)
    next_due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    days_overdue = models.IntegerField(default=0)
    disbursement_mpesa_receipt = models.CharField(max_length=50, null=True, blank=True)
    conversation_id = models.CharField(max_length=100, null=True, blank=True)
    
    def __str__(self):
        return f"{self.borrower.username} - {self.principal_amount} - {self.status}"
    
    class Meta:
        verbose_name = "Loan"
        verbose_name_plural = "Loans"


class LoanRepayment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('mpesa', 'M-Pesa'),
        ('wallet', 'Wallet'),
        ('cash', 'Cash'),
    ]
    
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='repayments')
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    mpesa_code = models.CharField(max_length=50, null=True, blank=True)
    merchant_request_id = models.CharField(max_length=100, null=True, blank=True)
    checkout_request_id = models.CharField(max_length=100, null=True, blank=True)
    mpesa_receipt_number = models.CharField(max_length=50, null=True, blank=True)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    
    def __str__(self):
        return f"{self.loan.borrower.username} - Payment: {self.amount_paid}"
    
    class Meta:
        verbose_name = "Loan Repayment"
        verbose_name_plural = "Loan Repayments"
        ordering = ['-payment_date']


class RepaymentSchedule(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
    ]
    
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='repayment_schedule')
    installment_number = models.IntegerField()
    due_date = models.DateField()
    amount_due = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    def __str__(self):
        return f"Installment {self.installment_number} - {self.loan.borrower.username}"
    
    class Meta:
        verbose_name = "Repayment Schedule"
        verbose_name_plural = "Repayment Schedules"
        ordering = ['loan', 'installment_number']


class TableBankingRound(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed'),
    ]
    
    round_number = models.IntegerField(unique=True)
    round_date = models.DateField()
    total_pool = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_lent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    
    def __str__(self):
        return f"Round {self.round_number} - {self.round_date}"
    
    class Meta:
        verbose_name = "Table Banking Round"
        verbose_name_plural = "Table Banking Rounds"
        ordering = ['-round_number']


class TableBankingLoan(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('repaid', 'Repaid'),
        ('overdue', 'Overdue'),
    ]
    
    round = models.ForeignKey(TableBankingRound, on_delete=models.CASCADE, related_name='loans')
    borrower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='table_banking_loans')
    amount_borrowed = models.DecimalField(max_digits=12, decimal_places=2)
    due_date = models.DateField()
    amount_repaid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    mpesa_receipt_number = models.CharField(max_length=50, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    def __str__(self):
        return f"{self.borrower.username} - Round {self.round.round_number} - {self.amount_borrowed}"
    
    class Meta:
        verbose_name = "Table Banking Loan"
        verbose_name_plural = "Table Banking Loans"


class Contribution(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('mpesa', 'M-Pesa'),
        ('wallet', 'Wallet'),
        ('cash', 'Cash'),
    ]
    
    STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('partial', 'Partial'),
        ('missed', 'Missed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contributions')
    period = models.CharField(max_length=20)
    expected_amount = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_date = models.DateTimeField(null=True, blank=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, null=True, blank=True)
    mpesa_receipt_number = models.CharField(max_length=50, null=True, blank=True)
    merchant_request_id = models.CharField(max_length=100, null=True, blank=True)
    checkout_request_id = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='missed')
    
    def __str__(self):
        return f"{self.user.username} - {self.period} - {self.status}"
    
    class Meta:
        verbose_name = "Contribution"
        verbose_name_plural = "Contributions"
        ordering = ['-period']