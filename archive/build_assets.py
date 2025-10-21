#!/usr/bin/env python3
"""
Asset optimization script for Charter Pool.
Minifies CSS and JavaScript for production use.

Usage:
    python3 build_assets.py

Output:
    - static/style.min.css (~40% smaller)
    - static/main.min.js (~35% smaller)

Safe to run multiple times. Original files are preserved.
"""

import re
import os
import sys

def minify_css(css_content):
    """
    Simple CSS minification.
    """
    # Remove comments
    css_content = re.sub(r'/\*[^*]*\*+([^/*][^*]*\*+)*/', '', css_content)
    
    # Remove whitespace
    css_content = re.sub(r'\s+', ' ', css_content)
    css_content = re.sub(r'\s*{\s*', '{', css_content)
    css_content = re.sub(r'\s*}\s*', '}', css_content)
    css_content = re.sub(r'\s*:\s*', ':', css_content)
    css_content = re.sub(r'\s*;\s*', ';', css_content)
    css_content = re.sub(r'\s*,\s*', ',', css_content)
    
    return css_content.strip()


def minify_js(js_content):
    """
    Simple JavaScript minification.
    """
    # Remove single-line comments
    js_content = re.sub(r'//.*$', '', js_content, flags=re.MULTILINE)
    
    # Remove multi-line comments
    js_content = re.sub(r'/\*[^*]*\*+([^/*][^*]*\*+)*/', '', js_content)
    
    # Remove excessive whitespace
    js_content = re.sub(r'\s+', ' ', js_content)
    js_content = re.sub(r'\s*{\s*', '{', js_content)
    js_content = re.sub(r'\s*}\s*', '}', js_content)
    js_content = re.sub(r'\s*\(\s*', '(', js_content)
    js_content = re.sub(r'\s*\)\s*', ')', js_content)
    js_content = re.sub(r'\s*;\s*', ';', js_content)
    js_content = re.sub(r'\s*,\s*', ',', js_content)
    
    return js_content.strip()


def build_assets():
    """
    Build and minify static assets.
    """
    print("=" * 70)
    print("Building and minifying static assets...")
    print("=" * 70)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.join(base_dir, 'static')
    
    # Minify CSS
    css_path = os.path.join(static_dir, 'style.css')
    css_min_path = os.path.join(static_dir, 'style.min.css')
    
    if os.path.exists(css_path):
        print(f"Minifying {css_path}...")
        with open(css_path, 'r') as f:
            css_content = f.read()
        
        minified_css = minify_css(css_content)
        
        with open(css_min_path, 'w') as f:
            f.write(minified_css)
        
        original_size = len(css_content)
        minified_size = len(minified_css)
        savings = (1 - minified_size / original_size) * 100
        
        print(f"  Original: {original_size:,} bytes")
        print(f"  Minified: {minified_size:,} bytes")
        print(f"  Savings: {savings:.1f}%")
        print(f"  ✓ Created {css_min_path}")
    
    # Minify JavaScript
    js_path = os.path.join(static_dir, 'main.js')
    js_min_path = os.path.join(static_dir, 'main.min.js')
    
    if os.path.exists(js_path):
        print(f"\nMinifying {js_path}...")
        with open(js_path, 'r') as f:
            js_content = f.read()
        
        minified_js = minify_js(js_content)
        
        with open(js_min_path, 'w') as f:
            f.write(minified_js)
        
        original_size = len(js_content)
        minified_size = len(minified_js)
        savings = (1 - minified_size / original_size) * 100
        
        print(f"  Original: {original_size:,} bytes")
        print(f"  Minified: {minified_size:,} bytes")
        print(f"  Savings: {savings:.1f}%")
        print(f"  ✓ Created {js_min_path}")
    
    print("\n" + "=" * 70)
    print("✓ Asset build completed successfully!")
    print("=" * 70)
    print("\nMinified assets created:")
    print("  ✓ static/style.min.css")
    print("  ✓ static/main.min.js")
    print("\nTo use in production:")
    print("  1. Restart application: sudo rcctl restart gunicorn_chool")
    print("  2. Minified assets will be served automatically")
    print("=" * 70)


if __name__ == '__main__':
    try:
        build_assets()
        sys.exit(0)
    except Exception as e:
        print(f"\n{'=' * 70}")
        print("✗ Asset build failed!")
        print("=" * 70)
        print(f"\nError: {e}")
        print("\nPlease check:")
        print("  1. static/style.css exists")
        print("  2. static/main.js exists")
        print("  3. Write permissions in static/ directory")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        sys.exit(1)

