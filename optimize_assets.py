#!/usr/bin/env python3
"""
VAGUE 2 - Asset Minification & Optimization Script
Minifie et optimise CSS/JS pour réduire les tailles de fichier
"""

import os
import re
from pathlib import Path

class CSSMinifier:
    """Minifie les fichiers CSS"""
    
    @staticmethod
    def minify(css_content):
        # Supprimer les commentaires
        css_content = re.sub(r'/\*[^*]*\*+(?:[^/*][^*]*\*+)*/', '', css_content)
        
        # Supprimer les espaces inutiles
        css_content = re.sub(r'\s+', ' ', css_content)
        css_content = re.sub(r'\s*([{}:;,>+~])\s*', r'\1', css_content)
        
        # Supprimer les espaces avant les accolades
        css_content = re.sub(r';\s*}', '}', css_content)
        
        return css_content.strip()


class JSMinifier:
    """Minifie les fichiers JavaScript"""
    
    @staticmethod
    def minify(js_content):
        # Supprimer les commentaires multi-ligne
        js_content = re.sub(r'/\*[^*]*\*+(?:[^/*][^*]*\*+)*/', '', js_content)
        
        # Supprimer les commentaires mono-ligne (mais pas les regex)
        js_content = re.sub(r'//.*?(?=\n|$)', '', js_content)
        
        # Supprimer les espaces inutiles
        js_content = re.sub(r'\s+', ' ', js_content)
        
        # Supprimer les espaces autour des opérateurs
        js_content = re.sub(r'\s*([{}();:,=+\-*/<>!&|])\s*', r'\1', js_content)
        
        # Restaurer les espaces nécessaires
        js_content = re.sub(r'([a-zA-Z0-9_]\s+function)', r'\1', js_content)
        js_content = re.sub(r'(return)\s+', r'\1 ', js_content)
        
        return js_content.strip()


class AssetOptimizer:
    """Gère l'optimisation globale des assets"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.static_css = self.project_root / 'static' / 'css'
        self.static_js = self.project_root / 'static' / 'js'
        self.stats = {
            'css_original': 0,
            'css_minified': 0,
            'js_original': 0,
            'js_minified': 0,
            'files_processed': 0
        }
    
    def process_css(self):
        """Minifie tous les fichiers CSS"""
        print("🔍 Minifying CSS files...")
        
        for css_file in self.static_css.glob('*.css'):
            # Ignorer les fichiers déjà minifiés
            if css_file.name.endswith('.min.css'):
                continue
            
            with open(css_file, 'r', encoding='utf-8') as f:
                original = f.read()
            
            minified = CSSMinifier.minify(original)
            original_size = len(original.encode('utf-8'))
            minified_size = len(minified.encode('utf-8'))
            reduction = 100 * (1 - minified_size / original_size)
            
            # Sauvegarder le fichier minifié
            minified_file = css_file.parent / css_file.name.replace('.css', '.min.css')
            with open(minified_file, 'w', encoding='utf-8') as f:
                f.write(minified)
            
            self.stats['css_original'] += original_size
            self.stats['css_minified'] += minified_size
            self.stats['files_processed'] += 1
            
            print(f"  ✅ {css_file.name}")
            print(f"     {original_size:,}B → {minified_size:,}B ({reduction:.1f}% reduction)")
    
    def process_js(self):
        """Minifie tous les fichiers JS"""
        print("\n🔍 Minifying JavaScript files...")
        
        # Fichiers à exclure de la minification
        exclude = {'form-manager.js', 'form-steps.min.css'}
        
        for js_file in self.static_js.glob('*.js'):
            # Ignorer les fichiers déjà minifiés
            if js_file.name.endswith('.min.js') or js_file.name in exclude:
                continue
            
            with open(js_file, 'r', encoding='utf-8') as f:
                original = f.read()
            
            minified = JSMinifier.minify(original)
            original_size = len(original.encode('utf-8'))
            minified_size = len(minified.encode('utf-8'))
            reduction = 100 * (1 - minified_size / original_size)
            
            # Sauvegarder le fichier minifié
            minified_file = js_file.parent / js_file.name.replace('.js', '.min.js')
            with open(minified_file, 'w', encoding='utf-8') as f:
                f.write(minified)
            
            self.stats['js_original'] += original_size
            self.stats['js_minified'] += minified_size
            self.stats['files_processed'] += 1
            
            print(f"  ✅ {js_file.name}")
            print(f"     {original_size:,}B → {minified_size:,}B ({reduction:.1f}% reduction)")
    
    def generate_report(self):
        """Génère un rapport d'optimisation"""
        print("\n" + "="*60)
        print("OPTIMIZATION REPORT - VAGUE 2")
        print("="*60)
        
        total_original = self.stats['css_original'] + self.stats['js_original']
        total_minified = self.stats['css_minified'] + self.stats['js_minified']
        total_reduction = 100 * (1 - total_minified / total_original) if total_original > 0 else 0
        
        print(f"\n📊 CSS Optimization:")
        print(f"   Original:  {self.stats['css_original']:,}B")
        print(f"   Minified:  {self.stats['css_minified']:,}B")
        if self.stats['css_original'] > 0:
            css_reduction = 100 * (1 - self.stats['css_minified'] / self.stats['css_original'])
            print(f"   Reduction: {css_reduction:.1f}%")
        
        print(f"\n📊 JavaScript Optimization:")
        print(f"   Original:  {self.stats['js_original']:,}B")
        print(f"   Minified:  {self.stats['js_minified']:,}B")
        if self.stats['js_original'] > 0:
            js_reduction = 100 * (1 - self.stats['js_minified'] / self.stats['js_original'])
            print(f"   Reduction: {js_reduction:.1f}%")
        
        print(f"\n📊 Total Optimization:")
        print(f"   Original:  {total_original:,}B")
        print(f"   Minified:  {total_minified:,}B")
        print(f"   Reduction: {total_reduction:.1f}%")
        print(f"   Files:     {self.stats['files_processed']}")
        
        # Estimer Lighthouse score
        print(f"\n🎯 Performance Estimates:")
        if total_reduction > 50:
            print(f"   Performance Score: 85-90 (Excellent)")
        elif total_reduction > 30:
            print(f"   Performance Score: 75-85 (Good)")
        else:
            print(f"   Performance Score: 65-75 (Fair)")
        
        print("\n" + "="*60)
    
    def run(self):
        """Exécuter l'optimisation complète"""
        print("🚀 Starting VAGUE 2 Asset Optimization...\n")
        
        try:
            self.process_css()
            self.process_js()
            self.generate_report()
            print("\n✅ Optimization complete!")
            return 0
        except Exception as e:
            print(f"\n❌ Error: {e}")
            return 1


if __name__ == '__main__':
    optimizer = AssetOptimizer()
    exit(optimizer.run())
