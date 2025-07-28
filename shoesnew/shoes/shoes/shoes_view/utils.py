"""
Utility functions for AL-QATHIFI Men's Shoe Store
"""

import requests
import json
import logging
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from datetime import datetime
import subprocess
import platform
import random
import os
from django.utils import timezone

logger = logging.getLogger(__name__)


class FileService:
    """File service for saving order details"""
    
    @staticmethod
    def save_order_to_file(order):
        """Save order details to text file"""
        try:
            # Create orders directory if it doesn't exist
            orders_dir = os.path.join(settings.BASE_DIR, 'orders')
            os.makedirs(orders_dir, exist_ok=True)
            
            # Ensure directory has write permissions
            try:
                os.chmod(orders_dir, 0o755)
            except (OSError, PermissionError):
                pass  # Continue if permission change fails
            
            # Generate filename with timestamp
            timestamp = order.created_at.strftime('%Y%m%d_%H%M%S')
            filename = f"order_{order.order_id}_{timestamp}.txt"
            filepath = os.path.join(orders_dir, filename)
            
            # Generate order content
            content = FileService._generate_order_content(order)
            
            # Save to file with explicit encoding
            with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
                f.write(content)
            
            # Ensure file has read permissions
            try:
                os.chmod(filepath, 0o644)
            except (OSError, PermissionError):
                pass  # Continue if permission change fails
            
            logger.info(f"✅ Order {order.order_id} saved to file: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save order {order.order_id} to file: {str(e)}")
            logger.error(f"   Orders directory: {os.path.join(settings.BASE_DIR, 'orders')}")
            logger.error(f"   Directory exists: {os.path.exists(os.path.join(settings.BASE_DIR, 'orders'))}")
            return False
    
    @staticmethod
    def save_cancellation_to_file(order):
        """Save order cancellation details to text file"""
        try:
            # Create orders directory if it doesn't exist
            orders_dir = os.path.join(settings.BASE_DIR, 'orders')
            os.makedirs(orders_dir, exist_ok=True)
            
            # Ensure directory has write permissions
            try:
                os.chmod(orders_dir, 0o755)
            except (OSError, PermissionError):
                pass  # Continue if permission change fails
            
            # Generate filename with timestamp
            timestamp = order.updated_at.strftime('%Y%m%d_%H%M%S')
            filename = f"cancelled_order_{order.order_id}_{timestamp}.txt"
            filepath = os.path.join(orders_dir, filename)
            
            # Generate cancellation content
            content = FileService._generate_cancellation_content(order)
            
            # Save to file with explicit encoding
            with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
                f.write(content)
            
            # Ensure file has read permissions
            try:
                os.chmod(filepath, 0o644)
            except (OSError, PermissionError):
                pass  # Continue if permission change fails
            
            logger.info(f"✅ Order cancellation {order.order_id} saved to file: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save order cancellation {order.order_id} to file: {str(e)}")
            logger.error(f"   Orders directory: {os.path.join(settings.BASE_DIR, 'orders')}")
            logger.error(f"   Directory exists: {os.path.exists(os.path.join(settings.BASE_DIR, 'orders'))}")
            return False
    
    @staticmethod
    def _generate_order_content(order):
        """Generate order content for text file"""
        content = f"""
{'='*60}
           AL-QATHIFI - القذيفي
        متجر الأحذية الرجالية
{'='*60}

رقم الطلب: {order.order_id}
التاريخ: {order.created_at.strftime('%Y-%m-%d %H:%M:%S')}

معلومات العميل:
----------------
الاسم: {order.customer.full_name}
الهاتف: {order.customer.phone}
البريد الإلكتروني: {order.customer.email if order.customer.email else 'غير متوفر'}
المدينة: {order.customer.city}
العنوان: {order.customer.street_address}
العنوان الكامل: {order.customer.get_full_address()}

تفاصيل المنتجات:
-----------------
"""
        
        for item in order.items.all():
            content += f"""
المنتج: {item.product.name}
العلامة التجارية: {item.product.brand.name}
المقاس: {item.size}
الكمية: {item.quantity}
سعر الوحدة: {item.price} ₪
السعر الإجمالي: {item.total_price} ₪
---
"""
        
        content += f"""

ملخص الطلب:
------------
المبلغ الإجمالي: {order.total_amount} ₪
الخصم: {order.discount_amount} ₪
المبلغ النهائي: {order.final_amount} ₪
طريقة الدفع: {order.get_payment_method_display()}

جوائز عجلة الحظ:
-----------------"""

        # Add wheel prizes information
        wheel_prizes = []
        if order.discount_amount > 0:
            wheel_prizes.append(f"خصم من عجلة الحظ: {order.discount_amount} ₪")
        
        if order.wheel_free_shipping:
            wheel_prizes.append("شحن مجاني من عجلة الحظ")
        
        if order.wheel_gift_name:
            wheel_prizes.append(f"هدية من عجلة الحظ: {order.wheel_gift_name}")
            if order.wheel_gift_description:
                wheel_prizes.append(f"وصف الهدية: {order.wheel_gift_description}")
        
        if wheel_prizes:
            for prize in wheel_prizes:
                content += f"\n{prize}"
        else:
            content += "\nلا توجد جوائز من عجلة الحظ"

        content += f"""

ملاحظات:
---------
{order.notes if order.notes else 'لا توجد ملاحظات'}

{'='*60}
تم إنشاء هذا الملف تلقائياً في: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*60}
"""
        return content
    
    @staticmethod
    def _generate_cancellation_content(order):
        """Generate cancellation content for text file"""
        content = f"""
{'='*60}
           AL-QATHIFI - القذيفي
        متجر الأحذية الرجالية
        طلب ملغي
{'='*60}

رقم الطلب: {order.order_id}
تاريخ الطلب: {order.created_at.strftime('%Y-%m-%d %H:%M:%S')}
تاريخ الإلغاء: {order.updated_at.strftime('%Y-%m-%d %H:%M:%S')}

معلومات العميل:
----------------
الاسم: {order.customer.full_name}
الهاتف: {order.customer.phone}
البريد الإلكتروني: {order.customer.email if order.customer.email else 'غير متوفر'}
المدينة: {order.customer.city}
العنوان: {order.customer.street_address}
العنوان الكامل: {order.customer.get_full_address()}

تفاصيل المنتجات الملغاة:
------------------------
"""
        
        for item in order.items.all():
            content += f"""
المنتج: {item.product.name}
العلامة التجارية: {item.product.brand.name}
المقاس: {item.size}
الكمية: {item.quantity}
سعر الوحدة: {item.price} ₪
السعر الإجمالي: {item.total_price} ₪
---
"""
        
        content += f"""

ملخص الطلب الملغي:
------------------
المبلغ الإجمالي: {order.total_amount} ₪
الخصم: {order.discount_amount} ₪
المبلغ النهائي: {order.final_amount} ₪
طريقة الدفع: {order.get_payment_method_display()}

جوائز عجلة الحظ الملغاة:
------------------------"""

        # Add wheel prizes information for cancelled order
        wheel_prizes = []
        if order.discount_amount > 0:
            wheel_prizes.append(f"خصم ملغي من عجلة الحظ: {order.discount_amount} ₪")
        
        if order.wheel_free_shipping:
            wheel_prizes.append("شحن مجاني ملغي من عجلة الحظ")
        
        if order.wheel_gift_name:
            wheel_prizes.append(f"هدية ملغاة من عجلة الحظ: {order.wheel_gift_name}")
            if order.wheel_gift_description:
                wheel_prizes.append(f"وصف الهدية الملغاة: {order.wheel_gift_description}")
        
        if wheel_prizes:
            for prize in wheel_prizes:
                content += f"\n{prize}"
        else:
            content += "\nلا توجد جوائز ملغاة من عجلة الحظ"

        content += f"""

ملاحظات الطلب الأصلي:
----------------------
{order.notes if order.notes else 'لا توجد ملاحظات'}

سبب الإلغاء:
------------
إلغاء من قبل العميل

{'='*60}
تم إنشاء هذا الملف تلقائياً في: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*60}
"""
        return content


