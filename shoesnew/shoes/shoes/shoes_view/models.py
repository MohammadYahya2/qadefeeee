"""
Models for AL-QATHIFI Men's Shoe Store
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.urls import reverse
import uuid


class Brand(models.Model):
    """Brand model for shoe brands like Adidas, Nike, etc."""
    name = models.CharField(max_length=100, unique=True, verbose_name="اسم العلامة التجارية")
    name_en = models.CharField(max_length=100, blank=True, verbose_name="Brand Name (English)")
    name_he = models.CharField(max_length=100, blank=True, verbose_name="Brand Name (Hebrew)")
    logo = models.ImageField(upload_to='brands/', blank=True, null=True, verbose_name="شعار العلامة التجارية")
    description = models.TextField(blank=True, verbose_name="وصف العلامة التجارية")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "علامة تجارية"
        verbose_name_plural = "العلامات التجارية"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shoes_view:brand_products', kwargs={'brand_id': self.pk})


class ColorVariant(models.Model):
    """Model for product color variants with separate images"""
    name = models.CharField(max_length=50, verbose_name="اسم اللون")
    code = models.CharField(max_length=20, unique=True, verbose_name="كود اللون")
    hex_color = models.CharField(max_length=7, default='#000000', verbose_name="كود اللون الهكس")
    thumbnail = models.ImageField(upload_to='colors/', blank=True, null=True, verbose_name="صورة مصغرة للون")
    
    class Meta:
        verbose_name = "متغير اللون"
        verbose_name_plural = "متغيرات الألوان"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Product(models.Model):
    """Product model for shoes"""
    SIZES = [
        ('38', '38'),
        ('39', '39'),
        ('40', '40'),
        ('41', '41'),
        ('42', '42'),
        ('43', '43'),
        ('44', '44'),
        ('45', '45'),
        ('46', '46'),
        ('47', '47'),
    ]

    COLORS = [
        ('black', 'أسود'),
        ('white', 'أبيض'),
        ('brown', 'بني'),
        ('blue', 'أزرق'),
        ('red', 'أحمر'),
        ('gray', 'رمادي'),
        ('green', 'أخضر'),
        ('yellow', 'أصفر'),
        ('navy', 'كحلي'),
        ('beige', 'بيج'),
    ]

    name = models.CharField(max_length=200, verbose_name="اسم المنتج")
    name_en = models.CharField(max_length=200, blank=True, verbose_name="Product Name (English)")
    name_he = models.CharField(max_length=200, blank=True, verbose_name="Product Name (Hebrew)")
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='products', verbose_name="العلامة التجارية")
    description = models.TextField(blank=True, verbose_name="وصف المنتج")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعر")
    sizes = models.JSONField(default=list, verbose_name="المقاسات المتاحة")  # Store multiple sizes
    color = models.CharField(max_length=20, choices=COLORS, verbose_name="اللون", blank=True, null=True)
    color_hex = models.CharField(max_length=7, default='#000000', verbose_name="كود اللون")
    stock_quantity = models.PositiveIntegerField(default=0, verbose_name="الكمية المتاحة")
    is_featured = models.BooleanField(default=False, verbose_name="منتج مميز")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views_count = models.PositiveIntegerField(default=0, verbose_name="عدد المشاهدات")

    class Meta:
        verbose_name = "منتج"
        verbose_name_plural = "المنتجات"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.brand.name}"

    def get_absolute_url(self):
        return reverse('shoes_view:product_detail', kwargs={'product_id': self.pk})

    def get_main_image(self):
        """Get the main product image"""
        main_image = self.images.filter(is_main=True).first()
        if main_image:
            return main_image.image
        first_image = self.images.first()
        return first_image.image if first_image else None

    def get_color_images(self):
        """Get images for the current color"""
        return self.images.filter(color=self.color)

    def is_in_stock(self):
        return self.stock_quantity > 0

    def get_display_price(self):
        """Format price for display"""
        from django.conf import settings
        currency_symbol = getattr(settings, 'CURRENCY_SYMBOL', '₪')
        return f"{self.price} {currency_symbol}"
    
    def get_available_colors(self):
        """
        Get all available colors for this product.
        This method is robust and handles both the new ColorVariant system
        and the old legacy color field system to prevent colors from disappearing.
        """
        found_colors = {}

        # 1. Prioritize images linked to a ColorVariant
        images_with_variants = self.images.filter(color_variant__isnull=False).select_related('color_variant').order_by('order')
        for image in images_with_variants:
            variant = image.color_variant
            if variant.code not in found_colors:
                found_colors[variant.code] = {
                    'code': variant.code,
                    'name': variant.name,
                    'hex': variant.hex_color,
                    'thumbnail_url': variant.thumbnail.url if variant.thumbnail else image.image.url,
                    'image_url': image.image.url
                }

        # 2. Fallback for images with the legacy 'color' field
        if not found_colors:
            image_colors = self.images.filter(color__isnull=False).exclude(color__exact='').values_list('color', flat=True).distinct()
            colors_to_process = set(image_colors)
            if self.color:
                colors_to_process.add(self.color)

            for color_code in colors_to_process:
                if color_code not in found_colors:
                    color_name = dict(self.COLORS).get(color_code, color_code)
                    color_hex_map = {
                        'black': '#000000', 'white': '#FFFFFF', 'brown': '#8B4513',
                        'blue': '#0000FF', 'red': '#FF0000', 'gray': '#808080',
                        'green': '#008000', 'yellow': '#FFFF00', 'navy': '#000080',
                        'beige': '#F5F5DC',
                    }
                    hex_code = color_hex_map.get(color_code, '#CCCCCC')
                    
                    color_image = self.images.filter(color=color_code).first()
                    image_url = color_image.image.url if color_image else self.get_main_image().url if self.get_main_image() else None

                    if image_url:
                        found_colors[color_code] = {
                            'code': color_code,
                            'name': color_name,
                            'hex': hex_code,
                            'thumbnail_url': image_url,
                            'image_url': image_url
                        }
        
        return list(found_colors.values())


class ProductImage(models.Model):
    """Model for product images with color variants"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name="المنتج")
    image = models.ImageField(upload_to='products/', verbose_name="الصورة")
    color = models.CharField(max_length=20, choices=Product.COLORS, verbose_name="لون الصورة", blank=True, null=True)
    color_variant = models.ForeignKey(ColorVariant, on_delete=models.SET_NULL, null=True, blank=True, related_name='product_images', verbose_name="متغير اللون")
    is_main = models.BooleanField(default=False, verbose_name="الصورة الرئيسية")
    alt_text = models.CharField(max_length=200, blank=True, verbose_name="نص بديل")
    order = models.PositiveIntegerField(default=0, verbose_name="الترتيب")

    class Meta:
        verbose_name = "صورة المنتج"
        verbose_name_plural = "صور المنتجات"
        ordering = ['-is_main', '?']

    def __str__(self):
        return f"{self.product.name} - {self.get_color_display()}"


