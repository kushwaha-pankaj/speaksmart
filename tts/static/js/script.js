// DOM Elements
const textInput = document.getElementById("textInput");
const voiceSelect = document.getElementById("voiceSelect");
const generateButton = document.getElementById("generateButton");
const playButton = document.getElementById("playButton");
const pauseButton = document.getElementById("pauseButton");
const downloadButton = document.getElementById("downloadButton");
const clearButton = document.getElementById("clearButton");
const audioInfoContainer = document.getElementById("audioInfoContainer");
const audioDuration = document.getElementById("audioDuration");
const audioSize = document.getElementById("audioSize");
const audioProgressBar = document.getElementById("audioProgressBar");

let audioURL = ""; // Store the generated audio URL
let audioElement = null; // Audio element for playback

// Populate the voice selection dropdown
const availableVoices = [
    // American voices (value starts with 'a')
    { name: "Default (Bella & Sarah) - American", value: "af" },
    { name: "Bella - American", value: "af_bella" },
    { name: "Sarah - American", value: "af_sarah" },
    { name: "Sky - American", value: "af_sky" },
    { name: "Adam - American", value: "am_adam" },
    { name: "Michael - American", value: "am_michael" },
    { name: "Nicole - American", value: "af_nicole" },
    
    // British voices (value starts with 'b')
    { name: "Emma - British", value: "bf_emma" },
    { name: "Isabella - British", value: "bf_isabella" },
    { name: "George - British", value: "bm_george" },
    { name: "Lewis - British", value: "bm_lewis" },

    
];


// Populate the dropdown dynamically
availableVoices.forEach((voice) => {
    const option = document.createElement("option");
    option.value = voice.value;
    option.textContent = voice.name;
    voiceSelect.appendChild(option);
});

// Clear Input Field
clearButton.addEventListener("click", () => {
    textInput.value = ""; // Clear text input
    audioURL = ""; // Clear audio URL
    playButton.style.display = "none"; // Hide Play button
    pauseButton.style.display = "none"; // Hide Pause button
    downloadButton.style.display = "none"; // Hide Download button
    audioInfoContainer.style.display = "none"; // Hide audio info
    audioProgressBar.style.width = "0%"; // Reset progress bar
    generateButton.innerHTML = '<i class="fas fa-cog"></i> Generate'; // Reset Generate button text
    generateButton.disabled = false; // Enable Generate button
    voiceSelect.disabled = false; // Re-enable voice selection
    if (audioElement) {
        audioElement.pause();
        audioElement = null;
    }
});

// Generate Audio
generateButton.addEventListener("click", async (e) => {
    e.preventDefault(); // Prevent form submission

    const text = textInput.value.trim();
    const voice = voiceSelect.value || "af"; // Default to 'af' if no voice is selected

    if (!text) {
        alert("Please enter some text.");
        return;
    }

    // Disable button and show loading state
    generateButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
    generateButton.disabled = true;
    voiceSelect.disabled = true; // Disable voice selection during generation

    try {
        // Send POST request to Django backend to generate audio
        const response = await fetch("/generate-audio/", {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
                "X-CSRFToken": getCookie("csrftoken"), // CSRF token
            },
            body: `text=${encodeURIComponent(text)}&voice=${encodeURIComponent(voice)}`,
        });

        if (response.ok) {
            const data = await response.json();
            audioURL = data.audio_url; // Set the generated audio URL

            // Use file size from the response
            const fileSize = data.file_size;
            audioElement = new Audio(audioURL);
            audioElement.addEventListener("loadedmetadata", () => {
                const minutes = Math.floor(audioElement.duration / 60);
                const seconds = Math.floor(audioElement.duration % 60);
                audioDuration.innerText = `Duration: ${minutes}:${seconds.toString().padStart(2, "0")}`;
                audioSize.innerText = `Size: ${fileSize}`;
                audioInfoContainer.style.display = "block"; // Show audio info
            });

            // Show Play button, hide Pause button, enable Download button
            playButton.style.display = "inline-block";
            pauseButton.style.display = "none";
            downloadButton.style.display = "inline-block";

            // Set the href for the download button
            downloadButton.href = audioURL;
            downloadButton.setAttribute("download", audioURL.split("/").pop());

            generateButton.innerHTML = '<i class="fas fa-check"></i> Generated';
            generateButton.disabled = true; // Disable Generate button after generation
        } else {
            const errorData = await response.json();
            alert(`Error: ${errorData.error || "Failed to generate audio."}`);
            voiceSelect.disabled = false; // Re-enable voice selection on error
        }
    } catch (error) {
        console.error("Error generating audio:", error);
        alert("Failed to generate audio. Please try again later.");
        generateButton.innerHTML = '<i class="fas fa-cog"></i> Generate';
        generateButton.disabled = false; // Re-enable the button on error
        voiceSelect.disabled = false; // Re-enable voice selection on error
    }
});

// Play Audio
playButton.addEventListener("click", () => {
    if (!audioURL || !audioElement) {
        alert("No audio available to play. Please generate the audio first.");
        return;
    }

    audioElement.play();
    playButton.style.display = "none";
    pauseButton.style.display = "inline-block";

    audioElement.addEventListener("timeupdate", () => {
        const progress = (audioElement.currentTime / audioElement.duration) * 100;
        audioProgressBar.style.width = `${progress}%`;
    });

    audioElement.addEventListener("ended", () => {
        playButton.style.display = "inline-block";
        pauseButton.style.display = "none";
        audioProgressBar.style.width = "0%";
    });
});

// Pause Audio
pauseButton.addEventListener("click", () => {
    if (audioElement) {
        audioElement.pause();
        playButton.style.display = "inline-block";
        pauseButton.style.display = "none";
    }
});

// Utility Function to Get CSRF Token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === `${name}=`) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
