from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Count
from django.http import JsonResponse
from .models import Product, Category, SubCategory, Brand, Tag, ProductReview


def index(request):
    """Homepage view with featured products, new arrivals, and categories"""
    # Get featured products
    featured_products = Product.objects.filter(
        is_featured=True, 
        is_active=True,
        stock_status__in=['in_stock', 'low_stock']
    ).select_related('category', 'subcategory', 'brand').prefetch_related('images', 'tags')[:8]
    
    # Get new products (last 30 days or latest 8)
    new_products = Product.objects.filter(
        is_active=True,
        stock_status__in=['in_stock', 'low_stock']
    ).select_related('category', 'subcategory', 'brand').prefetch_related('images', 'tags').order_by('-created_at')[:8]
    
    # Get organic products
    organic_products = Product.objects.filter(
        is_organic=True,
        is_active=True,
        stock_status__in=['in_stock', 'low_stock']
    ).select_related('category', 'subcategory', 'brand').prefetch_related('images', 'tags')[:8]
    
    # Get all categories with product count
    categories = Category.objects.filter(is_active=True).annotate(
        product_count=Count('products', filter=Q(products__is_active=True))
    ).order_by('name')
    
    # Get products by category for tabs
    vegetables = Product.objects.filter(
        subcategory__name__icontains='vegetable',
        is_active=True,
        stock_status__in=['in_stock', 'low_stock']
    ).select_related('category', 'subcategory', 'brand').prefetch_related('images', 'tags')[:8]
    
    fruits = Product.objects.filter(
        subcategory__name__icontains='fruit',
        is_active=True,
        stock_status__in=['in_stock', 'low_stock']
    ).select_related('category', 'subcategory', 'brand').prefetch_related('images', 'tags')[:8]
    
    # Get top-rated products
    top_rated = Product.objects.filter(
        is_active=True,
        stock_status__in=['in_stock', 'low_stock']
    ).annotate(
        avg_rating=Avg('reviews__rating'),
        review_count=Count('reviews')
    ).filter(review_count__gte=1).order_by('-avg_rating')[:8]
    
    context = {
        'featured_products': featured_products,
        'new_products': new_products,
        'organic_products': organic_products,
        'vegetables': vegetables,
        'fruits': fruits,
        'top_rated': top_rated,
        'categories': categories,
    }
    
    return render(request, 'home.html', context)

from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q, Count
from .models import Product, Category, SubCategory, Brand, Tag
from django.db.models import Max, Min
from django.db import models

