const DELAY_MS = 30; 

// A simple debounce utility function
function debounce(callback, delay) {
  let timer;
  return function() {
    const context = this;
    const args = arguments;
    clearTimeout(timer); // Clear the previous timer (the "reset" mechanism)
    timer = setTimeout(() => {
      callback.apply(context, args);
    }, delay);
  };
}

function fetchMA(key) {

    const startTime = performance.now();
    fetch("/analyze?key=" + key)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            const endTime = performance.now();
            const timeTaken = (endTime - startTime)/1000;
            
            let mode = $('#mode').val();
            if (mode.toLowerCase() == 'debug') 
                $('#ma_time').text(`Time taken: ${timeTaken.toFixed(2)} seconds`);

            $('#translation_animation').hide();
            showAnalysisResult(data);            
        })
        .catch(error => {
            console.error('There was a problem with the fetch operation:', error);
        });
}

function handleMouseOver() {
    $(this).addClass('bg-warning');
    $(this).popover({        
        placement: 'bottom',
        html: true,
        title: $(this).data('romaji'),
        content: $(this).data('baseForm') + '&nbsp;[' + $(this).data('pos') + ']' + '<hr>' + $(this).data('english')
    });
    $(this).popover('show');
}

function handleMouseLeave() {
    $(this).popover('hide');
    $(this).removeClass('bg-warning');
}

function returnMorphemesInHTML(bunsetsu) {
    var resultHtml = '';
    var index = 0, next = 0;
    var tokenId = 0;
    var morphemes = bunsetsu.morphological_analysis;

    while (tokenId < morphemes.length) {
        index = bunsetsu.japanese_phrase.indexOf(morphemes[tokenId].surface_form, next);
        if (index < 0) { 
            console.log("phrase: " + bunsetsu.japanese_phrase + " unknown morpheme: " + morphemes[tokenId].surface_form);
            //server can return invalid (nonexist) morpheme. When that happens, try the next morpheme. 
            tokenId += 1;
            continue;
        }
        else if (index != next) {
            //some words in the phrase are being skipped (no morpheme for them)
            missing_words = bunsetsu.japanese_phrase.slice(next, index).trim();
            if (missing_words.length > 0) {
                console.log(`phrase: ${bunsetsu.japanese_phrase} missinng morpheme: ${missing_words} `);
                resultHtml += missing_words;
            }           
        }
        next = index + morphemes[tokenId].surface_form.length;
        resultHtml += `<span data-base-form='${morphemes[tokenId].base_form}' data-english='${morphemes[tokenId].english_explanation}' `; 
        resultHtml += `data-pos='${morphemes[tokenId].POS}' data-romaji='${morphemes[tokenId].romaji}'>${morphemes[tokenId].surface_form}</span>`;
        tokenId += 1;       
    }            
    
    return resultHtml;
}
        

function showAnalysisResult(result) {
    var $bunsetsu = $('#bunsetsu_container');
    $bunsetsu.show();    
    
    if (!result || !result.bunsetsu_breakdown) {
        $('#ma_error').html('Something went wrong. Unable to do morthological analysis.');
    }
    else {
        resultHtml = '';
        tokenId = 0;
        (result.bunsetsu_breakdown).forEach(bunsetsu => {
            morphemes = returnMorphemesInHTML(bunsetsu);
            resultHtml += "<div class='row border-bottom pb-2 mb-2'><div class='col-4'>" + morphemes + "</div><div class='col'>" + bunsetsu.english_translation + "</div></div>";
        });
        $('#bunsetsu_phrases').html(resultHtml);

        //Delegate the event only targetting 'span' elements 
        $bunsetsu.on('mouseenter', 'span', handleMouseOver);
        $bunsetsu.on('mouseleave', 'span', handleMouseLeave);    
    }
}

$(document).ready(function() {
    var $bunsetsu = $('#bunsetsu_container');
    $bunsetsu.hide();

    key = $('#key').val();
    fetchMA(key);                
});