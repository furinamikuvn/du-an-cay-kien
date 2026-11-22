"""
Dịch vụ quản trị tồn kho FIFO và chuyển trạng thái đơn hàng nguyên tử (BIZ-02, BIZ-03).
"""

from django.db import transaction
from django.utils import timezone

from .models import Coupon, InventoryLot, Order, Product, ProductVariant

HEALTHY_LOT_STATUSES = ("healthy_submerged", "healthy_emerged")


def get_locked_product_lots(product, today=None):
    """
    Khóa toàn bộ lô tồn kho của sản phẩm theo thứ tự FIFO (received_date, id).
    Trả về (has_any_lots, eligible_healthy_lots).
    """
    if today is None:
        today = timezone.localdate()

    all_lots = list(InventoryLot.objects.select_for_update().filter(product=product).order_by("received_date", "id"))
    if not all_lots:
        return False, []

    eligible = [
        lot
        for lot in all_lots
        if lot.status in HEALTHY_LOT_STATUSES
        and lot.quantity_available > 0
        and (lot.expiry_date is None or lot.expiry_date >= today)
    ]
    return True, eligible


def deduct_lots_fifo(eligible_lots, qty_needed):
    """Khấu trừ tồn kho trên danh sách lô hợp lệ đã được khóa theo thứ tự FIFO."""
    remaining = qty_needed
    for lot in eligible_lots:
        if remaining <= 0:
            break
        take = min(lot.quantity_available, remaining)
        if take > 0:
            lot.quantity_available -= take
            remaining -= take
            lot.save(update_fields=["quantity_available"])
    return remaining


def restore_inventory_for_order(order):
    """
    Hoàn trả tồn kho (Product.stock_quantity, ProductVariant.stock, InventoryLot.quantity_available)
    và hoàn lượt sử dụng Coupon khi đơn hàng bị hủy.
    Phải được gọi bên trong transaction.atomic().
    """
    items = list(order.items.select_related("product", "variant").order_by("product_id", "variant_id", "id"))
    if not items:
        return

    # Khóa Product và ProductVariant theo thứ tự cố định (product_id, variant_id) để chống deadlock
    product_ids = sorted({item.product_id for item in items if item.product_id})
    locked_products = {p.id: p for p in Product.objects.select_for_update().filter(id__in=product_ids).order_by("id")}

    variant_ids = sorted({item.variant_id for item in items if item.variant_id})
    locked_variants = {
        v.id: v
        for v in ProductVariant.objects.select_for_update().filter(id__in=variant_ids).order_by("product_id", "id")
    }

    for item in items:
        qty = item.quantity or 0
        if qty <= 0:
            continue

        prod = locked_products.get(item.product_id)
        if prod:
            prod.stock_quantity += qty
            prod.save(update_fields=["stock_quantity"])

            has_any_lots = InventoryLot.objects.filter(product=prod).exists()
            if has_any_lots:
                healthy_lots = list(
                    InventoryLot.objects.select_for_update()
                    .filter(product=prod, status__in=HEALTHY_LOT_STATUSES)
                    .order_by("-received_date", "-id")
                )
                remaining = qty
                for lot in healthy_lots:
                    if remaining <= 0:
                        break
                    capacity = max(0, lot.quantity_received - lot.quantity_available)
                    if capacity > 0:
                        give_back = min(capacity, remaining)
                        lot.quantity_available += give_back
                        remaining -= give_back
                        lot.save(update_fields=["quantity_available"])

                if remaining > 0 and healthy_lots:
                    newest_lot = healthy_lots[0]
                    newest_lot.quantity_available += remaining
                    newest_lot.save(update_fields=["quantity_available"])
                    remaining = 0

                if remaining > 0:
                    InventoryLot.objects.create(
                        lot_code=f"LOT-RESTOCK-{order.id}-{prod.id}-{item.id}",
                        product=prod,
                        quantity_received=remaining,
                        quantity_available=remaining,
                        status="healthy_submerged",
                        note=f"Hoàn kho từ đơn hủy {order.order_code}",
                    )

        if item.variant_id:
            variant = locked_variants.get(item.variant_id)
            if variant:
                variant.stock += qty
                variant.save(update_fields=["stock"])

    if order.coupon_id:
        coupon = Coupon.objects.select_for_update().filter(pk=order.coupon_id).first()
        if coupon and coupon.used_count > 0:
            coupon.used_count -= 1
            coupon.save(update_fields=["used_count"])


def transition_order_status(order_id, new_status, append_tracking_note=True):
    """
    Chuyển trạng thái đơn hàng an toàn trong transaction.atomic():
    - Chặn tuyệt đối chuyển ngược ra khỏi trạng thái 'cancelled'.
    - Tự động hoàn kho khi chuyển từ trạng thái khác sang 'cancelled'.
    Trả về (success: bool, message: str, order: Order | None).
    """
    valid_statuses = dict(Order.STATUS_CHOICES)
    if new_status not in valid_statuses:
        return False, "Trạng thái đơn hàng không hợp lệ.", None

    with transaction.atomic():
        order = Order.objects.select_for_update().filter(pk=order_id).first()
        if not order:
            return False, "Không tìm thấy đơn hàng.", None

        old_status = order.status
        if old_status == "cancelled" and new_status != "cancelled":
            return (
                False,
                (
                    f"Đơn hàng {order.order_code} đã hủy nên không thể chuyển ngược sang trạng thái "
                    f"'{valid_statuses[new_status]}'."
                ),
                order,
            )

        if old_status == new_status:
            return True, f"Đơn hàng {order.order_code} hiện đang ở trạng thái '{valid_statuses[new_status]}'.", order

        old_status_name = order.get_status_display()
        if new_status == "cancelled":
            restore_inventory_for_order(order)

        order.status = new_status
        if append_tracking_note:
            time_str = timezone.localtime().strftime("%H:%M %d/%m/%Y")
            base_note = (order.tracking_note or "").strip()
            suffix = " (Đã hoàn tồn kho tự động)" if new_status == "cancelled" else ""
            append_line = (
                f"[{time_str}] Thay đổi trạng thái: {old_status_name} -> {valid_statuses[new_status]}{suffix}."
            )
            order.tracking_note = f"{base_note}\n{append_line}".strip()
            order.save(update_fields=["status", "tracking_note", "updated_at"])
        else:
            order.save(update_fields=["status", "updated_at"])

        return True, f"Đã chuyển trạng thái đơn {order.order_code} thành: '{valid_statuses[new_status]}'.", order
