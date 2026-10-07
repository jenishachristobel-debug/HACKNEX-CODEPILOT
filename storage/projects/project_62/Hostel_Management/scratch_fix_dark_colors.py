import os

CSS_DIR = 'd:/sem3/Hostel_Management/static/css'

replacements = {
    # Replace dark transparent backgrounds with variables or light equivalents
    'rgba(10, 14, 26, 0.85)': 'var(--bg-surface)',
    'rgba(18, 24, 43, 0.95)': 'var(--bg-surface)',
    'rgba(26, 35, 62, 0.85)': 'var(--bg-card-hover)',
    '#121829': 'var(--bg-elevated)',
    'rgba(255, 255, 255, 0.1)': 'var(--border-subtle)',
    'rgba(255, 255, 255, 0.15)': 'var(--border-hover)',
    'rgba(255, 255, 255, 0.04)': 'rgba(0, 0, 0, 0.04)',
    'rgba(255, 255, 255, 0.03)': 'rgba(0, 0, 0, 0.03)',
    '#0a0e1a': 'var(--bg-main)',
    'rgba(12, 17, 31, 0.8)': 'var(--bg-input)'
}

def update_css_files():
    for filename in os.listdir(CSS_DIR):
        if filename.endswith('.css'):
            filepath = os.path.join(CSS_DIR, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for old, new in replacements.items():
                content = content.replace(old, new)
                
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated {filename}")

if __name__ == '__main__':
    update_css_files()
