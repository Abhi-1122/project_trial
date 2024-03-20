function openImageUploadForm() {
    document.getElementById('uploadForm').style.display = 'block';
    document.getElementById('dropdowns').style.display = 'block';
}

function allowDrop(event) {
    event.preventDefault();
    document.getElementById('uploadForm').classList.add('dragover');
}

function handleDrop(event) {
    event.preventDefault();
    document.getElementById('uploadForm').classList.remove('dragover');
    var files = event.dataTransfer.files;
    handleFiles(files);
}

function handleFiles(files) {
    var previewFiles = document.getElementById('previewFiles');
    var defaultDuration = document.getElementById('defaultDurationInput').value;

    for (var i = 0; i < files.length; i++) {
        var file = files[i];

        if (file.type.startsWith('image/')) {
            // Use closure to capture the correct file
            (function (file) {
                var reader = new FileReader();

                reader.onload = function (e) {
                    var imageContainer = document.createElement('div');
                    imageContainer.classList.add('image-container');

                    var img = document.createElement('img');
                    img.src = e.target.result;
                    img.classList.add('scaled-image'); // Add this line to apply styling

                    var durationInput = document.createElement('input');
                    durationInput.type = 'number';
                    durationInput.placeholder = 'Duration (in seconds)';
                    durationInput.value = defaultDuration;
                    durationInput.classList.add('form-control', 'mb-2', 'w-full', 'md:w-1/2', 'mx-auto');

                    imageContainer.appendChild(img);
                    imageContainer.appendChild(durationInput);

                    previewFiles.appendChild(imageContainer);
                    var toggleSwitch = document.createElement('label');
                    toggleSwitch.classList.add('toggle-switch');
                    var input = document.createElement('input');
                    input.type = 'checkbox';
                    input.checked = true;
                    var slider = document.createElement('span');
                    slider.classList.add('slider', 'round');
                    toggleSwitch.appendChild(input);
                    toggleSwitch.appendChild(slider);
                    imageContainer.appendChild(toggleSwitch);
                };

                reader.readAsDataURL(file);
            })(file);
        } else if (file.type.startsWith('audio/')) {
            // Handle audio files
            var audioContainer = document.createElement('div');
            audioContainer.classList.add('image-container');

            var audioPlayer = document.createElement('audio');
            audioPlayer.src = URL.createObjectURL(file);
            audioPlayer.controls = false;
            audioPlayer.classList.add('scaled-image'); // Add this line to apply styling

            var playPauseBtn = document.createElement('button');
            playPauseBtn.textContent = 'Play';
            playPauseBtn.addEventListener('click', function () {
                toggleAudioPlayback(audioPlayer, playPauseBtn);
            });

            var progressBar = document.createElement('progress');
            progressBar.value = 0;
            progressBar.max = 100;

            var durationInput = document.createElement('input');
            durationInput.type = 'number';
            durationInput.placeholder = 'Duration (in seconds)';
            durationInput.value = defaultDuration;
            durationInput.classList.add('form-control', 'mb-2', 'w-full', 'md:w-1/2', 'mx-auto');

            audioContainer.appendChild(audioPlayer);
            audioContainer.appendChild(playPauseBtn);
            audioContainer.appendChild(progressBar);
            audioContainer.appendChild(durationInput);

            previewFiles.appendChild(audioContainer);
            var toggleSwitch = document.createElement('label');
        toggleSwitch.classList.add('toggle-switch');
        var input = document.createElement('input');
        input.type = 'checkbox';
        input.checked = true;
        var slider = document.createElement('span');
        slider.classList.add('slider', 'round');
        toggleSwitch.appendChild(input);
        toggleSwitch.appendChild(slider);
        audioContainer.appendChild(toggleSwitch);
        }
    }
}

function toggleAudioPlayback(audio, playPauseBtn) {
    if (audio.paused) {
        audio.play();
        playPauseBtn.textContent = 'Pause';
        updateProgressBar(audio);
    } else {
        audio.pause();
        playPauseBtn.textContent = 'Play';
    }
}

function updateProgressBar(audio) {
    var progressBar = audio.nextElementSibling.nextElementSibling; // Accessing the progress bar
    var durationInput = audio.nextElementSibling.nextElementSibling.nextElementSibling; // Accessing the duration input

    audio.addEventListener('timeupdate', function () {
        var progressValue = (audio.currentTime / audio.duration) * 100;
        progressBar.value = progressValue;

        // Update duration input with current time
        durationInput.value = Math.floor(audio.currentTime);

        if (audio.currentTime === audio.duration) {
            // Reset play button and progress bar when the audio ends
            playPauseBtn.textContent = 'Play';
            progressBar.value = 0;
        }
    });
}

// Rest of the code remains unchanged

function generateVideo() {
    var imageContainers = document.querySelectorAll('.image-container');
    var defaultDuration = document.getElementById('defaultDurationInput').value;
    var selectedTransition = document.getElementById('transitionSelect').value;
    var selectedResolution = document.getElementById('resolutionSelect').value;
    var video = document.getElementById('generatedVideo');
    var prevtext = document.getElementById('textprev');

    video.style.display = 'block';
    textprev.style.display = 'block';
    // Now you can use 'imageContainers', 'defaultDuration', 'selectedTransition', and 'selectedResolution' to create a slideshow
    imageContainers.forEach(function (container) {
        var imgSrc = container.querySelector('img').src;
        var durationInput = container.querySelector('input');
        var duration = durationInput.value || defaultDuration;

        // Implement your logic to create a slideshow using 'imgSrc', 'duration', 'selectedTransition', and 'selectedResolution'
        console.log('Image Source:', imgSrc, 'Duration:', duration, 'Transition:', selectedTransition, 'Resolution:', selectedResolution);
    });
}

// Open file input when clicking on the upload form
function uploadclick() {
    document.getElementById('fileInput').click();
}
document.getElementById('uploadForm').addEventListener('click', uploadclick);