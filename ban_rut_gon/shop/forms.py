# ==============================================================================
# CÁC LỚP BIỂU MẪU NHẬP LIỆU (SHOP/FORMS.PY)
# ==============================================================================
# Tệp này chứa các Form kiểm tra tính hợp lệ của dữ liệu người dùng gửi lên:
# 1. CheckoutForm: Form điền thông tin người nhận khi đặt mua hàng.
# 2. RegisterForm: Form đăng ký tài khoản khách hàng mới.
# 3. LoginForm: Form đăng nhập vào hệ thống.
# 4. ReviewForm: Form gửi đánh giá và nhận xét sản phẩm.
# 5. OrderTrackingForm: Form tra cứu đơn hàng bằng mã đơn hoặc số điện thoại.
# ==============================================================================

from django import forms
from django.contrib.auth.models import User
from .models import Order, ProductReview

# ------------------------------------------------------------------------------
# 1. BIỂU MẪU ĐẶT HÀNG (CHECKOUT FORM)
# ------------------------------------------------------------------------------
class CheckoutForm(forms.Form):
    """
    Form thu thập thông tin giao hàng của khách hàng tại trang Thanh toán.
    """
    customer_name = forms.CharField(
        max_length=150,
        required=True,
        label="Họ và tên người nhận",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-slate-300 rounded text-sm focus:outline-none focus:border-[#7AA88B]',
            'placeholder': 'Ví dụ: Nguyễn Văn A'
        })
    )
    email = forms.EmailField(
        required=True,
        label="Hộp thư điện tử (Email)",
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border border-slate-300 rounded text-sm focus:outline-none focus:border-[#7AA88B]',
            'placeholder': 'nguyenvana@gmail.com'
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=True,
        label="Số điện thoại nhận hàng",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-slate-300 rounded text-sm focus:outline-none focus:border-[#7AA88B]',
            'placeholder': '0901234567'
        })
    )
    shipping_address = forms.CharField(
        required=True,
        label="Địa chỉ giao hàng chi tiết",
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'w-full px-3 py-2 border border-slate-300 rounded text-sm focus:outline-none focus:border-[#7AA88B]',
            'placeholder': 'Số nhà, tên đường, phường/xã, quận/huyện, tỉnh/thành phố...'
        })
    )
    customer_note = forms.CharField(
        required=False,
        label="Ghi chú thêm cho người bán (nếu có)",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-slate-300 rounded text-sm focus:outline-none focus:border-[#7AA88B]',
            'placeholder': 'Ví dụ: Giao hàng vào giờ hành chính...'
        })
    )


# ------------------------------------------------------------------------------
# 2. BIỂU MẪU ĐĂNG KÝ THÀNH VIÊN (REGISTER FORM)
# ------------------------------------------------------------------------------
class RegisterForm(forms.ModelForm):
    """
    Form đăng ký tài khoản khách hàng mới vào bảng User của Django.
    """
    password = forms.CharField(
        label="Mật khẩu",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-slate-300 rounded text-sm focus:outline-none focus:border-[#7AA88B]',
            'placeholder': 'Nhập mật khẩu an toàn'
        })
    )
    confirm_password = forms.CharField(
        label="Xác nhận mật khẩu",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-slate-300 rounded text-sm focus:outline-none focus:border-[#7AA88B]',
            'placeholder': 'Nhập lại mật khẩu ở trên'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'email']
        labels = {
            'username': 'Tên đăng nhập',
            'first_name': 'Họ và tên hiển thị',
            'email': 'Email liên hệ',
        }
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-slate-300 rounded text-sm focus:outline-none focus:border-[#7AA88B]',
                'placeholder': 'Nhập tên đăng nhập viết liền không dấu'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-slate-300 rounded text-sm focus:outline-none focus:border-[#7AA88B]',
                'placeholder': 'Nhập họ và tên của bạn'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-3 py-2 border border-slate-300 rounded text-sm focus:outline-none focus:border-[#7AA88B]',
                'placeholder': 'email@example.com'
            }),
        }

    def clean_username(self):
        # Kiểm tra xem tên đăng nhập đã có ai dùng chưa
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Tên đăng nhập này đã có người sử dụng. Vui lòng chọn tên khác.")
        return username

    def clean(self):
        # Kiểm tra 2 ô mật khẩu có khớp nhau không
        cleaned_data = super().clean()
        pwd = cleaned_data.get('password')
        confirm_pwd = cleaned_data.get('confirm_password')
        if pwd and confirm_pwd and pwd != confirm_pwd:
            raise forms.ValidationError("Mật khẩu xác nhận không trùng khớp!")
        return cleaned_data

    def save(self, commit=True):
        # Mã hóa mật khẩu an toàn trước khi lưu vào CSDL
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


# ------------------------------------------------------------------------------
# 3. BIỂU MẪU ĐĂNG NHẬP (LOGIN FORM)
# ------------------------------------------------------------------------------
class LoginForm(forms.Form):
    username = forms.CharField(
        label="Tên đăng nhập",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-slate-300 rounded text-sm focus:outline-none focus:border-[#7AA88B]',
            'placeholder': 'Nhập tên đăng nhập của bạn'
        })
    )
    password = forms.CharField(
        label="Mật khẩu",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-slate-300 rounded text-sm focus:outline-none focus:border-[#7AA88B]',
            'placeholder': 'Nhập mật khẩu'
        })
    )


# ------------------------------------------------------------------------------
# 4. BIỂU MẪU ĐÁNH GIÁ SẢN PHẨM (REVIEW FORM)
# ------------------------------------------------------------------------------
class ReviewForm(forms.ModelForm):
    class Meta:
        model = ProductReview
        fields = ['reviewer_name', 'rating', 'comment']
        labels = {
            'reviewer_name': 'Họ và tên của bạn',
            'rating': 'Đánh giá số sao',
            'comment': 'Nội dung nhận xét về chất lượng cây',
        }
        widgets = {
            'reviewer_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-slate-300 rounded text-sm focus:outline-none focus:border-[#7AA88B]',
                'placeholder': 'Ví dụ: Anh Tuấn'
            }),
            'rating': forms.Select(
                choices=[(5, '5 Sao - Cây rất tươi đẹp'), (4, '4 Sao - Cây tươi tốt'), (3, '3 Sao - Bình thường'), (2, '2 Sao - Cần cải thiện'), (1, '1 Sao - Kém')],
                attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded text-sm focus:outline-none focus:border-[#7AA88B]'}
            ),
            'comment': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full px-3 py-2 border border-slate-300 rounded text-sm focus:outline-none focus:border-[#7AA88B]',
                'placeholder': 'Chia sẻ cảm nhận thực tế khi nhận cây...'
            }),
        }


# ------------------------------------------------------------------------------
# 5. BIỂU MẪU TRA CỨU ĐƠN HÀNG (ORDER TRACKING FORM)
# ------------------------------------------------------------------------------
class OrderTrackingForm(forms.Form):
    keyword = forms.CharField(
        label="Mã đơn hàng hoặc Số điện thoại",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-slate-300 rounded text-sm focus:outline-none focus:border-[#7AA88B]',
            'placeholder': 'Nhập mã đơn (vd: HD-...) hoặc số điện thoại đặt hàng'
        })
    )
