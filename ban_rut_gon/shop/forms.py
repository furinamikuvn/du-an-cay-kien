# ==============================================================================
# CÁC LỚP BIỂU MẪU NHẬP LIỆU (SHOP/FORMS.PY)
# ==============================================================================
# 1. CheckoutForm: Form điền thông tin người nhận khi đặt mua hàng.
# 2. RegisterForm: Form đăng ký tài khoản khách hàng mới + tự tạo UserProfile.
# 3. LoginForm: Form đăng nhập vào hệ thống.
# 4. ReviewForm: Form gửi đánh giá và nhận xét sản phẩm.
# 5. OrderTrackingForm: Form tra cứu đơn hàng bằng mã đơn hoặc số điện thoại.
# 6. ForgotPasswordForm: Form đặt lại mật khẩu cục bộ.
# 7. CouponApplyForm: Form áp dụng mã ưu đãi (AQUA2026, FREESHIP...).
# 8. ProfileUpdateForm: Form cập nhật thông tin hồ sơ cá nhân & UserProfile.
# 9. CustomPasswordChangeForm: Form đổi mật khẩu cho người dùng đã đăng nhập.
# ==============================================================================

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Order, ProductReview, UserProfile


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
            'class': 'w-full px-3 py-2 border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-[#3D6B4E]/30 focus:border-[#3D6B4E]',
            'placeholder': 'Ví dụ: Nguyễn Văn A'
        })
    )
    email = forms.EmailField(
        required=True,
        label="Hộp thư điện tử (Email)",
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-[#3D6B4E]/30 focus:border-[#3D6B4E]',
            'placeholder': 'nguyenvana@gmail.com'
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=True,
        label="Số điện thoại nhận hàng",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-[#3D6B4E]/30 focus:border-[#3D6B4E]',
            'placeholder': '0901234567'
        })
    )
    shipping_address = forms.CharField(
        required=True,
        label="Địa chỉ giao hàng chi tiết",
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'w-full px-3 py-2 border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-[#3D6B4E]/30 focus:border-[#3D6B4E]',
            'placeholder': 'Số nhà, tên đường, phường/xã, quận/huyện, tỉnh/thành phố...'
        })
    )
    customer_note = forms.CharField(
        required=False,
        label="Ghi chú thêm cho người bán (nếu có)",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-[#3D6B4E]/30 focus:border-[#3D6B4E]',
            'placeholder': 'Ví dụ: Giao hàng vào giờ hành chính, bọc thêm lớp giữ ẩm...'
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
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-[#3D6B4E]/30 focus:border-[#3D6B4E]',
            'placeholder': 'Tối thiểu 8 ký tự (có chữ & số)'
        })
    )
    confirm_password = forms.CharField(
        label="Xác nhận mật khẩu",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-[#3D6B4E]/30 focus:border-[#3D6B4E]',
            'placeholder': 'Nhập lại mật khẩu ở trên'
        })
    )

    email = forms.EmailField(
        required=True,
        label="Email liên hệ",
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-[#3D6B4E]/30 focus:border-[#3D6B4E]',
            'placeholder': 'email@example.com'
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
                'class': 'w-full px-3 py-2 border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-[#3D6B4E]/30 focus:border-[#3D6B4E]',
                'placeholder': 'Nhập tên đăng nhập viết liền không dấu'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-[#3D6B4E]/30 focus:border-[#3D6B4E]',
                'placeholder': 'Nhập họ và tên của bạn'
            }),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Tên đăng nhập này đã có người sử dụng. Vui lòng chọn tên khác.")
        return username

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if not email:
            raise forms.ValidationError("Vui lòng nhập địa chỉ email hợp lệ.")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Địa chỉ email này đã được đăng ký bởi một tài khoản khác.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        pwd = cleaned_data.get('password')
        confirm_pwd = cleaned_data.get('confirm_password')
        if pwd and confirm_pwd and pwd != confirm_pwd:
            raise forms.ValidationError("Mật khẩu xác nhận không trùng khớp!")
        if pwd:
            temp_user = User(
                username=cleaned_data.get('username', ''),
                email=cleaned_data.get('email', '')
            )
            try:
                validate_password(pwd, user=temp_user)
            except forms.ValidationError as exc:
                raise forms.ValidationError(list(exc.messages))
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = (self.cleaned_data.get('email') or '').strip().lower()
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            UserProfile.objects.get_or_create(user=user, defaults={'role': 'customer', 'email_verified': False})
        return user


# ------------------------------------------------------------------------------
# 3. BIỂU MẪU ĐĂNG NHẬP (LOGIN FORM)
# ------------------------------------------------------------------------------
class LoginForm(forms.Form):
    username = forms.CharField(
        label="Tên đăng nhập",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-[#3D6B4E]/30 focus:border-[#3D6B4E]',
            'placeholder': 'Nhập tên đăng nhập của bạn'
        })
    )
    password = forms.CharField(
        label="Mật khẩu",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-[#3D6B4E]/30 focus:border-[#3D6B4E]',
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
                'class': 'w-full px-3 py-2 border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-[#3D6B4E]/30 focus:border-[#3D6B4E]',
                'placeholder': 'Ví dụ: Anh Tuấn'
            }),
            'rating': forms.Select(
                choices=[
                    (5, '5 Sao - Cây rất tươi đẹp'),
                    (4, '4 Sao - Cây tươi tốt'),
                    (3, '3 Sao - Bình thường'),
                    (2, '2 Sao - Cần cải thiện'),
                    (1, '1 Sao - Kém'),
                ],
                attrs={'class': 'w-full px-3 py-2 border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-[#3D6B4E]/30 focus:border-[#3D6B4E]'}
            ),
            'comment': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full px-3 py-2 border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-[#3D6B4E]/30 focus:border-[#3D6B4E]',
                'placeholder': 'Chia sẻ cảm nhận thực tế khi nhận cây...'
            }),
        }

    def clean_rating(self):
        rating = int(self.cleaned_data.get('rating', 5))
        if rating < 1 or rating > 5:
            raise forms.ValidationError("Điểm đánh giá phải từ 1 đến 5 sao.")
        return rating


