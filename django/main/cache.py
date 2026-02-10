from collections import deque
from django.conf import settings
from typing import NamedTuple

class Translation(NamedTuple):
    english: str
    japanese: str

class CacheStore:

    def __init__(self):        
        self._request_queue = deque()
        self._translation_cache = {}
        self._analysis_cache = {}

    def add_translation(self, jp_text: str, en_text: str) -> str:
        self._checkCacheLimit()        
        
        key = str(hash(jp_text))
        self._request_queue.append(key)        
        self._translation_cache[key] = Translation(japanese=jp_text, english=en_text)
        
        return key
    
    def add_analysis(self, key: str, analysis: str) -> str:
        self._analysis_cache[key] = analysis
        
        return key

    def get_analysis(self, key: str) -> str:
        if key in self._analysis_cache:
            return self._analysis_cache[key]
        return ''

    def get_key(self, jp_text: str) -> str:
        return str(hash(jp_text))

    def get_original_text(self, key: str) -> str:    
        if key in self._translation_cache:
            return self._translation_cache[key].japanese
        return ''

    def get_translation(self, key: str) -> str:
        if key in self._translation_cache:
            return self._translation_cache[key].english
        return ''

    def has_analysis(self, key: str) -> bool:
        return key in self._analysis_cache
    
    def has_translation(self, key: str) -> bool:
        return key in self._translation_cache

    def _checkCacheLimit(self):
        if len(self._request_queue) >= settings.CACHE_SIZE:
            # hitting cache limit, remove the oldest entry
            del_key = self._request_queue.popleft()
            if del_key in self._translation_cache:
                del self._translation_cache[del_key]
            if del_key in self._analysis_cache:
                del self._analysis_cache[del_key]

CACHE_STORE = CacheStore()