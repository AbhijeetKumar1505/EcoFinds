from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('', views.home, name='home'),
    path('store/', views.store, name='store'),
    path('category/<slug:category_slug>/', views.store, name='products_by_category'),
    path('category/<slug:category_slug>/<slug:product_slug>/', views.product_detail, name='product_detail'),
    path('search/', views.search, name='search'),
    path('submit_review/<int:product_id>/', views.submit_review, name='submit_review'),
    path('submit_seller_review/<int:seller_id>/', views.submit_seller_review, name='submit_seller_review'),
    path('wishlist/', views.wishlist, name='wishlist'),
    path('add_to_wishlist/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('remove_from_wishlist/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('add-product/', views.add_product, name='add_product'),
    path('edit-product/<int:product_id>/', views.edit_product, name='edit_product'),
    path('save-search-query/', views.save_search_query, name='save_search_query'),
    path('add-price-alert/<int:product_id>/', views.add_price_alert, name='add_price_alert'),
    path('my-listings/', views.my_listings, name='my_listings'),
    path('cart/', views.cart, name='cart'),
    path('add_cart/<int:product_id>/', views.add_cart, name='add_cart'),
    path('remove_cart/<int:product_id>/', views.remove_cart, name='remove_cart'),
    path('remove_cart_item/<int:product_id>/', views.remove_cart_item, name='remove_cart_item'),
    path('checkout/', views.checkout, name='checkout'),
    path('profile/', views.profile, name='profile'),
    path('orders/', views.orders, name='orders'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('deactivate-product/<int:product_id>/', views.deactivate_product, name='deactivate_product'),
    path('activate-product/<int:product_id>/', views.activate_product, name='activate_product'),
    #path('orders/', views.orders, name='orders'),
]
