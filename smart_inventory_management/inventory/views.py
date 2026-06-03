from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from django.db.models import F
from decimal import Decimal, InvalidOperation

from .models import Inventory, StockHistory

from products.models import Product


def parse_decimal(value, default='0'):

    try:

        return Decimal(value or default)

    except (InvalidOperation, TypeError):

        return Decimal(default)


# INVENTORY LIST

def inventory_list(request):

    search = request.GET.get('search')

    inventories = Inventory.objects.all()


    # SEARCH PRODUCT

    if search:

        inventories = inventories.filter(

            product__name__icontains=search

        )


    # TOTAL PRODUCTS

    total_products = inventories.count()


    # LOW STOCK COUNT

    low_stock_count = inventories.filter(

        stock__lte=F('low_stock_threshold'),

        stock__gt=0

    ).count()


    # OUT OF STOCK COUNT

    out_stock_count = inventories.filter(

        stock=0

    ).count()


    # TOTAL INVENTORY VALUE

    total_inventory_value = 0

    for inventory in inventories:

        total_inventory_value += (

            inventory.stock * inventory.product.price

        )


    context = {

        'inventories': inventories,

        'total_products': total_products,

        'low_stock_count': low_stock_count,

        'out_stock_count': out_stock_count,

        'total_inventory_value': total_inventory_value,

    }


    return render(

        request,

        'inventory_list.html',

        context

    )


# ADD INVENTORY

def add_inventory(request):

    if request.method == 'POST':

        product_name = request.POST.get('product_name')

        quantity = parse_decimal(

            request.POST.get('quantity')

        )

        price = float(

            request.POST.get('price') or 0

        )

        category = request.POST.get('category')


        # CREATE OR GET PRODUCT

        product, created = Product.objects.get_or_create(

            name=product_name,

            defaults={

                'category': category,

                'quantity': quantity,

                'price': price,

                'supplier': 'Generic Supplier',

                'description': 'Added From Inventory'

            }

        )


        # UPDATE EXISTING PRODUCT

        if not created:

            product.quantity += quantity

            product.price = price

            product.category = category

            product.save()


        # CREATE OR UPDATE INVENTORY

        inventory, inv_created = Inventory.objects.get_or_create(

            product=product,

            defaults={

                'stock': quantity

            }

        )


        if not inv_created:

            inventory.stock = product.quantity

            inventory.save()


        # STOCK STATUS

        status = get_stock_status(inventory)


        # STOCK HISTORY

        StockHistory.objects.create(

            product=product,

            action='Added' if created else 'Updated',

            quantity=quantity,

            status=status

        )

        messages.success(request, f"{product.name} stock saved successfully.")


        return redirect('/inventory/')


    return render(

        request,

        'add_inventory.html'

    )


# UPDATE INVENTORY

def update_inventory(request, id):

    inventory = get_object_or_404(

        Inventory,

        id=id

    )


    if request.method == 'POST':

        stock = parse_decimal(

            request.POST.get('stock')

        )

        low_stock_threshold = parse_decimal(

            request.POST.get(

                'low_stock_threshold'

            ),
            '5'

        )


        difference = stock - inventory.stock


        inventory.stock = stock

        inventory.low_stock_threshold = low_stock_threshold

        inventory.save()


        # UPDATE PRODUCT QUANTITY

        product = inventory.product

        product.quantity = stock

        product.save()


        # STOCK STATUS

        status = get_stock_status(inventory)


        # STOCK HISTORY

        StockHistory.objects.create(

            product=product,

            action='Updated',

            quantity=difference,

            status=status

        )

        messages.success(request, f"{product.name} inventory updated successfully.")


        return redirect('/inventory/')


    return render(

        request,

        'update_inventory.html',

        {

            'inventory': inventory

        }

    )


# DELETE INVENTORY

def delete_inventory(request, id):

    inventory = get_object_or_404(

        Inventory,

        id=id

    )


    if request.method == 'POST':

        product_name = inventory.product.name

        StockHistory.objects.create(

            product=inventory.product,

            action='Deleted',

            quantity=-inventory.stock,

            status='Out Of Stock'

        )


        # DELETE PRODUCT ALSO

        inventory.product.delete()

        messages.success(request, f"{product_name} inventory deleted successfully.")


        return redirect('/inventory/')


    return render(

        request,

        'delete_inventory.html',

        {

            'inventory': inventory

        }

    )


# INVENTORY DETAILS

def inventory_details(request, id):

    inventory = get_object_or_404(

        Inventory,

        id=id

    )


    return render(

        request,

        'inventory_details.html',

        {

            'inventory': inventory

        }

    )


# LOW STOCK PAGE

def low_stock(request):

    inventories = Inventory.objects.filter(

        stock__lte=F('low_stock_threshold'),

        stock__gt=0

    )


    return render(

        request,

        'low_stock.html',

        {

            'inventories': inventories

        }

    )


# STOCK HISTORY

def stock_history(request):

    histories = StockHistory.objects.all().order_by(

        '-timestamp'

    )


    return render(

        request,

        'stock_history.html',

        {

            'histories': histories

        }

    )


# STOCK STATUS FUNCTION

def get_stock_status(inventory):

    if inventory.stock == 0:

        return 'Out Of Stock'


    elif inventory.stock <= inventory.low_stock_threshold:

        return 'Low Stock'


    return 'In Stock'
