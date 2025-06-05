from django.db import models
from category.models import Category
from django.urls import reverse
from accounts.models import Account
from django.db.models import Avg, Count
from django.utils import timezone
from django.utils.text import slugify
from django.contrib import admin

class Product(models.Model):
    CONDITION_CHOICES = [
        ('new', 'Like New'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('used', 'Acceptable'),
    ]

    LISTING_TYPE_CHOICES = [
        ('fixed', 'Fixed Price'),
        ('auction', 'Auction'),
    ]

    title = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    images = models.ImageField(upload_to='photos/products')
    is_available = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    created_by = models.ForeignKey(Account, on_delete=models.CASCADE)
    brand = models.CharField(max_length=100)
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES)
    listing_type = models.CharField(max_length=20, choices=LISTING_TYPE_CHOICES, default='fixed')
    location = models.CharField(max_length=200, help_text="Enter your city")
    is_featured = models.BooleanField(default=False)

    def get_url(self):
        return reverse('store:product_detail', args=[self.category.slug, self.slug])

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def averageReview(self):
        reviews = ReviewRating.objects.filter(product=self, status=True).aggregate(average=Avg('rating'))
        avg = 0
        if reviews['average'] is not None:
            avg = float(reviews['average'])
        return avg

    def countReview(self):
        reviews = ReviewRating.objects.filter(product=self, status=True).aggregate(count=Count('id'))
        count = 0
        if reviews['count'] is not None:
            count = int(reviews['count'])
        return count

    class Meta:
        ordering = ['-created_date']

class VariationManager(models.Manager):
    def colors(self):
        return super(VariationManager, self).filter(variation_category='color', is_active=True)

    def sizes(self):
        return super(VariationManager, self).filter(variation_category='size', is_active=True)

variation_category_choice = (
    ('color', 'color'),
    ('size', 'size'),
)

class Variation(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    variation_category = models.CharField(max_length=100, choices=variation_category_choice)
    variation_value     = models.CharField(max_length=100)
    is_active           = models.BooleanField(default=True)
    created_date        = models.DateTimeField(auto_now=True)

    objects = VariationManager()

    def __str__(self):
        return self.variation_value


class ReviewRating(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(Account, on_delete=models.CASCADE, default=None)
    subject = models.CharField(max_length=100, blank=True)
    review = models.TextField(max_length=500, blank=True)
    rating = models.FloatField()
    ip = models.CharField(max_length=20, blank=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.subject


class ProductGallery(models.Model):
    product = models.ForeignKey(Product, default=None, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='store/products', max_length=255)

    def __str__(self):
        return self.product.title

    class Meta:
        verbose_name = 'productgallery'
        verbose_name_plural = 'product gallery'
