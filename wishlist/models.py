from django.db import models
from django.conf import settings
from store.models import Product, Category
from django.core.validators import MinValueValidator

class WishlistItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_checked = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('user', 'product')
        verbose_name = 'Wishlist Item'
        verbose_name_plural = 'Wishlist Items'

    def __str__(self):
        return f"{self.user.username}'s wishlist - {self.product.product_name if self.product else 'Search Query'}"

class SearchQuery(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    query = models.CharField(max_length=255)
    min_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    max_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_checked = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    notification_frequency = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
        ],
        default='daily'
    )

    class Meta:
        verbose_name = 'Search Query'
        verbose_name_plural = 'Search Queries'
        unique_together = ('user', 'query', 'min_price', 'max_price', 'category')

    def __str__(self):
        return f"{self.user.username}'s search - {self.query}"

class PriceAlert(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    target_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True)
    last_checked = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    notification_frequency = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
        ],
        default='daily'
    )

    class Meta:
        verbose_name = 'Price Alert'
        verbose_name_plural = 'Price Alerts'
        unique_together = ('user', 'product', 'target_price')

    def __str__(self):
        return f"{self.user.username}'s alert for {self.product.product_name} at ₹{self.target_price}"

    def check_price(self):
        """Check if current price is below target price"""
        return self.product.price <= self.target_price 