class Customer(models.Model):
    """Customer model for guest and registered users"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name="المستخدم")
    session_key = models.CharField(max_length=40, null=True, blank=True, verbose_name="مفتاح الجلسة")
    full_name = models.CharField(max_length=200, verbose_name="الاسم الكامل")
    phone = models.CharField(max_length=20, verbose_name="رقم الهاتف")
    city = models.CharField(max_length=100, verbose_name="المدينة")
    street_address = models.TextField(verbose_name="عنوان الشارع")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "عميل"
        verbose_name_plural = "العملاء"

    def __str__(self):
        return self.full_name

    def get_full_address(self):
        return f"{self.street_address}, {self.city}"


class Order(models.Model):
    """Order model"""
    PAYMENT_METHODS = [
        ('cash', 'الدفع عند الاستلام'),
    ]

    STATUS_CHOICES = [
        ('pending', 'في الانتظار'),
        ('confirmed', 'مؤكد'),
        ('processing', 'قيد المعالجة'),
        ('shipped', 'تم الشحن'),
        ('delivered', 'تم التسليم'),
        ('cancelled', 'ملغي'),
    ]

    order_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="رقم الطلب")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders', verbose_name="العميل")
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS, verbose_name="طريقة الدفع")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="حالة الطلب")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="المبلغ الإجمالي")
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="مبلغ الخصم")
    final_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="المبلغ النهائي")
    
    # Wheel prizes information
    wheel_free_shipping = models.BooleanField(default=False, verbose_name="شحن مجاني من العجلة")
    wheel_gift_name = models.CharField(max_length=100, blank=True, verbose_name="اسم الهدية من العجلة")
    wheel_gift_description = models.TextField(blank=True, verbose_name="وصف الهدية من العجلة")
    
    notes = models.TextField(blank=True, verbose_name="ملاحظات")
    whatsapp_sent = models.BooleanField(default=False, verbose_name="تم إرسال واتساب")
    printed = models.BooleanField(default=False, verbose_name="تمت الطباعة")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "طلب"
        verbose_name_plural = "الطلبات"
        ordering = ['-created_at']

    def __str__(self):
        return f"طلب {self.order_id} - {self.customer.full_name}"

    def get_absolute_url(self):
        return reverse('shoes_view:order_detail', kwargs={'order_id': self.order_id})

    def save(self, *args, **kwargs):
        # Calculate final amount
        self.final_amount = self.total_amount - self.discount_amount
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    """Order item model"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="الطلب")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="المنتج")
    size = models.CharField(max_length=10, verbose_name="المقاس")
    color = models.CharField(max_length=50, blank=True, null=True, verbose_name="اللون")
    quantity = models.PositiveIntegerField(default=1, verbose_name="الكمية")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعر")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعر الإجمالي")

    class Meta:
        verbose_name = "عنصر الطلب"
        verbose_name_plural = "عناصر الطلبات"

    def __str__(self):
        return f"{self.quantity} x {self.product.name} ({self.size}, {self.color}) - {self.order.order_id}"

    def save(self, *args, **kwargs):
        self.total_price = self.price * self.quantity
        super().save(*args, **kwargs)


