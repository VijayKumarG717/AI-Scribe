// Prevent default drag behaviors on the entire page (but allow dropzones to handle)
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    document.addEventListener(eventName, function(e) {
        // Only prevent default if the target is not a dropzone
        if (!e.target.closest('#audio_dropzone') && !e.target.closest('#text_dropzone')) {
            e.preventDefault();
            e.stopPropagation();
        }
    }, false);
});

// Wait for DOM to load
document.addEventListener('DOMContentLoaded', function() {
    const inputTypeSelect = document.getElementById('input_type');
    const audioSection = document.getElementById('audio_section');
    const textSection = document.getElementById('text_section');
    const templateTypeSelect = document.getElementById('template_type');
    const audioTemplateType = document.getElementById('audio_template_type');
    const textTemplateType = document.getElementById('text_template_type');
    
    // Audio upload elements
    const audioDropzone = document.getElementById('audio_dropzone');
    const audioFileInput = document.getElementById('audio_file');
    const audioFilename = document.getElementById('audio_filename');
    const audioForm = document.getElementById('audio_form');
    const transcribeBtn = document.getElementById('transcribe_btn');
    const audioLoading = document.getElementById('audio_loading');
    let droppedAudioFile = null; // Store dropped file
    
    // Text upload elements
    const textDropzone = document.getElementById('text_dropzone');
    const textFileInput = document.getElementById('text_file');
    const textFilename = document.getElementById('text_filename');
    const textForm = document.getElementById('text_form');
    const processTextBtn = document.getElementById('process_text_btn');
    const textLoading = document.getElementById('text_loading');
    let droppedTextFile = null; // Store dropped file
    
    // Sync template type to both forms
    function syncTemplateType() {
        const selectedTemplate = templateTypeSelect.value;
        audioTemplateType.value = selectedTemplate;
        textTemplateType.value = selectedTemplate;
    }
    
    // Initialize template type sync
    syncTemplateType();
    templateTypeSelect.addEventListener('change', syncTemplateType);
    
    // Handle input type change
    inputTypeSelect.addEventListener('change', function() {
        const selectedType = inputTypeSelect.value;
        
        if (selectedType === 'audio') {
            audioSection.classList.remove('hidden');
            textSection.classList.add('hidden');
        } else {
            audioSection.classList.add('hidden');
            textSection.classList.remove('hidden');
        }
    });
    
    // Audio dropzone functionality
    audioDropzone.addEventListener('click', function() {
        audioFileInput.click();
    });
    
    audioFileInput.addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            const file = e.target.files[0];
            droppedAudioFile = file;
            audioFilename.textContent = `Selected: ${file.name}`;
            audioFilename.classList.remove('hidden');
            transcribeBtn.disabled = false;
        }
    });
    
    // Audio drag and drop
    audioDropzone.addEventListener('dragover', function(e) {
        e.preventDefault();
        audioDropzone.classList.add('drag-over');
    });
    
    audioDropzone.addEventListener('dragleave', function(e) {
        e.preventDefault();
        audioDropzone.classList.remove('drag-over');
    });
    
    audioDropzone.addEventListener('drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
        audioDropzone.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            const file = files[0];
            const fileExtension = file.name.split('.').pop().toLowerCase();
            const allowedExtensions = ['mp3', 'wav', 'm4a'];
            
            if (allowedExtensions.includes(fileExtension)) {
                // Create a new DataTransfer object to set files
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(file);
                audioFileInput.files = dataTransfer.files;
                droppedAudioFile = file;
                audioFilename.textContent = `Selected: ${file.name}`;
                audioFilename.classList.remove('hidden');
                transcribeBtn.disabled = false;
            } else {
                alert('Please upload a valid audio file (MP3, WAV, or M4A)');
            }
        }
    });
    
    // Text dropzone functionality
    textDropzone.addEventListener('click', function() {
        textFileInput.click();
    });
    
    textFileInput.addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            const file = e.target.files[0];
            droppedTextFile = file;
            textFilename.textContent = `Selected: ${file.name}`;
            textFilename.classList.remove('hidden');
            
            // Read text file content
            if (file.name.endsWith('.txt')) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    document.getElementById('text_input').value = e.target.result;
                };
                reader.readAsText(file);
            }
        }
    });
    
    // Text drag and drop
    textDropzone.addEventListener('dragover', function(e) {
        e.preventDefault();
        textDropzone.classList.add('drag-over');
    });
    
    textDropzone.addEventListener('dragleave', function(e) {
        e.preventDefault();
        textDropzone.classList.remove('drag-over');
    });
    
    textDropzone.addEventListener('drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
        textDropzone.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            const file = files[0];
            const fileExtension = file.name.split('.').pop().toLowerCase();
            const allowedExtensions = ['txt', 'docx'];
            
            if (allowedExtensions.includes(fileExtension)) {
                // Create a new DataTransfer object to set files
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(file);
                textFileInput.files = dataTransfer.files;
                droppedTextFile = file;
                textFilename.textContent = `Selected: ${file.name}`;
                textFilename.classList.remove('hidden');
                
                // Read text file content if it's a .txt file
                if (fileExtension === 'txt') {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        document.getElementById('text_input').value = e.target.result;
                    };
                    reader.readAsText(file);
                }
            } else {
                alert('Please upload a valid text file (TXT or DOCX)');
            }
        }
    });
    
    // Audio form submission
    audioForm.addEventListener('submit', function(e) {
        const file = droppedAudioFile || (audioFileInput.files && audioFileInput.files[0]);
        if (!file) {
            e.preventDefault();
            alert('Please select an audio file');
            return;
        }
        transcribeBtn.disabled = true;
        audioLoading.classList.remove('hidden');
    });
    
    // Text form submission
    textForm.addEventListener('submit', function(e) {
        const textInput = document.getElementById('text_input').value.trim();
        const file = droppedTextFile || (textFileInput.files && textFileInput.files[0]);
        const hasFile = !!file;
        
        if (!textInput && !hasFile) {
            e.preventDefault();
            alert('Please enter text or upload a file');
            return;
        }
        
        processTextBtn.disabled = true;
        textLoading.classList.remove('hidden');
    });
});

