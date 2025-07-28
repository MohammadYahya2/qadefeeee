"""
Context processors for the shoes_view app.
Provides global context data to all templates.
"""

from django.conf import settings
from .models import CartItem


def cart_context(request):
    """
    Add cart information to the context for all templates.
    """
    cart_count = 0
    cart_total = 0
    
    try:
        if hasattr(request, 'user') and request.user.is_authenticated:
            # For authenticated users with database cart
            cart_items = CartItem.objects.filter(user=request.user)
            cart_count = sum(item.quantity for item in cart_items)
            cart_total = sum(item.get_total_price() for item in cart_items)
        else:
            # For session-based cart (guest users)
            if hasattr(request, 'session') and request.session.get('cart'):
                cart = request.session['cart']
                cart_count = sum(item['quantity'] for item in cart.values())
                cart_total = sum(float(item['price']) * item['quantity'] for item in cart.values())
    except Exception as e:
        # Log error but don't break the page
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Cart context processor error: {str(e)}")
        cart_count = 0
        cart_total = 0
    
    # Get current language for RTL/LTR direction
    current_language = getattr(request, 'LANGUAGE_CODE', settings.LANGUAGE_CODE)
    is_rtl = current_language in ['ar', 'he']
    
    return {
        'cart_count': cart_count,
        'cart_total': cart_total,
        'currency_symbol': getattr(settings, 'CURRENCY_SYMBOL', '$'),
        'is_rtl': is_rtl,
        'current_language': current_language,
        'available_languages': settings.LANGUAGES,
        'site_name': 'AL-QATHIFI - القذيفي',
        'whatsapp_number': getattr(settings, 'WHATSAPP_ADMIN_NUMBER', ''),
    } 