# ------------------------------------------------------------------------------
# 5. BIỂU MẪU TRA CỨU ĐƠN HÀNG (ORDER TRACKING FORM)
# ------------------------------------------------------------------------------
class OrderTrackingForm(forms.Form):
    keyword = forms.CharField(
        label="Mã đơn hàng hoặc Số điện thoại",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-[#3D6B4E]/30 focus:border-[#3D6B4E]',
            'placeholder': 'Nhập mã đơn (vd: HD-...) hoặc số điện thoại đặt hàng'
        })
    )


# ------------------------------------------------------------------------------
# 6. BIỂU MẪU QUÊN MẬT KHẨU 2 BƯỚC (FORGOT PASSWORD REQUEST & TOKEN CONFIRM)
# ------------------------------------------------------------------------------
class ForgotPasswordRequestForm(forms.Form):
    """
    Bước 1 khôi phục mật khẩu: chỉ nhận tên đăng nhập và email để gửi token xác nhận.
    Không tiết lộ sự tồn tại của tài khoản hay email không khớp.
    """
    username = forms.CharField(
        max_length=150,
        required=True,
        label="Tên đăng nhập",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-[#3D6B4E]/30 focus:border-[#3D6B4E]',
            'placeholder': 'Nhập tên đăng nhập của bạn'
        })
    )
    email = forms.EmailField(
        required=True,
        label="Email đã đăng ký",
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-[#3D6B4E]/30 focus:border-[#3D6B4E]',
            'placeholder': 'Nhập email đã dùng khi tạo tài khoản'
        })
    )


class SetNewPasswordForm(forms.Form):
    """
    Bước 2 khôi phục mật khẩu: nhập mật khẩu mới sau khi xác thực token hợp lệ.
    """
    new_password = forms.CharField(
        min_length=8,
        required=True,
        label="Mật khẩu mới",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-[#3D6B4E]/30 focus:border-[#3D6B4E]',
            'placeholder': 'Tối thiểu 8 ký tự (có chữ & số)'
        })
    )
    confirm_new_password = forms.CharField(
        min_length=8,
        required=True,
        label="Xác nhận mật khẩu mới",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-[#3D6B4E]/30 focus:border-[#3D6B4E]',
            'placeholder': 'Nhập lại mật khẩu mới'
        })
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        new_pwd = cleaned_data.get('new_password')
        confirm_pwd = cleaned_data.get('confirm_new_password')

        if new_pwd and confirm_pwd and new_pwd != confirm_pwd:
            raise forms.ValidationError("Mật khẩu xác nhận không trùng khớp!")

        if new_pwd:
            try:
                validate_password(new_pwd, user=self.user)
            except ValidationError as exc:
                raise forms.ValidationError(list(exc.messages))

        return cleaned_data


