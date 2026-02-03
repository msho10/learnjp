from datetime import datetime
from pydantic import BaseModel

class JsonResponse(BaseModel):   
    class Bunsetsu(BaseModel):
        class Morpheme(BaseModel):        
            token_id: int
            surface_form: str
            base_form: str
            POS: str
            english_explanation: str
            romaji: str
    
        index: int
        japanese_phrase: str
        english_translation: str
        morphological_analysis: list[Morpheme]

    create_datetime: datetime
    bunsetsu_breakdown: list[Bunsetsu]
    

    
  