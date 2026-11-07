from django import forms
from .models import ProductReview

class ProductReviewForm(forms.ModelForm):
    RATING_CHOICES = [
        (5, '★★★★★ (5 sao) - Cây rất khỏe mạnh, thuần lá nước xuất sắc'),
        (4, '★★★★☆ (4 sao) - Cây tươi tốt, đóng gói bọc ẩm chu đáo'),
        (3, '★★★☆☆ (3 sao) - Chất lượng đạt tiêu chuẩn hồ nuôi'),
        (2, '★★☆☆☆ (2 sao) - Cây hơi yếu hoặc có lá vàng nhẹ'),
        (1, '★☆☆☆☆ (1 sao) - Cây úng rữa lá / Không hài lòng'),
    ]

    rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        initial=5,
        widget=forms.Select(attrs={
            'class': 'w-full bg-white border border-slate-300 rounded-none px-3.5 py-2.5 text-xs text-slate-800 focus:outline-none focus:border-[#7AA88B] focus:ring-0 transition'
        }),
        label="Mức độ hài lòng & Tình trạng cây khi nhận"
    )

    class Meta:
        model = ProductReview
        fields = ['reviewer_name', 'rating', 'comment']
        widgets = {
            'reviewer_name': forms.TextInput(attrs={
                'class': 'w-full bg-white border border-slate-300 rounded-none px-3.5 py-2.5 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-[#7AA88B] focus:ring-0 transition',
                'placeholder': 'Nhập họ và tên hoặc biệt danh của bạn...',
                'required': 'required'
            }),
            'comment': forms.Textarea(attrs={
                'rows': 4,
                'class': 'w-full bg-white border border-slate-300 rounded-none px-3.5 py-2.5 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-[#7AA88B] focus:ring-0 transition',
                'placeholder': 'Chia sẻ cảm nhận về tình trạng rễ cây, mức độ thích nghi trong bể, ánh sáng và CO2 thực tế tại hồ của bạn...',
                'required': 'required'
            }),
        }
        labels = {
            'reviewer_name': 'Họ tên người đánh giá',
            'comment': 'Nội dung nhận xét & kinh nghiệm trồng'
        }

    def clean_rating(self):
        rating = int(self.cleaned_data.get('rating', 5))
        if rating < 1 or rating > 5:
            raise forms.ValidationError("Điểm đánh giá phải từ 1 đến 5 sao.")
        return rating
