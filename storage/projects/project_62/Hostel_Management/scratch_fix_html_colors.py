import os

TEMPLATES_DIR = 'd:/sem3/Hostel_Management/templates'

replacements = {
    'rgba(18, 24, 43, 0.95)': 'var(--bg-card)',
    'rgba(26, 35, 62, 0.85)': 'var(--bg-card-hover)',
    'rgba(255,255,255,0.03)': 'rgba(0,0,0,0.03)',
    'rgba(255,255,255,0.04)': 'rgba(0,0,0,0.04)',
    '#ffffff 40%, #94a3b8 100%': 'var(--primary) 0%, var(--cyan) 100%'
}

def update_html_files():
    for filename in os.listdir(TEMPLATES_DIR):
        if filename.endswith('.html'):
            filepath = os.path.join(TEMPLATES_DIR, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for old, new in replacements.items():
                content = content.replace(old, new)
                
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated {filename}")

if __name__ == '__main__':
    update_html_files()