class CartItem(models.Model):
    """Cart item model for authenticated users and guests"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='cart_items', verbose_name="المستخدم")
    session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True, verbose_name="مفتاح الجلسة")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="المنتج")
    size = models.CharField(max_length=10, verbose_name="المقاس")
    color = models.CharField(max_length=50, blank=True, null=True, verbose_name="اللون")
    quantity = models.PositiveIntegerField(default=1, verbose_name="الكمية")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "عنصر السلة"
        verbose_name_plural = "عناصر السلة"
        unique_together = [['user', 'product', 'size', 'color'], ['session_key', 'product', 'size', 'color']]

    def __str__(self):
        if self.user:
            return f"Cart item for {self.user.username}: {self.product.name} ({self.size}, {self.color})"
        return f"Cart item for session {self.session_key}: {self.product.name} ({self.size}, {self.color})"

    def get_total_price(self):
        return self.product.price * self.quantity


class WheelSpin(models.Model):
    """Wheel of Fortune spin tracking"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='wheel_spins', verbose_name="المستخدم")
    session_key = models.CharField(max_length=40, null=True, blank=True, verbose_name="مفتاح الجلسة")
    discount_percentage = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name="نسبة الخصم")
    prize_type = models.CharField(max_length=20, default='discount', verbose_name="نوع الجائزة")
    prize_name = models.CharField(max_length=100, blank=True, verbose_name="اسم الجائزة")
    gift_description = models.TextField(blank=True, verbose_name="وصف الهدية")
    is_used = models.BooleanField(default=False, verbose_name="تم الاستخدام")
    spin_date = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الدوران")
    used_date = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ الاستخدام")

    class Meta:
        verbose_name = "دوران العجلة"
        verbose_name_plural = "دورانات العجلة"
        ordering = ['-spin_date']

    def __str__(self):
        user_info = self.user.username if self.user else f"Guest ({self.session_key[:10]})"
        if self.prize_type == 'gift':
            return f"{user_info} - {self.prize_name}"
        elif self.prize_type == 'discount':
            return f"{user_info} - {self.discount_percentage}% خصم"
        elif self.prize_type == 'free_shipping':
            return f"{user_info} - شحن مجاني"
        else:
            return f"{user_info} - لا يوجد جائزة"

    def can_spin_today(self):
        """Check if user/session can spin today"""
        today = timezone.now().date()
        if self.user:
            return not WheelSpin.objects.filter(
                user=self.user, 
                spin_date__date=today
            ).exists()
        else:
            return not WheelSpin.objects.filter(
                session_key=self.session_key, 
                spin_date__date=today
            ).exists()

    def get_prize_display(self):
        """Get human-readable prize display"""
        if self.prize_type == 'discount':
            return f"خصم {self.discount_percentage}%"
        elif self.prize_type == 'free_shipping':
            return "شحن مجاني"
        elif self.prize_type == 'gift':
            return f"هدية: {self.prize_name}"
        else:
            return "لا يوجد جائزة"


