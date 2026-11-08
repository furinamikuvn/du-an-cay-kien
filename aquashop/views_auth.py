# ==============================================================================
# AQUASHOP - XỬ LÝ XÁC THỰC, TÀI KHOẢN & VẬN ĐƠN (AUTH & PROFILES VIEWS)
# ==============================================================================
# Tệp này phụ trách toàn bộ phân hệ người dùng và quản lý đơn hàng cá nhân:
# 1. register_view: Đăng ký thành viên mới, mã hóa mật khẩu và tạo hồ sơ UserProfile.
# 2. login_view: Đăng nhập hệ thống, kiểm tra phân quyền (Admin / Staff / Khách hàng).
# 3. logout_view: Đăng xuất tài khoản và hủy phiên làm việc (Session).
# 4. profile_view: Xem và cập nhật thông tin cá nhân (SĐT, địa chỉ nhận hàng).
# 5. change_password_view: Đổi mật khẩu tài khoản và đồng bộ lại phiên làm việc an toàn.
# 6. order_tracking_view: Tra cứu đơn hàng công khai theo mã vận đơn hoặc số điện thoại.
# 7. my_orders_view: Xem danh sách và lọc toàn bộ lịch sử đơn hàng của cá nhân.
# ==============================================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from .models import Order, UserProfile
from .forms_auth import RegisterForm, LoginForm, ProfileUpdateForm, OrderTrackingForm, CustomPasswordChangeForm


# ------------------------------------------------------------------------------
# 1. ĐĂNG KÝ TÀI KHOẢN THÀNH VIÊN (REGISTER)
# ------------------------------------------------------------------------------
def register_view(request):
    """
    Xử lý đăng ký tài khoản khách hàng mới.
    
    Quy trình hoạt động:
    - Bước 1: Kiểm tra nếu người dùng đã đăng nhập thì tự động chuyển hướng về trang cá nhân.
    - Bước 2: Khi người dùng gửi form POST:
      + Kiểm tra tính hợp lệ của dữ liệu (tên đăng nhập không trùng, mật khẩu khớp).
      + Lưu User mới vào bảng auth_user (mật khẩu được tự động băm an toàn qua PBKDF2).
      + Tự động kích hoạt đăng nhập cho người dùng mới qua login(request, user).
      + Chuyển hướng người dùng về trang đích mong muốn (next) hoặc trang hồ sơ cá nhân.
    """
    if request.user.is_authenticated:
        return redirect('profile')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            # Lưu tài khoản và băm mật khẩu bảo mật
            user = form.save()
            # Tự động đăng nhập phiên làm việc ngay sau khi tạo tài khoản
            login(request, user)
            display_name = user.get_full_name() or user.username
            messages.success(request, f"Chào mừng {display_name}! Tài khoản của bạn đã được khởi tạo thành công.")
            
            # Điều hướng nếu có tham số next trên URL
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


# ------------------------------------------------------------------------------
# 2. ĐĂNG NHẬP HỆ THỐNG (LOGIN)
# ------------------------------------------------------------------------------
def login_view(request):
    """
    Xử lý đăng nhập tài khoản và phân luồng người dùng theo vai trò.
    
    Quy trình hoạt động:
    - Bước 1: Nhận username và password từ form gửi lên.
    - Bước 2: Sử dụng authenticate() của Django để kiểm tra tính chính xác của mật khẩu.
    - Bước 3: Nếu đúng, kiểm tra tài khoản có bị khóa không (is_active).
    - Bước 4: Gọi login() tạo phiên session đăng nhập.
    - Bước 5: Phân luồng chuyển hướng thông minh:
      + Nếu là Admin / Staff: Điều hướng về trang quản trị (/admin/).
      + Nếu là Khách hàng thường: Điều hướng về trang hồ sơ cá nhân hoặc trang đích (next_url).
    """
    if request.user.is_authenticated:
        return redirect('profile')

    next_url = request.GET.get('next') or request.POST.get('next')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            # Xác thực thông tin đăng nhập
            user = authenticate(request, username=username, password=password)

            if user is not None:
                if not user.is_active:
                    messages.error(request, "Tài khoản của bạn hiện đang bị tạm khóa. Vui lòng liên hệ bộ phận hỗ trợ.")
                else:
                    # Đăng nhập và lưu vào session
                    login(request, user)
                    display_name = user.get_full_name() or user.username
                    messages.success(request, f"Đăng nhập thành công! Chào mừng {display_name} trở lại.")

                    # Ưu tiên chuyển hướng về trang yêu cầu trước đó
                    if next_url:
                        return redirect(next_url)

                    # Phân luồng điều hướng theo vai trò (RBAC)
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


# ------------------------------------------------------------------------------
# 3. ĐĂNG XUẤT HỆ THỐNG (LOGOUT)
# ------------------------------------------------------------------------------
def logout_view(request):
    """
    Đăng xuất an toàn: Xóa toàn bộ dữ liệu phiên làm việc (Session)
    và điều hướng người dùng về trang đăng nhập kèm thông báo.
    """
    logout(request)
    messages.info(request, "Bạn đã đăng xuất tài khoản an toàn.")
    return redirect('login')


