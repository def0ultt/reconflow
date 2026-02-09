"""
Enhanced visual styles for ReconFlow menu system
Provides beautiful color schemes, questionary styles, and theme support
"""

from questionary import Style

# ═══════════════════════════════════════════════════════════════
# COLOR PALETTES
# ═══════════════════════════════════════════════════════════════

# Cyberpunk Neon Theme (Default)
CYBERPUNK_COLORS = {
    'primary': '#00F0FF',      # Electric Blue
    'secondary': '#FF006E',    # Hot Pink
    'accent': '#39FF14',       # Neon Green
    'success': '#10b981',      # Emerald
    'warning': '#F59E0B',      # Amber
    'error': '#EF4444',        # Red
    'highlight': '#A78BFA',    # Light Purple
    'dim': '#6B7280',          # Gray
    'text': '#E0E7FF',         # Light Indigo
}

# Matrix Hacker Theme
MATRIX_COLORS = {
    'primary': '#00FF41',      # Matrix Green
    'secondary': '#003B00',    # Dark Green
    'accent': '#CCFF00',       # Lime
    'success': '#00FF41',      # Matrix Green
    'warning': '#FFFF00',      # Yellow
    'error': '#FF0000',        # Red
    'highlight': '#00FF88',    # Aqua Green
    'dim': '#004400',          # Very Dark Green
    'text': '#00FF00',         # Bright Green
}

# Professional Dark Theme
PROFESSIONAL_COLORS = {
    'primary': '#4169E1',      # Royal Blue
    'secondary': '#4682B4',    # Steel Blue
    'accent': '#FFD700',       # Gold
    'success': '#22C55E',      # Green
    'warning': '#F59E0B',      # Amber
    'error': '#EF4444',        # Red
    'highlight': '#60A5FA',    # Sky Blue
    'dim': '#9CA3AF',          # Gray
    'text': '#E5E7EB',         # Light Gray
}

# ═══════════════════════════════════════════════════════════════
# QUESTIONARY STYLES
# ═══════════════════════════════════════════════════════════════

def get_questionary_style(theme='cyberpunk'):
    """Get questionary style based on theme"""
    
    if theme == 'matrix':
        colors = MATRIX_COLORS
    elif theme == 'professional':
        colors = PROFESSIONAL_COLORS
    else:
        colors = CYBERPUNK_COLORS
    
    return Style([
        ('qmark', f'fg:{colors["primary"]} bold'),           # Question mark
        ('question', f'fg:{colors["text"]} bold'),           # Question text
        ('answer', f'fg:{colors["accent"]} bold'),           # User's answer
        ('pointer', f'fg:{colors["secondary"]} bold'),       # Pointer >
        ('highlighted', f'fg:{colors["highlight"]} bold'),   # Highlighted option
        ('selected', f'fg:{colors["success"]}'),             # Selected item
        ('separator', f'fg:{colors["primary"]}'),            # Separator lines
        ('instruction', f'fg:{colors["dim"]} italic'),       # Instructions
        ('text', f'fg:{colors["text"]}'),                    # Regular text
        ('disabled', f'fg:{colors["dim"]}'),                 # Disabled items
    ])

# Default styles for quick access
CYBERPUNK_STYLE = get_questionary_style('cyberpunk')
MATRIX_STYLE = get_questionary_style('matrix')
PROFESSIONAL_STYLE = get_questionary_style('professional')

# ═══════════════════════════════════════════════════════════════
# RICH CONSOLE STYLES
# ═══════════════════════════════════════════════════════════════

def get_theme_colors(theme='cyberpunk'):
    """Get theme color dictionary for Rich console"""
    if theme == 'matrix':
        return MATRIX_COLORS
    elif theme == 'professional':
        return PROFESSIONAL_COLORS
    else:
        return CYBERPUNK_COLORS
