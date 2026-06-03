import datetime
from decimal import Decimal
from io import BytesIO

from django.http import HttpResponse
from django.shortcuts import render
from django.db.models import Sum, F
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

from sales.models import Sale
from inventory.models import Inventory
from products.models import Product


HEADER_FILL = PatternFill(
    start_color="00BFFF",
    end_color="00BFFF",
    fill_type="solid"
)

HEADER_FONT = Font(
    bold=True,
    color="FFFFFF"
)


def _format_excel_sheet(worksheet):
    for cell in worksheet[1]:
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center")

    for column_cells in worksheet.columns:
        max_length = 0
        column_letter = column_cells[0].column_letter

        for cell in column_cells:
            cell.alignment = Alignment(horizontal="center")
            cell_value = "" if cell.value is None else str(cell.value)
            max_length = max(max_length, len(cell_value))

        worksheet.column_dimensions[column_letter].width = max_length + 4


def _stock_status(inventory):
    if inventory.stock == 0:
        return "Out of Stock"

    if inventory.stock <= inventory.low_stock_threshold:
        return "Low Stock"

    return "In Stock"


def _decimal_to_float(value):
    if isinstance(value, Decimal):
        return float(value)

    return value


def reports_dashboard(request):
    return render(request, 'report_dashboard.html')