class TelegramService:
    """Telegram integration service"""
    
    @staticmethod
    def send_order_notification(order):
        """Send Telegram notification for new order with product images"""
        try:
            # Send order details with product images to Telegram channel
            result = TelegramService._send_order_with_images(
                order,
                f"🔔 طلب جديد #{order.order_id}"
            )
            
            if result:
                logger.info(f"Telegram notification sent for order {order.order_id}")
            else:
                logger.error(f"Failed to send Telegram notification for order {order.order_id}")
                
            return result
            
        except Exception as e:
            logger.error(f"Error sending Telegram notification for order {order.order_id}: {str(e)}")
            return False
    
    @staticmethod
    def send_cancellation_notification(order):
        """Send Telegram notification for cancelled order"""
        try:
            # Format cancellation message
            message = TelegramService._format_cancellation_message(order)
            
            # Send to Telegram channel
            result = TelegramService._send_telegram_message(
                f"❌ تم إلغاء الطلب #{order.order_id}\n\n{message}"
            )
                
            return result
            
        except Exception as e:
            logger.error(f"Telegram cancellation notification failed for order {order.order_id}: {str(e)}")
            return False
    
    @staticmethod
    def _send_order_with_images(order, title):
        """Send order message with product images to Telegram"""
        try:
            # Format the main message with product details
            message = TelegramService._format_order_message(order, title)
            
            # Get product images for the message
            product_images = []
            for item in order.items.all():
                product = item.product
                if product:
                    main_image = product.get_main_image()
                    if main_image:
                        # Create full URL for the image
                        image_url = f"{settings.SITE_URL}{main_image.url}"
                        product_images.append({
                            'url': image_url,
                            'caption': f"👤 {order.customer.full_name}\n📞 {order.customer.phone}\n\n🛍️ {product.name}\n📏 مقاس {item.size} - الكمية: {item.quantity}"
                        })
            
            # Send message with images if available
            if product_images:
                # Send message with product photos as media group
                return TelegramService._send_telegram_media_group(message, product_images)
            else:
                # Send message without images if no product images available
                return TelegramService._send_telegram_message(message)
                
        except Exception as e:
            logger.error(f"Error sending order with images to Telegram: {str(e)}")
            return False
    
    @staticmethod
    def _send_telegram_message(message):
        """Send a text message to Telegram"""
        try:
            import requests
            
            # Check if we have Telegram credentials configured
            if (settings.TELEGRAM_BOT_TOKEN == 'your_bot_token_here' or 
                settings.TELEGRAM_CHAT_ID == 'your_chat_id_here'):
                # If no real credentials, just log the message
                logger.info(f"Telegram message: {message}")
                logger.warning("Telegram credentials not configured - message logged only")
                return True
            
            # Send actual Telegram message
            url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
            data = {
                'chat_id': settings.TELEGRAM_CHAT_ID,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"Telegram message sent successfully")
                return True
            else:
                logger.error(f"Failed to send Telegram message: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {str(e)}")
            # Fall back to logging the message
            logger.info(f"Telegram message (fallback): {message}")
            return False

    @staticmethod
    def _send_telegram_media_group(message, product_images):
        """Send a media group with product images and caption to Telegram"""
        try:
            import requests
            import os
            from django.core.files.storage import default_storage
            
            # Check if we have Telegram credentials configured
            if (settings.TELEGRAM_BOT_TOKEN == 'your_bot_token_here' or 
                settings.TELEGRAM_CHAT_ID == 'your_chat_id_here'):
                # If no real credentials, just log the message
                logger.info(f"Telegram media group message: {message}")
                for img in product_images:
                    logger.info(f"   - Image: {img['url']} - {img['caption']}")
                logger.warning("Telegram credentials not configured - message logged only")
                return True
            
            # First send the text message
            text_sent = TelegramService._send_telegram_message(message)
            
            # Then send each product image with its caption
            for img_data in product_images:
                try:
                    # Extract the local file path from the URL
                    image_url = img_data['url']
                    # Remove the site URL to get the relative path
                    image_path = image_url.replace(settings.SITE_URL, '')
                    
                    # Construct the correct file path
                    if image_path.startswith('/media/'):
                        # Remove '/media/' from the start to get the relative path
                        relative_path = image_path[7:]  # Remove '/media/'
                        full_path = os.path.join(settings.MEDIA_ROOT, relative_path)
                    else:
                        # Fallback: assume it's already a relative path
                        full_path = os.path.join(settings.MEDIA_ROOT, image_path.lstrip('/'))
                    
                    if os.path.exists(full_path):
                        # Send photo with caption
                        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendPhoto"
                        
                        with open(full_path, 'rb') as photo:
                            files = {'photo': photo}
                            data = {
                                'chat_id': settings.TELEGRAM_CHAT_ID,
                                'caption': img_data['caption']
                            }
                            
                            response = requests.post(url, files=files, data=data, timeout=30)
                            
                            if response.status_code == 200:
                                logger.info(f"Telegram photo sent successfully: {img_data['caption']}")
                            else:
                                logger.error(f"Failed to send Telegram photo: {response.status_code} - {response.text}")
                    else:
                        logger.warning(f"Image file not found: {full_path}")
                        
                except Exception as img_error:
                    logger.error(f"Error sending individual image to Telegram: {str(img_error)}")
                    continue
            
            return text_sent
                
        except Exception as e:
            logger.error(f"Failed to send Telegram media group: {str(e)}")
            # Fall back to sending just the text message
            return TelegramService._send_telegram_message(message)

    @staticmethod
    def _format_order_message(order, title=""):
        """Format order details for Telegram message"""
        try:
            message = f"""
<b>{title}</b>

📋 <b>تفاصيل الطلب:</b>
🆔 رقم الطلب: <code>{order.order_id}</code>
👤 العميل: <b>{order.customer.full_name}</b>
📞 الهاتف: <code>{order.customer.phone}</code>
📍 العنوان: {order.customer.street_address}, {order.customer.city}

🛍️ <b>المنتجات:</b>
"""
            
            total_amount = 0
            for item in order.items.all():
                product = item.product
                if product:
                    item_total = item.quantity * item.price
                    total_amount += item_total
                    
                    message += f"""
▫️ <b>{product.name}</b>
   🎨 اللون: {item.color.name if item.color else 'اللون الافتراضي'}
   📏 المقاس: {item.size}
   🔢 الكمية: {item.quantity}
   💰 السعر: {item.price:,.0f} شيكل
   📊 المجموع: <b>{item_total:,.0f} شيكل</b>
"""
            
            message += f"""
💳 <b>المجموع الكلي: {total_amount:,.0f} شيكل</b>
📅 تاريخ الطلب: {order.created_at.strftime('%Y-%m-%d %H:%M')}
🚚 حالة الطلب: <b>{order.get_status_display()}</b>

🎁 <b>جوائز عجلة الحظ:</b>"""

            # Add wheel prizes information
            wheel_prizes = []
            if order.discount_amount > 0:
                wheel_prizes.append(f"🏷️ خصم من عجلة الحظ: <b>{order.discount_amount:,.0f} شيكل</b>")
            
            if order.wheel_free_shipping:
                wheel_prizes.append("🚚 شحن مجاني من عجلة الحظ")
            
            if order.wheel_gift_name:
                wheel_prizes.append(f"🎁 هدية من عجلة الحظ: <b>{order.wheel_gift_name}</b>")
                if order.wheel_gift_description:
                    wheel_prizes.append(f"📝 وصف الهدية: {order.wheel_gift_description}")
            
            if wheel_prizes:
                for prize in wheel_prizes:
                    message += f"\n{prize}"
            else:
                message += "\n✅ لا توجد جوائز من عجلة الحظ"

            message += f"""

✅ يرجى تأكيد استلام الطلب والبدء في التحضير.
"""
            
            return message.strip()
            
        except Exception as e:
            logger.error(f"Error formatting order message: {str(e)}")
            return f"خطأ في تنسيق رسالة الطلب #{order.order_id}"
    
    @staticmethod
    def _format_cancellation_message(order):
        """Format cancelled order details into Telegram message"""
        items_text = ""
        for item in order.items.all():
            items_text += f"• <b>{item.product.name}</b> ({item.product.brand.name})\n"
            items_text += f"  المقاس: {item.size} | الكمية: {item.quantity} | السعر: {item.price} شيكل\n\n"
        
        message = f"""
👤 العميل: <b>{order.customer.full_name}</b>
📱 الهاتف: <code>{order.customer.phone}</code>
📍 العنوان: {order.customer.get_full_address()}

🛍️ <b>المنتجات الملغاة:</b>
{items_text}

💰 المبلغ الإجمالي: <b>{order.total_amount} شيكل</b>
🎁 الخصم: <b>{order.discount_amount} شيكل</b>
💳 المبلغ النهائي: <b>{order.final_amount} شيكل</b>
💵 طريقة الدفع: <b>{order.get_payment_method_display()}</b>

❌ <b>جوائز عجلة الحظ الملغاة:</b>"""

        # Add cancelled wheel prizes to Telegram message
        wheel_prizes = []
        if order.discount_amount > 0:
            wheel_prizes.append(f"🏷️ خصم ملغي من عجلة الحظ: <b>{order.discount_amount} شيكل</b>")
        
        if order.wheel_free_shipping:
            wheel_prizes.append("🚚 شحن مجاني ملغي من عجلة الحظ")
        
        if order.wheel_gift_name:
            wheel_prizes.append(f"🎁 هدية ملغاة من عجلة الحظ: <b>{order.wheel_gift_name}</b>")
            if order.wheel_gift_description:
                wheel_prizes.append(f"📝 وصف الهدية الملغاة: {order.wheel_gift_description}")
        
        if wheel_prizes:
            for prize in wheel_prizes:
                message += f"\n{prize}"
        else:
            message += "\n✅ لا توجد جوائز ملغاة من عجلة الحظ"

        message += f"""

📅 تاريخ الطلب: {order.created_at.strftime('%Y-%m-%d %H:%M')}
❌ تاريخ الإلغاء: {order.updated_at.strftime('%Y-%m-%d %H:%M')}

⚠️ <b>طلب ملغي - لا حاجة للتوصيل</b>
🔄 تحديث حالة المخزون حسب الحاجة
        """.strip()
        
        return message
    
    @staticmethod
    def _send_whatsapp_image(phone_number, image_url, caption):
        """Send WhatsApp image with caption using Twilio"""
        try:
            # Check if we have Twilio credentials configured
            if (settings.TWILIO_ACCOUNT_SID == 'your_account_sid_here' or 
                settings.TWILIO_AUTH_TOKEN == 'your_auth_token_here'):
                # If no real credentials, just log the image
                logger.info(f"WhatsApp image to {phone_number}: {image_url} - {caption}")
                logger.warning("Twilio credentials not configured - image logged only")
                return True
            
            # Use Twilio to send actual WhatsApp image
            from twilio.rest import Client
            
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            
            twilio_message = client.messages.create(
                body=caption,
                media_url=[image_url],
                from_=settings.TWILIO_WHATSAPP_NUMBER,
                to=f'whatsapp:{phone_number}'
            )
            
            logger.info(f"WhatsApp image sent successfully to {phone_number} - Message SID: {twilio_message.sid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send WhatsApp image to {phone_number}: {str(e)}")
            # Fall back to logging the image
            logger.info(f"WhatsApp image (fallback) to {phone_number}: {image_url} - {caption}")
            return False
    
    @staticmethod
    def _send_whatsapp_message(phone_number, message):
        """Send WhatsApp message using Twilio"""
        try:
            # Check if we have Twilio credentials configured
            if (settings.TWILIO_ACCOUNT_SID == 'your_account_sid_here' or 
                settings.TWILIO_AUTH_TOKEN == 'your_auth_token_here'):
                # If no real credentials, just log the message
                logger.info(f"WhatsApp message to {phone_number}: {message}")
                logger.warning("Twilio credentials not configured - message logged only")
                return True
            
            # Use Twilio to send actual WhatsApp message
            from twilio.rest import Client
            
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            
            twilio_message = client.messages.create(
                body=message,
                from_=settings.TWILIO_WHATSAPP_NUMBER,
                to=f'whatsapp:{phone_number}'
            )
            
            logger.info(f"WhatsApp message sent successfully to {phone_number} - Message SID: {twilio_message.sid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message to {phone_number}: {str(e)}")
            # Fall back to logging the message
            logger.info(f"WhatsApp message (fallback) to {phone_number}: {message}")
            return False

    @staticmethod
    def _send_whatsapp_message_with_media(phone_number, message, media_urls):
        """Send WhatsApp message with media using Twilio"""
        try:
            # Check if we have Twilio credentials configured
            if (settings.TWILIO_ACCOUNT_SID == 'your_account_sid_here' or 
                settings.TWILIO_AUTH_TOKEN == 'your_auth_token_here'):
                # If no real credentials, just log the message and media
                logger.info(f"WhatsApp message to {phone_number}: {message}")
                for url in media_urls:
                    logger.info(f"   - Media: {url}")
                logger.warning("Twilio credentials not configured - message logged only")
                return True
            
            # Use Twilio to send actual WhatsApp message with media
            from twilio.rest import Client
            
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            
            twilio_message = client.messages.create(
                body=message,
                media_url=media_urls,
                from_=settings.TWILIO_WHATSAPP_NUMBER,
                to=f'whatsapp:{phone_number}'
            )
            
            logger.info(f"WhatsApp message with media sent successfully to {phone_number} - Message SID: {twilio_message.sid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message with media to {phone_number}: {str(e)}")
            # Fall back to logging the message
            logger.info(f"WhatsApp message (fallback) to {phone_number}: {message}")
            return False


