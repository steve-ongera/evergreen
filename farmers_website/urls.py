from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('category/<slug:slug>/', views.category_products, name='category_products'),
    path('search/', views.search_products, name='search_products'),
    
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/', views.remove_cart_item, name='remove_from_cart'),
    path('cart/summary/', views.get_cart_summary, name='cart_summary'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    path('checkout/', views.checkout , name='checkout'),

    # Product reviews AJAX endpoints
    path('products/<slug:slug>/reviews/', views.product_reviews, name='product_reviews'),
    path('products/<slug:slug>/reviews/submit/', views.submit_product_review, name='submit_product_review'),
    path('products/<slug:slug>/reviews/stats/', views.get_review_stats, name='review_stats'),
]
