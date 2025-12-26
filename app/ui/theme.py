"""
Theme and styling for PDF Scanner App.
Material Design 3 inspired theme system.
"""
from kivy.utils import get_color_from_hex


class Theme:
    """
    Application theme with colors, typography, and spacing.
    Material Design 3 inspired with a premium document scanner feel.
    """
    
    def __init__(self, dark_mode: bool = False):
        self.dark_mode = dark_mode
        self._init_colors()
        self._init_typography()
        self._init_spacing()
    
    def _init_colors(self):
        """Initialize color palette."""
        if self.dark_mode:
            self.colors = {
                # Primary colors
                'primary': get_color_from_hex('#6750A4'),
                'primary_container': get_color_from_hex('#EADDFF'),
                'on_primary': get_color_from_hex('#FFFFFF'),
                'on_primary_container': get_color_from_hex('#21005D'),
                
                # Secondary colors
                'secondary': get_color_from_hex('#625B71'),
                'secondary_container': get_color_from_hex('#E8DEF8'),
                
                # Surface colors (dark theme)
                'background': get_color_from_hex('#1C1B1F'),
                'surface': get_color_from_hex('#1C1B1F'),
                'surface_variant': get_color_from_hex('#49454F'),
                'on_surface': get_color_from_hex('#E6E1E5'),
                'on_surface_variant': get_color_from_hex('#CAC4D0'),
                
                # Other colors
                'error': get_color_from_hex('#F2B8B5'),
                'on_error': get_color_from_hex('#601410'),
                'success': get_color_from_hex('#A8DAB5'),
                'warning': get_color_from_hex('#FFE08D'),
                
                # Scanner specific
                'overlay': [0.4, 0.2, 0.8, 0.5],  # Quad overlay color
                'capture_button': get_color_from_hex('#FFFFFF'),
                'corner_handle': get_color_from_hex('#6750A4'),
            }
        else:
            self.colors = {
                # Primary colors (Purple)
                'primary': get_color_from_hex('#6750A4'),
                'primary_container': get_color_from_hex('#EADDFF'),
                'on_primary': get_color_from_hex('#FFFFFF'),
                'on_primary_container': get_color_from_hex('#21005D'),
                
                # Secondary colors
                'secondary': get_color_from_hex('#625B71'),
                'secondary_container': get_color_from_hex('#E8DEF8'),
                
                # Surface colors (light theme)
                'background': get_color_from_hex('#FFFBFE'),
                'surface': get_color_from_hex('#FFFBFE'),
                'surface_variant': get_color_from_hex('#E7E0EC'),
                'on_surface': get_color_from_hex('#1C1B1F'),
                'on_surface_variant': get_color_from_hex('#49454F'),
                
                # Other colors
                'error': get_color_from_hex('#B3261E'),
                'on_error': get_color_from_hex('#FFFFFF'),
                'success': get_color_from_hex('#2E7D32'),
                'warning': get_color_from_hex('#ED6C02'),
                
                # Scanner specific
                'overlay': [0.4, 0.2, 0.8, 0.6],  # Quad overlay color
                'capture_button': get_color_from_hex('#FFFFFF'),
                'corner_handle': get_color_from_hex('#6750A4'),
            }
    
    def _init_typography(self):
        """Initialize typography settings."""
        self.typography = {
            'display_large': {'font_size': '57sp', 'line_height': 1.12},
            'display_medium': {'font_size': '45sp', 'line_height': 1.16},
            'display_small': {'font_size': '36sp', 'line_height': 1.22},
            
            'headline_large': {'font_size': '32sp', 'line_height': 1.25},
            'headline_medium': {'font_size': '28sp', 'line_height': 1.29},
            'headline_small': {'font_size': '24sp', 'line_height': 1.33},
            
            'title_large': {'font_size': '22sp', 'line_height': 1.27},
            'title_medium': {'font_size': '16sp', 'line_height': 1.50},
            'title_small': {'font_size': '14sp', 'line_height': 1.43},
            
            'body_large': {'font_size': '16sp', 'line_height': 1.50},
            'body_medium': {'font_size': '14sp', 'line_height': 1.43},
            'body_small': {'font_size': '12sp', 'line_height': 1.33},
            
            'label_large': {'font_size': '14sp', 'line_height': 1.43},
            'label_medium': {'font_size': '12sp', 'line_height': 1.33},
            'label_small': {'font_size': '11sp', 'line_height': 1.45},
        }
    
    def _init_spacing(self):
        """Initialize spacing constants."""
        self.spacing = {
            'xs': 4,
            'sm': 8,
            'md': 16,
            'lg': 24,
            'xl': 32,
            'xxl': 48,
        }
        
        self.border_radius = {
            'sm': 4,
            'md': 8,
            'lg': 12,
            'xl': 16,
            'full': 9999,
        }
    
    def get_color(self, name: str) -> list:
        """Get a color by name."""
        return self.colors.get(name, [1, 1, 1, 1])
    
    def toggle_dark_mode(self):
        """Toggle between light and dark mode."""
        self.dark_mode = not self.dark_mode
        self._init_colors()


# Global theme instance
_theme_instance = None


def get_theme() -> Theme:
    """Get the global theme instance."""
    global _theme_instance
    if _theme_instance is None:
        _theme_instance = Theme()
    return _theme_instance
