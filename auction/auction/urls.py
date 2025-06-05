from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('create/', views.create_product, name='create_product'),
    path('bid/<int:product_id>/', views.bid_product, name='bid_product'),
] 