def product_list(request):
    """Product listing page with filtering and pagination matching HTML theme"""
    # Start with all active products
    products = Product.objects.filter(is_active=True).select_related(
        'category', 'subcategory', 'brand'
    ).prefetch_related('images', 'tags')
    
    # Get filter parameters
    category_slug = request.GET.get('category')
    subcategory_slug = request.GET.get('subcategory')
    brand_slug = request.GET.get('brand')
    tag_slug = request.GET.get('tag')
    search_query = request.GET.get('q')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort_by = request.GET.get('sort', 'name')
    is_organic = request.GET.get('organic')
    stock_status = request.GET.get('stock')
    
    # Check if any filters are applied
    has_filters = any([
        category_slug, subcategory_slug, brand_slug, tag_slug, 
        search_query, min_price, max_price, is_organic, stock_status
    ])
    
    # Apply filters only if they exist
    if category_slug:
        products = products.filter(category__slug=category_slug)
    
    if subcategory_slug:
        products = products.filter(subcategory__slug=subcategory_slug)
    
    if brand_slug:
        products = products.filter(brand__slug=brand_slug)
    
    if tag_slug:
        products = products.filter(tags__slug=tag_slug)
    
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(short_description__icontains=search_query) |
            Q(category__name__icontains=search_query) |
            Q(subcategory__name__icontains=search_query) |
            Q(brand__name__icontains=search_query) |
            Q(tags__name__icontains=search_query)
        ).distinct()
    
    if min_price:
        try:
            products = products.filter(price__gte=float(min_price))
        except (ValueError, TypeError):
            pass  # Ignore invalid price values
    
    if max_price:
        try:
            products = products.filter(price__lte=float(max_price))
        except (ValueError, TypeError):
            pass  # Ignore invalid price values
    
    if is_organic:
        products = products.filter(is_organic=True)
    
    if stock_status:
        products = products.filter(stock_status=stock_status)
    
    # Apply sorting
    sort_options = {
        'name': 'name',
        'name_desc': '-name',
        'price_low': 'price',
        'price_high': '-price',
        'newest': '-created_at',
        'oldest': 'created_at',
        'featured': '-is_featured',
        'rating': '-id',  # Placeholder for rating sort (implement when reviews are ready)
        'stock_high': '-stock_quantity',
        'stock_low': 'stock_quantity',
    }
    
    if sort_by in sort_options:
        products = products.order_by(sort_options[sort_by])
    else:
        # Default sorting: featured first, then newest
        products = products.order_by('-is_featured', '-created_at')
    
    # Get active categories for tabs (showing all categories, not just first 3)
    categories = Category.objects.filter(is_active=True).annotate(
        product_count=Count('products', filter=Q(products__is_active=True))
    ).filter(product_count__gt=0)  # Only show categories with products
    
    # For the tabbed view, we'll show products by category
    category_products = {}
    
    # If no filters are applied, show products grouped by category for tabs
    if not has_filters:
        # Get all products for "All Products" tab (limit to 8 for tab display)
        all_products_for_tab = Product.objects.filter(
            is_active=True
        ).select_related('category', 'subcategory', 'brand').prefetch_related('images', 'tags')
        
        # Apply default sorting for "All Products" tab
        all_products_for_tab = all_products_for_tab.order_by('-is_featured', '-created_at')[:8]
        category_products['all'] = all_products_for_tab
        
        for category in categories:
            # Get products for this category (limit to 8 for tab display)
            cat_products = Product.objects.filter(
                category=category, is_active=True
            ).select_related('category', 'subcategory', 'brand').prefetch_related('images', 'tags')
            
            # Apply default sorting for category tabs
            cat_products = cat_products.order_by('-is_featured', '-created_at')[:8]
            category_products[category.slug] = cat_products
    else:
        # If filters are applied, group filtered products by category
        # Also include "All Products" tab with filtered results
        category_products['all'] = products[:8]
        
        for category in categories:
            cat_products = products.filter(category=category)[:8]
            category_products[category.slug] = cat_products
    
    # Pagination for all products view
    paginator = Paginator(products, 12)  # 12 products per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get filter options for sidebar/filtering (only items with products)
    all_categories = Category.objects.filter(is_active=True).annotate(
        product_count=Count('products', filter=Q(products__is_active=True))
    ).filter(product_count__gt=0)
    
    subcategories = SubCategory.objects.filter(is_active=True).annotate(
        product_count=Count('products', filter=Q(products__is_active=True))
    ).filter(product_count__gt=0)
    
    brands = Brand.objects.filter(is_active=True).annotate(
        product_count=Count('products', filter=Q(products__is_active=True))
    ).filter(product_count__gt=0)
    
    tags = Tag.objects.filter(is_active=True).annotate(
        product_count=Count('products', filter=Q(products__is_active=True))
    ).filter(product_count__gt=0)
    
    # Price range for filter (get min and max from all products)
    price_range = Product.objects.filter(is_active=True).aggregate(
        min_price=models.Min('price'),
        max_price=models.Max('price')
    )
    
    context = {
        'page_obj': page_obj,
        'products': page_obj,
        'categories': categories,  # For tabs
        'all_categories': all_categories,  # For filtering sidebar
        'category_products': category_products,  # Products grouped by category for tabs (including 'all')
        'subcategories': subcategories,
        'brands': brands,
        'tags': tags,
        'current_category': category_slug,
        'current_subcategory': subcategory_slug,
        'current_brand': brand_slug,
        'current_tag': tag_slug,
        'search_query': search_query,
        'sort_by': sort_by,
        'is_organic': is_organic,
        'stock_status': stock_status,
        'min_price': min_price,
        'max_price': max_price,
        'has_filters': has_filters,  # To determine view mode in template
        'price_range': price_range,  # For price range filter
        'total_products': products.count(),  # Total count for display
        
        # Sort options for dropdown
        'sort_options': [
            ('name', 'Name A-Z'),
            ('name_desc', 'Name Z-A'),
            ('price_low', 'Price: Low to High'),
            ('price_high', 'Price: High to Low'),
            ('newest', 'Newest First'),
            ('oldest', 'Oldest First'),
            ('featured', 'Featured First'),
            ('stock_high', 'Stock: High to Low'),
            ('stock_low', 'Stock: Low to High'),
        ],
        
        # Stock status options for filter
        'stock_options': [
            ('in_stock', 'In Stock'),
            ('low_stock', 'Low Stock'),
            ('out_of_stock', 'Out of Stock'),
            ('pre_order', 'Pre-Order'),
        ],
    }
    
    return render(request, 'product_list.html', context)

from django.shortcuts import render, get_object_or_404
from django.db.models import Avg, Count, Q
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
from .models import Product, Category, ProductReview, Cart, CartItem


