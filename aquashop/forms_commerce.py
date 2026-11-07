from django import forms

class CouponApplyForm(forms.Form):
    coupon_code = forms.CharField(
        max_length=30,
        required=True,
        label="Mã giảm giá",
        widget=forms.TextInput(attrs={
            'placeholder': 'Nhập mã giảm giá (ví dụ: AQUA2026, FREESHIP)...',
            'class': 'w-full bg-white border border-slate-300 px-3.5 py-2.5 text-xs text-slate-800 rounded-none focus:outline-none focus:border-[#7AA88B] focus:ring-1 focus:ring-[#7AA88B] uppercase tracking-wider font-semibold placeholder:normal-case placeholder:font-normal placeholder:text-slate-400 transition',
            'autocomplete': 'off',
        })
    )
