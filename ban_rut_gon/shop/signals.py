from django.contrib.auth.signals import user_logged_in
from django.core.cache import cache
from django.dispatch import receiver

AI_DESK_CTX_CACHE_TTL = 900


@receiver(user_logged_in)
def bind_ai_desk_tokens_on_login(sender, request, user, **kwargs):
    """
    Giữ nguyên token quét góc bàn AI khi khách vãng lai đăng nhập (BIZ-04):
    login() xoay vòng session_key nên ta cập nhật user_id & session_key mới vào cache.
    """
    if request is None or not hasattr(request, "session"):
        return

    tokens = request.session.pop("ai_desk_tokens", None)
    if not tokens or not isinstance(tokens, (list, tuple)):
        return

    if not request.session.session_key:
        request.session.save()
    new_session_key = request.session.session_key

    for token in tokens:
        if not token or not isinstance(token, str):
            continue
        cache_key = f"ai_desk_ctx:{token}"
        cached_ctx = cache.get(cache_key)
        if not isinstance(cached_ctx, dict):
            continue
        existing_uid = cached_ctx.get("user_id")
        if existing_uid not in (None, user.id):
            continue
        cached_ctx["user_id"] = user.id
        cached_ctx["session_key"] = new_session_key
        cache.set(cache_key, cached_ctx, timeout=AI_DESK_CTX_CACHE_TTL)