def product_detail(request, slug):
    """Professional product detail page similar to Jumia"""
    product = get_object_or_404(
        Product.objects.select_related('category', 'subcategory', 'brand').prefetch_related(
            'images', 'tags', 'attributes', 'reviews'
        ),
        slug=slug,
        is_active=True
    )
    
    # Get all product images
    product_images = product.images.all().order_by('sort_order', 'created_at')
    main_image = product.main_image or (product_images.first().image if product_images.exists() else None)
    
    # Get related products (same category, excluding current)
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id).select_related(
        'category', 'subcategory', 'brand'
    ).prefetch_related('images')[:8]  # Show 8 related products
    
    # Get recently viewed products (same subcategory if available)
    recently_viewed = Product.objects.filter(
        Q(subcategory=product.subcategory) | Q(category=product.category),
        is_active=True
    ).exclude(id=product.id).select_related(
        'category', 'subcategory', 'brand'
    ).prefetch_related('images')[:6]
    
    # Get product reviews with statistics
    reviews = product.reviews.filter(is_approved=True).order_by('-created_at')
    
    # Calculate rating statistics
    rating_stats = reviews.aggregate(
        avg_rating=Avg('rating'),
        total_reviews=Count('id'),
        five_star=Count('id', filter=Q(rating=5)),
        four_star=Count('id', filter=Q(rating=4)),
        three_star=Count('id', filter=Q(rating=3)),
        two_star=Count('id', filter=Q(rating=2)),
        one_star=Count('id', filter=Q(rating=1)),
    )
    
    # Format average rating
    avg_rating = rating_stats['avg_rating']
    if avg_rating:
        avg_rating = round(avg_rating, 1)
        stars_full = int(avg_rating)
        stars_half = 1 if avg_rating - stars_full >= 0.5 else 0
        stars_empty = 5 - stars_full - stars_half
    else:
        avg_rating = 0
        stars_full = stars_half = stars_empty = 0
    
    # Calculate rating percentages for progress bars
    total_reviews = rating_stats['total_reviews']
    rating_percentages = {}
    if total_reviews > 0:
        for i in range(1, 6):
            count = rating_stats[f'{"one two three four five".split()[i-1]}_star']
            rating_percentages[i] = round((count / total_reviews) * 100)
    else:
        rating_percentages = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    
    # Get product attributes grouped by type
    attributes = product.attributes.all().order_by('name')
    grouped_attributes = {}
    for attr in attributes:
        if attr.name not in grouped_attributes:
            grouped_attributes[attr.name] = []
        grouped_attributes[attr.name].append(attr.value)
    
    # Calculate savings if discount available
    savings_amount = 0
    savings_percentage = 0
    if product.discount_price and product.discount_price < product.price:
        savings_amount = product.price - product.discount_price
        savings_percentage = round((savings_amount / product.price) * 100)
    
    # Check stock status for display
    stock_status_info = {
        'in_stock': {'class': 'success', 'text': 'In Stock', 'icon': 'check-circle'},
        'low_stock': {'class': 'warning', 'text': f'Only {product.stock_quantity} left', 'icon': 'exclamation-triangle'},
        'out_of_stock': {'class': 'danger', 'text': 'Out of Stock', 'icon': 'times-circle'},
        'pre_order': {'class': 'info', 'text': 'Pre-Order Available', 'icon': 'clock'},
    }
    
    current_stock_info = stock_status_info.get(product.stock_status, stock_status_info['out_of_stock'])
    
    # Generate WhatsApp message
    whatsapp_message = f"Hello! I'm interested in this product:\n\n" \
                      f"*{product.name}*\n" \
                      f"Price: KSh {product.selling_price:,.2f}\n" \
                      f"Category: {product.category.name}\n\n" \
                      f"Please provide more details about availability and delivery."
    
    # Similar products you might like (different algorithm)
    similar_products = Product.objects.filter(
        Q(tags__in=product.tags.all()) | Q(subcategory=product.subcategory),
        is_active=True
    ).exclude(id=product.id).distinct().select_related(
        'category', 'subcategory', 'brand'
    ).prefetch_related('images')[:6]
    
    # Frequently bought together (products from same category with similar price range)
    price_range = product.selling_price * 30/100  # 30% price variance
    frequently_bought = Product.objects.filter(
        category=product.category,
        cost_price__range=(
            product.cost_price - price_range,
            product.cost_price + price_range
        ),
        is_active=True
    ).exclude(id=product.id).select_related(
        'category', 'subcategory', 'brand'
    ).prefetch_related('images')[:4]
    
    context = {
        'product': product,
        'product_images': product_images,
        'main_image': main_image,
        'related_products': related_products,
        'recently_viewed': recently_viewed,
        'similar_products': similar_products,
        'frequently_bought': frequently_bought,
        'reviews': reviews[:10],  # Show first 10 reviews
        'avg_rating': avg_rating,
        'stars_full': stars_full,
        'stars_half': stars_half,
        'stars_empty': stars_empty,
        'rating_stats': rating_stats,
        'rating_percentages': rating_percentages,
        'total_reviews': total_reviews,
        'grouped_attributes': grouped_attributes,
        'savings_amount': savings_amount,
        'savings_percentage': savings_percentage,
        'stock_info': current_stock_info,
        'whatsapp_message': whatsapp_message,
        'whatsapp_number': '254112284093',  # Your WhatsApp number
    }
    
    return render(request, 'product_detail.html', context)


def product_reviews(request, slug):
    """Load more reviews via AJAX"""
    product = get_object_or_404(Product, slug=slug, is_active=True)
    page = int(request.GET.get('page', 1))
    per_page = 5
    
    reviews = product.reviews.filter(is_approved=True).order_by('-created_at')
    start = (page - 1) * per_page
    end = start + per_page
    page_reviews = reviews[start:end]
    
    reviews_data = []
    for review in page_reviews:
        reviews_data.append({
            'customer_name': review.customer_name,
            'rating': review.rating,
            'title': review.title,
            'comment': review.comment,
            'created_at': review.created_at.strftime('%B %d, %Y')
        })
    
    return JsonResponse({
        'reviews': reviews_data,
        'has_more': end < reviews.count()
    })


def category_products(request, slug):
    """Products by category"""
    category = get_object_or_404(Category, slug=slug, is_active=True)
    
    products = Product.objects.filter(
        category=category,
        is_active=True
    ).select_related('category', 'subcategory', 'brand').prefetch_related('images', 'tags')
    
    # Apply additional filters
    subcategory_slug = request.GET.get('subcategory')
    if subcategory_slug:
        products = products.filter(subcategory__slug=subcategory_slug)
    
    # Sorting
    sort_by = request.GET.get('sort', 'name')
    sort_options = {
        'name': 'name',
        'price_low': 'price',
        'price_high': '-price',
        'newest': '-created_at',
    }
    
    if sort_by in sort_options:
        products = products.order_by(sort_options[sort_by])
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get subcategories for this category
    subcategories = category.subcategories.filter(is_active=True).annotate(
        product_count=Count('products', filter=Q(products__is_active=True))
    )
    
    context = {
        'category': category,
        'page_obj': page_obj,
        'products': page_obj,
        'subcategories': subcategories,
        'current_subcategory': subcategory_slug,
        'sort_by': sort_by,
    }
    
    return render(request, 'products/category_products.html', context)


def search_products(request):
    """Search products via AJAX"""
    query = request.GET.get('q', '')
    
    if len(query) < 2:
        return JsonResponse({'products': []})
    
    products = Product.objects.filter(
        Q(name__icontains=query) |
        Q(description__icontains=query) |
        Q(category__name__icontains=query),
        is_active=True
    ).select_related('category').prefetch_related('images')[:10]
    
    results = []
    for product in products:
        results.append({
            'id': product.id,
            'name': product.name,
            'slug': product.slug,
            'price': str(product.selling_price),
            'image': product.main_image.url if product.main_image else '',
            'category': product.category.name,
            'url': product.get_absolute_url(),
        })
    
    return JsonResponse({'products': results})


