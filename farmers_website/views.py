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


def product_list(request):
    """Product listing page with filtering and pagination"""
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
    
    # Apply filters
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
            Q(subcategory__name__icontains=search_query)
        )
    
    if min_price:
        products = products.filter(price__gte=min_price)
    
    if max_price:
        products = products.filter(price__lte=max_price)
    
    if is_organic:
        products = products.filter(is_organic=True)
    
    if stock_status:
        products = products.filter(stock_status=stock_status)
    
    # Apply sorting
    sort_options = {
        'name': 'name',
        'price_low': 'price',
        'price_high': '-price',
        'newest': '-created_at',
        'featured': '-is_featured',
        'rating': '-reviews__rating',
    }
    
    if sort_by in sort_options:
        products = products.order_by(sort_options[sort_by])
    
    # Pagination
    paginator = Paginator(products, 12)  # 12 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options for sidebar
    categories = Category.objects.filter(is_active=True).annotate(
        product_count=Count('products', filter=Q(products__is_active=True))
    )
    
    subcategories = SubCategory.objects.filter(is_active=True).annotate(
        product_count=Count('products', filter=Q(products__is_active=True))
    )
    
    brands = Brand.objects.filter(is_active=True).annotate(
        product_count=Count('products', filter=Q(products__is_active=True))
    )
    
    tags = Tag.objects.filter(is_active=True).annotate(
        product_count=Count('products', filter=Q(products__is_active=True))
    )
    
    context = {
        'page_obj': page_obj,
        'products': page_obj,
        'categories': categories,
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
    }
    
    return render(request, 'product_list.html', context)


def product_detail(request, slug):
    """Product detail page"""
    product = get_object_or_404(
        Product.objects.select_related('category', 'subcategory', 'brand').prefetch_related(
            'images', 'tags', 'attributes', 'reviews'
        ),
        slug=slug,
        is_active=True
    )
    
    # Get related products
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id).select_related(
        'category', 'subcategory', 'brand'
    ).prefetch_related('images')[:4]
    
    # Get product reviews
    reviews = product.reviews.filter(is_approved=True).order_by('-created_at')
    
    # Calculate average rating
    avg_rating = reviews.aggregate(avg=Avg('rating'))['avg']
    if avg_rating:
        avg_rating = round(avg_rating, 1)
    
    # Rating distribution
    rating_distribution = {}
    for i in range(1, 6):
        rating_distribution[i] = reviews.filter(rating=i).count()
    
    context = {
        'product': product,
        'related_products': related_products,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'rating_distribution': rating_distribution,
        'total_reviews': reviews.count(),
    }
    
    return render(request, 'products/product_detail.html', context)


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