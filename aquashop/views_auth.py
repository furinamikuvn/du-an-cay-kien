from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from .models import Order, UserProfile
from .forms_auth import RegisterForm, LoginForm, ProfileUpdateForm, OrderTrackingForm, CustomPasswordChangeForm


def register_view(request):
    """
    Xử lý đăng ký tài khoản khách hàng mới.
    Tự động tạo User, UserProfile với role='customer' và tự động đăng nhập.
    """
    if request.user.is_authenticated:
        return redirect('profile')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            display_name = user.get_full_name() or user.username
            messages.success(request, f"Chào mừng {display_name}! Tài khoản của bạn đã được khởi tạo thành công.")
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('profile')
    else:
        form = RegisterForm()

    context = {
        'form': form,
        'title': 'Đăng Ký Tài Khoản Thành Viên',
    }
    return render(request, 'aquashop/auth/register.html', context)


def login_view(request):
    """
    Xử lý đăng nhập tài khoản.
    Điều hướng phân quyền: Staff/Admin về trang quản trị tương ứng, Khách hàng về trang cá nhân hoặc URL đích.
    """
    if request.user.is_authenticated:
        return redirect('profile')

    next_url = request.GET.get('next') or request.POST.get('next')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)

            if user is not None:
                if not user.is_active:
                    messages.error(request, "Tài khoản của bạn hiện đang bị tạm khóa. Vui lòng liên hệ bộ phận hỗ trợ.")
                else:
                    login(request, user)
                    display_name = user.get_full_name() or user.username
                    messages.success(request, f"Đăng nhập thành công! Chào mừng {display_name} trở lại.")

                    if next_url:
                        return redirect(next_url)

                    # Phân luồng điều hướng theo vai trò
                    if user.is_staff or user.is_superuser:
                        return redirect('/admin/')
                    
                    profile = getattr(user, 'profile', None)
                    if profile and profile.role in ['staff', 'admin']:
                        return redirect('/admin/')

                    return redirect('profile')
            else:
                messages.error(request, "Tên đăng nhập hoặc mật khẩu không chính xác. Vui lòng kiểm tra lại.")
    else:
        form = LoginForm()

    context = {
        'form': form,
        'next': next_url,
        'title': 'Đăng Nhập Hệ Thống',
    }
    return render(request, 'aquashop/auth/login.html', context)


def logout_view(request):
    """
    Đăng xuất an toàn người dùng khỏi phiên làm việc.
    """
    logout(request)
    messages.info(request, "Bạn đã đăng xuất tài khoản an toàn.")
    return redirect('login')


@login_required(login_url='login')
def profile_view(request):
    """
    Xem và cập nhật thông tin tài khoản người dùng (@login_required).
    Hiển thị thông tin hồ sơ và danh sách các đơn hàng gần đây của khách.
    """
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user, defaults={'role': 'customer'})

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, user=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Cập nhật hồ sơ thông tin cá nhân thành công!")
            return redirect('profile')
    else:
        initial_data = {
            'full_name': user.get_full_name() or user.username,
            'email': user.email,
            'phone': profile.phone,
            'address': profile.address,
        }
        form = ProfileUpdateForm(initial=initial_data, user=user)

    # Đơn hàng gần nhất của người dùng
    user_orders = Order.objects.filter(user=user).prefetch_related('items__product').order_by('-created_at')
    recent_orders = user_orders[:5]
    total_orders_count = user_orders.count()
    completed_orders = user_orders.filter(status='completed')
    total_spent = completed_orders.aggregate(total=Sum('total_amount'))['total'] or 0

    password_form = CustomPasswordChangeForm(user=user)

    context = {
        'form': form,
        'password_form': password_form,
        'profile': profile,
        'recent_orders': recent_orders,
        'total_orders_count': total_orders_count,
        'completed_orders_count': completed_orders.count(),
        'total_spent': total_spent,
        'title': 'Hồ Sơ Tài Khoản Cá Nhân',
    }
    return render(request, 'aquashop/auth/profile.html', context)