from django.shortcuts import render, get_object_or_404
from django.db.models import Avg, Count, Q
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
import json
import logging
from .models import Product, Category, ProductReview, Cart, CartItem

# Set up logging
logger = logging.getLogger(__name__)

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from .models import Cart, CartItem, Product, Customer
import logging
import urllib.parse

logger = logging.getLogger(__name__)

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.db.models import Sum, F
from .models import Cart, CartItem, Product, Customer, ProductImage
import logging
import urllib.parse

logger = logging.getLogger(__name__)

def get_cart_summary(request):
    """Get cart summary for display"""
    try:
        # Create session if doesn't exist
        if not request.session.session_key:
            request.session.create()
            logger.info(f"Created new session: {request.session.session_key}")
        
        # Try to get cart
        cart = None
        try:
            cart = Cart.objects.get(session_id=request.session.session_key)
            logger.info(f"Found cart for session: {request.session.session_key}")
        except Cart.DoesNotExist:
            logger.info(f"No cart found for session: {request.session.session_key}")
            cart = None
        
        # Initialize empty cart data
        cart_items = []
        cart_total = 0
        cart_amount = 0.0
        
        if cart and cart.items.exists():
            # Get cart items with related data
            items = cart.items.select_related('product', 'product__category', 'product__brand').prefetch_related('product__images').all()
            
            for item in items:
                try:
                    # Safely get main image
                    main_image = None
                    try:
                        main_image = item.product.images.filter(is_main=True).first()
                        if not main_image:
                            main_image = item.product.images.first()
                    except Exception as img_error:
                        logger.warning(f"Error getting image for product {item.product.id}: {str(img_error)}")
                        main_image = None
                    
                    # Build cart item data
                    cart_item_data = {
                        'id': item.id,
                        'product_id': item.product.id,
                        'product_name': item.product.name,
                        'product_slug': item.product.slug,
                        'product_image': main_image.image.url if main_image else None,
                        'unit_price': float(item.product.selling_price),
                        'quantity': item.quantity,
                        'total_price': float(item.total_price),
                        'stock_available': item.product.stock_quantity,
                        'unit': item.product.get_unit_display(),
                        'sku': item.product.sku,
                        'is_in_stock': item.product.is_in_stock,
                        'category': item.product.category.name if item.product.category else 'Unknown'
                    }
                    
                    cart_items.append(cart_item_data)
                    
                except Exception as item_error:
                    logger.error(f"Error processing cart item {item.id}: {str(item_error)}")
                    continue
            
            # Calculate totals safely
            try:
                cart_total = cart.total_items
                cart_amount = float(cart.total_amount)
            except Exception as calc_error:
                logger.error(f"Error calculating cart totals: {str(calc_error)}")
                # Fallback calculation
                cart_total = sum(item['quantity'] for item in cart_items)
                cart_amount = sum(item['total_price'] for item in cart_items)
        
        context = {
            'cart_items': cart_items,
            'cart_total': cart_total,
            'cart_amount': cart_amount,
            'cart': cart,
            'has_items': len(cart_items) > 0
        }
        
        logger.info(f"Cart summary successful: {cart_total} items, KSh {cart_amount}")
        return render(request, 'cart_summary.html', context)
        
    except Exception as e:
        logger.error(f"Critical error in get_cart_summary: {str(e)}", exc_info=True)
        messages.error(request, f'An error occurred while fetching cart: {str(e)}')
        
        # Return empty cart context
        return render(request, 'cart_summary.html', {
            'cart_items': [],
            'cart_total': 0,
            'cart_amount': 0.0,
            'cart': None,
            'has_items': False
        })


import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import logging

logger = logging.getLogger(__name__)

@require_POST
def add_to_cart(request, product_id=None):
    """Add product to cart - handles both AJAX and form submissions"""
    try:
        # Handle JSON data (AJAX request)
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            product_id = data.get('product_id') or product_id
            quantity = int(data.get('quantity', 1))
            is_ajax = True
        else:
            # Handle form data
            product_id = product_id or request.POST.get('product_id')
            quantity = int(request.POST.get('quantity', 1))
            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if not product_id:
            if is_ajax:
                return JsonResponse({'success': False, 'message': 'Product ID is required'})
            messages.error(request, 'Product ID is required')
            return redirect(request.META.get('HTTP_REFERER', '/'))
            
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        if quantity <= 0:
            if is_ajax:
                return JsonResponse({'success': False, 'message': 'Invalid quantity'})
            messages.error(request, 'Invalid quantity')
            return redirect(request.META.get('HTTP_REFERER', '/'))
            
        if quantity > product.stock_quantity:
            message = f'Only {product.stock_quantity} items available in stock'
            if is_ajax:
                return JsonResponse({'success': False, 'message': message})
            messages.error(request, message)
            return redirect(request.META.get('HTTP_REFERER', '/'))
        
        # Create session if doesn't exist
        if not request.session.session_key:
            request.session.create()
            
        # Get or create cart
        cart, created = Cart.objects.get_or_create(
            session_id=request.session.session_key
        )
        
        # Get or create cart item
        cart_item, item_created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not item_created:
            # Update quantity if item already exists
            new_quantity = cart_item.quantity + quantity
            if new_quantity > product.stock_quantity:
                message = f'Cannot add more items. Only {product.stock_quantity} available in stock'
                if is_ajax:
                    return JsonResponse({'success': False, 'message': message})
                messages.error(request, message)
                return redirect(request.META.get('HTTP_REFERER', '/'))
            cart_item.quantity = new_quantity
            cart_item.save()
            success_message = f'Updated {product.name} quantity in cart'
        else:
            success_message = f'Added {product.name} to cart'
        
        if is_ajax:
            return JsonResponse({
                'success': True, 
                'message': success_message,
                'cart_total': cart.total_items,
                'cart_amount': float(cart.total_amount)
            })
        
        messages.success(request, success_message)
        return redirect('cart_summary')
        
    except ValueError:
        message = 'Invalid quantity'
        if is_ajax:
            return JsonResponse({'success': False, 'message': message})
        messages.error(request, message)
    except Exception as e:
        logger.error(f"Error adding to cart: {str(e)}")
        message = 'An error occurred while adding item to cart'
        if is_ajax:
            return JsonResponse({'success': False, 'message': message})
        messages.error(request, message)
            
    return redirect(request.META.get('HTTP_REFERER', '/'))

