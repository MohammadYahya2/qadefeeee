"""
Custom Admin URLs
"""
from django.urls import path
from .admin_analytics import analytics_dashboard, sales_report
from . import views

app_name = 'custom_admin'

urlpatterns = [
    path('analytics/', analytics_dashboard, name='analytics_dashboard'),
    path('sales-report/', sales_report, name='sales_report'),
    path('print-order/<uuid:order_id>/', views.admin_print_order, name='admin_print_order'),
    path('test-printer/', views.admin_test_printer, name='admin_test_printer'),
] 