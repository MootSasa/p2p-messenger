import json
import os

class Translator:
    def __init__(self, lang="en"):
        self.lang = lang
        self.translations = {}
        self.load_lang(lang)

    def load_lang(self, lang: str):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        filepath = os.path.join(base_dir, 'locales', f'{lang}.json')
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
        except FileNotFoundError:
            print(f"[!] Warning: Language file {lang}.json not found. Fallback to keys.")
            self.translations = {}

    def t(self, key: str, **kwargs) -> str:
        text = self.translations.get(key, key)
        
        if kwargs:
            try:
                return text.format(**kwargs)
            except KeyError as e:
                return f"{text} (Missing format var: {e})"
        return text
    
_ = Translator("en")