def update_cart_item(request, item_id):
    """Update cart item quantity"""
    if request.method == 'POST':
        try:
            cart_item = get_object_or_404(CartItem, id=item_id, cart__session_id=request.session.session_key)
            quantity = int(request.POST.get('quantity', 1))
            
            if quantity <= 0:
                cart_item.delete()
                messages.success(request, 'Item removed from cart')
            elif quantity > cart_item.product.stock_quantity:
                messages.error(request, f'Only {cart_item.product.stock_quantity} items available in stock')
            else:
                cart_item.quantity = quantity
                cart_item.save()
                messages.success(request, 'Cart updated successfully')
                
        except ValueError:
            messages.error(request, 'Invalid quantity')
        except Exception as e:
            logger.error(f"Error updating cart: {str(e)}")
            messages.error(request, 'An error occurred while updating cart')
            
    return redirect('cart_summary')

def remove_cart_item(request, item_id):
    """Remove item from cart"""
    try:
        cart_item = get_object_or_404(CartItem, id=item_id, cart__session_id=request.session.session_key)
        product_name = cart_item.product.name
        cart_item.delete()
        messages.success(request, f'Removed {product_name} from cart')
    except Exception as e:
        logger.error(f"Error removing cart item: {str(e)}")
        messages.error(request, 'An error occurred while removing item')
        
    return redirect('cart_summary')

import urllib.parse
import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from .models import Cart, Customer, Order, OrderItem

logger = logging.getLogger(__name__)

def checkout(request):
    """Checkout page for WhatsApp order"""
    try:
        # Create session key if it doesn't exist
        if not request.session.session_key:
            request.session.create()
            
        try:
            cart = Cart.objects.get(session_id=request.session.session_key)
        except Cart.DoesNotExist:
            messages.error(request, 'Your cart is empty')
            return redirect('cart_summary')
            
        if not cart.items.exists():
            messages.error(request, 'Your cart is empty')
            return redirect('cart_summary')
            
        # Get cart items with product details
        cart_items = []
        for item in cart.items.select_related('product').all():
            # Handle missing product image
            product_image_url = None
            if item.product.main_image:
                try:
                    product_image_url = item.product.main_image.url
                except (ValueError, AttributeError):
                    product_image_url = None
            
            cart_items.append({
                'id': item.id,
                'product_id': item.product.id,
                'product_name': item.product.name,
                'product_slug': item.product.slug,
                'product_image': product_image_url,
                'unit_price': float(item.product.selling_price),
                'quantity': item.quantity,
                'total_price': float(item.total_price),
                'unit': item.product.get_unit_display(),
                'sku': item.product.sku
            })
            
        context = {
            'cart_items': cart_items,
            'cart_total': cart.total_items,
            'cart_amount': float(cart.total_amount),
            'cart': cart
        }
        
        return render(request, 'checkout.html', context)
        
    except Exception as e:
        logger.error(f"Error in checkout: {str(e)}", exc_info=True)
        messages.error(request, 'An error occurred during checkout. Please try again.')
        return redirect('product_list')


