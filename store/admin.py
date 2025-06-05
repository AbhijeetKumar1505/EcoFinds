from django.contrib import admin
from .models import Product, ProductGallery, ReviewRating, Variation
from category.models import Category
import admin_thumbnails

@admin_thumbnails.thumbnail('image')
class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'brand', 'category', 'price', 'stock', 'condition', 'is_available', 'created_date')
    list_filter = ('category', 'brand', 'condition', 'is_available', 'created_date')
    list_editable = ('is_available', 'price', 'stock')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ProductGalleryInline]
    search_fields = ('title', 'brand', 'description')
    list_per_page = 20

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('category_name', 'slug')
    prepopulated_fields = {'slug': ('category_name',)}

@admin.register(ReviewRating)
class ReviewRatingAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('product__title', 'user__email', 'review')

admin.site.register(Variation)
