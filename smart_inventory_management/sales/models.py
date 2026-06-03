from django.db import models

from products.models import Product


class Sale(models.Model):

    customer_name = models.CharField(max_length=200)

    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    quantity = models.DecimalField(max_digits=10, decimal_places=2)

    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    payment_method = models.CharField(max_length=100)

    payment_status = models.CharField(max_length=100)

    order_date = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):

        return self.customer_name
