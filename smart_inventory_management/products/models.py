from django.db import models


class Product(models.Model):

    name = models.CharField(max_length=200)

    category = models.CharField(max_length=100)

    price = models.DecimalField(max_digits=10, decimal_places=2)

    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    quantity = models.DecimalField(max_digits=10, decimal_places=2)

    supplier = models.CharField(max_length=200)

    description = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):

        return self.name