class PrintService:
    """Print service for order receipts"""
    
    @staticmethod
    def print_order(order):
        """Print order receipt"""
        try:
            if not settings.ENABLE_AUTO_PRINT:
                if getattr(settings, 'PRINT_DEBUG', False):
                    logger.info("Auto-print is disabled in settings")
                return False
                
            logger.info(f"🖨️ Starting print job for order {order.order_id}")
            
            # Generate receipt content
            receipt_content = PrintService._generate_receipt_content(order)
            
            if getattr(settings, 'PRINT_DEBUG', False):
                logger.info("Receipt content generated successfully")
            
            # Print based on operating system and method preference
            print_method = getattr(settings, 'PRINT_METHOD', 'auto')
            
            if print_method == 'thermal':
                # Direct thermal printer printing
                result = PrintService._print_thermal(receipt_content)
            elif platform.system() == "Windows":
                result = PrintService._print_windows(receipt_content, print_method)
            elif platform.system() == "Darwin":  # macOS
                result = PrintService._print_macos(receipt_content)
            else:  # Linux
                result = PrintService._print_linux(receipt_content)
            
            if result:
                order.printed = True
                order.save()
                logger.info(f"✅ Order {order.order_id} printed successfully and marked as printed")
            else:
                logger.error(f"❌ Failed to print order {order.order_id}")
                
            return result
            
        except Exception as e:
            logger.error(f"Printing failed for order {order.order_id}: {str(e)}")
            return False
    
    @staticmethod
    def test_print():
        """Test printer functionality"""
        try:
            logger.info("🖨️ Running printer test...")
            
            # Generate test content based on print method
            print_method = getattr(settings, 'PRINT_METHOD', 'auto')
            
            if print_method == 'thermal':
                test_content = PrintService._generate_thermal_test_content()
            else:
                test_content = PrintService._generate_standard_test_content()
            
            # Use the same printing logic as orders
            if print_method == 'thermal':
                # Direct thermal printer printing
                result = PrintService._print_thermal(test_content)
            elif platform.system() == "Windows":
                result = PrintService._print_windows(test_content, print_method)
            elif platform.system() == "Darwin":  # macOS
                result = PrintService._print_macos(test_content)
            else:  # Linux
                result = PrintService._print_linux(test_content)
            
            if result:
                logger.info("✅ Printer test completed successfully")
            else:
                logger.error("❌ Printer test failed")
                
            return result
            
        except Exception as e:
            logger.error(f"Printer test failed: {str(e)}")
            return False
    
    @staticmethod
    def _generate_thermal_test_content():
        """Generate thermal printer test content - plain text format"""
        # Simple plain text content without ESC/POS commands
        content = ""
        
        # Simple test content matching receipt format
        content += f"رقم الطلب: اختبار-طباعة-حرارية\n"
        content += f"التاريخ: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
        content += "\n"
        
        content += "العميل: اختبار الطابعة\n"
        content += "الهاتف: +970123456789\n"
        content += "العنوان: فلسطين, رام الله\n"
        content += "\n"
        
        content += "-" * 30 + "\n"
        content += "المنتجات:\n"
        content += "-" * 30 + "\n"
        content += "\n"
        
        content += "منتج تجريبي للاختبار\n"
        content += "المقاس: 42 | الكمية: 1\n"
        content += "السعر: 100.00 شيكل\n"
        content += "\n"
        
        content += "-" * 30 + "\n"
        content += "المجموع: 100.00 شيكل\n"
        content += "المبلغ النهائي: 100.00 شيكل\n"
        content += "طريقة الدفع: الدفع عند الاستلام\n"
        content += "\n\n"
        
        return content
    
    @staticmethod
    def _generate_standard_test_content():
        """Generate standard test content for regular printers"""
        return f"""
{'='*40}
          اختبار الطابعة
{'='*40}

التاريخ: {datetime.now().strftime('%d/%m/%Y %H:%M')}
النظام: متجر الأحذية الرجالية

هذا اختبار للطابعة للتأكد من أنها
تعمل بشكل صحيح مع النظام.

إذا رأيت هذه الرسالة، فالطابعة تعمل! ✅

{'='*40}
"""
    
    @staticmethod
    def _generate_receipt_content(order):
        """Generate receipt content based on printer type"""
        print_method = getattr(settings, 'PRINT_METHOD', 'auto')
        
        if print_method == 'thermal':
            return PrintService._generate_thermal_receipt_content(order)
        else:
            return PrintService._generate_standard_receipt_content(order)
    
    @staticmethod
    def _generate_thermal_receipt_content(order):
        """Generate thermal printer receipt content - plain text format"""
        # Simple plain text content without ESC/POS commands
        content = ""
        
        # Order info
        content += f"رقم الطلب: {order.order_id}\n"
        content += f"التاريخ: {order.created_at.strftime('%d/%m/%Y %H:%M')}\n"
        content += "-" * 16 + "\n"
        content += "\n"
        
        # Customer info
        content += "-" * 16+"\n"
        content += f"العميل: {order.customer.full_name}\n"
        content += f"الهاتف: {order.customer.phone}\n"
        content += f"العنوان: {order.customer.get_full_address()}\n"
        content += "-" * 16 + "\n"
        content += "\n"
        
        # Products separator
        content += "-" * 16+"\n"
        content += "المنتجات:\n"
        content += "-" * 16 + "\n"
        content += "\n"
        
        # Products
        for item in order.items.all():
            # Product name
            product_name = item.product.name
            color_info = f" - {item.color.name}" if item.color else ""
            full_name = product_name + color_info
            content += f"{full_name}\n"
            content += f"المقاس: {item.size} | الكمية: {item.quantity}\n"
            content += f"السعر: {item.price} شيكل\n"
            content += "\n"
        
        # Totals
        content += "-" * 16 + "\n"
        content += f"المجموع: {order.total_amount} شيكل\n"
        
        # Wheel prizes
        if order.discount_amount > 0:
            content += f"جوائز العجلة: خصم: {order.discount_amount} شيكل\n"
        elif order.wheel_free_shipping:
            content += "جوائز العجلة: شحن مجاني\n"
        elif order.wheel_gift_name:
            content += f"جوائز العجلة: هدية: {order.wheel_gift_name}\n"
        
        content += f"المبلغ النهائي: {order.final_amount} شيكل\n"
        content += f"طريقة الدفع: {order.get_payment_method_display()}\n"
        content += "\n\n"
        
        return content
    
    @staticmethod
    def _generate_standard_receipt_content(order):
        """Generate standard receipt content for regular printers"""
        content = f"""
رقم الطلب: {order.order_id}
التاريخ: {order.created_at.strftime('%d/%m/%Y %H:%M')}

العميل: {order.customer.full_name}
الهاتف: {order.customer.phone}
العنوان: {order.customer.get_full_address()}

{'-'*16}
المنتجات:
{'-'*16}
"""
        
        for item in order.items.all():
            color_info = f" - {item.color.name}" if item.color else ""
            content += f"""
{item.product.name}{color_info}
المقاس: {item.size} | الكمية: {item.quantity}
السعر: {item.price} شيكل
"""
        
        content += f"""
{'-'*16}
المجموع: {order.total_amount} شيكل"""

        # Add wheel prizes only if they exist
        wheel_info = []
        if order.discount_amount > 0:
            wheel_info.append(f"خصم: {order.discount_amount} شيكل")
        
        if order.wheel_free_shipping:
            wheel_info.append("شحن مجاني")
        
        if order.wheel_gift_name:
            wheel_info.append(f"هدية: {order.wheel_gift_name}")
        
        if wheel_info:
            content += f"""
جوائز العجلة: {' | '.join(wheel_info)}"""

        content += f"""
المبلغ النهائي: {order.final_amount} شيكل
طريقة الدفع: {order.get_payment_method_display()}

"""
        return content
    
    @staticmethod
    def _print_windows(content, print_method='auto'):
        """Print on Windows - improved for bill printers"""
        try:
            import tempfile
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                f.write(content)
                temp_path = f.name
            
            if getattr(settings, 'PRINT_DEBUG', False):
                logger.info(f"Created temp file: {temp_path}")
            
            # Get printer timeout from settings
            timeout = getattr(settings, 'PRINT_TIMEOUT', 30)
            
            try:
                # Method 1: Try direct printing with win32print if available and method allows
                if print_method in ['auto', 'direct']:
                    try:
                        import win32print
                        import win32api
                        
                        # Get default printer name
                        printer_name = win32print.GetDefaultPrinter()
                        logger.info(f"🖨️ Printing to: {printer_name}")
                        
                        # Direct print to default printer
                        win32api.ShellExecute(0, "print", temp_path, None, ".", 0)
                        logger.info(f"✅ Order printed successfully to {printer_name}")
                        return True
                        
                    except ImportError:
                        if getattr(settings, 'PRINT_DEBUG', False):
                            logger.info("win32print not available, trying alternative methods")
                    except Exception as direct_error:
                        logger.warning(f"Direct printing failed: {direct_error}, trying alternative method")
                
                # Method 2: Use notepad for printing (most compatible)
                if print_method in ['auto', 'notepad']:
                    try:
                        subprocess.run(['notepad', '/p', temp_path], check=True, timeout=timeout)
                        logger.info("✅ Order printed using Notepad")
                        return True
                    except Exception as notepad_error:
                        if getattr(settings, 'PRINT_DEBUG', False):
                            logger.warning(f"Notepad printing failed: {notepad_error}")
                
                # Method 3: Use print command (final fallback)
                if print_method in ['auto', 'command']:
                    try:
                        subprocess.run(['print', temp_path], check=True, timeout=timeout)
                        logger.info("✅ Order printed using print command")
                        return True
                    except Exception as print_error:
                        logger.error(f"Print command failed: {print_error}")
                
                return False
            
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_path)
                    if getattr(settings, 'PRINT_DEBUG', False):
                        logger.info("Temp file cleaned up")
                except:
                    pass
                    
        except ImportError:
            logger.warning("win32print not available, using fallback method")
            # Fallback to original method if win32print not available
            return PrintService._print_windows_fallback(content)
        except Exception as e:
            logger.error(f"Windows printing error: {str(e)}")
            return PrintService._print_windows_fallback(content)
    
    @staticmethod
    def _print_windows_fallback(content):
        """Fallback Windows printing method"""
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                f.write(content)
                temp_path = f.name
            
            # Use print command
            subprocess.run(['print', temp_path], check=True, timeout=30)
            
            # Clean up
            try:
                os.unlink(temp_path)
            except:
                pass
                
            logger.info("✅ Order printed using fallback method")
            return True
            
        except Exception as e:
            logger.error(f"Fallback printing error: {str(e)}")
            return False
    
    @staticmethod
    def _print_macos(content):
        """Print on macOS"""
        try:
            # Use lpr command
            process = subprocess.Popen(['lpr'], stdin=subprocess.PIPE, text=True)
            process.communicate(input=content)
            return process.returncode == 0
        except Exception as e:
            logger.error(f"macOS printing error: {str(e)}")
            return False
    
    @staticmethod
    def _print_linux(content):
        """Print on Linux"""
        try:
            # Use lpr command
            process = subprocess.Popen(['lpr'], stdin=subprocess.PIPE, text=True)
            process.communicate(input=content)
            return process.returncode == 0
        except Exception as e:
            logger.error(f"Linux printing error: {str(e)}")
            return False
    
    @staticmethod
    def _print_thermal(content):
        """Print directly to thermal printer (U80II)"""
        try:
            import serial
            import time
            
            # Get thermal printer settings
            printer_port = getattr(settings, 'THERMAL_PRINTER_PORT', 'auto')
            encoding = getattr(settings, 'THERMAL_PRINTER_ENCODING', 'cp720')
            
            if getattr(settings, 'PRINT_DEBUG', False):
                logger.info(f"Attempting thermal print to port: {printer_port}")
            
            # Auto-detect thermal printer port if needed
            if printer_port == 'auto':
                printer_port = PrintService._detect_thermal_printer()
                if not printer_port:
                    logger.warning("No thermal printer detected, falling back to Windows printing")
                    return PrintService._print_windows(content, 'notepad')
            
            # Try to connect to thermal printer
            try:
                # Common settings for U80II thermal printer
                ser = serial.Serial(
                    port=printer_port,
                    baudrate=9600,  # Standard for U80II
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=1
                )
                
                if getattr(settings, 'PRINT_DEBUG', False):
                    logger.info(f"Connected to thermal printer on {printer_port}")
                
                # Encode content for thermal printer
                try:
                    encoded_content = content.encode(encoding)
                except UnicodeEncodeError:
                    # Fallback to utf-8 if cp720 fails
                    encoded_content = content.encode('utf-8', errors='replace')
                    logger.warning("Using UTF-8 encoding as fallback for thermal printer")
                
                # Send to printer
                ser.write(encoded_content)
                ser.flush()
                time.sleep(0.5)  # Wait for printing to complete
                
                ser.close()
                
                logger.info("✅ Thermal printer job completed successfully")
                return True
                
            except serial.SerialException as e:
                logger.error(f"Serial connection error: {str(e)}")
                # Fallback to Windows printing
                logger.info("Falling back to Windows printing method")
                return PrintService._print_windows(content, 'notepad')
                
        except ImportError:
            logger.warning("pyserial not installed, cannot use direct thermal printing")
            # Fallback to Windows printing
            return PrintService._print_windows(content, 'notepad')
        except Exception as e:
            logger.error(f"Thermal printing error: {str(e)}")
            # Fallback to Windows printing
            return PrintService._print_windows(content, 'notepad')
    
    @staticmethod
    def _detect_thermal_printer():
        """Auto-detect thermal printer port"""
        try:
            import serial.tools.list_ports
            
            # Common port names for thermal printers
            common_ports = ['COM1', 'COM2', 'COM3', 'COM4', 'COM5']
            
            # Get all available ports
            available_ports = [port.device for port in serial.tools.list_ports.comports()]
            
            if getattr(settings, 'PRINT_DEBUG', False):
                logger.info(f"Available ports: {available_ports}")
            
            # Check common ports first
            for port in common_ports:
                if port in available_ports:
                    try:
                        # Test connection
                        test_ser = serial.Serial(port, 9600, timeout=1)
                        test_ser.close()
                        logger.info(f"Detected thermal printer on {port}")
                        return port
                    except:
                        continue
            
            # If no common port works, try the first available port
            if available_ports:
                first_port = available_ports[0]
                try:
                    test_ser = serial.Serial(first_port, 9600, timeout=1)
                    test_ser.close()
                    logger.info(f"Using first available port for thermal printer: {first_port}")
                    return first_port
                except:
                    pass
            
            logger.warning("No thermal printer port detected")
            return None
            
        except ImportError:
            logger.warning("pyserial not available for port detection")
            return None
        except Exception as e:
            logger.error(f"Error detecting thermal printer: {str(e)}")
            return None