@login_required(login_url='login')
def change_password_view(request):
    """
    Xử lý đổi mật khẩu an toàn cho tài khoản thành viên.
    Sử dụng update_session_auth_hash để không làm gián đoạn phiên làm việc.
    """
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, "Đổi mật khẩu bảo mật thành công! Mật khẩu mới của bạn đã có hiệu lực.")
            return redirect('profile')
        else:
            messages.error(request, "Đổi mật khẩu thất bại. Vui lòng kiểm tra lại thông tin bên dưới.")
    else:
        form = CustomPasswordChangeForm(user=request.user)

    context = {
        'form': form,
        'title': 'Đổi Mật Khẩu Bảo Mật',
    }
    return render(request, 'aquashop/auth/change_password.html', context)


def order_tracking_view(request):
    """
    Tra cứu đơn hàng công khai không bắt buộc đăng nhập.
    Tìm kiếm bằng mã đơn hàng (order_code) hoặc số điện thoại (phone).
    Hiển thị chi tiết mặt hàng, trạng thái quy trình bọc ẩm - vận chuyển, và nhật ký tracking_note.
    """
    query = request.GET.get('q', '').strip()
    selected_code = request.GET.get('code', '').strip()

    orders_list = []
    selected_order = None
    has_searched = bool(query)

    form = OrderTrackingForm(initial={'search_query': query} if query else None)

    if query:
        orders_matched = Order.objects.filter(
            Q(order_code__iexact=query) | Q(phone__iexact=query)
        ).prefetch_related('items__product').order_by('-created_at')

        orders_list = list(orders_matched)

        if orders_list:
            if selected_code:
                for ord_item in orders_list:
                    if ord_item.order_code.lower() == selected_code.lower():
                        selected_order = ord_item
                        break
            if not selected_order:
                selected_order = orders_list[0]

    # Map trạng thái sang bước tiến trình
    status_step = 1
    if selected_order:
        st = selected_order.status
        if st == 'pending':
            status_step = 1
        elif st == 'confirmed':
            status_step = 2
        elif st == 'shipping':
            status_step = 3
        elif st == 'completed':
            status_step = 4
        elif st == 'cancelled':
            status_step = -1

    context = {
        'form': form,
        'query': query,
        'has_searched': has_searched,
        'orders_list': orders_list,
        'order': selected_order,
        'status_step': status_step,
        'title': 'Tra Cứu Tiến Trình Đơn Hàng',
    }
    return render(request, 'aquashop/auth/order_tracking.html', context)


@login_required(login_url='login')
def my_orders_view(request):
    """
    Hiển thị danh sách toàn bộ lịch sử đơn hàng của người dùng đã đăng nhập.
    Hỗ trợ lọc theo trạng thái đơn hàng.
    """
    user = request.user
    status_filter = request.GET.get('status', '').strip()

    orders_qs = Order.objects.filter(user=user).prefetch_related('items__product').order_by('-created_at')

    # Thống kê nhanh
    total_orders = orders_qs.count()
    pending_count = orders_qs.filter(status='pending').count()
    confirmed_count = orders_qs.filter(status='confirmed').count()
    shipping_count = orders_qs.filter(status='shipping').count()
    completed_count = orders_qs.filter(status='completed').count()
    cancelled_count = orders_qs.filter(status='cancelled').count()

    if status_filter:
        orders_qs = orders_qs.filter(status=status_filter)

    context = {
        'orders': orders_qs,
        'status_filter': status_filter,
        'total_orders': total_orders,
        'pending_count': pending_count,
        'confirmed_count': confirmed_count,
        'shipping_count': shipping_count,
        'completed_count': completed_count,
        'cancelled_count': cancelled_count,
        'title': 'Lịch Sử Đơn Đặt Hàng Của Tôi',
    }
    return render(request, 'aquashop/auth/my_orders.html', context)
