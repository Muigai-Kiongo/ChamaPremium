from django.urls import path
from . import views

app_name = 'lending'

urlpatterns = [
    path('check-eligibility', views.check_eligibility_view, name='check_eligibility'),
    path('loan/' , views.loan_view, name='loan'),
    path('apply/', views.apply_loan_view, name='apply_loan'),
    path('my-loans', views.my_loans_view, name='my_loans'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('repay/<int:loan_id>/', views.repay_loan_view, name='repay_loan'),
    path('calculator/', views.loan_calculator_view, name='loan_calculator'),
    path('table-banking/apply/', views.apply_table_banking_view, name='apply_table_banking'),
    path('contribution/pay/', views.pay_contribution_view, name='pay_contribution'),
]