class TranslationService:
    """Translation service using Libre Translate API"""
    
    @staticmethod
    def translate_text(text, source_lang, target_lang):
        """Translate text using Libre Translate API"""
        try:
            if source_lang == target_lang:
                return text
                
            url = settings.LIBRE_TRANSLATE_URL
            data = {
                'q': text,
                'source': source_lang,
                'target': target_lang
            }
            
            if settings.LIBRE_TRANSLATE_API_KEY:
                data['api_key'] = settings.LIBRE_TRANSLATE_API_KEY
            
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            return result.get('translatedText', text)
            
        except Exception as e:
            logger.error(f"Translation failed: {str(e)}")
            return text
    
    @staticmethod
    def get_language_direction(language_code):
        """Get text direction for language"""
        rtl_languages = ['ar', 'he', 'fa', 'ur']
        return 'rtl' if language_code in rtl_languages else 'ltr'


class CartService:
    """Cart management service"""
    
    @staticmethod
    def add_to_cart(request, product_id, size, color, quantity=1):
        """Add item to cart (session or database)"""
        try:
            from .models import Product, CartItem
            
            product = Product.objects.get(id=product_id, is_active=True)
            
            if request.user.is_authenticated:
                # Add to database cart
                cart_item, created = CartItem.objects.get_or_create(
                    user=request.user,
                    product=product,
                    size=size,
                    color=color,
                    defaults={'quantity': quantity}
                )
                
                if not created:
                    cart_item.quantity += quantity
                    cart_item.save()
                logger.info(f"Added to authenticated user cart: {product.name} x{quantity}")
            else:
                # Ensure session exists for anonymous users
                if not request.session.session_key:
                    request.session.create()
                
                # Add to session cart
                cart = request.session.get('cart', {})
                cart_key = f"{product_id}_{size}_{color}"
                
                if cart_key in cart:
                    cart[cart_key]['quantity'] += quantity
                else:
                    cart[cart_key] = {
                        'product_id': int(product_id),
                        'name': product.name,
                        'brand': product.brand.name,
                        'price': str(product.price),
                        'size': size,
                        'color': color,
                        'quantity': quantity,
                        'image': product.get_main_image().url if product.get_main_image() else None
                    }
                
                request.session['cart'] = cart
                request.session.modified = True
                # Force save the session
                request.session.save()
                logger.info(f"Added to session cart: {product.name} x{quantity}, Session key: {request.session.session_key}")
            
            return True
            
        except Exception as e:
            logger.error(f"Add to cart failed: {str(e)}")
            return False
    
    @staticmethod
    def remove_from_cart(request, product_id, size):
        """Remove item from cart"""
        try:
            if request.user.is_authenticated:
                from .models import CartItem
                CartItem.objects.filter(
                    user=request.user,
                    product_id=product_id,
                    size=size
                ).delete()
            else:
                cart = request.session.get('cart', {})
                cart_key = f"{product_id}_{size}"
                if cart_key in cart:
                    del cart[cart_key]
                    request.session['cart'] = cart
                    request.session.modified = True
            
            return True
            
        except Exception as e:
            logger.error(f"Remove from cart failed: {str(e)}")
            return False
    
    @staticmethod
    def get_cart_total(request):
        """Get cart total amount"""
        total = 0
        
        try:
            if request.user.is_authenticated:
                from .models import CartItem
                cart_items = CartItem.objects.filter(user=request.user)
                total = sum(item.get_total_price() for item in cart_items)
                logger.debug(f"Authenticated user cart total: {total} from {cart_items.count()} items")
            else:
                cart = request.session.get('cart', {})
                total = sum(float(item['price']) * item['quantity'] for item in cart.values())
                logger.debug(f"Anonymous user cart total: {total} from session cart: {cart}")
        except Exception as e:
            logger.error(f"Error calculating cart total: {str(e)}")
            
        return total


