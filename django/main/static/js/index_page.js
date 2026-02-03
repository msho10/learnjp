
$(document).ready(function() {
    $('#upload_animation').hide();
    const photoInput = document.getElementById('id_image_file');
    photoInput.addEventListener('change', function(event) {
        const file = event.target.files[0];
        if (file) {
            $('#input_form').submit();
            $('#input_container').hide();
            $('#upload_animation').show();
        }
    });

    const inputForm = document.getElementById('input_form');
    const textArea = document.getElementById('id_jp_text');
    const error_msg = document.getElementById('error_message');
    inputForm.addEventListener('submit', function(event) {
        input_text = textArea.value;
        if (!isJapanese(input_text)) {
            error_msg.textContent = "Input is not Japanese. Please enter Japanese text only.";
            // Prevent the form from actually submitting
            event.preventDefault();
        }
        else {
            error_msg.textContent = "";
        }
    });
});

/**
 * Check for Japanese text including punctuation and full-width forms.
 */
function isJapanese(text, minRatio = 0.3) {
    if (!text) return false;

    // Ranges:
    // Hiragana: \u3040-\u309F
    // Katakana: \u30A0-\u30FF
    // Kanji: \u4E00-\u9FFF
    // Japanese Punctuation: \u3000-\u303F
    // Full-width Romaji/Forms: \uFF00-\uFFEF
    const japaneseRegex = /[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\u3000-\u303F\uFF00-\uFFEF]/g;
    
    const japaneseChars = text.match(japaneseRegex) || [];
    
    // Total "meaningful" characters now includes letters, numbers, and symbols
    // to ensure the denominator matches the complexity of the input.
    const meaningfulChars = text.match(/[\p{L}\p{N}\p{P}]/gu) || [];

    if (meaningfulChars.length === 0) return false;

    const ratio = japaneseChars.length / meaningfulChars.length;
    
    return ratio >= minRatio;
}