def generate_whatsapp_message(request):
    """Generate WhatsApp message for order"""
    if request.method != 'POST':
        return redirect('checkout')
    
    try:
        # Get customer info from form
        customer_name = request.POST.get('customer_name', '').strip()
        customer_phone = request.POST.get('customer_phone', '').strip()
        customer_address = request.POST.get('customer_address', '').strip()
        customer_notes = request.POST.get('customer_notes', '').strip()
        customer_email = request.POST.get('customer_email', '').strip()
        customer_type = request.POST.get('customer_type', 'individual')
        
        # Optional farm information
        farm_name = request.POST.get('farm_name', '').strip()
        farm_size = request.POST.get('farm_size', '').strip()
        farming_type = request.POST.get('farming_type', '').strip()
        contact_method = request.POST.get('contact_method', 'whatsapp')
        
        # Validate required fields
        if not all([customer_name, customer_phone, customer_address]):
            messages.error(request, 'Please fill in all required fields (Name, Phone, and Address)')
            return redirect('checkout')
        
        # Validate phone number format
        phone_cleaned = customer_phone.replace(' ', '').replace('+', '')
        if not phone_cleaned.isdigit() or len(phone_cleaned) < 10:
            messages.error(request, 'Please enter a valid phone number')
            return redirect('checkout')
        
        # Ensure session exists
        if not request.session.session_key:
            request.session.create()
            
        # Get cart
        try:
            cart = Cart.objects.get(session_id=request.session.session_key)
        except Cart.DoesNotExist:
            messages.error(request, 'Your cart is empty')
            return redirect('cart_summary')
            
        cart_items = cart.items.select_related('product').all()
        if not cart_items.exists():
            messages.error(request, 'Your cart is empty')
            return redirect('cart_summary')
        
        # Create or get customer
        customer = None
        try:
            with transaction.atomic():
                if customer_email:
                    try:
                        customer = Customer.objects.get(email=customer_email)
                        # Update customer info
                        customer.first_name = customer_name.split(' ')[0] if ' ' in customer_name else customer_name
                        customer.last_name = ' '.join(customer_name.split(' ')[1:]) if ' ' in customer_name else ''
                        customer.phone = customer_phone
                        customer.address_line1 = customer_address
                        customer.customer_type = customer_type
                        if farm_name:
                            customer.farm_name = farm_name
                        if farm_size:
                            try:
                                customer.farm_size = float(farm_size)
                            except ValueError:
                                pass
                        if farming_type:
                            customer.farming_type = farming_type
                        customer.save()
                    except Customer.DoesNotExist:
                        # Create new customer
                        name_parts = customer_name.split(' ', 1)
                        customer = Customer.objects.create(
                            first_name=name_parts[0],
                            last_name=name_parts[1] if len(name_parts) > 1 else '',
                            email=customer_email,
                            phone=customer_phone,
                            address_line1=customer_address,
                            customer_type=customer_type,
                            farm_name=farm_name if farm_name else '',
                            farm_size=float(farm_size) if farm_size else None,
                            farming_type=farming_type if farming_type else '',
                            city='', # Will be filled later
                            county='' # Will be filled later
                        )
                else:
                    # Create customer without email (for WhatsApp-only orders)
                    name_parts = customer_name.split(' ', 1)
                    customer = Customer.objects.create(
                        first_name=name_parts[0],
                        last_name=name_parts[1] if len(name_parts) > 1 else '',
                        email=f"temp_{customer_phone}@temp.com",  # Temporary email
                        phone=customer_phone,
                        address_line1=customer_address,
                        customer_type=customer_type,
                        farm_name=farm_name if farm_name else '',
                        farm_size=float(farm_size) if farm_size else None,
                        farming_type=farming_type if farming_type else '',
                        city='', # Will be filled later
                        county='' # Will be filled later
                    )
        except Exception as e:
            logger.error(f"Error creating/updating customer: {str(e)}", exc_info=True)
            messages.error(request, 'Error processing customer information')
            return redirect('checkout')
        
        # Build WhatsApp message
        message_parts = []
        message_parts.append("🌾 *NEW ORDER REQUEST* 🌾")
        message_parts.append("")
        message_parts.append("📋 *Customer Information:*")
        message_parts.append(f"👤 Name: {customer_name}")
        message_parts.append(f"📱 Phone: {customer_phone}")
        message_parts.append(f"📍 Address: {customer_address}")
        
        if customer_email:
            message_parts.append(f"📧 Email: {customer_email}")
        
        message_parts.append(f"👥 Customer Type: {dict([('individual', 'Individual Farmer'), ('cooperative', 'Farmers Cooperative'), ('business', 'Agribusiness'), ('institution', 'Institution')]).get(customer_type, customer_type)}")
        
        if farm_name:
            message_parts.append(f"🏡 Farm: {farm_name}")
        if farm_size:
            message_parts.append(f"📏 Farm Size: {farm_size} acres")
        if farming_type:
            message_parts.append(f"🌱 Farming Type: {farming_type}")
            
        message_parts.append("")
        message_parts.append("🛒 *Order Details:*")
        
        total_amount = 0
        for item in cart_items:
            try:
                product_total = float(item.quantity * item.product.selling_price)
                total_amount += product_total
                message_parts.append(f"• {item.product.name}")
                message_parts.append(f"  Quantity: {item.quantity} {item.product.get_unit_display()}")
                message_parts.append(f"  Price: KSh {float(item.product.selling_price):,.2f} each")
                message_parts.append(f"  Subtotal: KSh {product_total:,.2f}")
                message_parts.append("")
            except Exception as e:
                logger.error(f"Error processing cart item {item.id}: {str(e)}")
                continue
        
        message_parts.append(f"💰 *Total Amount: KSh {total_amount:,.2f}*")
        message_parts.append("")
        
        if customer_notes:
            message_parts.append("📝 *Special Instructions:*")
            message_parts.append(customer_notes)
            message_parts.append("")
        
        message_parts.append(f"📞 *Preferred Contact: {contact_method.title()}*")
        message_parts.append("")
        message_parts.append("⏰ *Order Time:* " + timezone.now().strftime("%d/%m/%Y %I:%M %p"))
        message_parts.append("")
        message_parts.append("Please confirm this order and let me know the delivery details. Thank you! 🙏")
        
        # Join message
        whatsapp_message = "\n".join(message_parts)
        
        try:
            # URL encode the message
            encoded_message = urllib.parse.quote(whatsapp_message)
            
            # WhatsApp business number (replace with your actual WhatsApp business number)
            whatsapp_number = getattr(settings, 'WHATSAPP_BUSINESS_NUMBER', "254112284093")
            
            # Generate WhatsApp URL
            whatsapp_url = f"https://wa.me/{whatsapp_number}?text={encoded_message}"
            
            # Save order to database (optional - for tracking)
            try:
                with transaction.atomic():
                    order = Order.objects.create(
                        customer=customer,
                        total_amount=total_amount,
                        final_amount=total_amount,
                        whatsapp_message=whatsapp_message,
                        customer_notes=customer_notes,
                        delivery_address=customer_address,
                        delivery_phone=customer_phone,
                        status='pending'
                    )
                    
                    # Create order items
                    for item in cart_items:
                        try:
                            OrderItem.objects.create(
                                order=order,
                                product=item.product,
                                quantity=item.quantity,
                                unit_price=item.product.selling_price,
                                product_name=item.product.name,
                                product_sku=item.product.sku
                            )
                        except Exception as e:
                            logger.error(f"Error creating order item: {str(e)}")
                            continue
                    
                    logger.info(f"Order {order.order_number} created successfully")
                    
            except Exception as e:
                logger.error(f"Error saving order to database: {str(e)}", exc_info=True)
                # Continue anyway - WhatsApp message can still be sent
        
        except Exception as e:
            logger.error(f"Error encoding WhatsApp message: {str(e)}", exc_info=True)
            messages.error(request, 'Error preparing WhatsApp message')
            return redirect('checkout')
        
        context = {
            'whatsapp_url': whatsapp_url,
            'whatsapp_message': whatsapp_message,
            'customer_name': customer_name,
            'customer_phone': customer_phone,
            'customer_address': customer_address,
            'customer_notes': customer_notes,
            'total_amount': total_amount,
            'cart_items': cart_items,
            'order_number': order.order_number if 'order' in locals() else 'N/A'
        }
        
        return render(request, 'whatsapp_order.html', context)
        
    except Exception as e:
        logger.error(f"Error generating WhatsApp message: {str(e)}", exc_info=True)
        messages.error(request, f'An error occurred while preparing your order: {str(e)}')
        return redirect('checkout')

