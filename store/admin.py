from django.contrib import admin
from .models import Product, Variation, ReviewRating, ProductGallery, Category
import admin_thumbnails

@admin_thumbnails.thumbnail('image')
class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1

class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'stock', 'category', 'brand', 'condition', 'is_available', 'created_date')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ProductGalleryInline]
    list_editable = ('is_available',)
    list_filter = ('category', 'brand', 'condition', 'is_available')
    search_fields = ('title', 'description', 'brand')
    list_per_page = 20

class VariationAdmin(admin.ModelAdmin):
    list_display = ('product', 'variation_category', 'variation_value', 'is_active')
    list_editable = ('is_active',)
    list_filter = ('product', 'variation_category', 'variation_value')

admin.site.register(Product, ProductAdmin)
admin.site.register(Variation, VariationAdmin)
admin.site.register(ReviewRating)
admin.site.register(ProductGallery)
#admin.site.register(Category)
