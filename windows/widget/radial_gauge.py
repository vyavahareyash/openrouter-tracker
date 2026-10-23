"""High-DPI anti-aliased Radial Donut Gauge widget using QPainter."""

from __future__ import annotations

import math
from typing import Optional

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPen,
)
from PySide6.QtWidgets import QWidget

from windows.core.models import OpenRouterTheme, WidgetPayload


class RadialGauge(QWidget):
    """Custom donut gauge component mirroring macOS SwiftUI radial ring gauge."""

    def __init__(
        self,
        stroke_width: float = 7.5,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.stroke_width = stroke_width
        self.payload: Optional[WidgetPayload] = None
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def set_payload(self, payload: WidgetPayload) -> None:
        self.payload = payload
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        width = self.width()
        height = self.height()
        side = min(width, height)
        margin = self.stroke_width / 2.0 + 2.0
        rect = QRectF(margin, margin, side - 2 * margin, side - 2 * margin)

        # Center in widget rect
        dx = (width - side) / 2.0
        dy = (height - side) / 2.0
        rect.translate(dx, dy)

        payload = self.payload or WidgetPayload.placeholder()

        # Handle unlimited spend view vs radial gauge
        has_limit = payload.key_limit is not None and payload.key_limit > 0

        if not has_limit:
            self._paint_unlimited(painter, rect, payload)
            return

        # 1. Background Track
        track_pen = QPen(QColor(150, 150, 150, 45), self.stroke_width)
        track_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(track_pen)
        painter.drawEllipse(rect)

        # 2. Foreground Progress Arc
        usage_pct = payload.usage_percent
        if usage_pct > 0.0:
            stroke_color = self._get_stroke_color(usage_pct)
            arc_pen = QPen(stroke_color, self.stroke_width)
            arc_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(arc_pen)

            # Qt angles: start at 90 degrees (12 o'clock), negative spans clockwise
            start_angle = 90 * 16
            span_angle = -int(usage_pct * 360 * 16)
            painter.drawArc(rect, start_angle, span_angle)

        # 3. Center Text
        self._paint_center_text(painter, rect, payload)

    def _get_stroke_color(self, pct: float) -> QColor:
        if pct > 0.90:
            return QColor(OpenRouterTheme.CORAL_RED)
        if pct > 0.75:
            return QColor(OpenRouterTheme.AMBER_WARNING)
        return QColor(OpenRouterTheme.ELECTRIC_BLUE)

    def _paint_center_text(
        self, painter: QPainter, rect: QRectF, payload: WidgetPayload
    ) -> None:
        cx = rect.center().x()
        cy = rect.center().y()
        radius = rect.width() / 2.0

        # Subtitle: "REMAINING"
        sub_font_size = max(6.5, radius * 0.16)
        sub_font = QFont("Segoe UI", int(sub_font_size), QFont.Weight.Bold)
        painter.setFont(sub_font)
        painter.setPen(QColor(140, 140, 150))
        sub_rect = QRectF(rect.left(), cy - radius * 0.65, rect.width(), radius * 0.35)
        painter.drawText(sub_rect, Qt.AlignmentFlag.AlignCenter, "REMAINING")

        # Main Balance: "$X.XX"
        main_font_size = max(11.0, radius * 0.36)
        main_font = QFont("Segoe UI", int(main_font_size), QFont.Weight.Bold)
        painter.setFont(main_font)

        if payload.is_critical_balance:
            main_color = QColor(OpenRouterTheme.CORAL_RED)
        elif payload.is_low_balance:
            main_color = QColor(OpenRouterTheme.AMBER_WARNING)
        else:
            main_color = QColor(OpenRouterTheme.EMERALD_GREEN)

        painter.setPen(main_color)
        rem = payload.key_remaining if payload.key_remaining is not None else 0.0
        main_rect = QRectF(rect.left(), cy - radius * 0.28, rect.width(), radius * 0.55)
        painter.drawText(main_rect, Qt.AlignmentFlag.AlignCenter, f"${rem:.2f}")

        # Bottom % USED: "X% USED"
        used_font_size = max(6.5, radius * 0.16)
        used_font = QFont("Segoe UI", int(used_font_size), QFont.Weight.Bold)
        painter.setFont(used_font)

        if payload.usage_percent > 0.90:
            used_color = QColor(OpenRouterTheme.CORAL_RED)
        elif payload.usage_percent > 0.75:
            used_color = QColor(OpenRouterTheme.AMBER_WARNING)
        else:
            used_color = QColor(140, 140, 150)

        painter.setPen(used_color)
        used_rect = QRectF(rect.left(), cy + radius * 0.28, rect.width(), radius * 0.35)
        pct_int = int(payload.usage_percent * 100)
        painter.drawText(used_rect, Qt.AlignmentFlag.AlignCenter, f"{pct_int}% USED")

    def _paint_unlimited(
        self, painter: QPainter, rect: QRectF, payload: WidgetPayload
    ) -> None:
        cx = rect.center().x()
        cy = rect.center().y()
        radius = rect.width() / 2.0

        # Infinity Symbol / Key Spend
        inf_font = QFont("Segoe UI", int(max(14.0, radius * 0.45)), QFont.Weight.Bold)
        painter.setFont(inf_font)
        painter.setPen(QColor(OpenRouterTheme.NEON_VIOLET))
        inf_rect = QRectF(rect.left(), cy - radius * 0.7, rect.width(), radius * 0.45)
        painter.drawText(inf_rect, Qt.AlignmentFlag.AlignCenter, "∞")

        sub_font = QFont("Segoe UI", int(max(6.5, radius * 0.16)), QFont.Weight.Bold)
        painter.setFont(sub_font)
        painter.setPen(QColor(140, 140, 150))
        sub_rect = QRectF(rect.left(), cy - radius * 0.2, rect.width(), radius * 0.25)
        painter.drawText(sub_rect, Qt.AlignmentFlag.AlignCenter, "KEY SPEND")

        main_font = QFont("Segoe UI", int(max(10.0, radius * 0.32)), QFont.Weight.Bold)
        painter.setFont(main_font)
        painter.setPen(QColor(OpenRouterTheme.NEON_VIOLET))
        val_rect = QRectF(rect.left(), cy + radius * 0.05, rect.width(), radius * 0.4)
        painter.drawText(val_rect, Qt.AlignmentFlag.AlignCenter, f"${payload.key_usage:.4f}")

        tier_font = QFont("Segoe UI", int(max(6.0, radius * 0.14)))
        painter.setFont(tier_font)
        painter.setPen(QColor(140, 140, 150))
        tier_rect = QRectF(rect.left(), cy + radius * 0.45, rect.width(), radius * 0.25)
        painter.drawText(tier_rect, Qt.AlignmentFlag.AlignCenter, "Unlimited")
