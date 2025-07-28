"""
Forms for AL-QATHIFI Men's Shoe Store
"""

import random
import os
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.conf import settings
from .models import ContactMessage, Order


class InteractiveCaptchaField(forms.CharField):
    """Modern interactive captcha field with checkbox and image challenges"""
    
    def __init__(self, *args, **kwargs):
        # Generate a random challenge
        self.challenge_type = random.choice(['images', 'text'])
        self.challenge_id = random.randint(1000, 9999)
        
        if self.challenge_type == 'images':
            self.challenge_text = random.choice([
                'اختر جميع الصور التي تحتوي على أحذية',
                'اختر جميع الصور التي تحتوي على سيارات',
                'اختر جميع الصور التي تحتوي على إشارات مرور',
                'اختر جميع الصور التي تحتوي على أشخاص'
            ])
        else:
            num1 = random.randint(1, 10)
            num2 = random.randint(1, 10)
            self.challenge_text = f'كم يساوي {num1} + {num2}؟'
            self.correct_answer = str(num1 + num2)
        
        kwargs['widget'] = forms.HiddenInput()
        kwargs['required'] = False
        super().__init__(*args, **kwargs)
    
    def clean(self, value):
        # This will be validated via JavaScript on the frontend
        return value


class UserRegistrationForm(UserCreationForm):
    """User registration form without email requirement"""
    
    username = forms.CharField(
        label='اسم المستخدم',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'أدخل اسم المستخدم',
            'dir': 'rtl'
        })
    )
    
    password1 = forms.CharField(
        label='كلمة المرور',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'أدخل كلمة المرور',
            'dir': 'rtl'
        })
    )
    
    password2 = forms.CharField(
        label='تأكيد كلمة المرور',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'أعد إدخال كلمة المرور',
            'dir': 'rtl'
        })
    )
    
    captcha = InteractiveCaptchaField()
    
    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('اسم المستخدم موجود بالفعل')
        return username
    
    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user


class CustomLoginForm(AuthenticationForm):
    """Custom login form with captcha"""
    
    username = forms.CharField(
        label='اسم المستخدم',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'أدخل اسم المستخدم',
            'dir': 'rtl'
        })
    )
    
    password = forms.CharField(
        label='كلمة المرور',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'أدخل كلمة المرور',
            'dir': 'rtl'
        })
    )
    
    captcha = InteractiveCaptchaField()


class ContactForm(forms.ModelForm):
    """Contact form with captcha"""
    
    name = forms.CharField(
        label='الاسم',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'أدخل اسمك الكامل',
            'dir': 'rtl'
        })
    )
    

    
    phone = forms.CharField(
        label='رقم الهاتف',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+970591234567',
            'dir': 'ltr'
        }),
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message='يرجى إدخال رقم هاتف صحيح'
        )]
    )
    
    subject = forms.CharField(
        label='الموضوع',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'موضوع الرسالة',
            'dir': 'rtl'
        })
    )
    
    message = forms.CharField(
        label='الرسالة',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'اكتب رسالتك هنا...',
            'rows': 5,
            'dir': 'rtl'
        })
    )
    
    captcha = InteractiveCaptchaField()
    
    class Meta:
        model = ContactMessage
        fields = ['name', 'phone', 'subject', 'message']
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone and not phone.startswith('+'):
            phone = '+970' + phone.lstrip('0')
        return phone


class CheckoutForm(forms.Form):
    """Checkout form with captcha"""
    
    full_name = forms.CharField(
        label='الاسم الكامل',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'أدخل اسمك الكامل',
            'dir': 'rtl'
        })
    )
    

    
    phone = forms.CharField(
        label='رقم الهاتف',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+970591234567',
            'dir': 'ltr'
        }),
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message='يرجى إدخال رقم هاتف صحيح'
        )]
    )
    
    address = forms.CharField(
        label='العنوان',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'أدخل عنوانك الكامل',
            'dir': 'rtl'
        })
    )
    
    city = forms.CharField(
        label='المدينة',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'أدخل اسم المدينة',
            'dir': 'rtl'
        })
    )
    
    notes = forms.CharField(
        label='ملاحظات إضافية',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'أي ملاحظات إضافية...',
            'rows': 3,
            'dir': 'rtl'
        })
    )
    
    payment_method = forms.ChoiceField(
        label='طريقة الدفع',
        choices=[
            ('cash', 'الدفع عند الاستلام'),
        ],
        initial='cash',
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        })
    )
    
    captcha = InteractiveCaptchaField()
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone and not phone.startswith('+'):
            phone = '+970' + phone.lstrip('0')
        return phone 