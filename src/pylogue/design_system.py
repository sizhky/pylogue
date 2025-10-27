"""
Design System for Pylogue
Centralized design tokens for colors, spacing, typography, and breakpoints.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class DesignSystem:
    """Centralized design system with consistent tokens across the application."""

    # Color palette
    COLORS: Dict[str, str] = None

    # Spacing scale (using em for better scalability)
    SPACING: Dict[str, str] = None

    # Typography scale
    TYPOGRAPHY: Dict[str, str] = None

    # Border radius values
    BORDER_RADIUS: Dict[str, str] = None

    # Breakpoints for responsive design
    BREAKPOINTS: Dict[str, str] = None

    def __post_init__(self):
        """Initialize default design tokens."""
        if self.COLORS is None:
            self.COLORS = {
                # Background colors
                "dark_bg": "#1a1a1a",

                # Message role colors
                "user_msg": "#1C0069",
                "assistant_msg": "#004539",

                # Text colors (calculated via WCAG for contrast)
                "light_text": "#FFFFFF",
                "dark_text": "#000000",

                # Spinner colors
                "spinner_light": "rgba(255, 255, 255, 0.3)",
                "spinner_border": "rgba(255, 255, 255, 0.1)",
            }

        if self.SPACING is None:
            self.SPACING = {
                "xs": "0.5em",      # 8px at base 16px
                "sm": "0.75em",     # 12px at base 16px
                "md": "1em",        # 16px at base 16px
                "lg": "1.25em",     # 20px at base 16px
                "xl": "1.5em",      # 24px at base 16px
                "2xl": "2em",       # 32px at base 16px
                "3xl": "3em",       # 48px at base 16px
            }

        if self.TYPOGRAPHY is None:
            self.TYPOGRAPHY = {
                "base": "1em",
                "sm": "0.875em",    # 14px at base 16px
                "md": "1em",        # 16px
                "lg": "1.1em",      # 17.6px
                "xl": "1.25em",     # 20px
                "2xl": "1.5em",     # 24px
                "weight_normal": "normal",
                "weight_bold": "bold",
            }

        if self.BORDER_RADIUS is None:
            self.BORDER_RADIUS = {
                "sm": "0.5em",
                "md": "1em",
                "lg": "1.5em",
            }

        if self.BREAKPOINTS is None:
            self.BREAKPOINTS = {
                "mobile": "768px",
                "tablet": "1024px",
            }


# Global default instance
default_design_system = DesignSystem()


def get_color(name: str) -> str:
    """Get a color value from the design system."""
    return default_design_system.COLORS.get(name, "")


def get_spacing(name: str) -> str:
    """Get a spacing value from the design system."""
    return default_design_system.SPACING.get(name, "")


def get_typography(name: str) -> str:
    """Get a typography value from the design system."""
    return default_design_system.TYPOGRAPHY.get(name, "")


def get_border_radius(name: str) -> str:
    """Get a border radius value from the design system."""
    return default_design_system.BORDER_RADIUS.get(name, "")


def get_breakpoint(name: str) -> str:
    """Get a breakpoint value from the design system."""
    return default_design_system.BREAKPOINTS.get(name, "")


def get_mobile_media_query() -> str:
    """Get the standard mobile media query."""
    return f"@media (max-width: {get_breakpoint('mobile')})"