class WheelConfiguration(models.Model):
    """Configuration for the Wheel of Fortune"""
    PRIZE_TYPES = [
        ('discount', 'خصم'),
        ('free_shipping', 'شحن مجاني'),
        ('gift', 'هدية'),
        ('no_prize', 'لا يوجد جائزة'),
    ]

    name = models.CharField(max_length=100, verbose_name="اسم الجائزة")
    prize_type = models.CharField(max_length=20, choices=PRIZE_TYPES, verbose_name="نوع الجائزة")
    value = models.PositiveIntegerField(verbose_name="القيمة")  # Percentage for discount, 0 for others
    gift_description = models.TextField(blank=True, verbose_name="وصف الهدية", help_text="وصف تفصيلي للهدية (مطلوب فقط لنوع الهدية)")
    probability = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name="الاحتمالية")
    color = models.CharField(max_length=7, default='#FF0000', verbose_name="لون القطاع")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    can_win = models.BooleanField(default=True, verbose_name="يمكن الفوز بها")

    class Meta:
        verbose_name = "إعداد العجلة"
        verbose_name_plural = "إعدادات العجلة"

    def __str__(self):
        if self.prize_type == 'gift':
            return f"{self.name} - {self.gift_description[:50]}..."
        elif self.prize_type == 'discount':
            return f"{self.name} - {self.value}%"
        else:
            return f"{self.name}"

    def get_display_text(self):
        """Get the text to display on the wheel"""
        if self.prize_type == 'discount':
            return f"خصم {self.value}%"
        elif self.prize_type == 'free_shipping':
            return "شحن مجاني"
        elif self.prize_type == 'gift':
            return self.name
        else:
            return "حاول مرة أخرى"


class WheelAdminControl(models.Model):
    """Admin control for wheel outcomes - allows forcing specific results"""
    CONTROL_MODES = [
        ('random', 'عشوائي (حسب الاحتمالية)'),
        ('force_prize', 'فرض جائزة معينة'),
        ('force_no_prize', 'فرض عدم وجود جائزة'),
        ('sequence', 'تسلسل محدد'),
    ]

    name = models.CharField(max_length=100, verbose_name="اسم التحكم", default="التحكم الافتراضي")
    control_mode = models.CharField(max_length=20, choices=CONTROL_MODES, default='random', verbose_name="نمط التحكم")
    forced_prize = models.ForeignKey(WheelConfiguration, on_delete=models.CASCADE, null=True, blank=True, verbose_name="الجائزة المفروضة")
    sequence_prizes = models.JSONField(default=list, blank=True, verbose_name="تسلسل الجوائز")  # List of WheelConfiguration IDs
    current_sequence_index = models.PositiveIntegerField(default=0, verbose_name="فهرس التسلسل الحالي")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "تحكم إداري في العجلة"
        verbose_name_plural = "تحكم إداري في العجلة"
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.name} - {self.get_control_mode_display()}"

    def get_next_prize(self):
        """Get the next prize based on control mode"""
        if self.control_mode == 'force_prize' and self.forced_prize:
            return self.forced_prize
        elif self.control_mode == 'force_no_prize':
            # Return a no-prize configuration
            no_prize_config = WheelConfiguration.objects.filter(
                prize_type='no_prize', 
                is_active=True
            ).first()
            return no_prize_config
        elif self.control_mode == 'sequence' and self.sequence_prizes:
            if self.current_sequence_index < len(self.sequence_prizes):
                prize_id = self.sequence_prizes[self.current_sequence_index]
                try:
                    prize = WheelConfiguration.objects.get(id=prize_id, is_active=True)
                    # Move to next in sequence
                    self.current_sequence_index += 1
                    if self.current_sequence_index >= len(self.sequence_prizes):
                        self.current_sequence_index = 0  # Reset to beginning
                    self.save()
                    return prize
                except WheelConfiguration.DoesNotExist:
                    pass
        
        # Default to random mode
        return None


class UserProfile(models.Model):
    """Extended user profile"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name="المستخدم")
    phone = models.CharField(max_length=20, blank=True, verbose_name="رقم الهاتف")
    city = models.CharField(max_length=100, blank=True, verbose_name="المدينة")
    street_address = models.TextField(blank=True, verbose_name="عنوان الشارع")
    preferred_language = models.CharField(max_length=5, choices=[('ar', 'العربية'), ('en', 'English'), ('he', 'עברית')], default='ar', verbose_name="اللغة المفضلة")
    newsletter_subscribed = models.BooleanField(default=False, verbose_name="مشترك في النشرة الإخبارية")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "ملف المستخدم"
        verbose_name_plural = "ملفات المستخدمين"

    def __str__(self):
        return f"ملف {self.user.username}"


class ContactMessage(models.Model):
    """Contact form messages"""
    name = models.CharField(max_length=200, verbose_name="الاسم")
    phone = models.CharField(max_length=20, blank=True, verbose_name="رقم الهاتف")
    subject = models.CharField(max_length=200, verbose_name="الموضوع")
    message = models.TextField(verbose_name="الرسالة")
    is_read = models.BooleanField(default=False, verbose_name="تم القراءة")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "رسالة التواصل"
        verbose_name_plural = "رسائل التواصل"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.subject}"
