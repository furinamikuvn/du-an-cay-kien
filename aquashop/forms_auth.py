from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import UserProfile


class RegisterForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        required=True,
        label="Tên đăng nhập",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-none text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-[#7AA88B] transition',
            'placeholder': 'Nhập tên đăng nhập (viết liền không dấu)...'
        })
    )
    full_name = forms.CharField(
        max_length=150,
        required=True,
        label="Họ và tên đầy đủ",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-none text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-[#7AA88B] transition',
            'placeholder': 'Ví dụ: Nguyễn Văn Bảo'
        })
    )
    email = forms.EmailField(
        required=True,
        label="Địa chỉ Email",
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-none text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-[#7AA88B] transition',
            'placeholder': 'name@example.com'
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=True,
        label="Số điện thoại nhận hàng",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-none text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-[#7AA88B] transition',
            'placeholder': 'Ví dụ: 0912345678'
        })
    )
    address = forms.CharField(
        required=True,
        label="Địa chỉ giao hàng mặc định",
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-none text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-[#7AA88B] transition resize-none',
            'placeholder': 'Số nhà, đường, phường/xã, quận/huyện, tỉnh/thành phố...',
            'rows': 3
        })
    )
    password = forms.CharField(
        min_length=6,
        required=True,
        label="Mật khẩu bảo mật",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-none text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-[#7AA88B] transition',
            'placeholder': 'Tối thiểu 6 ký tự'
        })
    )
    confirm_password = forms.CharField(
        min_length=6,
        required=True,
        label="Xác nhận mật khẩu",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-none text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-[#7AA88B] transition',
            'placeholder': 'Nhập lại chính xác mật khẩu trên'
        })
    )

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("Tên đăng nhập này đã được sử dụng. Vui lòng chọn tên khác.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Địa chỉ email này đã được đăng ký tài khoản.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Mật khẩu xác nhận không khớp. Vui lòng kiểm tra lại.")
        return cleaned_data

    def save(self):
        username = self.cleaned_data['username'].strip()
        email = self.cleaned_data['email'].strip().lower()
        password = self.cleaned_data['password']
        full_name = self.cleaned_data['full_name'].strip()
        phone = self.cleaned_data['phone'].strip()
        address = self.cleaned_data['address'].strip()

        parts = full_name.split(' ', 1)
        first_name = parts[1] if len(parts) > 1 else parts[0]
        last_name = parts[0] if len(parts) > 1 else ''

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        UserProfile.objects.create(
            user=user,
            role='customer',
            phone=phone,
            address=address
        )
        return user


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        required=True,
        label="Tên đăng nhập",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-none text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-[#7AA88B] transition',
            'placeholder': 'Nhập tên đăng nhập...'
        })
    )
    password = forms.CharField(
        required=True,
        label="Mật khẩu",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-none text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-[#7AA88B] transition',
            'placeholder': 'Nhập mật khẩu...'
        })
    )


class ProfileUpdateForm(forms.Form):
    full_name = forms.CharField(
        max_length=150,
        required=True,
        label="Họ và tên đầy đủ",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-none text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-[#7AA88B] transition',
            'placeholder': 'Họ và tên'
        })
    )
    email = forms.EmailField(
        required=True,
        label="Địa chỉ Email",
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-none text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-[#7AA88B] transition',
            'placeholder': 'name@example.com'
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        label="Số điện thoại liên hệ",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-none text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-[#7AA88B] transition',
            'placeholder': 'Ví dụ: 0912345678'
        })
    )
    address = forms.CharField(
        required=False,
        label="Địa chỉ giao hàng mặc định",
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-none text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-[#7AA88B] transition resize-none',
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
        full_name = self.cleaned_data['full_name'].strip()
        parts = full_name.split(' ', 1)
        first_name = parts[1] if len(parts) > 1 else parts[0]
        last_name = parts[0] if len(parts) > 1 else ''

        self.user.first_name = first_name
        self.user.last_name = last_name
        self.user.email = self.cleaned_data['email'].strip()
        self.user.save()

        profile, _ = UserProfile.objects.get_or_create(user=self.user)
        profile.phone = self.cleaned_data['phone'].strip()
        profile.address = self.cleaned_data['address'].strip()
        profile.save()
        return self.user


class OrderTrackingForm(forms.Form):
    search_query = forms.CharField(
        max_length=100,
        required=True,
        label="Mã đơn hàng hoặc Số điện thoại",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 bg-white border border-slate-300 rounded-none text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-[#7AA88B] transition',
            'placeholder': 'Nhập mã đơn hàng (ví dụ: AQ-88912) hoặc số điện thoại...'
        })
    )
