from django.contrib import admin
from django.urls import path

from accounts import views
from dashboard import views as dashboard_views
from products import views as product_views
from inventory import views as inventory_views
from report import views as report_views
from sales import views as sales_views

# API IMPORTS
from products.views import ProductListAPI, ProductDetailAPI


urlpatterns = [

    # =========================================
    # ADMIN
    # =========================================

    path('admin/', admin.site.urls),

    # =========================================
    # ACCOUNTS
    # =========================================

    path('', dashboard_views.dashboard),

    path('login/', views.login_view),

    path('signup/', views.signup_view),

    path('logout/', views.logout_view),

    # =========================================
    # DASHBOARD
    # =========================================

    path('dashboard/', dashboard_views.dashboard),

    # =========================================
    # PRODUCTS
    # =========================================

    path(
        'products/',
        product_views.product_list
    ),

    path(
        'products/add/',
        product_views.add_product
    ),

    path(
        'products/update/<int:id>/',
        product_views.update_product
    ),

    path(
        'products/delete/<int:id>/',
        product_views.delete_product
    ),

    path(
        'products/details/<int:id>/',
        product_views.product_detail
    ),

    # =========================================
    # PRODUCT API
    # =========================================

    path(
        'api/products/',
        ProductListAPI.as_view(),
        name='api-products'
    ),

    path(
        'api/products/<int:pk>/',
        ProductDetailAPI.as_view(),
        name='api-product-detail'
    ),

    # =========================================
    # INVENTORY
    # =========================================

    path(
        'inventory/',
        inventory_views.inventory_list
    ),

    path(
        'inventory/update/<int:id>/',
        inventory_views.update_inventory
    ),

    path(
        'inventory/delete/<int:id>/',
        inventory_views.delete_inventory
    ),

    path(
        'inventory/low-stock/',
        inventory_views.low_stock
    ),

    path(
        'inventory/stock-history/',
        inventory_views.stock_history
    ),

    path(
        'inventory/details/<int:id>/',
        inventory_views.inventory_details
    ),

    # =========================================
    # REPORTS
    # =========================================

    path(
        'report/',
        report_views.reports_dashboard
    ),

    path(
        'report/monthly/',
        report_views.monthly_report
    ),

    path(
        'report/profit/',
        report_views.profit_report
    ),

    path(
        'report/revenue/',
        report_views.revenue_report
    ),

    path(
        'report/stock/',
        report_views.stock_report
    ),

    path(
        'report/yearly/',
        report_views.yearly_report
    ),

    path(
        'report/export-inventory/',
        report_views.export_inventory_report
    ),

    path(
        'report/export-sales/',
        report_views.export_sales_report
    ),

    # =========================================
    # SALES
    # =========================================

    path(
        'sales/',
        sales_views.sales_dashboard
    ),

    path(
        'sales/list/',
        sales_views.sales_list
    ),

    path(
        'sales/add/',
        sales_views.add_sale
    ),

    path(
        'sales/update/<int:id>/',
        sales_views.update_sale
    ),

    path(
        'sales/delete/<int:id>/',
        sales_views.delete_sale
    ),

    path(
        'sales/details/<int:id>/',
        sales_views.sale_detail
    ),

    path(
        'sales/monthly-report/',
        sales_views.monthly_sales_report
    ),

]
