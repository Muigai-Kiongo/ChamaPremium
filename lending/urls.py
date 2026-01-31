from django.urls import path
from . import views

app_name = 'lending'

urlpatterns = [
    path('', views.check_eligibility_view, name='check_eligibility'),
    path('apply/', views.apply_loan_view, name='apply_loan'),
    path('repay/<int:loan_id>/', views.repay_loan_view, name='repay_loan'),
    path('calculator/', views.loan_calculator_view, name='loan_calculator'),
    path('table-banking/apply/', views.apply_table_banking_view, name='apply_table_banking'),
    path('contribution/pay/', views.pay_contribution_view, name='pay_contribution'),
]