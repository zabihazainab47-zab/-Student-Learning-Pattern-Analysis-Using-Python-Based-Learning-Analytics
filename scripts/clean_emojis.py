import re, glob

files = glob.glob('frontend/**/*.html', recursive=True)
changed = []
for path in files:
    with open(path, 'r', encoding='utf-8') as f:
        original = f.read()
    cleaned = original
    # Remove leading whitespace right after > in nav-link anchors
    cleaned = re.sub(r'(class="nav-link[^"]*">)\s+', r'\1', cleaned)
    # Remove stat-icon spans that are now empty or whitespace-only
    cleaned = re.sub(r'<span class="stat-icon"([^>]*)>\s*</span>', r'<span class="stat-icon"\1></span>', cleaned)
    # Remove empty <span></span> left behind by emoji removal in quick-login buttons
    cleaned = re.sub(r'<span>\s*</span>\s*', '', cleaned)
    # Collapse multiple consecutive spaces inside tags to single space
    cleaned = re.sub(r'>  +', '> ', cleaned)
    if cleaned != original:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(cleaned)
        changed.append(path)

print(f'Tidied {len(changed)} files:')
for c in changed:
    print(' ', c)
