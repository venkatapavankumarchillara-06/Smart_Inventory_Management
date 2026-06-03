from django.urls import path

from . import views


urlpatterns = [
    path('', views.reports_dashboard, name='reports-dashboard'),
    path('monthly/', views.monthly_report, name='monthly-report'),
    path('profit/', views.profit_report, name='profit-report'),
    path('revenue/', views.revenue_report, name='revenue-report'),
    path('stock/', views.stock_report, name='stock-report'),
    path('yearly/', views.yearly_report, name='yearly-report'),
    path(
        'export-inventory/',
        views.export_inventory_report,
        name='export-inventory-report'
    ),
    path(
        'export-sales/',
        views.export_sales_report,
        name='export-sales-report'
    ),
]
