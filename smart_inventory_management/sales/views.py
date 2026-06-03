import datetime
from decimal import Decimal, InvalidOperation

from django.shortcuts import (
    render,
    redirect,
    get_object_or_404
)
from django.contrib import messages

from django.db.models import Sum

from .models import Sale

from products.models import Product

from inventory.models import (
    Inventory,
    StockHistory
)


def parse_decimal(value, default='0'):

    try:

        return Decimal(value or default)

    except (InvalidOperation, TypeError):

        return Decimal(default)


# =========================================
# SALES DASHBOARD
# =========================================

def sales_dashboard(request):

    today = datetime.date.today()

    current_month = today.month

    current_year = today.year

    total_sales_revenue = (

        Sale.objects.aggregate(
            total=Sum('total_price')
        )['total'] or 0

    )

    total_orders = Sale.objects.count()

    pending_payments = Sale.objects.filter(
        payment_status='Pending'
    ).count()

    # MONTHLY GROWTH

    this_month_sales = (

        Sale.objects.filter(
            order_date__month=current_month,
            order_date__year=current_year
        ).aggregate(
            total=Sum('total_price')
        )['total'] or 0

    )

    last_month = (
        current_month - 1
        if current_month > 1
        else 12
    )

    last_year = (
        current_year
        if current_month > 1
        else current_year - 1
    )

    last_month_sales = (

        Sale.objects.filter(
            order_date__month=last_month,
            order_date__year=last_year
        ).aggregate(
            total=Sum('total_price')
        )['total'] or 0

    )

    if last_month_sales > 0:

        monthly_growth = int(

            (
                (
                    float(this_month_sales)
                    -
                    float(last_month_sales)
                )
                /
                float(last_month_sales)
            )
            * 100

        )

    else:

        monthly_growth = (
            100 if this_month_sales > 0 else 0
        )

    context = {

        'total_sales_revenue': float(
            total_sales_revenue
        ),

        'total_orders': total_orders,

        'pending_payments': pending_payments,

        'monthly_growth': monthly_growth,

    }

    return render(
        request,
        'sales_dashboard.html',
        context
    )


# =========================================
# SALES LIST
# =========================================

def sales_list(request):

    search = request.GET.get('search')

    sales = Sale.objects.all().order_by(
        '-order_date',
        '-id'
    )

    # SEARCH

    if search:

        sales = sales.filter(

            product__name__icontains=search

        )

    return render(

        request,

        'sales_list.html',

        {

            'sales': sales,

            'search': search

        }

    )


# =========================================
# ADD SALE
# =========================================

def add_sale(request):

    products = Product.objects.all()

    error = None

    if request.method == 'POST':

        customer_name = request.POST.get(
            'customer_name'
        )

        product_id = request.POST.get(
            'product_id'
        )

        quantity = parse_decimal(
            request.POST.get('quantity')
        )

        payment_method = request.POST.get(
            'payment_method'
        )

        payment_status = request.POST.get(
            'payment_status'
        )

        order_date = request.POST.get(
            'order_date'
        )

        # VALIDATION

        if quantity <= 0:

            error = (
                "Quantity must be greater than 0"
            )
            messages.error(request, error)

        elif not product_id:

            error = (
                "Please select a product"
            )
            messages.error(request, error)

        else:

            product = get_object_or_404(
                Product,
                id=product_id
            )

            inventory = get_object_or_404(
                Inventory,
                product=product
            )

            # OUT OF STOCK

            if inventory.stock == 0:

                error = (

                    f"{product.name} is Out Of Stock"

                )
                messages.error(request, error)

            # INSUFFICIENT STOCK

            elif inventory.stock < quantity:

                error = (

                    f"Only {inventory.stock} kg "
                    f"available for {product.name}"

                )
                messages.error(request, error)

            else:

                # REDUCE STOCK

                inventory.stock -= quantity

                inventory.save()

                # SYNC PRODUCT QUANTITY

                product.quantity = inventory.stock

                product.save()

                # TOTAL PRICE

                total_price = (

                    product.price * quantity

                )

                # CREATE SALE

                Sale.objects.create(

                    customer_name=customer_name,

                    product=product,

                    quantity=quantity,

                    total_price=total_price,

                    payment_method=payment_method,

                    payment_status=payment_status,

                    order_date=order_date

                )

                # STOCK STATUS

                status = "In Stock"

                if inventory.stock == 0:

                    status = "Out Of Stock"

                elif (

                    inventory.stock
                    <=
                    inventory.low_stock_threshold

                ):

                    status = "Low Stock"

                # STOCK HISTORY

                StockHistory.objects.create(

                    product=product,

                    action="Sold",

                    quantity=-quantity,

                    status=status

                )

                messages.success(request, "Sale added successfully.")

                return redirect('/sales/list/')

    return render(

        request,

        'add_sale.html',

        {

            'products': products,

            'error': error

        }

    )