def clear_cart(request):
    """Clear the cart after successful order"""
    try:
        if request.session.session_key:
            Cart.objects.filter(session_id=request.session.session_key).delete()
        messages.success(request, 'Order sent successfully! Your cart has been cleared.')
    except Exception as e:
        logger.error(f"Error clearing cart: {str(e)}")
        
    return redirect('product_list')

# Context processor to add cart data to all templates
def cart_context_processor(request):
    """Add cart information to all template contexts"""
    cart_total = 0
    cart_amount = 0.0
    
    try:
        if request.session.session_key:
            cart = Cart.objects.get(session_id=request.session.session_key)
            cart_total = cart.total_items
            cart_amount = float(cart.total_amount)
    except Cart.DoesNotExist:
        pass
    except Exception as e:
        logger.error(f"Error in cart context processor: {str(e)}")
    
    return {
        'cart_total': cart_total,
        'cart_amount': cart_amount
    }



from django.shortcuts import render, get_object_or_404
from django.db.models import Avg, Count, Q
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.exceptions import ValidationError
import json
import logging
from .models import Product, Category, ProductReview, Cart, CartItem

# Set up logging
logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def product_reviews(request, slug):
    """
    Load product reviews with pagination via AJAX
    Returns JSON response with reviews data and pagination info
    """
    try:
        # Get the product
        try:
            product = get_object_or_404(Product, slug=slug, is_active=True)
        except:
            return JsonResponse({
                'success': False,
                'message': 'Product not found'
            }, status=404)
        
        # Get pagination parameters
        page = request.GET.get('page', 1)
        per_page = int(request.GET.get('per_page', 5))  # Default 5 reviews per page
        rating_filter = request.GET.get('rating')  # Optional rating filter
        sort_by = request.GET.get('sort', '-created_at')  # Default sort by newest
        
        # Validate page number
        try:
            page = int(page)
            if page < 1:
                page = 1
        except (ValueError, TypeError):
            page = 1
        
        # Validate per_page (limit to reasonable range)
        if per_page < 1 or per_page > 50:
            per_page = 5
        
        # Build reviews queryset
        reviews_queryset = product.reviews.filter(is_approved=True)
        
        # Apply rating filter if specified
        if rating_filter:
            try:
                rating_filter = int(rating_filter)
                if 1 <= rating_filter <= 5:
                    reviews_queryset = reviews_queryset.filter(rating=rating_filter)
            except (ValueError, TypeError):
                pass  # Ignore invalid rating filter
        
        # Apply sorting
        valid_sort_options = [
            '-created_at',    # Newest first
            'created_at',     # Oldest first
            '-rating',        # Highest rating first
            'rating',         # Lowest rating first
            'customer_name'   # Alphabetical by name
        ]
        
        if sort_by in valid_sort_options:
            reviews_queryset = reviews_queryset.order_by(sort_by)
        else:
            reviews_queryset = reviews_queryset.order_by('-created_at')
        
        # Set up pagination
        paginator = Paginator(reviews_queryset, per_page)
        
        try:
            page_reviews = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page
            page_reviews = paginator.page(1)
            page = 1
        except EmptyPage:
            # If page is out of range, deliver last page
            page_reviews = paginator.page(paginator.num_pages)
            page = paginator.num_pages
        
        # Format reviews data for JSON response
        reviews_data = []
        for review in page_reviews:
            review_data = {
                'id': review.id,
                'customer_name': review.customer_name,
                'rating': review.rating,
                'title': review.title or '',
                'comment': review.comment,
                'created_at': review.created_at.strftime('%B %d, %Y'),
                'created_at_iso': review.created_at.isoformat(),
                'updated_at': review.updated_at.strftime('%B %d, %Y') if review.updated_at != review.created_at else None,
                'is_verified': hasattr(review, 'is_verified') and review.is_verified,  # If you add this field later
            }
            reviews_data.append(review_data)
        
        # Calculate pagination info
        pagination_info = {
            'current_page': page,
            'total_pages': paginator.num_pages,
            'per_page': per_page,
            'total_reviews': paginator.count,
            'has_next': page_reviews.has_next(),
            'has_previous': page_reviews.has_previous(),
            'next_page': page_reviews.next_page_number() if page_reviews.has_next() else None,
            'previous_page': page_reviews.previous_page_number() if page_reviews.has_previous() else None,
        }
        
        # Get overall rating statistics (for context)
        rating_stats = reviews_queryset.aggregate(
            avg_rating=Avg('rating'),
            total_reviews=Count('id'),
            five_star=Count('id', filter=Q(rating=5)),
            four_star=Count('id', filter=Q(rating=4)),
            three_star=Count('id', filter=Q(rating=3)),
            two_star=Count('id', filter=Q(rating=2)),
            one_star=Count('id', filter=Q(rating=1)),
        )
        
        # Format average rating
        avg_rating = rating_stats['avg_rating']
        if avg_rating:
            avg_rating = round(avg_rating, 1)
        else:
            avg_rating = 0
        
        # Log the request
        logger.info(f"Reviews loaded for product {product.slug}, page {page}, filter: {rating_filter}, sort: {sort_by}")
        
        # Return success response
        return JsonResponse({
            'success': True,
            'reviews': reviews_data,
            'pagination': pagination_info,
            'has_more': page_reviews.has_next(),  # For backward compatibility
            'rating_stats': {
                'avg_rating': avg_rating,
                'total_reviews': rating_stats['total_reviews'],
                'five_star': rating_stats['five_star'],
                'four_star': rating_stats['four_star'],
                'three_star': rating_stats['three_star'],
                'two_star': rating_stats['two_star'],
                'one_star': rating_stats['one_star'],
            },
            'filters': {
                'rating_filter': rating_filter,
                'sort_by': sort_by,
                'per_page': per_page
            }
        })
        
    except Exception as e:
        logger.error(f"Error loading reviews for product {slug}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while loading reviews'
        }, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def submit_product_review(request, slug):
    """
    Submit a new product review
    Handles both AJAX and regular form submissions
    """
    try:
        # Get the product
        try:
            product = get_object_or_404(Product, slug=slug, is_active=True)
        except:
            return JsonResponse({
                'success': False,
                'message': 'Product not found'
            }, status=404)
        
        # Parse request data (handle both JSON and form data)
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid JSON data'
                }, status=400)
        else:
            data = request.POST
        
        # Extract and validate review data
        customer_name = data.get('customer_name', '').strip()
        customer_email = data.get('customer_email', '').strip()
        customer_phone = data.get('customer_phone', '').strip()
        rating = data.get('rating')
        title = data.get('title', '').strip()
        comment = data.get('comment', '').strip()
        
        # Validation
        errors = {}
        
        if not customer_name:
            errors['customer_name'] = 'Name is required'
        elif len(customer_name) < 2:
            errors['customer_name'] = 'Name must be at least 2 characters'
        
        if customer_email and '@' not in customer_email:
            errors['customer_email'] = 'Please enter a valid email address'
        
        if not rating:
            errors['rating'] = 'Rating is required'
        else:
            try:
                rating = int(rating)
                if rating < 1 or rating > 5:
                    errors['rating'] = 'Rating must be between 1 and 5'
            except (ValueError, TypeError):
                errors['rating'] = 'Invalid rating value'
        
        if not comment:
            errors['comment'] = 'Review comment is required'
        elif len(comment) < 10:
            errors['comment'] = 'Review must be at least 10 characters long'
        elif len(comment) > 1000:
            errors['comment'] = 'Review must be less than 1000 characters'
        
        if title and len(title) > 200:
            errors['title'] = 'Title must be less than 200 characters'
        
        # Return validation errors if any
        if errors:
            return JsonResponse({
                'success': False,
                'message': 'Please correct the following errors:',
                'errors': errors
            }, status=400)
        
        # Check for duplicate reviews (same email for same product)
        if customer_email:
            existing_review = ProductReview.objects.filter(
                product=product,
                customer_email=customer_email
            ).first()
            
            if existing_review:
                return JsonResponse({
                    'success': False,
                    'message': 'You have already reviewed this product'
                }, status=400)
        
        # Create the review
        review = ProductReview.objects.create(
            product=product,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            rating=rating,
            title=title,
            comment=comment,
            is_approved=False  # Reviews need approval by default
        )
        
        # Log the submission
        logger.info(f"New review submitted for product {product.slug} by {customer_name}")
        
        # Return success response
        return JsonResponse({
            'success': True,
            'message': 'Thank you for your review! It will be published after approval.',
            'review_id': review.id,
            'data': {
                'customer_name': review.customer_name,
                'rating': review.rating,
                'title': review.title,
                'comment': review.comment,
                'created_at': review.created_at.strftime('%B %d, %Y')
            }
        })
        
    except Exception as e:
        logger.error(f"Error submitting review for product {slug}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while submitting your review'
        }, status=500)