def export_inventory_report(request):
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Inventory Report"

    headers = [
        "Product Name",
        "Category",
        "Quantity",
        "Price",
        "Supplier",
        "Stock Status",
    ]
    worksheet.append(headers)

    inventories = Inventory.objects.select_related("product").order_by("product__name")

    for inventory in inventories:
        product = inventory.product
        worksheet.append([
            product.name,
            product.category,
            _decimal_to_float(inventory.stock),
            _decimal_to_float(product.price),
            product.supplier,
            _stock_status(inventory),
        ])

    _format_excel_sheet(worksheet)

    output = BytesIO()
    workbook.save(output)
    output.seek(0)

    response = HttpResponse(
        output.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="inventory_report.xlsx"'

    return response


def export_sales_report(request):
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Sales Report"

    headers = [
        "Product Name",
        "Quantity Sold",
        "Selling Price",
        "Revenue",
        "Sale Date",
    ]
    worksheet.append(headers)

    sales = Sale.objects.select_related("product").order_by("-order_date", "-id")

    for sale in sales:
        worksheet.append([
            sale.product.name,
            _decimal_to_float(sale.quantity),
            _decimal_to_float(sale.product.price),
            _decimal_to_float(sale.total_price),
            sale.order_date.strftime("%Y-%m-%d"),
        ])

    _format_excel_sheet(worksheet)

    output = BytesIO()
    workbook.save(output)
    output.seek(0)

    response = HttpResponse(
        output.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="sales_report.xlsx"'

    return response

def monthly_report(request):
    today = datetime.date.today()
    current_month = today.month
    current_year = today.year
    
    # Filter sales for current month
    sales_this_month = Sale.objects.filter(order_date__month=current_month, order_date__year=current_year)
    
    total_revenue = sales_this_month.aggregate(total=Sum('total_price'))['total'] or 0
    total_orders = sales_this_month.count()
    
    # Expenses = sum of (sale.quantity * sale.product.cost_price)
    total_expenses = sum([s.quantity * (s.product.cost_price or 0) for s in sales_this_month])
    total_profit = float(total_revenue) - float(total_expenses)
    
    # Low stock items count
    low_stock_count = Inventory.objects.filter(stock__lte=F('low_stock_threshold')).count()
    
    # Calculate weekly data
    # Split the month into 4 weeks: 1-7, 8-14, 15-21, 22-end
    weekly_data = []
    weeks = [
        ("Week 1", 1, 7),
        ("Week 2", 8, 14),
        ("Week 3", 15, 21),
        ("Week 4", 22, 31)
    ]
    
    for name, start_day, end_day in weeks:
        week_sales = sales_this_month.filter(order_date__day__gte=start_day, order_date__day__lte=end_day)
        orders = week_sales.count()
        revenue = week_sales.aggregate(total=Sum('total_price'))['total'] or 0
        expenses = sum([s.quantity * (s.product.cost_price or 0) for s in week_sales])
        profit = float(revenue) - float(expenses)
        status = "Profit" if profit >= 0 else "Loss"
        
        if orders > 0 or revenue > 0:
            weekly_data.append({
                'week': name,
                'orders': orders,
                'revenue': float(revenue),
                'expenses': float(expenses),
                'profit': float(profit),
                'status': status
            })
        
    context = {
        'total_revenue': float(total_revenue),
        'total_orders': total_orders,
        'total_profit': float(total_profit),
        'low_stock_count': low_stock_count,
        'weekly_data': weekly_data,
    }
    return render(request, 'monthly_report.html', context)

def profit_report(request):
    today = datetime.date.today()
    current_year = today.year
    current_month = today.month

    # All-time sales
    all_sales = Sale.objects.all()
    all_revenue = all_sales.aggregate(total=Sum('total_price'))['total'] or 0
    all_expenses = sum([s.quantity * (s.product.cost_price or 0) for s in all_sales])
    total_profit = float(all_revenue) - float(all_expenses)

    # Monthly profit data for the current year (months 1 to 12)
    monthly_profit_data = []
    highest_profit = 0
    lowest_profit = float('inf')
    
    # For growth comparison
    this_month_profit = 0
    
    last_month = current_month - 1 if current_month > 1 else 12
    last_month_year = current_year if current_month > 1 else current_year - 1
    
    for m in range(1, 13):
        month_sales = Sale.objects.filter(order_date__month=m, order_date__year=current_year)
        orders = month_sales.count()
        if orders > 0:
            rev = month_sales.aggregate(total=Sum('total_price'))['total'] or 0
            exp = sum([s.quantity * (s.product.cost_price or 0) for s in month_sales])
            prof = float(rev) - float(exp)
            
            month_name = datetime.date(current_year, m, 1).strftime('%B')
            monthly_profit_data.append({
                'month_name': month_name,
                'revenue': float(rev),
                'expenses': float(exp),
                'profit': float(prof),
            })
            
            if prof > highest_profit:
                highest_profit = prof
            if prof < lowest_profit:
                lowest_profit = prof
                
            if m == current_month:
                this_month_profit = prof
                
    # Get previous month's profit for growth computation
    prev_sales = Sale.objects.filter(order_date__month=last_month, order_date__year=last_month_year)
    prev_month_profit = 0
    if prev_sales.exists():
        prev_rev = prev_sales.aggregate(total=Sum('total_price'))['total'] or 0
        prev_exp = sum([s.quantity * (s.product.cost_price or 0) for s in prev_sales])
        prev_month_profit = float(prev_rev) - float(prev_exp)
        
    if lowest_profit == float('inf'):
        lowest_profit = 0
        
    if prev_month_profit > 0:
        profit_growth = int(((this_month_profit - prev_month_profit) / prev_month_profit) * 100)
    else:
        profit_growth = 100 if this_month_profit > 0 else 0
        
    context = {
        'total_profit': total_profit,
        'highest_profit': highest_profit,
        'lowest_profit': lowest_profit,
        'profit_growth': profit_growth,
        'monthly_profit_data': monthly_profit_data,
    }
    return render(request, 'profit_report.html', context)

def revenue_report(request):
    today = datetime.date.today()
    current_year = today.year
    current_month = today.month

    # All-time total revenue
    total_revenue = Sale.objects.aggregate(total=Sum('total_price'))['total'] or 0

    monthly_revenue_data = []
    highest_revenue = 0
    lowest_revenue = float('inf')
    top_month_name = "N/A"
    
    for m in range(1, 13):
        month_sales = Sale.objects.filter(order_date__month=m, order_date__year=current_year)
        orders = month_sales.count()
        rev = float(month_sales.aggregate(total=Sum('total_price'))['total'] or 0)
        
        # Growth compared to previous month
        if m == 1:
            prev_s = Sale.objects.filter(order_date__month=12, order_date__year=current_year-1)
            prev_val = float(prev_s.aggregate(total=Sum('total_price'))['total'] or 0)
        else:
            prev_s = Sale.objects.filter(order_date__month=m-1, order_date__year=current_year)
            prev_val = float(prev_s.aggregate(total=Sum('total_price'))['total'] or 0)
            
        if prev_val > 0:
            growth = int(((rev - prev_val) / prev_val) * 100)
        else:
            growth = 100 if rev > 0 else 0
            
        if rev >= 150000:
            status = "Excellent"
        elif rev >= 50000:
            status = "Moderate"
        else:
            status = "Low"
            
        if orders > 0 or rev > 0:
            month_name = datetime.date(current_year, m, 1).strftime('%B')
            monthly_revenue_data.append({
                'month_name': month_name,
                'orders': orders,
                'revenue': rev,
                'growth': growth,
                'status': status
            })
            
            if rev > highest_revenue:
                highest_revenue = rev
                top_month_name = month_name
            if rev < lowest_revenue:
                lowest_revenue = rev

    if lowest_revenue == float('inf'):
        lowest_revenue = 0
        
    top_revenue_month = f"{top_month_name} - ₹{highest_revenue}" if highest_revenue > 0 else "N/A"
    
    # Compute current month growth compared to last month
    last_month = current_month - 1 if current_month > 1 else 12
    last_month_year = current_year if current_month > 1 else current_year - 1
    
    cur_month_sales = Sale.objects.filter(order_date__month=current_month, order_date__year=current_year)
    cur_month_rev = float(cur_month_sales.aggregate(total=Sum('total_price'))['total'] or 0)
    
    last_month_sales = Sale.objects.filter(order_date__month=last_month, order_date__year=last_month_year)
    last_month_rev = float(last_month_sales.aggregate(total=Sum('total_price'))['total'] or 0)
    
    if last_month_rev > 0:
        revenue_growth = int(((cur_month_rev - last_month_rev) / last_month_rev) * 100)
    else:
        revenue_growth = 100 if cur_month_rev > 0 else 0
        
    trend_dir = "↑" if revenue_growth >= 0 else "↓"
    revenue_trend = f"{trend_dir} {abs(revenue_growth)}% Change This Month"

    context = {
        'total_revenue': float(total_revenue),
        'highest_revenue': highest_revenue,
        'lowest_revenue': lowest_revenue,
        'revenue_growth': revenue_growth,
        'top_revenue_month': top_revenue_month,
        'revenue_trend': revenue_trend,
        'monthly_revenue_data': monthly_revenue_data,
    }
    return render(request, 'revenue_report.html', context)

def stock_report(request):
    inventories = Inventory.objects.all()
    
    total_products = Product.objects.count()
    total_stock = inventories.aggregate(total=Sum('stock'))['total'] or 0
    low_stock_count = inventories.filter(stock__lte=F('low_stock_threshold'), stock__gt=0).count()
    out_of_stock_count = inventories.filter(stock=0).count()
    
    # Best stocked category
    best_cat = Product.objects.values('category').annotate(total_qty=Sum('quantity')).order_by('-total_qty').first()
    best_stocked_category = f"{best_cat['category']} - {best_cat['total_qty']} Units" if best_cat else "N/A"
    
    # Critical inventory warning
    total_critical = low_stock_count + out_of_stock_count
    critical_warning = f"{total_critical} Products Need Immediate Restocking" if total_critical > 0 else "All products are well stocked!"
    
    stock_data = []
    for inv in inventories:
        sold = Sale.objects.filter(product=inv.product).aggregate(total=Sum('quantity'))['total'] or 0
        
        if inv.stock == 0:
            status = "Out Of Stock"
        elif inv.stock <= inv.low_stock_threshold:
            status = "Low Stock"
        else:
            status = "In Stock"
            
        stock_data.append({
            'product_name': inv.product.name,
            'category': inv.product.category,
            'stock': inv.stock,
            'sold_units': sold,
            'status': status
        })
        
    context = {
        'total_products': total_products,
        'total_stock': total_stock,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'best_stocked_category': best_stocked_category,
        'critical_warning': critical_warning,
        'stock_data': stock_data,
    }
    return render(request, 'stock_report.html', context)

def yearly_report(request):
    today = datetime.date.today()
    current_year = today.year

    all_sales = Sale.objects.all()
    total_revenue = all_sales.aggregate(total=Sum('total_price'))['total'] or 0
    total_expenses = sum([s.quantity * (s.product.cost_price or 0) for s in all_sales])
    total_profit = float(total_revenue) - float(total_expenses)
    total_orders = all_sales.count()

    # Group by year
    years = Sale.objects.dates('order_date', 'year')
    yearly_data = []
    
    best_revenue = 0
    best_yr_val = current_year
    
    for dt in years:
        yr = dt.year
        yr_sales = Sale.objects.filter(order_date__year=yr)
        orders = yr_sales.count()
        rev = float(yr_sales.aggregate(total=Sum('total_price'))['total'] or 0)
        exp = sum([s.quantity * (s.product.cost_price or 0) for s in yr_sales])
        prof = float(rev) - float(exp)
        
        if prof >= 100000:
            status = "Excellent"
        elif prof >= 50000:
            status = "Average"
        else:
            status = "Low"
            
        yearly_data.append({
            'year': yr,
            'revenue': rev,
            'expenses': float(exp),
            'profit': prof,
            'orders': orders,
            'status': status
        })
        
        if rev > best_revenue:
            best_revenue = rev
            best_yr_val = yr
            
    best_year = f"{best_yr_val} - Highest Revenue Generated (₹{best_revenue})" if best_revenue > 0 else "N/A"
    
    # Dominating category
    best_cat_data = Sale.objects.values('product__category').annotate(total_qty=Sum('quantity')).order_by('-total_qty').first()
    business_observation = f"{best_cat_data['product__category']} Category Dominated Sales" if best_cat_data else "No sales recorded yet."

    # Compute inventory growth
    this_year_rev = float(Sale.objects.filter(order_date__year=current_year).aggregate(total=Sum('total_price'))['total'] or 0)
    last_year_rev = float(Sale.objects.filter(order_date__year=current_year - 1).aggregate(total=Sum('total_price'))['total'] or 0)
    
    if last_year_rev > 0:
        inventory_growth = int(((this_year_rev - last_year_rev) / last_year_rev) * 100)
    else:
        inventory_growth = 100 if this_year_rev > 0 else 0

    context = {
        'total_revenue': float(total_revenue),
        'total_profit': float(total_profit),
        'total_orders': total_orders,
        'inventory_growth': inventory_growth,
        'best_year': best_year,
        'business_observation': business_observation,
        'yearly_data': yearly_data,
    }
    return render(request, 'yearly_report.html', context)