# =========================================
# UPDATE SALE
# =========================================

def update_sale(request, id):

    sale = get_object_or_404(

        Sale,

        id=id

    )

    error = None

    if request.method == 'POST':

        customer_name = request.POST.get(
            'customer_name'
        )

        quantity = parse_decimal(
            request.POST.get('quantity')
        )

        payment_method = request.POST.get(
            'payment_method'
        )

        payment_status = request.POST.get(
            'payment_status'
        )

        order_date = request.POST.get(
            'order_date'
        )

        inventory = get_object_or_404(

            Inventory,

            product=sale.product

        )

        qty_diff = quantity - sale.quantity

        # VALIDATION

        if quantity <= 0:

            error = (
                "Quantity must be greater than 0"
            )
            messages.error(request, error)

        elif qty_diff > inventory.stock:

            error = (

                f"Only {inventory.stock} extra kg "
                f"available"

            )
            messages.error(request, error)

        else:

            # UPDATE STOCK

            inventory.stock -= qty_diff

            inventory.save()

            # SYNC PRODUCT QUANTITY

            sale.product.quantity = inventory.stock

            sale.product.save()

            # UPDATE SALE

            sale.customer_name = customer_name

            sale.quantity = quantity

            sale.total_price = (

                sale.product.price * quantity

            )

            sale.payment_method = payment_method

            sale.payment_status = payment_status

            sale.order_date = order_date

            sale.save()

            # STATUS

            status = "In Stock"

            if inventory.stock == 0:

                status = "Out Of Stock"

            elif (

                inventory.stock
                <=
                inventory.low_stock_threshold

            ):

                status = "Low Stock"

            # STOCK HISTORY

            StockHistory.objects.create(

                product=sale.product,

                action="Updated Sale",

                quantity=-qty_diff,

                status=status

            )

            messages.success(request, "Sale updated successfully.")

            return redirect('/sales/list/')

    return render(

        request,

        'update_sale.html',

        {

            'sale': sale,

            'error': error

        }

    )


# =========================================
# DELETE SALE
# =========================================

def delete_sale(request, id):

    sale = get_object_or_404(

        Sale,

        id=id

    )

    if request.method == 'POST':

        inventory = get_object_or_404(

            Inventory,

            product=sale.product

        )

        # RESTORE STOCK

        inventory.stock += sale.quantity

        inventory.save()

        # SYNC PRODUCT QUANTITY

        sale.product.quantity = inventory.stock

        sale.product.save()

        # STOCK HISTORY

        StockHistory.objects.create(

            product=sale.product,

            action="Returned",

            quantity=sale.quantity,

            status="In Stock"

        )

        sale.delete()

        messages.success(request, "Sale deleted and stock restored.")

        return redirect('/sales/list/')

    return render(

        request,

        'delete_sale.html',

        {

            'sale': sale

        }

    )


# =========================================
# SALE DETAIL
# =========================================

def sale_detail(request, id):

    sale = get_object_or_404(

        Sale,

        id=id

    )

    return render(

        request,

        'sale_detail.html',

        {

            'sale': sale

        }

    )


# =========================================
# MONTHLY SALES REPORT
# =========================================

def monthly_sales_report(request):

    total_sales_revenue = (

        Sale.objects.aggregate(
            total=Sum('total_price')
        )['total'] or 0

    )

    total_orders = Sale.objects.count()

    # BEST SELLING PRODUCT

    best_product_data = (

        Sale.objects.values(
            'product__name'
        ).annotate(
            total_qty=Sum('quantity')
        ).order_by(
            '-total_qty'
        ).first()

    )

    best_selling_product = (

        best_product_data['product__name']
        if best_product_data
        else "None"

    )

    context = {

        'total_sales_revenue': float(
            total_sales_revenue
        ),

        'total_orders': total_orders,

        'best_selling_product': best_selling_product,

    }

    return render(

        request,

        'monthlyreport_sales.html',

        context

    )
