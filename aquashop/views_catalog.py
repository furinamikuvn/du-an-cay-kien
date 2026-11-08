# ==============================================================================
# AQUASHOP - XỬ LÝ CHI TIẾT SẢN PHẨM, ĐÁNH GIÁ, CẨM NANG & CHÍNH SÁCH
# ==============================================================================
# Tệp này xử lý hiển thị nội dung và tương tác của danh mục sản phẩm:
# 1. product_detail_view: Chi tiết cây cảnh, hồ sơ sinh học (pH, nhiệt độ), sản phẩm liên quan.
# 2. submit_review_view: Tiếp nhận và lưu đánh giá sao (1-5★) từ khách hàng.
# 3. article_list_view & article_detail_view: Cẩm nang hướng dẫn dưỡng cây, diệt rêu hại.
# 4. faq_view: Hỏi đáp các thắc mắc thường gặp.
# 5. policy_detail_view: Chi tiết các chính sách bán hàng & bảo hiểm dập nát 1 đổi 1.
# ==============================================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Avg, Count
from django.contrib import messages
from .models import Product, ProductReview, Article, FAQ, Category
from .forms_catalog import ProductReviewForm

def product_detail_view(request, slug):
    """
    Trang chi tiết sản phẩm cây thủy sinh.
    Hiển thị thông số sinh học chi tiết, hướng dẫn cắm bể, nhân giống,
    các sản phẩm liên quan và đánh giá từ khách hàng.
    """
    product = get_object_or_404(Product, slug=slug)
    
    # Danh sách đánh giá
    reviews = product.reviews.all().order_by('-created_at')
    reviews_count = reviews.count()
    
    avg_rating_agg = reviews.aggregate(Avg('rating'))['rating__avg']
    avg_rating = round(avg_rating_agg, 1) if avg_rating_agg is not None else 5.0
    
    # Thống kê phân bố sao đánh giá (1 -> 5)
    rating_distribution = {}
    for star in range(5, 0, -1):
        count_star = reviews.filter(rating=star).count()
        percent = (count_star / reviews_count * 100) if reviews_count > 0 else 0
        rating_distribution[star] = {
            'count': count_star,
            'percent': round(percent, 0)
        }
    
    # Sản phẩm liên quan cùng danh mục
    related_products = Product.objects.filter(
        category=product.category
    ).exclude(id=product.id).order_by('?')[:4]
    
    # Form đánh giá
    initial_data = {}
    if request.user.is_authenticated:
        initial_data['reviewer_name'] = request.user.get_full_name() or request.user.username
    review_form = ProductReviewForm(initial=initial_data)

    context = {
        'product': product,
        'reviews': reviews,
        'reviews_count': reviews_count,
        'avg_rating': avg_rating,
        'rating_distribution': rating_distribution,
        'related_products': related_products,
        'review_form': review_form,
    }
    return render(request, 'aquashop/catalog/product_detail.html', context)


def submit_review_view(request, slug):
    """
    Xử lý gửi form đánh giá cho cây thủy sinh.
    """
    product = get_object_or_404(Product, slug=slug)
    
    if request.method == 'POST':
        form = ProductReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            if request.user.is_authenticated:
                review.user = request.user
                if not review.reviewer_name:
                    review.reviewer_name = request.user.get_full_name() or request.user.username
            review.save()
            messages.success(request, "Cảm ơn bạn đã gửi đánh giá trải nghiệm thực tế cho dòng cây này!")
        else:
            messages.error(request, "Vui lòng kiểm tra lại thông tin đánh giá.")
            
    return redirect('product_detail', slug=product.slug)