def get_review_stats(request, slug):
    """Get detailed review statistics for a product"""
    try:
        product = get_object_or_404(Product, slug=slug, is_active=True)
        
        reviews = product.reviews.filter(is_approved=True)
        
        # Calculate detailed statistics
        stats = reviews.aggregate(
            avg_rating=Avg('rating'),
            total_reviews=Count('id'),
            five_star=Count('id', filter=Q(rating=5)),
            four_star=Count('id', filter=Q(rating=4)),
            three_star=Count('id', filter=Q(rating=3)),
            two_star=Count('id', filter=Q(rating=2)),
            one_star=Count('id', filter=Q(rating=1)),
        )
        
        # Calculate percentages
        total = stats['total_reviews']
        if total > 0:
            percentages = {
                5: round((stats['five_star'] / total) * 100, 1),
                4: round((stats['four_star'] / total) * 100, 1),
                3: round((stats['three_star'] / total) * 100, 1),
                2: round((stats['two_star'] / total) * 100, 1),
                1: round((stats['one_star'] / total) * 100, 1),
            }
        else:
            percentages = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
        
        return JsonResponse({
            'success': True,
            'stats': {
                'avg_rating': round(stats['avg_rating'], 1) if stats['avg_rating'] else 0,
                'total_reviews': total,
                'rating_counts': {
                    5: stats['five_star'],
                    4: stats['four_star'],
                    3: stats['three_star'],
                    2: stats['two_star'],
                    1: stats['one_star'],
                },
                'rating_percentages': percentages
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting review stats for {slug}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Error loading review statistics'
        }, status=500)