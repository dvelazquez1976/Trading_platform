"""Alertas via Telegram Bot API (gratuito, sin dependencias externas)."""

from __future__ import annotations

import json
import urllib.request
import urllib.parse
from typing import Optional

from trading_platform.core.logging import get_logger

logger = get_logger(__name__)

_API_BASE = "https://api.telegram.org/bot{token}/{method}"


class TelegramAlerter:
    """
    Envía mensajes a un chat de Telegram cuando se detectan señales fuertes.

    Configuración en Settings de la app:
        - bot_token: token de @BotFather  (ej. "123456:ABC-DEF...")
        - chat_id:   ID del chat destino  (ej. "-1001234567890" o "987654321")

    Activación:
        1. Habla con @BotFather en Telegram → /newbot → copia el token.
        2. Añade el bot a un grupo o usa @userinfobot para obtener tu chat_id.
        3. Pega token y chat_id en ⚙️ Configuración → Alertas.
    """

    def __init__(self, bot_token: str, chat_id: str, timeout: int = 10):
        self.bot_token = bot_token.strip()
        self.chat_id = str(chat_id).strip()
        self.timeout = timeout
        self._enabled = bool(self.bot_token and self.chat_id)

    @property
    def enabled(self) -> bool:
        return self._enabled

    def send(self, text: str, parse_mode: str = "Markdown") -> bool:
        """Envía un mensaje. Devuelve True si tuvo éxito."""
        if not self._enabled:
            logger.debug("Telegram no configurado — alerta omitida.")
            return False
        url = _API_BASE.format(token=self.bot_token, method="sendMessage")
        payload = json.dumps({
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True,
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                result = json.loads(resp.read())
                if result.get("ok"):
                    logger.info("Telegram: mensaje enviado correctamente.")
                    return True
                logger.warning(f"Telegram API error: {result.get('description')}")
                return False
        except Exception as e:
            logger.error(f"Error enviando alerta Telegram: {e}")
            return False

    def test_connection(self) -> tuple[bool, str]:
        """Comprueba que el token y chat_id son válidos. Devuelve (ok, mensaje)."""
        ok = self.send("✅ *Trading Platform* — conexión de prueba correcta.")
        if ok:
            return True, "Mensaje de prueba enviado correctamente."
        return False, "No se pudo enviar el mensaje. Revisa el token y el chat_id."

    def alert_signals(self, results: list[dict], min_signal: str = "both") -> int:
        """
        Envía una alerta resumen con las señales detectadas.

        Args:
            results:    lista de dicts devueltos por TradingPlatform.run_tickers()
            min_signal: 'buy' solo compras, 'sell' solo ventas, 'both' ambas

        Returns:
            Número de alertas enviadas.
        """
        if not self._enabled:
            return 0

        buys  = [r for r in results if r["resultado_analisis"].get("resumen") == "COMPRA"]
        sells = [r for r in results if r["resultado_analisis"].get("resumen") == "VENTA"]

        selected: list[dict] = []
        if min_signal in ("both", "buy"):
            selected += buys
        if min_signal in ("both", "sell"):
            selected += sells

        if not selected:
            logger.info("Sin señales para alertar.")
            return 0

        lines = ["📊 *Trading Platform — Señales detectadas*\n"]
        for item in selected:
            res = item["resultado_analisis"]
            sig = res.get("resumen", "")
            ticker = res.get("ticker", "")
            precio = res.get("precio_cierre", 0)
            empresa = item.get("company_name", "")
            icon = "📈" if sig == "COMPRA" else "📉"
            lines.append(f"{icon} *{ticker}* ({empresa})\nSeñal: *{sig}* · Precio: {precio:.2f}\n")

        lines.append(f"_Total: {len(buys)} compras · {len(sells)} ventas_")
        text = "\n".join(lines)

        sent = self.send(text)
        return 1 if sent else 0


def from_config(cfg: dict) -> Optional[TelegramAlerter]:
    """Construye un TelegramAlerter desde el dict de configuración. Devuelve None si no configurado."""
    alerts_cfg = cfg.get("alerts", {})
    token = alerts_cfg.get("telegram_token", "")
    chat_id = alerts_cfg.get("telegram_chat_id", "")
    if not token or not chat_id:
        return None
    return TelegramAlerter(bot_token=token, chat_id=chat_id)