# ------------------------------------------------------------------------------
# 7. BIỂU MẪU ÁP DỤNG MÃ GIẢM GIÁ (COUPON APPLY FORM)
# ------------------------------------------------------------------------------
class CouponApplyForm(forms.Form):
    coupon_code = forms.CharField(
        max_length=30,
        required=True,
        label="Mã giảm giá",
        widget=forms.TextInput(attrs={
            'placeholder': 'Nhập mã ưu đãi (vd: AQUA2026, FREESHIP)...',
            'class': 'w-full bg-white border border-slate-300 px-3 py-2 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-[#3D6B4E]/30 focus:border-[#3D6B4E] uppercase tracking-wider font-semibold placeholder:normal-case placeholder:font-normal placeholder:text-slate-500 transition',
            'autocomplete': 'off',
        })
    )


# ------------------------------------------------------------------------------
# 8. BIỂU MẪU CẬP NHẬT HỒ SƠ CÁ NHÂN (PROFILE UPDATE FORM)
# ------------------------------------------------------------------------------
class ProfileUpdateForm(forms.Form):
    full_name = forms.CharField(
        max_length=150,
        required=True,
        label="Họ và tên đầy đủ",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 bg-white border border-slate-300 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-[#3D6B4E]/30 focus:border-[#3D6B4E] transition',
            'placeholder': 'Họ và tên'
        })
    )
    email = forms.EmailField(
        required=True,
        label="Địa chỉ Email",
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 bg-white border border-slate-300 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-[#3D6B4E]/30 focus:border-[#3D6B4E] transition',
            'placeholder': 'name@example.com'
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        label="Số điện thoại liên hệ",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 bg-white border border-slate-300 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-[#3D6B4E]/30 focus:border-[#3D6B4E] transition',
            'placeholder': 'Ví dụ: 0912345678'
        })
    )
    address = forms.CharField(
        required=False,
        label="Địa chỉ giao hàng mặc định",
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 bg-white border border-slate-300 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-[#3D6B4E]/30 focus:border-[#3D6B4E] transition resize-none',
            'rows': 3,
            'placeholder': 'Số nhà, đường, phường/xã, quận/huyện, tỉnh/thành phố...'
        })
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if self.user:
            duplicate = User.objects.filter(email__iexact=email).exclude(pk=self.user.pk).exists()
            if duplicate:
                raise ValidationError("Địa chỉ email này đã được sử dụng bởi một tài khoản khác.")
        return email

    def save(self):
        if not self.user:
            return None
        old_email = (self.user.email or '').strip().lower()
        new_email = self.cleaned_data['email'].strip().lower()
        full_name = self.cleaned_data['full_name'].strip()
        self.user.first_name = full_name
        self.user.last_name = ''
        self.user.email = new_email
        self.user.save()

        profile, _ = UserProfile.objects.get_or_create(user=self.user, defaults={'role': 'customer'})
        if old_email != new_email:
            profile.email_verified = False
        profile.phone = self.cleaned_data['phone'].strip()
        profile.address = self.cleaned_data['address'].strip()
        profile.save()
        return self.user


# ------------------------------------------------------------------------------
# 9. BIỂU MẪU ĐỔI MẬT KHẨU (CUSTOM PASSWORD CHANGE FORM)
# ------------------------------------------------------------------------------
class CustomPasswordChangeForm(forms.Form):
    old_password = forms.CharField(
        label="Mật khẩu hiện tại",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 bg-white border border-slate-300 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-[#3D6B4E]/30 focus:border-[#3D6B4E] transition',
            'placeholder': 'Nhập mật khẩu đang sử dụng...'
        })
    )
    new_password = forms.CharField(
        min_length=8,
        label="Mật khẩu mới",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 bg-white border border-slate-300 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-[#3D6B4E]/30 focus:border-[#3D6B4E] transition',
            'placeholder': 'Tối thiểu 8 ký tự (có chữ & số)...'
        })
    )
    confirm_password = forms.CharField(
        min_length=8,
        label="Xác nhận mật khẩu mới",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 bg-white border border-slate-300 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-[#3D6B4E]/30 focus:border-[#3D6B4E] transition',
            'placeholder': 'Nhập lại chính xác mật khẩu mới...'
        })
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if self.user and not self.user.check_password(old_password):
            raise ValidationError("Mật khẩu hiện tại không chính xác.")
        return old_password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")
        if new_password and confirm_password and new_password != confirm_password:
            self.add_error('confirm_password', "Mật khẩu xác nhận không khớp.")
        if new_password:
            try:
                validate_password(new_password, user=self.user)
            except ValidationError as exc:
                self.add_error('new_password', list(exc.messages))
        return cleaned_data

    def save(self):
        new_password = self.cleaned_data['new_password']
        self.user.set_password(new_password)
        self.user.save()
        return self.user
