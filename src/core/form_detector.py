import re
from bs4 import BeautifulSoup

FIELD_PATTERNS = {
    'name': r'name|author|full.?name|first.?name|last.?name|your.?name|userName',
    'email': r'email|e.?mail|contact|commentEmail',
    'website': r'website|url|site|blog|link|commentURL',
    'message': r'message|msg|content|body|text|commentText',
    'comment': r'comment|review|feedback|note|commentText'
}

def detect_form_fields(html):
    """Detect form fields and return dict with field info"""
    soup = BeautifulSoup(html, 'html.parser')
    forms = soup.find_all('form')
    
    result = {'forms': []}
    
    for i, form in enumerate(forms):
        form_data = {'index': i, 'fields': {}}
        
        fields = form.find_all(['input', 'textarea'])
        
        for field in fields:
            field_type = _detect_field_type(field)
            if field_type:
                selector = _get_selector(field)
                form_data['fields'][field_type] = {
                    'selector': selector,
                    'tag': field.name,
                    'type': field.get('type', 'text')
                }
        
        if form_data['fields']:
            result['forms'].append(form_data)
    
    return result

def _detect_field_type(field):
    """Detect field type based on attributes"""
    attrs = [
        field.get('name', ''),
        field.get('id', ''),
        field.get('placeholder', ''),
        field.get('class', '')
    ]
    
    text = ' '.join(str(attr) for attr in attrs).lower()
    
    for field_type, pattern in FIELD_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            return field_type
    
    return None

def _get_selector(field):
    """Generate CSS selector for field"""
    if field.get('id'):
        return f"#{field['id']}"
    elif field.get('name'):
        return f"[name='{field['name']}']"
    else:
        return f"{field.name}[placeholder*='{field.get('placeholder', '')[:10]}']"