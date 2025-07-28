"""
Views for AL-QATHIFI Men's Shoe Store
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg, Min, Max
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import activate, get_language
from django.utils import translation, timezone
from django.conf import settings
from django.urls import reverse
from decimal import Decimal
import json
import logging
from django.template.loader import render_to_string

from .models import (
    Brand, Product, ProductImage, Customer, Order, OrderItem, CartItem, 
    WheelSpin, WheelConfiguration, UserProfile, ContactMessage
)
from .utils import (
    TelegramService, PrintService, TranslationService, 
    CartService, WheelService, FileService
)
from .forms import CheckoutForm, ContactForm, UserRegistrationForm, CustomLoginForm

logger = logging.getLogger(__name__)


def home(request):
    """Home page view"""
    try:
        # Get featured products
        featured_products = Product.objects.filter(
            is_featured=True, 
            is_active=True,
            stock_quantity__gt=0
        ).select_related('brand')[:8]
        
        # Get popular brands
        popular_brands = Brand.objects.filter(
            is_active=True
        ).annotate(
            product_count=Count('products')
        ).filter(product_count__gt=0)[:6]
        
        # Get latest products
        latest_products = Product.objects.filter(
            is_active=True,
            stock_quantity__gt=0
        ).select_related('brand').order_by('-created_at')[:12]
        
        # Check if user can spin wheel today
        can_spin_today = WheelService.can_spin_today(request)
        
        # Show welcome popup for new visitors
        show_welcome_popup = not request.session.get('visited_before', False)
        if show_welcome_popup:
            request.session['visited_before'] = True
        
        context = {
            'featured_products': featured_products,
            'popular_brands': popular_brands,
            'latest_products': latest_products,
            'can_spin_today': can_spin_today,
            'show_welcome_popup': show_welcome_popup,
        }
        
        return render(request, 'shoes_view/home.html', context)
        
    except Exception as e:
        logger.error(f"Home view error: {str(e)}")
        messages.error(request, 'حدث خطأ في تحميل الصفحة الرئيسية')
        return render(request, 'shoes_view/home.html', {})


def products(request):
    """Products listing page with search and filters"""
    try:
        # Start with optimized base query
        products_list = Product.objects.filter(
            is_active=True
        ).select_related('brand').only(
            'id', 'name', 'name_en', 'price', 'description',
            'color', 'sizes', 'stock_quantity', 'brand__name', 'brand__id'
        )
        
        # Get selected brands from the request
        selected_brands = request.GET.getlist('brand')

        # Build filters dict to reduce repeated GET calls
        filters = {
            'search': request.GET.get('search', '').strip(),
            'brand': selected_brands, # Use the list of brands
            'color': request.GET.get('color'),
            'size': request.GET.get('size'),
            'min_price': request.GET.get('min_price'),
            'max_price': request.GET.get('max_price'),
            'sort': request.GET.get('sort', '-created_at')
        }
        
        # Apply filters
        if filters['search']:
            products_list = products_list.filter(
                Q(name__icontains=filters['search']) |
                Q(name_en__icontains=filters['search']) |
                Q(brand__name__icontains=filters['search'])
            )
        
        if filters['brand']:
            products_list = products_list.filter(brand_id__in=filters['brand'])
        
        if filters['color']:
            products_list = products_list.filter(color=filters['color'])
        
        if filters['size']:
            # SQLite-compatible size filtering
            from django.db import connection
            if 'sqlite' in connection.vendor:
                # Use icontains for SQLite compatibility
                products_list = products_list.filter(sizes__icontains=f'"{filters["size"]}"')
            else:
                products_list = products_list.filter(sizes__contains=[filters['size']])
        
        if filters['min_price']:
            try:
                products_list = products_list.filter(price__gte=Decimal(filters['min_price']))
            except (ValueError, TypeError):
                pass
                
        if filters['max_price']:
            try:
                products_list = products_list.filter(price__lte=Decimal(filters['max_price']))
            except (ValueError, TypeError):
                pass
        
        # Apply sorting
        valid_sorts = ['price', '-price', 'name', '-name', '-created_at', 'created_at']
        if filters['sort'] in valid_sorts:
            products_list = products_list.order_by(filters['sort'])
        else:
            products_list = products_list.order_by('-created_at')
        
        # Pagination with optimized count
        paginator = Paginator(products_list, 9)  # 9 products per page for better grid layout
        page_number = request.GET.get('page', 1)
        try:
            page_number = int(page_number)
        except (ValueError, TypeError):
            page_number = 1
        products = paginator.get_page(page_number)
        
        # Get filter options efficiently
        brands = Brand.objects.filter(is_active=True).only('id', 'name')
        
        # Only get price range if needed (no filters applied)
        price_range = None
        if not any([filters['brand'], filters['color'], filters['size'], filters['search']]):
            price_range = Product.objects.filter(is_active=True).aggregate(
                min_price=Min('price'),
                max_price=Max('price')
            )
        
        context = {
            'products': products,
            'brands': brands,
            'colors': Product.COLORS,
            'sizes': Product.SIZES,
            'price_range': price_range,
            'current_filters': filters,
            'total_products': paginator.count,
            'selected_brands': selected_brands, # Pass the list to the template
        }
        
        return render(request, 'shoes_view/products.html', context)
        
    except Exception as e:
        logger.error(f"Products view error: {str(e)}")
        messages.error(request, 'حدث خطأ في تحميل المنتجات')
        return render(request, 'shoes_view/products.html', {'products': [], 'brands': []})


def product_detail(request, product_id):
    """Product detail page"""
    try:
        product = get_object_or_404(
            Product.objects.select_related('brand').prefetch_related('images'),
            id=product_id,
            is_active=True
        )
        
        # Increment view count
        product.views_count += 1
        product.save(update_fields=['views_count'])
        
        # Get related products (same brand)
        related_products = Product.objects.filter(
            brand=product.brand,
            is_active=True
        ).exclude(id=product.id)[:4]
        
        # Get product images
        product_images = product.images.all().order_by('order')
        
        # Get color variants
        color_variants = Product.objects.filter(
            name=product.name,
            brand=product.brand,
            is_active=True
        ).exclude(id=product.id)
        
        context = {
            'product': product,
            'related_products': related_products,
            'product_images': product_images,
            'color_variants': color_variants,
        }
        
        return render(request, 'shoes_view/product_detail.html', context)
        
    except Exception as e:
        logger.error(f"Product detail view error: {str(e)}")
        messages.error(request, 'حدث خطأ في تحميل تفاصيل المنتج')
        return redirect('shoes_view:products')


@require_POST
def add_to_cart(request):
    """Add product to cart via AJAX"""
    try:
        product_id = request.POST.get('product_id')
        size = request.POST.get('size')
        color = request.POST.get('color')
        quantity = int(request.POST.get('quantity', 1))
        
        if not product_id or not size or not color:
            return JsonResponse({
                'success': False, 
                'message': 'معلومات المنتج غير مكتملة'
            })
        
        # Check product availability
        product = get_object_or_404(Product, id=product_id, is_active=True)
        if product.stock_quantity < quantity:
            return JsonResponse({
                'success': False,
                'message': 'الكمية المطلوبة غير متاحة'
            })
        
        # Ensure session exists for anonymous users
        if not request.user.is_authenticated and not request.session.session_key:
            request.session.create()
        
        # Add to cart
        success = CartService.add_to_cart(request, product_id, size, color, quantity)
        
        if success:
            # Force session save for anonymous users
            if not request.user.is_authenticated:
                request.session.save()
            
            # Get updated cart count and total
            cart_count = 0
            if request.user.is_authenticated:
                cart_items = CartItem.objects.filter(user=request.user)
                cart_count = sum(item.quantity for item in cart_items)
            else:
                cart = request.session.get('cart', {})
                cart_count = sum(item['quantity'] for item in cart.values())
            
            cart_total = CartService.get_cart_total(request)
            
            return JsonResponse({
                'success': True,
                'message': 'تم إضافة المنتج إلى السلة',
                'cart_count': cart_count,
                'cart_total': float(cart_total)
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'حدث خطأ في إضافة المنتج'
            })
            
    except Exception as e:
        logger.error(f"Add to cart error: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'حدث خطأ في إضافة المنتج'
        })


def cart(request):
    """Shopping cart page"""
    try:
        cart_items = []
        total_amount = 0
        
        if request.user.is_authenticated:
            # Get cart items from database
            db_cart_items = CartItem.objects.filter(
                user=request.user
            ).select_related('product', 'product__brand')
            
            for item in db_cart_items:
                cart_items.append({
                    'id': item.id,
                    'product': item.product,
                    'size': item.size,
                    'quantity': item.quantity,
                    'total_price': item.get_total_price()
                })
                total_amount += item.get_total_price()
        else:
            # Get cart items from session
            session_cart = request.session.get('cart', {})
            for cart_key, item_data in session_cart.items():
                try:
                    product = Product.objects.get(id=item_data['product_id'])
                    item_total = Decimal(item_data['price']) * item_data['quantity']
                    cart_items.append({
                        'cart_key': cart_key,
                        'product': product,
                        'size': item_data['size'],
                        'quantity': item_data['quantity'],
                        'total_price': item_total
                    })
                    total_amount += item_total
                except Product.DoesNotExist:
                    continue
        
        # Check for available wheel discount
        available_discount = WheelService.get_available_discount(request)
        discount_amount = (total_amount * available_discount / 100) if available_discount else 0
        final_amount = total_amount - discount_amount
        
        # Check for other wheel prizes
        available_free_shipping = request.session.get('wheel_free_shipping', False)
        available_gift = request.session.get('wheel_gift', {})
        
        # Get wheel prize information for display
        wheel_prizes = {
            'discount': available_discount > 0,
            'free_shipping': available_free_shipping,
            'gift': available_gift
        }
        
        # Get recent orders to show in cart
        recent_orders = []
        try:
            if request.user.is_authenticated:
                # Get recent orders for authenticated user
                orders = Order.objects.filter(
                    customer__user=request.user
                ).select_related('customer').prefetch_related(
                    'items__product', 'items__product__brand'
                ).order_by('-created_at')[:3]
            else:
                # Get recent orders for anonymous user by session
                if request.session.session_key:
                    orders = Order.objects.filter(
                        customer__session_key=request.session.session_key
                    ).select_related('customer').prefetch_related(
                        'items__product', 'items__product__brand'
                    ).order_by('-created_at')[:3]
                else:
                    orders = []
            
            recent_orders = orders
        except Exception as e:
            logger.error(f"Error getting recent orders: {str(e)}")
            recent_orders = []
        
        context = {
            'cart_items': cart_items,
            'total_amount': total_amount,
            'available_discount': available_discount,
            'discount_amount': discount_amount,
            'final_amount': final_amount,
            'wheel_prizes': wheel_prizes,
            'recent_orders': recent_orders,
        }
        
        return render(request, 'shoes_view/cart.html', context)
        
    except Exception as e:
        logger.error(f"Cart view error: {str(e)}")
        messages.error(request, 'حدث خطأ في تحميل السلة')
        return render(request, 'shoes_view/cart.html', {})


@require_POST
def remove_from_cart(request):
    """Remove item from cart"""
    try:
        cart_key = request.POST.get('cart_key')
        if not cart_key:
            return JsonResponse({'success': False, 'message': 'لم يتم تقديم معرّف المنتج'})

        if request.user.is_authenticated:
            # For authenticated users, cart_key is the CartItem ID
            CartItem.objects.filter(id=cart_key, user=request.user).delete()
        else:
            # For guest users, cart_key is the session key for the item
            cart = request.session.get('cart', {})
            if cart_key in cart:
                del cart[cart_key]
                request.session['cart'] = cart
                request.session.modified = True
        
        # Calculate new cart count
        cart_count = 0
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user)
            cart_count = sum(item.quantity for item in cart_items)
        else:
            cart = request.session.get('cart', {})
            cart_count = sum(item['quantity'] for item in cart.values())

        return JsonResponse({
            'success': True, 
            'message': 'تم حذف المنتج من السلة',
            'cart_count': cart_count
        })
        
    except Exception as e:
        logger.error(f"Remove from cart error: {str(e)}")
        return JsonResponse({'success': False, 'message': 'حدث خطأ في حذف المنتج'})


def checkout(request):
    """Checkout page"""
    try:
        # Get cart items and total
        cart_total = CartService.get_cart_total(request)
        logger.info(f"Checkout - Cart total: {cart_total}, User: {request.user.username if request.user.is_authenticated else 'Anonymous'}")
        
        if cart_total == 0:
            # Debug: Check what's in the cart
            if request.user.is_authenticated:
                cart_items_count = CartItem.objects.filter(user=request.user).count()
                logger.warning(f"Empty cart for authenticated user - DB cart items: {cart_items_count}")
            else:
                session_cart = request.session.get('cart', {})
                logger.warning(f"Empty cart for anonymous user - Session cart: {session_cart}")
                logger.warning(f"Session key: {request.session.session_key}")
            
            messages.warning(request, 'السلة فارغة')
            return redirect('shoes_view:cart')

        # Get cart items for display
        cart_items = []
        if request.user.is_authenticated:
            # Get cart items from database
            db_cart_items = CartItem.objects.filter(
                user=request.user
            ).select_related('product', 'product__brand')
            
            for item in db_cart_items:
                cart_items.append({
                    'id': item.id,
                    'product': item.product,
                    'size': item.size,
                    'quantity': item.quantity,
                    'total_price': item.get_total_price()
                })
        else:
            # Get cart items from session
            session_cart = request.session.get('cart', {})
            for cart_key, item_data in session_cart.items():
                try:
                    product = Product.objects.get(id=item_data['product_id'])
                    item_total = Decimal(item_data['price']) * item_data['quantity']
                    cart_items.append({
                        'cart_key': cart_key,
                        'product': product,
                        'size': item_data['size'],
                        'quantity': item_data['quantity'],
                        'total_price': item_total
                    })
                except Product.DoesNotExist:
                    continue
        
        # Apply wheel discount
        available_discount = WheelService.get_available_discount(request)
        discount_amount = (cart_total * available_discount / 100) if available_discount else 0
        final_amount = cart_total - discount_amount
        
        # Check for free shipping and gifts from session
        available_free_shipping = request.session.get('wheel_free_shipping', False)
        available_gift = request.session.get('wheel_gift', {})
        
        # Get wheel prize information for display
        wheel_prizes = {
            'discount': None,
            'free_shipping': None,
            'gift': None
        }
        
        if available_discount > 0:
            wheel_prizes['discount'] = {
                'type': 'discount',
                'value': available_discount,
                'description': f'خصم {available_discount}% من عجلة الحظ'
            }
        
        if available_free_shipping:
            wheel_prizes['free_shipping'] = {
                'type': 'free_shipping',
                'description': 'شحن مجاني من عجلة الحظ'
            }
        
        if available_gift:
            wheel_prizes['gift'] = {
                'type': 'gift',
                'name': available_gift.get('name', ''),
                'description': available_gift.get('description', ''),
                'display': f"هدية: {available_gift.get('name', '')}"
            }
        
        if request.method == 'POST':
            form = CheckoutForm(request.POST)
            if form.is_valid():
                try:
                    # Create or get customer
                    customer_data = {
                        'full_name': form.cleaned_data['full_name'],
                        'phone': form.cleaned_data['phone'],
                        'city': form.cleaned_data['city'],
                        'street_address': form.cleaned_data['address'],
                    }
                    
                    if request.user.is_authenticated:
                        customer, created = Customer.objects.get_or_create(
                            user=request.user,
                            defaults=customer_data
                        )
                        if not created:
                            # Update customer info
                            for field, value in customer_data.items():
                                setattr(customer, field, value)
                            customer.save()
                    else:
                        # Ensure session is created for guest users
                        if not request.session.session_key:
                            request.session.create()
                        customer_data['session_key'] = request.session.session_key
                        customer = Customer.objects.create(**customer_data)
                    
                    # Create order
                    order = Order.objects.create(
                        customer=customer,
                        payment_method=form.cleaned_data['payment_method'],
                        total_amount=cart_total,
                        discount_amount=discount_amount,
                        final_amount=final_amount,
                        wheel_free_shipping=available_free_shipping,
                        wheel_gift_name=available_gift.get('name', '') if available_gift else '',
                        wheel_gift_description=available_gift.get('description', '') if available_gift else '',
                        notes=form.cleaned_data.get('notes', '')
                    )
                    
                    # Create order items
                    if request.user.is_authenticated:
                        db_cart_items = CartItem.objects.filter(user=request.user)
                        for item in db_cart_items:
                            OrderItem.objects.create(
                                order=order,
                                product=item.product,
                                size=item.size,
                                quantity=item.quantity,
                                price=item.product.price
                            )
                        # Clear cart
                        db_cart_items.delete()
                    else:
                        session_cart = request.session.get('cart', {})
                        for item_data in session_cart.values():
                            product = Product.objects.get(id=item_data['product_id'])
                            OrderItem.objects.create(
                                order=order,
                                product=product,
                                size=item_data['size'],
                                quantity=item_data['quantity'],
                                price=product.price
                            )
                        # Clear session cart
                        request.session['cart'] = {}
                        request.session.modified = True
                    
                    # Mark wheel prizes as used
                    if available_discount > 0 or available_free_shipping or available_gift:
                        if request.user.is_authenticated:
                            # Mark all unused wheel spins as used for authenticated users
                            WheelSpin.objects.filter(
                                user=request.user, 
                                is_used=False
                            ).update(is_used=True, used_date=timezone.now())
                        else:
                            # Mark all unused wheel spins as used for session users
                            WheelSpin.objects.filter(
                                session_key=request.session.session_key, 
                                is_used=False
                            ).update(is_used=True, used_date=timezone.now())
                    
                    # Clear wheel prizes from session
                    session_keys_to_clear = [
                        'wheel_discount', 'wheel_discount_date',
                        'wheel_free_shipping', 'wheel_free_shipping_date',
                        'wheel_gift', 'wheel_gift_date'
                    ]
                    for key in session_keys_to_clear:
                        if key in request.session:
                            del request.session[key]
                    request.session.modified = True
                    
                    # Save order to file first (most important)
                    try:
                        FileService.save_order_to_file(order)
                    except Exception as e:
                        logger.error(f"File service failed for order {order.order_id}: {str(e)}")
                    
                    # Send notifications (non-blocking)
                    try:
                        TelegramService.send_order_notification(order)
                    except Exception as e:
                        logger.warning(f"Telegram notification failed for order {order.order_id}: {str(e)}")
                    
                    try:
                        PrintService.print_order(order)
                    except Exception as e:
                        logger.warning(f"Print service failed for order {order.order_id}: {str(e)}")
                    
                    # Email service removed - no longer needed
                    
                    messages.success(request, f'تم إنشاء طلبك بنجاح. رقم الطلب: {order.order_id}')
                    return redirect('shoes_view:order_confirmation', order_id=order.order_id)
                    
                except Exception as e:
                    logger.error(f"Checkout error: {str(e)}")
                    messages.error(request, 'حدث خطأ في معالجة الطلب')
        else:
            # Pre-fill form if user is authenticated
            initial_data = {}
            if request.user.is_authenticated and hasattr(request.user, 'profile'):
                profile = request.user.profile
                initial_data = {
                    'full_name': f"{request.user.first_name} {request.user.last_name}".strip(),
                    'phone': profile.phone,
                    'city': profile.city,
                    'street_address': profile.street_address,
                }
            
            form = CheckoutForm(initial=initial_data)
        
        context = {
            'form': form,
            'cart_items': cart_items,
            'cart_total': cart_total,
            'available_discount': available_discount,
            'discount_amount': discount_amount,
            'final_amount': final_amount,
            'wheel_prizes': wheel_prizes, # Pass wheel prizes to the template
        }
        
        return render(request, 'shoes_view/checkout.html', context)
        
    except Exception as e:
        logger.error(f"Checkout view error: {str(e)}")
        messages.error(request, 'حدث خطأ في صفحة الدفع')
        return redirect('shoes_view:cart')


def order_confirmation(request, order_id):
    """Order confirmation page"""
    try:
        order = get_object_or_404(Order, order_id=order_id)
        
        # Check if user has access to this order
        if request.user.is_authenticated:
            if order.customer.user != request.user:
                messages.error(request, 'لا يمكنك الوصول لهذا الطلب')
                return redirect('shoes_view:home')
        else:
            # Ensure session is created for guest users
            if not request.session.session_key:
                request.session.create()
                
            if order.customer.session_key != request.session.session_key:
                messages.error(request, 'لا يمكنك الوصول لهذا الطلب')
                return redirect('shoes_view:home')
        
        context = {
            'order': order,
        }
        
        return render(request, 'shoes_view/order_confirmation.html', context)
        
    except Exception as e:
        logger.error(f"Order confirmation error: {str(e)}")
        messages.error(request, 'حدث خطأ في تحميل تأكيد الطلب')
        return redirect('shoes_view:home')


def order_detail(request, order_id):
    """Order detail page"""
    try:
        order = get_object_or_404(Order, order_id=order_id)
        
        # Check if user has access to this order
        if request.user.is_authenticated:
            if order.customer.user != request.user:
                messages.error(request, 'لا يمكنك الوصول لهذا الطلب')
                return redirect('shoes_view:home')
        else:
            # Ensure session is created for guest users
            if not request.session.session_key:
                request.session.create()
                
            if order.customer.session_key != request.session.session_key:
                messages.error(request, 'لا يمكنك الوصول لهذا الطلب')
                return redirect('shoes_view:home')
        
        context = {
            'order': order,
        }
        
        return render(request, 'shoes_view/order_detail.html', context)
        
    except Exception as e:
        logger.error(f"Order detail error: {str(e)}")
        messages.error(request, 'حدث خطأ في تحميل تفاصيل الطلب')
        return redirect('shoes_view:home')


@require_POST
def print_order(request, order_id):
    """Print order receipt"""
    try:
        order = get_object_or_404(Order, order_id=order_id)
        
        # Check if user has access to this order (for frontend users)
        if not request.user.is_staff:  # Allow staff to print any order
            if request.user.is_authenticated:
                if order.customer.user != request.user:
                    return JsonResponse({'success': False, 'message': 'لا يمكنك الوصول لهذا الطلب'})
            else:
                # Ensure session is created for guest users
                if not request.session.session_key:
                    request.session.create()
                    
                if order.customer.session_key != request.session.session_key:
                    return JsonResponse({'success': False, 'message': 'لا يمكنك الوصول لهذا الطلب'})
        
        # Print the order
        try:
            result = PrintService.print_order(order)
            if result:
                return JsonResponse({'success': True, 'message': f'تم طباعة الطلب {order.order_id} بنجاح'})
            else:
                return JsonResponse({'success': False, 'message': 'فشل في طباعة الطلب'})
        except Exception as print_error:
            logger.error(f"Print order error: {str(print_error)}")
            return JsonResponse({'success': False, 'message': 'حدث خطأ أثناء طباعة الطلب'})
        
    except Exception as e:
        logger.error(f"Print order view error: {str(e)}")
        return JsonResponse({'success': False, 'message': 'حدث خطأ في طباعة الطلب'})


@require_POST
def admin_print_order(request, order_id):
    """Admin print order functionality"""
    from django.contrib.admin.views.decorators import staff_member_required
    
    # Check if user is staff
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'غير مسموح لك بالوصول'})
    
    try:
        order = get_object_or_404(Order, order_id=order_id)
        
        # Print the order
        try:
            result = PrintService.print_order(order)
            if result:
                # Update printed status
                order.printed = True
                order.save(update_fields=['printed'])
                
                return JsonResponse({
                    'success': True, 
                    'message': f'✅ تم طباعة الطلب {order.order_id} بنجاح'
                })
            else:
                return JsonResponse({
                    'success': False, 
                    'message': '❌ فشل في طباعة الطلب'
                })
        except Exception as print_error:
            logger.error(f"Admin print order error: {str(print_error)}")
            return JsonResponse({
                'success': False, 
                'message': f'❌ حدث خطأ أثناء طباعة الطلب: {str(print_error)}'
            })
        
    except Exception as e:
        logger.error(f"Admin print order view error: {str(e)}")
        return JsonResponse({
            'success': False, 
            'message': '❌ حدث خطأ في طباعة الطلب'
        })


@require_POST
def admin_test_printer(request):
    """Admin test printer functionality"""
    # Check if user is staff
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'غير مسموح لك بالوصول'})
    
    try:
        result = PrintService.test_print()
        if result:
            return JsonResponse({
                'success': True, 
                'message': '✅ اختبار الطباعة نجح! الطابعة تعمل بشكل صحيح'
            })
        else:
            return JsonResponse({
                'success': False, 
                'message': '❌ فشل اختبار الطباعة. تأكد من توصيل الطابعة'
            })
    except Exception as e:
        logger.error(f"Admin test printer error: {str(e)}")
        return JsonResponse({
            'success': False, 
            'message': f'❌ خطأ في اختبار الطباعة: {str(e)}'
        })


def wheel_of_fortune(request):
    """Wheel of Fortune page"""
    try:
        can_spin_today = WheelService.can_spin_today(request)
        available_discount_percentage = WheelService.get_available_discount(request)
        
        # Get available prizes from session (discount, free shipping, gift)
        available_discount = None
        available_free_shipping = False
        available_gift = None
        
        # Check for discount
        if available_discount_percentage > 0:
            # Find the wheel configuration that matches this discount
            wheel_config = WheelConfiguration.objects.filter(
                is_active=True,
                prize_type='discount',
                value=available_discount_percentage
            ).first()
            
            if wheel_config:
                available_discount = {
                    'name': wheel_config.name,
                    'prize_type': wheel_config.prize_type,
                    'value': wheel_config.value,
                    'discount_percentage': wheel_config.value,
                }
        
        # Check for free shipping
        if request.session.get('wheel_free_shipping', False):
            available_free_shipping = True
        
        # Check for gift
        wheel_gift = request.session.get('wheel_gift', {})
        if wheel_gift:
            available_gift = {
                'name': wheel_gift.get('name', ''),
                'description': wheel_gift.get('description', ''),
                'prize_type': 'gift'
            }
        
        # Get wheel configurations for display - show ALL active prizes in consistent order
        wheel_configs = WheelConfiguration.objects.filter(is_active=True).order_by('id')
        
        # Serialize wheel configs for JavaScript
        wheel_configs_json = []
        for config in wheel_configs:
            wheel_configs_json.append({
                'id': config.id,
                'name': config.name,
                'prize_type': config.prize_type,
                'value': config.value,
                'gift_description': config.gift_description,
                'probability': config.probability,
                'color': config.color,
                'is_active': config.is_active,
                'can_win': config.can_win,
                'display_text': config.get_display_text()
            })
        
        context = {
            'can_spin_today': can_spin_today,
            'available_discount': available_discount,
            'available_free_shipping': available_free_shipping,
            'available_gift': available_gift,
            'wheel_configs': wheel_configs,
            'wheel_configs_json': json.dumps(wheel_configs_json),
        }
        
        return render(request, 'shoes_view/wheel.html', context)
        
    except Exception as e:
        logger.error(f"Wheel page error: {str(e)}")
        messages.error(request, 'حدث خطأ في تحميل صفحة العجلة')
        return render(request, 'shoes_view/wheel.html', {})



@require_POST
def wheel_api_v2(request):
    """Advanced Wheel API v2 - Returns exact rotation angle"""
    try:
        import math
        import random
        
        # Check if user can spin
        if not WheelService.can_spin_today(request):
            return JsonResponse({
                'success': False,
                'message': 'لقد دورت العجلة اليوم بالفعل. جرب غداً مرة أخرى!'
            })
        
        # Get all active wheel configurations in display order
        wheel_configs = list(WheelConfiguration.objects.filter(is_active=True).order_by('id'))
        
        if not wheel_configs:
            return JsonResponse({
                'success': False,
                'message': 'لا توجد جوائز متاحة'
            })
        
        # Get winnable segments with their indices
        winnable_segments = []
        for index, config in enumerate(wheel_configs):
            if config.can_win:
                winnable_segments.append({
                    'index': index,
                    'config': config
                })
        
        if not winnable_segments:
            return JsonResponse({
                'success': False,
                'message': 'لا توجد جوائز قابلة للفوز'
            })
        
        # Select random winnable segment
        selected = random.choice(winnable_segments)
        target_index = selected['index']
        selected_config = selected['config']
        
        # Calculate wheel parameters
        total_segments = len(wheel_configs)
        segment_angle_degrees = 360 / total_segments
        segment_angle_radians = (2 * math.pi) / total_segments
        
        # Calculate exact rotation needed to put target segment center at top
        # The drawing starts from top and goes clockwise
        # Segment center is at: (index * segment_angle) + (segment_angle / 2)
        # To bring this to top (0 degrees), we need to rotate by:
        # rotation = -(segment_center_position)
        segment_center_position = (target_index * segment_angle_radians) + (segment_angle_radians / 2)
        
        # We want to bring the segment center to the top, so we rotate backwards
        target_rotation_radians = -segment_center_position
        
        # Add random full rotations for effect (8-12 full rotations)
        full_rotations = random.randint(8, 12)
        final_rotation_radians = (full_rotations * 2 * math.pi) + target_rotation_radians
        
        # Convert to degrees for debugging
        target_rotation_degrees = math.degrees(target_rotation_radians)
        final_rotation_degrees = math.degrees(final_rotation_radians)
        
        # Create wheel spin record
        if not request.user.is_authenticated and not request.session.session_key:
            request.session.create()
        
        # Create wheel spin record with appropriate fields based on prize type
        wheel_spin_data = {
            'user': request.user if request.user.is_authenticated else None,
            'session_key': request.session.session_key if not request.user.is_authenticated else None,
            'prize_type': selected_config.prize_type,
            'prize_name': selected_config.name,
            'discount_percentage': selected_config.value if selected_config.prize_type == 'discount' else 0,
        }
        
        if selected_config.prize_type == 'gift':
            wheel_spin_data['gift_description'] = selected_config.gift_description
        
        WheelSpin.objects.create(**wheel_spin_data)
        
        # Set session variables based on prize type
        if selected_config.prize_type == 'discount' and selected_config.value > 0:
            request.session['wheel_discount'] = selected_config.value
            request.session['wheel_discount_date'] = timezone.now().date().isoformat()
        elif selected_config.prize_type == 'free_shipping':
            request.session['wheel_free_shipping'] = True
            request.session['wheel_free_shipping_date'] = timezone.now().date().isoformat()
        elif selected_config.prize_type == 'gift':
            request.session['wheel_gift'] = {
                'name': selected_config.name,
                'description': selected_config.gift_description
            }
            request.session['wheel_gift_date'] = timezone.now().date().isoformat()
        
        request.session['wheel_spun_today'] = True
        request.session.modified = True
        
        # Prepare segment text using the new get_display_text method
        segment_text = selected_config.get_display_text()
        
        # Prepare success message based on prize type
        if selected_config.prize_type == 'discount':
            success_message = f'تهانينا! لقد حصلت على {selected_config.name}!'
        elif selected_config.prize_type == 'free_shipping':
            success_message = f'تهانينا! لقد حصلت على شحن مجاني!'
        elif selected_config.prize_type == 'gift':
            success_message = f'تهانينا! لقد حصلت على {selected_config.name}!'
        else:
            success_message = 'حاول مرة أخرى!'
        
        return JsonResponse({
            'success': True,
            'target_index': target_index,
            'target_rotation_radians': final_rotation_radians,
            'segment_text': segment_text,
            'prize_type': selected_config.prize_type,
            'prize_name': selected_config.name,
            'discount_percentage': selected_config.value if selected_config.prize_type == 'discount' else 0,
            'gift_description': selected_config.gift_description if selected_config.prize_type == 'gift' else '',
            'message': success_message
        })
        
    except Exception as e:
        logger.error(f"Wheel API v2 error: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'حدث خطأ في دوران العجلة'
        })


def contact(request):
    """Contact page"""
    try:
        if request.method == 'POST':
            form = ContactForm(request.POST)
            if form.is_valid():
                contact_message = form.save()
                messages.success(request, 'تم إرسال رسالتك بنجاح. سنتواصل معك قريباً.')
                return redirect('shoes_view:contact')
        else:
            form = ContactForm()
        
        context = {
            'form': form,
        }
        
        return render(request, 'shoes_view/contact.html', context)
        
    except Exception as e:
        logger.error(f"Contact view error: {str(e)}")
        messages.error(request, 'حدث خطأ في إرسال الرسالة')
        return render(request, 'shoes_view/contact.html', {'form': ContactForm()})


def brand_products(request, brand_id):
    """Products by brand"""
    try:
        brand = get_object_or_404(Brand, id=brand_id, is_active=True)
        
        products_list = Product.objects.filter(
            brand=brand,
            is_active=True
        ).order_by('-created_at')
        
        # Pagination
        paginator = Paginator(products_list, 12)
        page_number = request.GET.get('page')
        products = paginator.get_page(page_number)
        
        context = {
            'brand': brand,
            'products': products,
        }
        
        return render(request, 'shoes_view/brand_products.html', context)
        
    except Exception as e:
        logger.error(f"Brand products error: {str(e)}")
        messages.error(request, 'حدث خطأ في تحميل منتجات العلامة التجارية')
        return redirect('shoes_view:products')


def user_register(request):
    """User registration"""
    try:
        if request.user.is_authenticated:
            return redirect('shoes_view:home')
        
        if request.method == 'POST':
            form = UserRegistrationForm(request.POST)
            if form.is_valid():
                user = form.save()
                
                # Create user profile
                UserProfile.objects.create(
                    user=user,
                    phone=form.cleaned_data.get('phone', ''),
                    preferred_language=get_language()
                )
                
                # Migrate session cart to user cart
                session_cart = request.session.get('cart', {})
                for item_data in session_cart.values():
                    try:
                        product = Product.objects.get(id=item_data['product_id'])
                        CartItem.objects.create(
                            user=user,
                            product=product,
                            size=item_data['size'],
                            quantity=item_data['quantity']
                        )
                    except Product.DoesNotExist:
                        continue
                
                # Clear session cart
                request.session['cart'] = {}
                request.session.modified = True
                
                # Login user
                username = form.cleaned_data['username']
                password = form.cleaned_data['password1']
                user = authenticate(username=username, password=password)
                if user:
                    login(request, user)
                
                messages.success(request, 'تم إنشاء حسابك بنجاح!')
                return redirect('shoes_view:home')
        else:
            form = UserRegistrationForm()
        
        context = {
            'form': form,
        }
        
        return render(request, 'registration/register.html', context)
        
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        messages.error(request, 'حدث خطأ في إنشاء الحساب')
        return render(request, 'registration/register.html', {'form': UserRegistrationForm()})


def user_login(request):
    """User login with custom form"""
    try:
        if request.user.is_authenticated:
            return redirect('shoes_view:home')
        
        if request.method == 'POST':
            form = CustomLoginForm(request, data=request.POST)
            if form.is_valid():
                username = form.cleaned_data['username']
                password = form.cleaned_data['password']
                user = authenticate(username=username, password=password)
                if user:
                    login(request, user)
                    
                    # Migrate session cart to user cart
                    session_cart = request.session.get('cart', {})
                    for item_data in session_cart.values():
                        try:
                            product = Product.objects.get(id=item_data['product_id'])
                            cart_item, created = CartItem.objects.get_or_create(
                                user=user,
                                product=product,
                                size=item_data['size'],
                                defaults={'quantity': item_data['quantity']}
                            )
                            if not created:
                                cart_item.quantity += item_data['quantity']
                                cart_item.save()
                        except Product.DoesNotExist:
                            continue
                    
                    # Clear session cart
                    request.session['cart'] = {}
                    request.session.modified = True
                    
                    messages.success(request, 'تم تسجيل الدخول بنجاح!')
                    next_url = request.GET.get('next', 'shoes_view:home')
                    return redirect(next_url)
        else:
            form = CustomLoginForm()
        
        context = {
            'form': form,
        }
        
        return render(request, 'registration/login.html', context)
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        messages.error(request, 'حدث خطأ في تسجيل الدخول')
        return render(request, 'registration/login.html', {'form': CustomLoginForm()})


@login_required
def user_profile(request):
    """User profile page"""
    try:
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        # Get user orders
        if hasattr(request.user, 'customer'):
            orders = request.user.customer.orders.all().order_by('-created_at')[:10]
        else:
            orders = []
        
        context = {
            'profile': profile,
            'orders': orders,
        }
        
        return render(request, 'shoes_view/profile.html', context)
        
    except Exception as e:
        logger.error(f"Profile view error: {str(e)}")
        messages.error(request, 'حدث خطأ في تحميل الملف الشخصي')
        return render(request, 'shoes_view/profile.html', {})


def get_cart_content(request):
    """Get cart content for side cart"""
    try:
        cart = request.session.get('cart', {})
        cart_items_data = []
        total_amount = 0

        if request.user.is_authenticated:
            # Get cart items from database
            cart_items = CartItem.objects.filter(user=request.user).select_related('product', 'product__brand')
            for item in cart_items:
                cart_items_data.append({
                    'product': item.product,
                    'quantity': item.quantity,
                    'size': item.size,
                    'color': item.color,
                    'id': item.id,  # Using DB id for logged in users
                })
                total_amount += item.get_total_price()
        else:
            # Session-based cart for anonymous users
            if cart:
                product_ids = [item['product_id'] for item in cart.values()]
                products = Product.objects.filter(id__in=product_ids).select_related('brand')
                product_map = {p.id: p for p in products}

                for key, item in cart.items():
                    product = product_map.get(item.get('product_id'))
                    if product:
                        cart_items_data.append({
                            'product': product,
                            'quantity': item['quantity'],
                            'size': item['size'],
                            'color': item.get('color', ''),
                            'id': key,  # Using cart_key for session users
                        })
                        total_amount += product.price * item['quantity']

        # Get available discount
        available_discount = WheelService.get_available_discount(request)
        discount_amount = (total_amount * available_discount) / 100 if available_discount else 0
        final_amount = total_amount - discount_amount

        # Get cart count
        num_items = sum(item['quantity'] for item in cart_items_data)

        # Render cart content template
        context = {
            'cart_items': cart_items_data,
            'total_amount': total_amount,
            'available_discount': available_discount,
            'discount_amount': discount_amount,
            'final_amount': final_amount,
            'num_items': num_items,
        }

        html = render_to_string('shoes_view/includes/_side_cart.html', context, request)
        
        return JsonResponse({
            'success': True,
            'html': html,
            'cart_count': num_items,
            'cart_total': float(total_amount)
        })
        
    except Exception as e:
        logger.error(f"Side cart content view error: {str(e)}")
        return JsonResponse({
            'success': False,
            'html': '<div class="p-4 text-center text-red-500">خطأ في تحميل السلة</div>',
            'cart_count': 0,
            'cart_total': 0
        })


def set_language(request):
    """Change language"""
    try:
        language = request.POST.get('language')
        if language and language in [lang[0] for lang in settings.LANGUAGES]:
            translation.activate(language)
            request.session['django_language'] = language
            
            # Update user profile if authenticated
            if request.user.is_authenticated:
                profile, created = UserProfile.objects.get_or_create(user=request.user)
                profile.preferred_language = language
                profile.save()
        
        # Redirect to referring page or home
        next_url = request.POST.get('next', request.META.get('HTTP_REFERER', '/'))
        return redirect(next_url)
        
    except Exception as e:
        logger.error(f"Language change error: {str(e)}")
        return redirect('shoes_view:home')


@require_POST
def update_cart_quantity(request):
    """Update cart item quantity"""
    try:
        quantity = int(request.POST.get('quantity', 1))
        cart_key = request.POST.get('cart_key')
        
        if not cart_key:
            return JsonResponse({'success': False, 'message': 'لم يتم تقديم معرّف المنتج'})

        if request.user.is_authenticated:
            cart_item = get_object_or_404(CartItem, id=cart_key, user=request.user)
            
            if quantity > 0:
                # Check against stock
                if quantity > cart_item.product.stock_quantity:
                    return JsonResponse({
                        'success': False, 
                        'message': f'الكمية المتاحة هي {cart_item.product.stock_quantity} فقط'
                    })
                cart_item.quantity = quantity
                cart_item.save()
            else:
                cart_item.delete()
        else:
            cart = request.session.get('cart', {})
            
            if cart_key in cart:
                product_id = cart[cart_key]['product_id']
                product = Product.objects.get(id=product_id)

                if quantity > 0:
                    if quantity > product.stock_quantity:
                         return JsonResponse({
                            'success': False, 
                            'message': f'الكمية المتاحة هي {product.stock_quantity} فقط'
                        })
                    cart[cart_key]['quantity'] = quantity
                else:
                    del cart[cart_key]
                
                request.session['cart'] = cart
                request.session.modified = True
        
        # Calculate new cart count
        cart_count = 0
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user)
            cart_count = sum(item.quantity for item in cart_items)
        else:
            cart = request.session.get('cart', {})
            cart_count = sum(item['quantity'] for item in cart.values())
        
        return JsonResponse({
            'success': True, 
            'message': 'تم تحديث الكمية',
            'cart_count': cart_count
        })
        
    except Exception as e:
        logger.error(f"Update cart quantity error: {str(e)}")
        return JsonResponse({'success': False, 'message': 'حدث خطأ في تحديث الكمية'})


@require_POST
def cancel_order(request, order_id):
    """Cancel an order"""
    try:
        order = get_object_or_404(Order, order_id=order_id)
        
        # Check if user has access to this order
        if request.user.is_authenticated:
            if order.customer.user != request.user:
                return JsonResponse({
                    'success': False,
                    'message': 'لا يمكنك الوصول لهذا الطلب'
                })
        else:
            # Ensure session is created for guest users
            if not request.session.session_key:
                request.session.create()
            
            # Check if guest has access to this order
            if order.customer.session_key != request.session.session_key:
                return JsonResponse({
                    'success': False,
                    'message': 'لا يمكنك الوصول لهذا الطلب'
                })
        
        # Check if order can be cancelled
        if order.status not in ['pending', 'confirmed', 'processing']:
            return JsonResponse({
                'success': False,
                'message': 'لا يمكن إلغاء هذا الطلب في الوقت الحالي'
            })
        
        # Cancel the order
        order.status = 'cancelled'
        order.save()
        
        # Save cancellation to file first (most important)
        try:
            FileService.save_cancellation_to_file(order)
        except Exception as e:
            logger.error(f"Cancellation file service failed for order {order.order_id}: {str(e)}")
        
        # Send cancellation notifications (non-blocking)
        try:
                            TelegramService.send_cancellation_notification(order)
        except Exception as e:
                          logger.warning(f"Telegram cancellation notification failed for order {order.order_id}: {str(e)}")
        
        logger.info(f"Order {order.order_id} cancelled by user")
        
        return JsonResponse({
            'success': True,
            'message': 'تم إلغاء الطلب بنجاح'
        })
        
    except Exception as e:
        logger.error(f"Cancel order error: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'حدث خطأ في إلغاء الطلب'
        })


@require_POST
def reorder(request, order_id):
    """Reorder items from a previous order"""
    try:
        order = get_object_or_404(Order, order_id=order_id)
        
        # Check if user has access to this order
        if request.user.is_authenticated:
            if order.customer.user != request.user:
                return JsonResponse({
                    'success': False,
                    'message': 'لا يمكنك الوصول لهذا الطلب'
                })
        else:
            # Ensure session is created for guest users
            if not request.session.session_key:
                request.session.create()
            
            # Check if guest has access to this order
            if order.customer.session_key != request.session.session_key:
                return JsonResponse({
                    'success': False,
                    'message': 'لا يمكنك الوصول لهذا الطلب'
                })
        
        # Add all order items back to cart
        items_added = 0
        for order_item in order.items.all():
            # Check if product is still active and in stock
            if order_item.product.is_active and order_item.product.stock_quantity > 0:
                # Check if we have enough stock
                available_quantity = min(order_item.quantity, order_item.product.stock_quantity)
                
                success = CartService.add_to_cart(
                    request, 
                    order_item.product.id, 
                    order_item.size, 
                    available_quantity
                )
                
                if success:
                    items_added += 1
                    logger.info(f"Reordered item: {order_item.product.name} x{available_quantity}")
        
        if items_added > 0:
            return JsonResponse({
                'success': True,
                'message': f'تم إضافة {items_added} منتج إلى السلة بنجاح',
                'items_added': items_added
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'لا توجد منتجات متاحة للإعادة طلب'
            })
        
    except Exception as e:
        logger.error(f"Reorder error: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'حدث خطأ في إعادة الطلب'
        })


def search_suggestions(request):
    """AJAX endpoint for search suggestions"""
    try:
        query = request.GET.get('q', '').strip()
        
        if len(query) < 1:
            return JsonResponse({'suggestions': []})
        
        # Search products - faster query with only needed fields
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(name_en__icontains=query) | Q(brand__name__icontains=query),
            is_active=True
        ).select_related('brand').only(
            'id', 'name', 'name_en', 'price', 'brand__name'
        )[:10]
        
        suggestions = []
        for product in products:
            # Use the existing get_main_image method
            main_image = product.get_main_image()
            image_url = main_image.url if main_image else None
            
            suggestions.append({
                'id': product.id,
                'name': product.name,
                'brand': product.brand.name,
                'price': str(product.price),
                'image': image_url,
                'url': f'/product/{product.id}/'
            })
        
        return JsonResponse({'suggestions': suggestions})
        
    except Exception as e:
        logger.error(f"Search suggestions error: {str(e)}")
        return JsonResponse({'suggestions': []})


def cart_count_api(request):
    """API endpoint to get current cart count"""
    try:
        cart_count = 0
        
        if request.user.is_authenticated:
            # Get cart count from database
            cart_items = CartItem.objects.filter(user=request.user)
            cart_count = sum(item.quantity for item in cart_items)
            logger.debug(f"Authenticated user cart count: {cart_count}")
        else:
            # Ensure session exists for anonymous users
            if not request.session.session_key:
                request.session.create()
            
            # Get cart count from session
            cart = request.session.get('cart', {})
            cart_count = sum(item['quantity'] for item in cart.values())
            logger.debug(f"Anonymous user cart count: {cart_count}, Session key: {request.session.session_key}")
        
        return JsonResponse({'count': cart_count})
        
    except Exception as e:
        logger.error(f"Cart count API error: {str(e)}")
        return JsonResponse({'count': 0})


def robots_txt(request):
    """Robots.txt file"""
    content = """User-agent: *
Allow: /
Disallow: /admin/
Disallow: /cart/
Disallow: /checkout/

Sitemap: {}/sitemap.xml""".format(request.build_absolute_uri('/'))
    
    return HttpResponse(content, content_type='text/plain')


def user_logout(request):
    """Custom logout view that handles both GET and POST"""
    try:
        if request.method == 'POST':
            # Handle POST logout (proper way)
            logout(request)
            messages.success(request, 'تم تسجيل الخروج بنجاح')
        elif request.method == 'GET':
            # Handle GET logout (for compatibility)
            logout(request)
            messages.success(request, 'تم تسجيل الخروج بنجاح')
        
        return redirect('shoes_view:home')
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        messages.error(request, 'حدث خطأ في تسجيل الخروج')
        return redirect('shoes_view:home')