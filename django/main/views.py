from .cache import CACHE_STORE
from .JsonResponse import JsonResponse
from .services import *
from .utils import *
from django.shortcuts import render
from django import forms
from django.conf import settings
from django.http import HttpResponse
from pydantic import ValidationError
import time

MAX_TEXT_LENGTH = 200

class InputForm(forms.Form):
    jp_text = forms.CharField(
        max_length = MAX_TEXT_LENGTH,    
        label='Enter Japanese text (max 200 characters)',  
        required=False,  
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                'rows': 4,                 
            }            
        )
    )
    image_file = forms.FileField(
        label='Upload an image with Japanese text. Larger files may take longer to process.', 
        required = False,
        widget=forms.FileInput(
            attrs={
                "accept": "image/*",
                "class": "form-control"
            }
        )
    )

def analyze(request):
    key = str(request.GET.get('key', '')).strip()
    json_result = ''

    if CACHE_STORE.has_analysis(key):
        json_result = CACHE_STORE.get_analysis(key)        
    else:
        jp_text = CACHE_STORE.get_original_text(key)
        json_result = openAI_analyze(jp_text) 

        try: 
            JsonResponse.model_validate_json(json_result) 
            CACHE_STORE.add_analysis(key, json_result)  
        except ValidationError as e:
            print(json_result)
            print(e)
            json_result = '{}'
                 
    return HttpResponse(json_result, content_type='application/json')


    
def index(request):
    form = InputForm()
        
    if request.method == 'GET':
        return render(request, 'index.html', {'form': form})
    
    elif request.method == 'POST':
        return translate_only(request)
    
    else:
        error_message = 'Something went wrong. Please try again later.'
        return render(request, 'index.html', {'form': form, 'error_message': error_message})


def translate_only(request):
        
        form = InputForm(request.POST, request.FILES)
        error_message = ''
        time_taken = 'Time Taken:  '

        if not form.is_valid():
            error_message = 'Invalid input. Please enter Japanese text only.'
            return render(request, 'index.html', {'form': form, 'error_message': error_message})

        uploaded_file = form.files['image_file'] if form.files else None
        
        if uploaded_file:
            start_time = time.time()        
            jp_text = extract_text_from_image(uploaded_file)
            end_time = time.time()
            time_taken += f"{end_time - start_time:.2f} seconds (OCR), "   
            if len(jp_text) > MAX_TEXT_LENGTH:
                jp_text = jp_text[:MAX_TEXT_LENGTH]         
                error_message = "**Text in image has exceeded the allowed limit. Extra characters are trimmed."       
        else:
            jp_text = form.cleaned_data['jp_text']

        key = CACHE_STORE.get_key(jp_text)
        if CACHE_STORE.has_translation(key):
            result = CACHE_STORE.get_translation(key)
            time_taken += '0 seconds (translation)'
        else:
            start_time = time.time()        
            result = openAI_translate(jp_text)    
            end_time = time.time()
            time_taken += f"{end_time - start_time:.2f} seconds (translation)"
            CACHE_STORE.add_translation(jp_text=jp_text, en_text=result)

        if not result:
            error_message = 'Unable to process request. Please try again later.'
            return render(request, 'index.html', {'form': form, 'error_message': error_message})


        context = {
            'error_message': error_message,
            'input_text': jp_text,
            'key' : key,
            'translation': result
        }

        if settings.DEBUG:
            context['mode'] = 'debug'
            context['time_taken'] = time_taken

        return render(request, 'translate.html', context)
            