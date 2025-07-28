# دليل إعداد الطابعة الحرارية U80II(U)

## 📋 المتطلبات

### الأجهزة:
- طابعة حرارية U80II(U) أو متوافقة
- كابل USB أو Serial
- ورق حراري بعرض 80mm

### البرمجيات:
- تم تثبيت `pyserial` تلقائياً مع النظام
- Windows 10/11 مع تعريفات الطابعة

## ⚙️ خطوات الإعداد

### 1. توصيل الطابعة:
```
1. وصل الطابعة بالكمبيوتر عبر USB
2. تأكد من تشغيل الطابعة
3. اذهب إلى Device Manager وتأكد من ظهور الطابعة
4. لاحظ رقم المنفذ (مثل COM3, COM4)
```

### 2. إعداد النظام:
في ملف `shoes/settings.py`، قم بضبط الإعدادات التالية:

```python
# Print settings
ENABLE_AUTO_PRINT = True
PRINTER_NAME = 'U80II(U)'  # اسم الطابعة
PRINT_METHOD = 'thermal'   # طريقة الطباعة الحرارية
RECEIPT_WIDTH = 48         # عرض الفاتورة

# Thermal printer specific settings
THERMAL_PRINTER_PORT = 'auto'      # أو حدد المنفذ مثل 'COM3'
THERMAL_PRINTER_ENCODING = 'cp720' # تشفير عربي
THERMAL_CUT_PAPER = True           # قطع الورق تلقائياً
THERMAL_PRINT_LOGO = False         # طباعة الشعار
```

### 3. إعدادات المنفذ:
إذا كان الكشف التلقائي لا يعمل، حدد المنفذ يدوياً:

```python
THERMAL_PRINTER_PORT = 'COM3'  # استبدل برقم المنفذ الصحيح
```

لمعرفة رقم المنفذ:
1. اذهب إلى Device Manager
2. ابحث عن "Ports (COM & LPT)"
3. ابحث عن الطابعة واكتب رقم المنفذ

## 🧪 اختبار الطابعة

### من لوحة الإدارة:
1. اذهب إلى Admin Panel
2. قسم "الطلبات" 
3. اختر أي طلب
4. من قائمة Actions اختر "اختبار الطابعة"
5. انقر "تنفيذ"

### من الأوامر:
```bash
cd shoesnew/shoes/shoes
python manage.py shell -c "from shoes_view.utils import PrintService; PrintService.test_print()"
```

## 🔧 حل المشاكل

### المشكلة: لا تطبع الطابعة
**الحلول:**
1. تأكد من توصيل الطابعة وتشغيلها
2. تحقق من رقم المنفذ في Device Manager
3. جرب منافذ مختلفة: COM1, COM2, COM3, COM4
4. تأكد من وجود ورق في الطابعة

### المشكلة: النص العربي لا يظهر بشكل صحيح
**الحلول:**
1. جرب تشفيرات مختلفة:
   ```python
   THERMAL_PRINTER_ENCODING = 'cp720'  # الافتراضي
   THERMAL_PRINTER_ENCODING = 'utf-8'  # بديل
   THERMAL_PRINTER_ENCODING = 'cp1256' # بديل آخر
   ```

### المشكلة: خطأ "Serial port not found"
**الحلول:**
1. تأكد من تثبيت pyserial: `pip install pyserial`
2. تحقق من تعريفات الطابعة في Windows
3. جرب إعادة توصيل الطابعة
4. استخدم الوضع اليدوي:
   ```python
   THERMAL_PRINTER_PORT = 'COM3'  # حدد المنفذ يدوياً
   ```

## 📝 تخصيص الفاتورة

### تغيير عرض الفاتورة:
```python
RECEIPT_WIDTH = 32  # للطابعات 58mm
RECEIPT_WIDTH = 48  # للطابعات 80mm (الافتراضي)
```

### إضافة شعار:
```python
THERMAL_PRINT_LOGO = True
# ضع صورة الشعار في: static/images/logo.png
```

### تعطيل قطع الورق:
```python
THERMAL_CUT_PAPER = False
```

## 📋 أوامر ESC/POS المستخدمة

النظام يستخدم أوامر ESC/POS القياسية:
- **التهيئة:** `ESC @`
- **النص الغامق:** `ESC E 1` / `ESC E 0`
- **المحاذاة:** `ESC a 0/1/2`
- **الحجم المضاعف:** `ESC ! 16`
- **قطع الورق:** `ESC m`

## 🔄 الوضع الاحتياطي

إذا فشلت الطباعة الحرارية، النظام يتحول تلقائياً إلى:
1. الطباعة عبر Notepad
2. الطباعة عبر الأمر print
3. حفظ نسخة في مجلد orders/

## 📞 الدعم الفني

للمساعدة في الإعداد:
1. تأكد من تشغيل وضع التشخيص: `PRINT_DEBUG = True`
2. راجع ملف السجلات: `logs/django.log`
3. ابحث عن رسائل الطباعة في السجلات

---
**ملاحظة:** هذا النظام متوافق مع معظم الطابعات الحرارية التي تدعم أوامر ESC/POS. 