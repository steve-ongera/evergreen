from django.db.models import Count
from .models import Category, Cart, CartItem
from django.db.models import Max, Min
from django.db import models

def categories(request):
    """
    Context processor to make categories available across all templates
    """
    categories = Category.objects.filter(is_active=True).annotate(
        product_count=Count('products', filter=models.Q(products__is_active=True))
    ).order_by('name')
    
    return {
        'global_categories': categories,
    }


def cart_context(request):
    """
    Context processor to make cart information available across all templates
    """
    cart_items_count = 0
    cart_total = 0
    
    # For authenticated users, try to get cart by customer
    if request.user.is_authenticated:
        try:
            customer = request.user.customer
            cart = Cart.objects.filter(customer=customer).first()
        except:
            cart = None
    else:
        # For anonymous users, use session
        session_id = request.session.session_key
        if not session_id:
            request.session.create()
            session_id = request.session.session_key
        
        cart = Cart.objects.filter(session_id=session_id).first()
    
    if cart:
        cart_items_count = cart.total_items
        cart_total = cart.total_amount
    
    return {
        'cart_items_count': cart_items_count,
        'cart_total': cart_total,
    }