from django.shortcuts import (

    render,
    redirect,
    get_object_or_404

)

from django.contrib.auth.decorators import login_required
from django.contrib import messages

from django.db.models import Q
from decimal import Decimal, InvalidOperation

from .models import Product

from inventory.models import Inventory

from rest_framework import generics
from .serializers import ProductSerializer


def parse_decimal(value, default='0'):

    try:

        return Decimal(value or default)

    except (InvalidOperation, TypeError):

        return Decimal(default)


# =========================================
# PRODUCT LIST
# =========================================

def product_list(request):

    search = request.GET.get('search')

    products = Product.objects.all()

    # SEARCH

    if search:

        products = products.filter(

            Q(name__icontains=search)

            |

            Q(category__icontains=search)

            |

            Q(supplier__icontains=search)

        )

    # LOW STOCK

    low_stock_count = products.filter(

        quantity__lte=5,

        quantity__gt=0

    ).count()

    # OUT OF STOCK

    out_stock_count = products.filter(

        quantity=0

    ).count()

    context = {

        'products': products,

        'search': search,

        'low_stock_count': low_stock_count,

        'out_stock_count': out_stock_count,

    }

    return render(

        request,

        'product_list.html',

        context

    )


# =========================================
# ADD PRODUCT
# =========================================

@login_required(login_url='/login/')

def add_product(request):

    error = None

    if request.method == 'POST':

        name = request.POST.get('name')

        category = request.POST.get('category')

        quantity = parse_decimal(

            request.POST.get('quantity')

        )

        price = float(

            request.POST.get('price') or 0

        )

        supplier = request.POST.get('supplier')

        description = request.POST.get('description')

        # VALIDATION

        if not name:

            error = "Product name required"
            messages.error(request, error)

        elif quantity < 0:

            error = "Quantity cannot be negative"
            messages.error(request, error)

        elif price <= 0:

            error = "Price must be greater than 0"
            messages.error(request, error)

        else:

            # CREATE PRODUCT

            product = Product.objects.create(

                name=name,

                category=category,

                quantity=quantity,

                price=price,

                supplier=supplier,

                description=description

            )

            # CREATE INVENTORY

            Inventory.objects.create(

                product=product,

                stock=quantity

            )

            messages.success(request, f"{product.name} added successfully.")

            return redirect('/products/')

    return render(

        request,

        'add_product.html',

        {

            'error': error

        }

    )


# =========================================
# UPDATE PRODUCT
# =========================================

@login_required(login_url='/login/')

def update_product(request, id):

    product = get_object_or_404(

        Product,

        id=id

    )

    inventory = Inventory.objects.filter(

        product=product

    ).first()

    error = None

    if request.method == 'POST':

        name = request.POST.get('name')

        category = request.POST.get('category')

        quantity = parse_decimal(

            request.POST.get('quantity')

        )

        price = float(

            request.POST.get('price') or 0

        )

        supplier = request.POST.get('supplier')

        description = request.POST.get('description')

        # VALIDATION

        if not name:

            error = "Product name required"
            messages.error(request, error)

        elif quantity < 0:

            error = "Quantity cannot be negative"
            messages.error(request, error)

        elif price <= 0:

            error = "Price must be greater than 0"
            messages.error(request, error)

        else:

            # UPDATE PRODUCT

            product.name = name

            product.category = category

            product.quantity = quantity

            product.price = price

            product.supplier = supplier

            product.description = description

            product.save()

            # UPDATE INVENTORY

            if inventory:

                inventory.stock = quantity

                inventory.save()

            messages.success(request, f"{product.name} updated successfully.")

            return redirect('/products/')

    return render(

        request,

        'update_product.html',

        {

            'product': product,

            'error': error

        }

    )


# =========================================
# DELETE PRODUCT
# =========================================

@login_required(login_url='/login/')

def delete_product(request, id):

    product = get_object_or_404(

        Product,

        id=id

    )

    if request.method == 'POST':

        product_name = product.name

        product.delete()

        messages.success(request, f"{product_name} deleted successfully.")

        return redirect('/products/')

    return render(

        request,

        'delete_product.html',

        {

            'product': product

        }

    )


# =========================================
# PRODUCT DETAIL
# =========================================

def product_detail(request, id):

    product = get_object_or_404(

        Product,

        id=id

    )

    inventory = Inventory.objects.filter(

        product=product

    ).first()

    context = {

        'product': product,

        'inventory': inventory

    }

    return render(

        request,

        'product_detail.html',

        context

    )
# =========================================
# PRODUCT API LIST + CREATE
# =========================================

class ProductListAPI(generics.ListCreateAPIView):

    queryset = Product.objects.all()

    serializer_class = ProductSerializer


# =========================================
# PRODUCT API DETAIL
# =========================================

class ProductDetailAPI(generics.RetrieveUpdateDestroyAPIView):

    queryset = Product.objects.all()

    serializer_class = ProductSerializer
