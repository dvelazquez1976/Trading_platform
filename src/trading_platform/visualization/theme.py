"""Tokens de diseño para temas light y dark."""

THEMES = {
    "light": {
        "background":   "#f8fafc",
        "card_bg":      "#ffffff",
        "text":         "#1e293b",
        "text_muted":   "#64748b",
        "buy":          "#10b981",
        "sell":         "#ef4444",
        "hold":         "#94a3b8",
        "accent":       "#0284c7",
        "grid":         "#e2e8f0",
    },
    "dark": {
        "background":   "#0f172a",
        "card_bg":      "#1e293b",
        "text":         "#e2e8f0",
        "text_muted":   "#94a3b8",
        "buy":          "#34d399",
        "sell":         "#f87171",
        "hold":         "#64748b",
        "accent":       "#38bdf8",
        "grid":         "#334155",
    }
}

DEFAULT_THEME = "light"


def get_theme(name: str = DEFAULT_THEME) -> dict:
    return THEMES.get(name, THEMES[DEFAULT_THEME])