# ------------------------------------------------------------------------------
# 4. HỒ SƠ TÀI KHOẢN CÁ NHÂN (PROFILE)
# ------------------------------------------------------------------------------
@login_required(login_url='login')
def profile_view(request):
    """
    Xem và cập nhật thông tin tài khoản cá nhân.
    - Yêu cầu bắt buộc phải đăng nhập (@login_required).
    - Cho phép cập nhật Họ tên, Email, Số điện thoại và Địa chỉ giao hàng mặc định.
    - Thống kê tổng số đơn hàng đã đặt và tổng chi tiêu thực tế của người dùng.
    """
    user = request.user
    # Lấy hoặc tự động tạo hồ sơ UserProfile nếu chưa tồn tại
    profile, _ = UserProfile.objects.get_or_create(user=user, defaults={'role': 'customer'})

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, user=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Cập nhật hồ sơ thông tin cá nhân thành công!")
            return redirect('profile')
    else:
        # Nạp dữ liệu ban đầu vào form để hiển thị cho người dùng chỉnh sửa
        initial_data = {
            'full_name': user.get_full_name() or user.username,
            'email': user.email,
            'phone': profile.phone,
            'address': profile.address,
        }
        form = ProfileUpdateForm(initial=initial_data, user=user)

    # Lấy danh sách 5 đơn hàng gần nhất của người dùng
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


# ------------------------------------------------------------------------------
# 5. ĐỔI MẬT KHẨU TÀI KHOẢN (CHANGE PASSWORD)
# ------------------------------------------------------------------------------
@login_required(login_url='login')
def change_password_view(request):
    """
    Xử lý đổi mật khẩu cho người dùng.
    - Kiểm tra mật khẩu cũ có đúng không.
    - Mật khẩu mới phải đủ độ dài và không trùng với mật khẩu cũ.
    - Dùng update_session_auth_hash() để người dùng không bị đăng xuất đột ngột sau khi đổi mật khẩu.
    """
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            # Đồng bộ lại phiên đăng nhập với mật khẩu mới để không bị văng session
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


# ------------------------------------------------------------------------------
# 6. TRA CỨU ĐƠN HÀNG CÔNG KHAI (ORDER TRACKING)
# ------------------------------------------------------------------------------
def order_tracking_view(request):
    """
    Tra cứu tiến trình vận đơn công khai: Khách hàng không cần đăng nhập vẫn tra cứu được.
    
    Cơ chế hoạt động:
    - Tìm kiếm theo mã vận đơn (order_code ví dụ: AQ-20261108-1603) hoặc số điện thoại đặt hàng.
    - Hiển thị danh sách sản phẩm cây trong đơn, tình trạng đóng gói bọc ẩm và lịch sử trạng thái:
      + Bước 1 (pending): Đơn mới nhận, đang chuyển giao kho kiểm kê sinh học.
      + Bước 2 (confirmed): Đã xác nhận đơn, chuẩn bị đóng gói rêu ẩm chuyên dụng.
      + Bước 3 (shipping): Đang vận chuyển xe lạnh / hỏa tốc.
      + Bước 4 (completed): Khách đã nhận cây tươi nguyên vẹn.
    """
    query = request.GET.get('q', '').strip()
    selected_code = request.GET.get('code', '').strip()

    orders_list = []
    selected_order = None
    has_searched = bool(query)

    form = OrderTrackingForm(initial={'search_query': query} if query else None)

    # Tìm kiếm theo mã đơn hoặc số điện thoại
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

    # Ánh xạ trạng thái sang bước tiến trình hiển thị trên thanh Progress Bar
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


# ------------------------------------------------------------------------------
# 7. LỊCH SỬ ĐƠN HÀNG CỦA TÔI (MY ORDERS)
# ------------------------------------------------------------------------------
@login_required(login_url='login')
def my_orders_view(request):
    """
    Hiển thị toàn bộ lịch sử đơn hàng của thành viên đã đăng nhập.
    - Hỗ trợ bộ lọc theo từng trạng thái (Tất cả, Đang xử lý, Đang giao, Đã giao, Đã hủy).
    - Thống kê nhanh số lượng đơn tương ứng cho từng trạng thái.
    """
    user = request.user
    status_filter = request.GET.get('status', '').strip()

    # Truy vấn toàn bộ đơn của user hiện tại, sắp xếp mới nhất lên đầu
    orders_qs = Order.objects.filter(user=user).prefetch_related('items__product').order_by('-created_at')

    # Thống kê số lượng đơn theo các trạng thái
    total_orders = orders_qs.count()
    pending_count = orders_qs.filter(status='pending').count()
    confirmed_count = orders_qs.filter(status='confirmed').count()
    shipping_count = orders_qs.filter(status='shipping').count()
    completed_count = orders_qs.filter(status='completed').count()
    cancelled_count = orders_qs.filter(status='cancelled').count()

    # Lọc đơn nếu người dùng chọn tab cụ thể
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