def article_list_view(request):
    """
    Danh sách bài viết cẩm nang thủy sinh, hướng dẫn setup bể và phòng chống rêu hại.
    """
    articles = Article.objects.all().order_by('-published_at')
    
    # Lọc theo chuyên mục hoặc tìm kiếm
    category_filter = request.GET.get('category', '').strip()
    query = request.GET.get('q', '').strip()
    
    if category_filter:
        articles = articles.filter(category=category_filter)
    if query:
        articles = articles.filter(title__icontains=query)
        
    categories = Article.objects.values_list('category', flat=True).distinct()
    
    # Bài viết mới nhất làm tiêu điểm
    featured_article = articles.first() if articles.exists() else None
    remaining_articles = articles[1:] if articles.count() > 1 else articles
    
    context = {
        'articles': remaining_articles,
        'featured_article': featured_article,
        'categories': categories,
        'selected_category': category_filter,
        'search_query': query,
        'total_articles': articles.count(),
    }
    return render(request, 'aquashop/catalog/article_list.html', context)


def article_detail_view(request, slug):
    """
    Trang chi tiết bài viết cẩm nang kỹ thuật thủy sinh.
    """
    article = get_object_or_404(Article, slug=slug)
    
    # Các bài viết liên quan hoặc đọc thêm
    related_articles = Article.objects.exclude(id=article.id).order_by('-published_at')[:3]
    
    context = {
        'article': article,
        'related_articles': related_articles,
    }
    return render(request, 'aquashop/catalog/article_detail.html', context)


def faq_view(request):
    """
    Trang giải đáp các thắc mắc thường gặp (FAQ) của người chơi thủy sinh.
    """
    faqs = FAQ.objects.all().order_by('order_num')
    query = request.GET.get('q', '').strip()
    
    if query:
        faqs = faqs.filter(question__icontains=query) | faqs.filter(answer__icontains=query)
        
    context = {
        'faqs': faqs,
        'search_query': query,
    }
    return render(request, 'aquashop/catalog/faq.html', context)


