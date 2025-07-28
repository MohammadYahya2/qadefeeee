"""
Admin configuration for AL-QATHIFI Men's Shoe Store
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta
from .models import (
    Brand, Product, ProductImage, Customer, Order, OrderItem,
    CartItem, WheelSpin, WheelConfiguration, UserProfile, ContactMessage,
    ColorVariant, WheelAdminControl
)


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['logo_preview', 'name', 'name_en', 'name_he', 'product_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'name_en', 'name_he']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['is_active']
    
    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="60" height="60" style="border-radius: 8px; object-fit: contain;" />', obj.logo.url)
        return format_html('<div style="width: 60px; height: 60px; background: #f0f0f0; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #666; font-size: 12px;">لا توجد صورة</div>')
    logo_preview.short_description = "الشعار"
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = "عدد المنتجات"

    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('name', 'logo', 'description', 'is_active')
        }),
        ('الترجمات', {
            'fields': ('name_en', 'name_he'),
            'classes': ('collapse',)
        }),
        ('معلومات النظام', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# ColorVariant admin removed - colors can be managed directly on product pages
# @admin.register(ColorVariant)
# class ColorVariantAdmin(admin.ModelAdmin):
#     list_display = ['name', 'code', 'color_preview', 'has_thumbnail']
#     search_fields = ['name', 'code']
#     
#     def color_preview(self, obj):
#         return format_html(
#             '<div style="width: 30px; height: 30px; background-color: {}; border: 1px solid #ccc; border-radius: 4px;"></div>',
#             obj.hex_color
#         )
#     color_preview.short_description = "معاينة اللون"
#     
#     def has_thumbnail(self, obj):
#         return "✓" if obj.thumbnail else "✗"
#     has_thumbnail.short_description = "يوجد صورة مصغرة"


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 2
    fields = ['image_preview', 'image', 'color_info', 'color', 'main_photo_status', 'is_main', 'alt_text']
    readonly_fields = ['image_preview', 'color_info', 'main_photo_status']
    
    class Media:
        css = {
            'all': ('admin/css/product_image_inline.css',)
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.verbose_name = "صورة المنتج"
        self.verbose_name_plural = "صور المنتج"
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="80" height="80" style="border-radius: 8px; border: 2px solid #ddd;" />', obj.image.url)
        return format_html('<div style="width: 80px; height: 80px; background: #f0f0f0; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #666;">لا توجد صورة</div>')
    image_preview.short_description = "معاينة الصورة"
    
    def color_info(self, obj):
        from .models import Product
        if obj.color:
            color_name = dict(Product.COLORS).get(obj.color, obj.color)
            return format_html('<strong>{}</strong>', color_name)
        return "لم يتم تحديد اللون"
    color_info.short_description = "اللون"
    
    def main_photo_status(self, obj):
        if obj.is_main:
            return format_html('<span style="color: #28a745; font-weight: bold;">✓ الصورة الرئيسية</span>')
        return format_html('<span style="color: #6c757d;">صورة إضافية</span>')
    main_photo_status.short_description = "حالة الصورة"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['image_preview', 'name', 'brand', 'price', 'color', 'stock_quantity', 'views_count', 'is_featured', 'is_active']
    list_filter = ['brand', 'color', 'is_featured', 'is_active', 'created_at']
    search_fields = ['name', 'name_en', 'name_he', 'brand__name']
    readonly_fields = ['created_at', 'updated_at', 'views_count']
    list_editable = ['price', 'stock_quantity', 'is_featured', 'is_active']
    inlines = [ProductImageInline]
    
    fields = ('name', 'brand', 'description', 'price', 'sizes', 'color', 'color_hex', 'stock_quantity', 'is_featured', 'is_active', 'name_en', 'name_he')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('brand')
    
    def image_preview(self, obj):
        # Get the main product image
        main_image = obj.images.filter(is_main=True).first()
        if main_image and main_image.image:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 4px;" />', main_image.image.url)
        # If no main image, get the first available image
        first_image = obj.images.first()
        if first_image and first_image.image:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 4px;" />', first_image.image.url)
        return "لا توجد صورة"
    image_preview.short_description = "الصورة"


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'phone', 'city', 'user', 'order_count', 'created_at']
    list_filter = ['city', 'created_at']
    search_fields = ['full_name', 'phone', 'user__username']
    readonly_fields = ['created_at', 'updated_at']

    def order_count(self, obj):
        return obj.orders.count()
    order_count.short_description = "عدد الطلبات"

    fieldsets = (
        ('معلومات العميل', {
            'fields': ('user', 'session_key', 'full_name', 'phone')
        }),
        ('العنوان', {
            'fields': ('city', 'street_address')
        }),
        ('معلومات النظام', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['image_preview', 'total_price']
    fields = ['image_preview', 'product', 'size', 'quantity', 'price', 'total_price']

    def image_preview(self, obj):
        product = obj.product
        # Get the main product image
        main_image = product.images.filter(is_main=True).first()
        if main_image and main_image.image:
            return format_html('<img src="{}" width="100" height="100" style="border-radius: 4px;" />', main_image.image.url)
        # Fallback to the first image if no main image is set
        first_image = product.images.first()
        if first_image and first_image.image:
            return format_html('<img src="{}" width="100" height="100" style="border-radius: 4px;" />', first_image.image.url)
        return "لا توجد صورة"
    image_preview.short_description = "الصورة"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.verbose_name_plural = 'عناصر الطلبات'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'customer_name', 'total_amount', 'discount_amount', 'final_amount', 'payment_method', 'wheel_prizes_display', 'status', 'printed', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at', 'wheel_free_shipping', 'printed']
    search_fields = ['order_id', 'customer__full_name', 'customer__phone']
    readonly_fields = ['order_id', 'total_amount', 'final_amount', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    inlines = [OrderItemInline]
    actions = ['print_selected_orders', 'test_printer']
    
    jazzmin_section_order = ('عناصر الطلبات', 'معلومات الطلب', 'المبالغ', 'جوائز عجلة الحظ', 'ملاحظات', 'حالة الإرسال', 'تواريخ')

    fieldsets = (
        ('معلومات الطلب', {
            'fields': ('order_id', 'customer', 'payment_method', 'status')
        }),
        ('المبالغ', {
            'fields': ('total_amount', 'discount_amount', 'final_amount')
        }),
        ('جوائز عجلة الحظ', {
            'fields': ('wheel_free_shipping', 'wheel_gift_name', 'wheel_gift_description'),
            'classes': ('collapse',)
        }),
        ('ملاحظات', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('حالة الإرسال', {
            'fields': ('whatsapp_sent', 'printed'),
            'classes': ('collapse',)
        }),
        ('تواريخ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def customer_name(self, obj):
        return obj.customer.full_name
    customer_name.short_description = "اسم العميل"
    
    def wheel_prizes_display(self, obj):
        prizes = []
        if obj.discount_amount > 0:
            prizes.append(f"خصم {obj.discount_amount}₪")
        if obj.wheel_free_shipping:
            prizes.append("شحن مجاني")
        if obj.wheel_gift_name:
            prizes.append(f"هدية: {obj.wheel_gift_name}")
        return " | ".join(prizes) if prizes else "-"
    wheel_prizes_display.short_description = "جوائز العجلة"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('customer')
    
    def print_selected_orders(self, request, queryset):
        """Print selected orders"""
        from .utils import PrintService
        
        printed_count = 0
        failed_count = 0
        
        for order in queryset:
            try:
                if PrintService.print_order(order):
                    printed_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                failed_count += 1
        
        if printed_count > 0:
            self.message_user(request, f"تم طباعة {printed_count} طلب بنجاح.")
        if failed_count > 0:
            self.message_user(request, f"فشل في طباعة {failed_count} طلب.", level='ERROR')
    print_selected_orders.short_description = "طباعة الطلبات المحددة"
    
    def test_printer(self, request, queryset):
        """Test printer functionality"""
        from .utils import PrintService
        
        try:
            if PrintService.test_print():
                self.message_user(request, "✅ اختبار الطباعة نجح! الطابعة تعمل بشكل صحيح.")
            else:
                self.message_user(request, "❌ فشل اختبار الطباعة. تأكد من توصيل الطابعة.", level='ERROR')
        except Exception as e:
            self.message_user(request, f"❌ خطأ في اختبار الطباعة: {str(e)}", level='ERROR')
    test_printer.short_description = "اختبار الطابعة"


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'size', 'quantity', 'created_at']
    list_filter = ['product__brand', 'size', 'created_at']
    search_fields = ['user__username', 'product__name']
    readonly_fields = ['created_at', 'updated_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'product', 'product__brand')


@admin.register(WheelSpin)
class WheelSpinAdmin(admin.ModelAdmin):
    list_display = ['user_info', 'prize_display', 'is_used', 'spin_date', 'used_date']
    list_filter = ['prize_type', 'is_used', 'spin_date']
    search_fields = ['user__username', 'session_key', 'prize_name']
    readonly_fields = ['spin_date', 'used_date']
    date_hierarchy = 'spin_date'

    fieldsets = (
        ('معلومات المستخدم', {
            'fields': ('user', 'session_key')
        }),
        ('معلومات الجائزة', {
            'fields': ('prize_type', 'prize_name', 'discount_percentage', 'gift_description')
        }),
        ('حالة الاستخدام', {
            'fields': ('is_used', 'spin_date', 'used_date')
        }),
    )

    def user_info(self, obj):
        if obj.user:
            return obj.user.username
        return f"Guest ({obj.session_key[:10]})"
    user_info.short_description = "المستخدم"

    def prize_display(self, obj):
        return obj.get_prize_display()
    prize_display.short_description = "الجائزة"

    actions = ['mark_as_used']

    def mark_as_used(self, request, queryset):
        updated = queryset.update(is_used=True, used_date=timezone.now())
        self.message_user(request, f'{updated} جائزة تم استخدامها.')
    mark_as_used.short_description = "تحديد كمستخدم"





@admin.register(WheelConfiguration)
class WheelConfigurationAdmin(admin.ModelAdmin):
    list_display = ['name', 'prize_type', 'value', 'probability', 'color_preview', 'is_active', 'can_win']
    list_filter = ['prize_type', 'is_active', 'can_win']
    list_editable = ['value', 'probability', 'is_active', 'can_win']

    fieldsets = (
        ('معلومات الجائزة', {
            'fields': ('name', 'prize_type', 'value', 'gift_description', 'color')
        }),
        ('إعدادات الاحتمالية', {
            'fields': ('probability', 'is_active', 'can_win'),
            'description': 'فعل "يمكن الفوز بها" للتحكم في الجوائز التي يمكن للمستخدمين الحصول عليها. الجوائز غير المفعلة ستظهر على العجلة ولكن لن يتم الفوز بها.'
        }),
    )

    def color_preview(self, obj):
        return format_html(
            '<div style="width: 30px; height: 20px; background-color: {}; border: 1px solid #ccc;"></div>',
            obj.color
        )
    color_preview.short_description = "اللون"

    def get_queryset(self, request):
        return super().get_queryset(request).order_by('prize_type', '-value')

    class Media:
        js = ('admin/js/wheel_admin.js',)
        css = {
            'all': ('admin/css/wheel_admin.css',)
        }


# WheelAdminControl admin removed - using simple checkbox system only


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'city', 'preferred_language', 'newsletter_subscribed']
    list_filter = ['preferred_language', 'newsletter_subscribed', 'city']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'phone']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('معلومات المستخدم', {
            'fields': ('user', 'phone', 'preferred_language')
        }),
        ('العنوان', {
            'fields': ('city', 'street_address')
        }),
        ('التفضيلات', {
            'fields': ('newsletter_subscribed',)
        }),
        ('معلومات النظام', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'subject', 'phone', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['name', 'subject']
    readonly_fields = ['created_at']
    list_editable = ['is_read']
    date_hierarchy = 'created_at'

    actions = ['mark_as_read', 'mark_as_unread']

    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} رسالة تم تحديدها كمقروءة.')
    mark_as_read.short_description = "تحديد كمقروء"

    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} رسالة تم تحديدها كغير مقروءة.')
    mark_as_unread.short_description = "تحديد كغير مقروء"

    fieldsets = (
        ('معلومات المرسل', {
            'fields': ('name', 'phone')
        }),
        ('الرسالة', {
            'fields': ('subject', 'message', 'is_read')
        }),
        ('معلومات النظام', {
            'fields': ('created_at',)
        }),
    )


# Customize admin site
admin.site.site_header = "AL-QATHIFI - القذيفي | إدارة متجر الأحذية"
admin.site.site_title = "AL-QATHIFI Admin"
admin.site.index_title = "لوحة التحكم"

# Explicitly unregister OrderItem to ensure it doesn't appear in admin
try:
    admin.site.unregister(OrderItem)
except admin.sites.NotRegistered:
    pass

# Explicitly unregister ColorVariant to ensure it doesn't appear in admin
try:
    admin.site.unregister(ColorVariant)
except admin.sites.NotRegistered:
    pass

# Custom dashboard widgets would go here
# This could include sales statistics, recent orders, low stock alerts, etc.

# Import analytics views at the end to avoid circular imports
# We'll add custom URLs through a different approach
