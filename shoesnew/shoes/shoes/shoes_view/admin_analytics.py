"""
Analytics views for Admin Dashboard
"""

from django.contrib import admin
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, Count, Avg, Q, F
from django.db.models.functions import TruncMonth, TruncDay, TruncWeek
from django.utils import timezone
from datetime import datetime, timedelta
import json

# Import plotly components with error handling
try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.utils import PlotlyJSONEncoder
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    go = None
    px = None
    PlotlyJSONEncoder = None

from .models import Order, OrderItem, Product, Brand, Customer, WheelSpin, ContactMessage


def safe_chart_creation(chart_func, *args, **kwargs):
    """Safely create plotly charts with error handling"""
    try:
        if not PLOTLY_AVAILABLE:
            return None
        return chart_func(*args, **kwargs)
    except Exception as e:
        # Chart creation failed, return None
        return None


@login_required
@user_passes_test(lambda u: u.is_staff)
def analytics_dashboard(request):
    """Main analytics dashboard view"""
    
    # Get date range from query params or default to last 30 days
    days_range = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days_range)
    
    # Basic Statistics
    total_orders = Order.objects.filter(created_at__gte=start_date).count()
    total_revenue = Order.objects.filter(
        created_at__gte=start_date,
        status__in=['confirmed', 'shipped', 'delivered']
    ).aggregate(total=Sum('final_amount'))['total'] or 0
    
    total_customers = Customer.objects.filter(created_at__gte=start_date).count()
    
    # Average order value
    avg_order_value = Order.objects.filter(
        created_at__gte=start_date,
        status__in=['confirmed', 'shipped', 'delivered']
    ).aggregate(avg=Avg('final_amount'))['avg'] or 0
    
    # Top selling products
    top_products = OrderItem.objects.filter(
        order__created_at__gte=start_date,
        order__status__in=['confirmed', 'shipped', 'delivered']
    ).values('product__name', 'product__id').annotate(
        total_sold=Sum('quantity'),
        revenue=Sum(F('quantity') * F('price'))
    ).order_by('-total_sold')[:10]
    
    # Sales by brand
    brand_sales = OrderItem.objects.filter(
        order__created_at__gte=start_date,
        order__status__in=['confirmed', 'shipped', 'delivered']
    ).values('product__brand__name').annotate(
        total_revenue=Sum(F('quantity') * F('price'))
    ).order_by('-total_revenue')
    
    # Order status distribution
    order_status = Order.objects.filter(
        created_at__gte=start_date
    ).values('status').annotate(
        count=Count('id')
    )
    
    # Revenue over time (daily for last 30 days, monthly for longer periods)
    if days_range <= 30:
        revenue_over_time = Order.objects.filter(
            created_at__gte=start_date,
            status__in=['confirmed', 'shipped', 'delivered']
        ).annotate(
            date=TruncDay('created_at')
        ).values('date').annotate(
            revenue=Sum('final_amount'),
            orders=Count('id')
        ).order_by('date')
    else:
        revenue_over_time = Order.objects.filter(
            created_at__gte=start_date,
            status__in=['confirmed', 'shipped', 'delivered']
        ).annotate(
            date=TruncMonth('created_at')
        ).values('date').annotate(
            revenue=Sum('final_amount'),
            orders=Count('id')
        ).order_by('date')
    
    # Initialize chart variables
    revenue_chart = None
    brand_chart = None
    products_chart = None
    status_chart = None
    
    # Create Charts with error handling
    if PLOTLY_AVAILABLE:
        try:
            # 1. Revenue Chart
            revenue_dates = [item['date'].strftime('%Y-%m-%d') for item in revenue_over_time]
            revenue_values = [float(item['revenue'] or 0) for item in revenue_over_time]
            order_counts = [int(item['orders']) for item in revenue_over_time]
            
            revenue_chart = go.Figure()
            revenue_chart.add_trace(go.Scatter(
                x=list(revenue_dates),  # Convert to list to avoid pandas detection
                y=list(revenue_values),  # Convert to list to avoid pandas detection
                mode='lines+markers',
                name='الإيرادات',
                line=dict(color='#28a745', width=3),
                fill='tozeroy',
                fillcolor='rgba(40, 167, 69, 0.1)'
            ))
            
            revenue_chart.add_trace(go.Bar(
                x=list(revenue_dates),  # Convert to list to avoid pandas detection
                y=list(order_counts),  # Convert to list to avoid pandas detection
                name='عدد الطلبات',
                yaxis='y2',
                marker_color='rgba(52, 152, 219, 0.6)'
            ))
            
            revenue_chart.update_layout(
                title='الإيرادات وعدد الطلبات',
                xaxis_title='التاريخ',
                yaxis_title='الإيرادات (₪)',
                yaxis2=dict(
                    title='عدد الطلبات',
                    overlaying='y',
                    side='right'
                ),
                hovermode='x unified',
                template='plotly_white',
                font=dict(family="Arial", size=14),
                height=400
            )
            
            # 2. Brand Sales Pie Chart
            brand_names = [str(item['product__brand__name']) for item in brand_sales]
            brand_revenues = [float(item['total_revenue'] or 0) for item in brand_sales]
            
            if brand_names and brand_revenues:
                brand_chart = px.pie(
                    values=list(brand_revenues),  # Convert to list
                    names=list(brand_names),  # Convert to list
                    title='المبيعات حسب العلامة التجارية',
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                brand_chart.update_traces(textposition='inside', textinfo='percent+label')
                brand_chart.update_layout(height=400)
            
            # 3. Top Products Bar Chart
            product_names = [str(item['product__name'][:30] + '...' if len(item['product__name']) > 30 else item['product__name']) 
                             for item in top_products[:10]]
            product_quantities = [int(item['total_sold']) for item in top_products[:10]]
            product_revenues = [float(item['revenue'] or 0) for item in top_products[:10]]
            
            if product_names:
                products_chart = go.Figure(data=[
                    go.Bar(name='الكمية المباعة', x=list(product_names), y=list(product_quantities), yaxis='y2', 
                           marker_color='lightblue'),
                    go.Bar(name='الإيرادات', x=list(product_names), y=list(product_revenues), 
                           marker_color='darkgreen')
                ])
                
                products_chart.update_layout(
                    title='أفضل 10 منتجات مبيعاً',
                    xaxis_title='المنتج',
                    yaxis_title='الإيرادات (₪)',
                    yaxis2=dict(
                        title='الكمية',
                        overlaying='y',
                        side='right'
                    ),
                    barmode='group',
                    template='plotly_white',
                    height=400
                )
            
            # 4. Order Status Chart
            status_labels = {
                'pending': 'قيد الانتظار',
                'confirmed': 'مؤكد',
                'shipped': 'تم الشحن',
                'delivered': 'تم التسليم',
                'cancelled': 'ملغي'
            }
            
            status_names = [str(status_labels.get(item['status'], item['status'])) for item in order_status]
            status_counts = [int(item['count']) for item in order_status]
            
            if status_names:
                status_chart = go.Figure(data=[
                    go.Bar(x=list(status_names), y=list(status_counts), 
                           marker_color=['#ffc107', '#28a745', '#17a2b8', '#6c757d', '#dc3545'])
                ])
                
                status_chart.update_layout(
                    title='توزيع حالات الطلبات',
                    xaxis_title='الحالة',
                    yaxis_title='عدد الطلبات',
                    template='plotly_white',
                    height=300
                )
                
        except Exception as e:
            # Charts will remain None if there's an error
            pass
    
    # Additional metrics
    # Low stock products
    low_stock_products = Product.objects.filter(
        is_active=True,
        stock_quantity__lte=10
    ).order_by('stock_quantity')[:10]
    
    # Recent wheel spins
    recent_spins = WheelSpin.objects.filter(
        spin_date__gte=start_date
    ).count()
    
    # Unread messages
    unread_messages = ContactMessage.objects.filter(is_read=False).count()
    
    # Customer cities distribution
    city_distribution = Customer.objects.values('city').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    context = {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_customers': total_customers,
        'avg_order_value': avg_order_value,
        'revenue_chart': json.dumps(revenue_chart, cls=PlotlyJSONEncoder) if revenue_chart and PLOTLY_AVAILABLE else None,
        'brand_chart': json.dumps(brand_chart, cls=PlotlyJSONEncoder) if brand_chart and PLOTLY_AVAILABLE else None,
        'products_chart': json.dumps(products_chart, cls=PlotlyJSONEncoder) if products_chart and PLOTLY_AVAILABLE else None,
        'status_chart': json.dumps(status_chart, cls=PlotlyJSONEncoder) if status_chart and PLOTLY_AVAILABLE else None,
        'low_stock_products': low_stock_products,
        'recent_spins': recent_spins,
        'unread_messages': unread_messages,
        'city_distribution': city_distribution,
        'days_range': days_range,
        'start_date': start_date,
        'plotly_available': PLOTLY_AVAILABLE
    }
    
    return render(request, 'admin/analytics_dashboard.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def sales_report(request):
    """Detailed sales report view"""
    
    # Get date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    else:
        start_date = timezone.now().date() - timedelta(days=30)
    
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    else:
        end_date = timezone.now().date()
    
    # Get orders in date range
    orders = Order.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date,
        status__in=['confirmed', 'shipped', 'delivered']
    )
    
    # Summary statistics
    total_revenue = orders.aggregate(total=Sum('final_amount'))['total'] or 0
    total_orders = orders.count()
    total_items_sold = OrderItem.objects.filter(
        order__in=orders
    ).aggregate(total=Sum('quantity'))['total'] or 0
    
    # Calculate average order value
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    # Daily breakdown
    daily_sales = orders.annotate(
        date=TruncDay('created_at')
    ).values('date').annotate(
        revenue=Sum('final_amount'),
        orders=Count('id'),
        items=Count('items__id')
    ).order_by('-date')
    
    # Product performance
    product_performance = OrderItem.objects.filter(
        order__in=orders
    ).values(
        'product__name',
        'product__brand__name'
    ).annotate(
        quantity_sold=Sum('quantity'),
        revenue=Sum(F('quantity') * F('price'))
    ).order_by('-revenue')
    
    # Payment method breakdown
    payment_breakdown = orders.values('payment_method').annotate(
        count=Count('id'),
        revenue=Sum('final_amount')
    )
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'total_items_sold': total_items_sold,
        'avg_order_value': avg_order_value,
        'daily_sales': daily_sales,
        'product_performance': product_performance[:20],
        'payment_breakdown': payment_breakdown,
    }
    
    return render(request, 'admin/sales_report.html', context) 