# ==============================================================================
# HỆ THỐNG CHÍNH SÁCH BÁN HÀNG & BẢO HIỂM THỰC VẬT THỦY SINH THỰC TẾ
# Tham khảo nghiệp vụ chuẩn từ: Thuỷ Sinh Tím, Tây Nguyên Xanh Aqua, La Nhà Treehouse
# ==============================================================================
POLICIES_DATA = {
    'huong-dan-dat-hang-va-thanh-toan': {
        'slug': 'huong-dan-dat-hang-va-thanh-toan',
        'title': 'Hướng Dẫn Đặt Hàng & Thanh Toán Trực Tuyến',
        'subtitle': 'Quy trình mua hàng 4 bước tinh giản, thanh toán mã VietQR tự động hoặc COD đồng kiểm toàn quốc.',
        'icon': 'fa-solid fa-cart-shopping',
        'category': 'Quy Trình Mua Hàng',
        'updated_at': '07/11/2026',
        'summary': 'AquaPlant tối ưu hóa trải nghiệm mua sắm cây cảnh thủy sinh: tích hợp công cụ tính toán số lượng cây theo diện tích bể và các cổng thanh toán tức thời, bảo mật tuyệt đối.',
        'sections': [
            {
                'heading': '1. Lựa chọn dòng cây & Bố cục hồ mẫu phù hợp',
                'content': (
                    'Khách hàng có thể tìm kiếm cây thủy sinh theo vị trí trồng: Tiền cảnh (Trân châu ngọc trai, Ngưu mao chiên), '
                    'Trung cảnh (Tiêu thảo, Dương xỉ Trident), Hậu cảnh (Vảy ốc siêu đỏ, Cỏ thìa) hoặc Ráy cắm lũa đá. '
                    'Đặc biệt, hệ thống cung cấp <strong>Trợ Lý Chọn Cây</strong> và công cụ <strong>Dự Toán Số Lượng Cây Theo Kích Thước Hồ</strong> '
                    'để tính toán chính xác số cốc cây cần phủ kín nền mà không bị thiếu hoặc lãng phí.'
                )
            },
            {
                'heading': '2. Kiểm tra giỏ hàng & Áp dụng mã ưu đãi thành viên',
                'content': (
                    'Tại trang Giỏ Hàng, quý khách dễ dàng tăng giảm số lượng từng dòng cây bằng bộ đếm [+ / -] hoặc xóa sản phẩm khỏi giỏ. '
                    'Nhập mã giảm giá tại ô khuyến mãi:<br>'
                    '• <code>AQUA2026</code>: Giảm ngay 10% cho đơn hàng đầu tiên từ 100.000₫.<br>'
                    '• <code>FREESHIP</code>: Miễn phí vận chuyển cho đơn hàng từ 300.000₫ trên phạm vi toàn quốc.<br>'
                    'Tất cả đơn hàng đều tự động khấu trừ kho theo nguyên tắc FIFO (First In First Out) bảo đảm lô cây xuất kho luôn tươi mới nhất.'
                )
            },
            {
                'heading': '3. Phương thức thanh toán linh hoạt & An toàn',
                'content': (
                    'AquaPlant hỗ trợ 2 hình thức thanh toán thuận tiện nhất:<br>'
                    '• <strong>Thanh toán Quét mã VietQR (Tự động):</strong> Hệ thống sinh mã QR ngân hàng có sẵn số tiền và nội dung chuyển khoản. Đơn hàng tự động kích hoạt trạng thái "Đã thanh toán" chỉ sau 3 giây.<br>'
                    '• <strong>Thanh toán tiền mặt khi nhận hàng (COD):</strong> Quý khách thanh toán trực tiếp cho bưu tá khi bưu phẩm được giao tận tay, được phép kiểm tra ngoại quan kiện hàng trước khi thanh toán.'
                )
            },
            {
                'heading': '4. Nhận mã vận đơn & Theo dõi hành trình giao nhận',
                'content': (
                    'Sau khi đặt hàng thành công, hệ thống cấp ngay <strong>Mã Vận Đơn</strong> (định dạng <code>AQUA-XXXXXX</code>). '
                    'Khách hàng có thể nhập mã này tại trang <strong>Tra Cứu Đơn Hàng</strong> để theo dõi trực tiếp lộ trình vận chuyển, '
                    'thời gian bọc ẩm, thời điểm bàn giao đơn vị vận chuyển và thời gian dự kiến giao hàng tận nhà.'
                )
            }
        ]
    },
    'chinh-sach-bao-hiem-dap-nat-1-doi-1': {
        'slug': 'chinh-sach-bao-hiem-dap-nat-1-doi-1',
        'title': 'Chính Sách Bảo Hiểm Cây Sống & Dập Nát 1 Đổi 1 Tận Nơi',
        'subtitle': 'Cam kết gánh chịu 100% rủi ro vận chuyển thực vật sống. Đổi mới miễn phí hoặc hoàn tiền trong 24 giờ.',
        'icon': 'fa-solid fa-shield-heart',
        'category': 'Cam Kết Bảo Hiểm Sinh Học',
        'updated_at': '07/11/2026',
        'summary': 'Khác với hàng tiêu dùng thông thường, cây thủy sinh là sinh vật sống nhạy cảm với nhiệt độ và va đập. AquaPlant áp dụng chính sách bảo hiểm dập nát độc quyền: Cứ hư hỏng là đổi mới 100%.',
        'sections': [
            {
                'heading': '1. Phạm vi áp dụng bảo hiểm 1 đổi 1',
                'content': (
                    'Áp dụng cho 100% đơn hàng mua sắm tại AquaPlant trên phạm vi toàn quốc gặp các sự cố sau khi mở hộp:<br>'
                    '• Cây bị dập nát, gãy ngọn chính, úng rễ hoặc rữa lá do va chạm cơ học trong quá trình vận chuyển.<br>'
                    '• Cây bị sốc nhiệt chuyển vàng, thối nõn do thời gian giao hàng kéo dài vượt cam kết.<br>'
                    '• Giao sai chủng loại cây hoặc thiếu số lượng cốc cây so với đơn hàng đã xác nhận.'
                )
            },
            {
                'heading': '2. Quy trình yêu cầu bồi thường trong 3 bước siêu tốc',
                'content': (
                    '• <strong>Bước 1 (Ghi nhận bằng chứng):</strong> Khách hàng quay video ngắn mở hộp (unboxing) hoặc chụp 2-3 bức ảnh rõ nét tình trạng cây dập nát ngay khi mở thùng xốp.<br>'
                    '• <strong>Bước 2 (Gửi yêu cầu):</strong> Gửi thông tin qua Zalo Hotline <code>1900000</code> hoặc email <code>tawa@gmail.com</code> kèm Mã Đơn Hàng trong vòng <strong>24 giờ</strong> kể từ thời điểm bưu tá ký giao thành công.<br>'
                    '• <strong>Bước 3 (Xử lý bồi thường):</strong> Chuyên viên hỗ trợ của AquaPlant tiếp nhận và phản hồi giải quyết trong vòng <strong>15 phút</strong>.'
                )
            },
            {
                'heading': '3. Hình thức đền bù minh bạch',
                'content': (
                    'Khách hàng được toàn quyền lựa chọn một trong hai phương án bồi thường:<br>'
                    '• <strong>Phương án 1 (Gửi bù hỏa tốc):</strong> AquaPlant đóng gói lô cây mới đạt chuẩn và gửi hỏa tốc miễn phí 100% cước vận chuyển đến tận địa chỉ của quý khách.<br>'
                    '• <strong>Phương án 2 (Hoàn tiền ngay lập tức):</strong> Hoàn lại 100% giá trị sản phẩm hư hỏng vào tài khoản ngân hàng hoặc ví MoMo của quý khách không giữ bất kỳ chi phí nào.'
                )
            },
            {
                'heading': '4. Các trường hợp miễn trừ bảo hiểm',
                'content': (
                    'Bảo hiểm không áp dụng trong các trường hợp:<br>'
                    '• Quý khách thông báo quá thời hạn 24 giờ kể từ khi đơn vị vận chuyển ghi nhận giao hàng thành công.<br>'
                    '• Cây bị hư hỏng do khách hàng tự ý ngâm hóa chất tẩy rêu quá liều lượng, thả vào hồ có nhiệt độ nước vượt quá 32°C hoặc độ mặn cao không phù hợp sinh thái cây.'
                )
            }
        ]
    },
    'huong-dan-duong-cay-moi-cam-ho': {
        'slug': 'huong-dan-duong-cay-moi-cam-ho',
        'title': 'Hướng Dẫn Dưỡng & Cắm Cây Mới Vào Hồ Thủy Sinh Chuẩn Kỹ Thuật',
        'subtitle': 'Cẩm nang hạ phèn, thuần nước, điều chỉnh quang kỳ và sủi CO₂ giúp cây bén rễ trắng sau 5 ngày.',
        'icon': 'fa-solid fa-seedling',
        'category': 'Cẩm Nang Kỹ Thuật Sinh Học',
        'updated_at': '07/11/2026',
        'summary': '90% nguyên nhân rữa lá cây thủy sinh xuất phát từ việc cắm sai kỹ thuật và sốc môi trường nước mới. Làm theo cẩm nang chuyên sâu dưới đây để cây đạt tỷ lệ sống sót tuyệt đối.',
        'sections': [
            {
                'heading': '1. Chuẩn bị cây: Rửa sạch gel cấy mô & Cắt tỉa rễ già',
                'content': (
                    '• Đối với cây cấy mô trong cốc thạch: Dùng ngón tay nhẹ nhàng tách khóm cây ra khỏi cốc, ngâm vào chậu nước sạch từ 1-2 phút và rửa trôi lớp gel dinh dưỡng. Việc để lại gel trong hồ sẽ dễ gây nấm mốc trắng và rêu hại.<br>'
                    '• Dùng kéo thủy sinh bén tỉa bớt các rễ già đen, chỉ giữ lại độ dài rễ từ 1.5 - 2 cm. Vết cắt gọn gàng sẽ kích thích mô sẹo phân bào nhanh, bung rễ tơ trắng chỉ sau 72 giờ cắm nền.'
                )
            },
            {
                'heading': '2. Kỹ thuật cắm cây vào phân nền không bị nổi',
                'content': (
                    '• Rút cạn nước hồ, chỉ giữ lại mực nước xăm xắp mặt phân nền (khoảng 2-3 cm). Mực nước thấp triệt tiêu lực đẩy Ác-si-mét, giúp thao tác cắm chính xác tuyệt đối.<br>'
                    '• Dùng nhíp mũi nhọn kẹp nhẹ phần rễ cây ở góc nghiêng 45 độ. Ấn sâu nhíp vào phân nền từ 2.5 - 3.5 cm, sau đó hơi lắc nhẹ cổ tay mở nhíp và rút thẳng lên theo góc nghiêng để đất nền tự lấp chặt gốc rễ.'
                )
            },
            {
                'heading': '3. Chế độ ánh sáng và CO₂ trong 7 ngày đầu',
                'content': (
                    '• <strong>Thời gian chiếu sáng:</strong> Trong tuần đầu tiên chỉ bật đèn từ 5 - 6 tiếng/ngày với cường độ 50-60% công suất đèn. Không bật đèn quá 8 tiếng vì rễ cây chưa hút được dinh dưỡng, ánh sáng mạnh sẽ làm bùng phát rêu tóc và rêu chùm đen.<br>'
                    '• <strong>Hệ thống CO₂:</strong> Bật sủi CO₂ từ 1.5 - 2 giọt/giây trước khi mở đèn 30 phút. Nồng độ CO₂ hòa tan ổn định ở mức 20-30 ppm là chìa khóa vàng giúp cây thích nghi và quang hợp phục hồi.'
                )
            },
            {
                'heading': '4. Lịch thay nước và châm vi sinh ổn định chu trình Nitơ',
                'content': (
                    '• Phân nền mới setup thường nhả hàm lượng dinh dưỡng hữu cơ và amoniac (NH₃/NH₄⁺) rất lớn.<br>'
                    '• Tiến hành thay 30% - 40% nước đều đặn cách ngày trong tuần đầu tiên (Ngày 2, Ngày 4, Ngày 6). Luôn dùng nước đã khử clo.<br>'
                    '• Bổ sung vi sinh quang hợp hoặc vi sinh sống sau mỗi lần thay nước để hỗ trợ hệ đệm sinh học, giữ nước trong vắt và lá cây bóng mượt.'
                )
            }
        ]
    },
    'quy-dinh-giao-nhan-cod-toan-quoc': {
        'slug': 'quy-dinh-giao-nhan-cod-toan-quoc',
        'title': 'Quy Định Giao Nhận COD & Tiêu Chuẩn Đóng Gói Túi Khí Chuyên Dụng',
        'subtitle': 'Quy chuẩn đóng gói 3 lớp bảo quản độ ẩm tối đa. Giao hỏa tốc 2 giờ nội thành và ship COD hỏa tốc toàn quốc.',
        'icon': 'fa-solid fa-truck-fast',
        'category': 'Vận Chuyển & Giao Hàng',
        'updated_at': '07/11/2026',
        'summary': 'Mỗi kiện hàng cây thủy sinh xuất kho từ AquaPlant đều được kiểm tra sinh học nghiêm ngặt và đóng gói theo công nghệ túi khí vi khí hậu chịu lực chống sốc.',
        'sections': [
            {
                'heading': '1. Tiêu chuẩn đóng gói 3 lớp bảo vệ sinh học',
                'content': (
                    'Mọi đơn hàng cây sống đều tuân thủ quy chuẩn đóng gói chuyên dụng phòng chống dập nát:<br>'
                    '• <strong>Lớp 1 (Giữ ẩm & Bọc khí):</strong> Cây được bọc giấy ẩm chuyên dụng vô trùng hoặc cố định trong túi khí kháng khuẩn, duy trì độ ẩm vi khí hậu 95-98% trong suốt hành trình 5 ngày.<br>'
                    '• <strong>Lớp 2 (Chống sốc nhiệt & va đập):</strong> Bọc màng xốp bong bóng khí đa tầng xung quanh từng cốc cây, cách ly hoàn toàn với các tác động ngoại lực.<br>'
                    '• <strong>Lớp 3 (Thùng xốp giữ nhiệt):</strong> Toàn bộ cây được xếp gọn gàng trong thùng xốp giữ nhiệt cách nhiệt với môi trường nắng nóng bên ngoài, dán băng keo niêm phong và tem cảnh báo "HÀNG CÂY THỦY SINH SỐNG - XIN NHẸ TAY".'
                )
            },
            {
                'heading': '2. Thời gian giao hàng cam kết',
                'content': (
                    '• <strong>Khu vực Nội thành TP.HCM:</strong> Giao hàng hỏa tốc Grab/Ahamove trong vòng <strong>2 giờ</strong> hoặc giao tiêu chuẩn trong ngày theo giờ hẹn của quý khách.<br>'
                    '• <strong>Khu vực Các tỉnh thành toàn quốc:</strong> Vận chuyển qua tuyến đường ưu tiên xe lạnh chuyển phát nhanh Viettel Post / VNPost Special trong <strong>24 đến 48 giờ</strong>.'
                )
            },
            {
                'heading': '3. Biểu phí vận chuyển & Chính sách Freeship',
                'content': (
                    '• <strong>Đồng giá toàn quốc:</strong> 30.000₫ / đơn hàng cho mọi kích thước kiện hàng.<br>'
                    '• <strong>Miễn phí vận chuyển (FREESHIP 100%):</strong> Áp dụng tự động cho mọi đơn hàng có giá trị thanh toán từ <strong>300.000₫</strong> trở lên.<br>'
                    '• Chi phí bảo hiểm dập nát và vật tư đóng gói thùng xốp túi khí được AquaPlant <strong>tài trợ 100%</strong>, khách hàng không phải trả thêm bất kỳ phụ phí nào.'
                )
            },
            {
                'heading': '4. Quyền lợi đồng kiểm và bảo đảm người mua',
                'content': (
                    '• Khách hàng có quyền yêu cầu bưu tá cho <strong>đồng kiểm ngoại quan</strong> gói hàng trước khi thanh toán tiền mặt (COD).<br>'
                    '• Nếu phát hiện thùng hàng bị móp méo nặng, bẹp rách do va đập của đơn vị vận chuyển, quý khách có thể từ chối nhận hàng và gọi ngay Hotline <code>1900000</code> để AquaPlant gửi bù đơn mới ngay lập tức.'
                )
            }
        ]
    }
}


def policy_detail_view(request, slug):
    """
    Trang chi tiết các chính sách thực tế của cửa hàng:
    - Hướng dẫn đặt hàng & thanh toán
    - Chính sách bảo hiểm dập nát 1 đổi 1
    - Hướng dẫn dưỡng cây mới cắm hồ
    - Quy định giao nhận COD toàn quốc
    """
    policy = POLICIES_DATA.get(slug)
    if not policy:
        # Nếu slug không khớp, mặc định chuyển về chính sách đặt hàng
        return redirect('policy_detail', slug='huong-dan-dat-hang-va-thanh-toan')

    # Danh sách các chính sách khác để hiển thị menu bên cạnh
    all_policies = [
        {
            'slug': key,
            'title': val['title'],
            'category': val['category'],
            'icon': val['icon'],
            'is_active': (key == slug)
        }
        for key, val in POLICIES_DATA.items()
    ]

    context = {
        'policy': policy,
        'all_policies': all_policies,
    }
    return render(request, 'aquashop/catalog/policy_detail.html', context)
