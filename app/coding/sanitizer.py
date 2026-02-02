"""
Text sanitization for clinical notes
Handles problematic Unicode characters that can break embeddings
"""

def sanitize_text(text: str) -> str:
    """Clean problematic Unicode characters from clinical text"""
    replacements = {
        # Dashes
        '\u2010': '-', '\u2013': '-', '\u2014': '-', '\u2212': '-',
        # Math symbols
        '\u00d7': 'x', '\u00f7': '/', '\u00b1': '+/-',
        # Superscripts
        '\u2070': '0', '\u00b9': '1', '\u00b2': '2', '\u00b3': '3', '\u2074': '4',
        '\u2075': '5', '\u2076': '6', '\u2077': '7', '\u2078': '8', '\u2079': '9',
        # Subscripts
        '\u2080': '0', '\u2081': '1', '\u2082': '2', '\u2083': '3', '\u2084': '4',
        '\u2085': '5', '\u2086': '6', '\u2087': '7', '\u2088': '8', '\u2089': '9',
        # Temperature/degrees
        '\u00b0': ' degrees ', '\u2103': 'C', '\u2109': 'F',
        # Quotes
        '\u201c': '"', '\u201d': '"', '\u2018': "'", '\u2019': "'", '\u0060': "'",
        # Bullets
        '\u2022': '-', '\u00b7': '-', '\u25cf': '-', '\u25cb': '-',
        # Whitespace
        '\u00a0': ' ', '\u2009': ' ', '\u200b': '',
        # Other
        '\u2026': '...', '\u2122': '', '\u00ae': '', '\u00a9': '',
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Remove any remaining non-ASCII characters
    return ''.join(char if ord(char) < 256 else ' ' for char in text)