class WheelService:
    """Wheel of Fortune service"""
    
    @staticmethod
    def can_spin_today(request):
        """Check if user can spin today"""
        from .models import WheelSpin
        from django.utils import timezone
        
        today = timezone.now().date()
        
        # Additional check: if session flag is set, user has already spun
        if request.session.get('wheel_spun_today', False):
            return False
        
        if request.user.is_authenticated:
            return not WheelSpin.objects.filter(
                user=request.user,
                spin_date__date=today
            ).exists()
        else:
            # For anonymous users, only check if session already exists
            # Don't create session just to check spin status
            session_key = request.session.session_key
            if not session_key:
                # No session exists yet, user hasn't spun
                return True
            
            return not WheelSpin.objects.filter(
                session_key=session_key,
                spin_date__date=today
            ).exists()
    
    @staticmethod
    def spin_wheel(request):
        """Spin the wheel and get result"""
        from .models import WheelSpin, WheelConfiguration, WheelAdminControl
        
        # Double-check if user can spin today before proceeding
        if not WheelService.can_spin_today(request):
            return {'success': False, 'message': 'لقد قمت بالدوران اليوم بالفعل'}
        
        try:
            # Ensure session exists for anonymous users
            if not request.user.is_authenticated and not request.session.session_key:
                request.session.create()
            
            selected_config = None
            
            # Check for active admin control first
            admin_control = WheelAdminControl.objects.filter(is_active=True).first()
            if admin_control:
                selected_config = admin_control.get_next_prize()
            
            # If no admin control or admin control returned None, use normal selection
            if not selected_config:
                # Use normal probability-based selection from winnable prizes only
                configs = WheelConfiguration.objects.filter(is_active=True, can_win=True, probability__gt=0)
                if not configs.exists():
                    # No winnable prizes, return no prize
                    discount_percentage = 0
                    prize_type = 'no_prize'
                else:
                    # Weighted random selection based on probability
                    total_probability = sum(config.probability for config in configs)
                    if total_probability == 0:
                        # All probabilities are 0, return no prize
                        discount_percentage = 0
                        prize_type = 'no_prize'
                    else:
                        random_num = random.randint(1, total_probability)
                        
                        current_prob = 0
                        for config in configs:
                            current_prob += config.probability
                            if random_num <= current_prob:
                                selected_config = config
                                break
            
            # Set result based on selected config
            if selected_config:
                discount_percentage = selected_config.value
                prize_type = selected_config.prize_type
            else:
                discount_percentage = 0
                prize_type = 'no_prize'
            
            # Create wheel spin record
            wheel_spin = WheelSpin.objects.create(
                user=request.user if request.user.is_authenticated else None,
                session_key=request.session.session_key if not request.user.is_authenticated else None,
                discount_percentage=discount_percentage
            )
            
            # Set session variable for discount if won
            if discount_percentage > 0:
                request.session['wheel_discount'] = discount_percentage
                request.session['wheel_discount_date'] = timezone.now().date().isoformat()
            
            return {
                'success': True,
                'discount_percentage': discount_percentage,
                'prize_type': prize_type,
                'selected_config_id': selected_config.id if selected_config else None,
                'selected_config_name': selected_config.name if selected_config else None,
                'message': f'تهانينا! لقد حصلت على خصم {discount_percentage}%' if discount_percentage > 0 else 'حظ أوفر في المرة القادمة!'
            }
            
        except Exception as e:
            logger.error(f"Error in spin_wheel: {e}")
            return {'success': False, 'message': 'حدث خطأ أثناء دوران العجلة'}
    
    @staticmethod
    def get_available_discount(request):
        """Get available wheel discount for user"""
        from .models import WheelSpin
        
        if request.user.is_authenticated:
            wheel_spin = WheelSpin.objects.filter(
                user=request.user,
                is_used=False
            ).first()
        else:
            session_key = request.session.session_key
            if not session_key:
                return 0
            
            wheel_spin = WheelSpin.objects.filter(
                session_key=session_key,
                is_used=False
            ).first()
        
        return wheel_spin.discount_percentage if wheel_spin else 0


class EmailService:
    """Email service for notifications"""
    
    @staticmethod
    def send_order_confirmation(order):
        """Send order confirmation email"""
        try:
            if not order.customer.email:
                return False
            
            subject = f"تأكيد طلب #{order.order_id} - AL-QATHIFI"
            
            html_message = render_to_string('emails/order_confirmation.html', {
                'order': order,
                'customer': order.customer
            })
            
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [order.customer.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Email sending failed for order {order.order_id}: {str(e)}")
            return False 