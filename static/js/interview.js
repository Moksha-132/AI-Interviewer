const webcam = document.getElementById('webcam');
const chatMessages = document.getElementById('chatMessages');
const startBtn = document.getElementById('startBtn');
const listenBtn = document.getElementById('listenBtn');
const endBtn = document.getElementById('endBtn');

let recognition;
let ollamaContext = [];
const candidateName = "{{ name }}";

// Initialize Speech Recognition
if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.lang = 'en-US';
    recognition.interimResults = false;

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        addMessage(transcript, 'user');
        sendToAI(transcript);
        listenBtn.innerText = 'SPEAK NOW';
        listenBtn.style.opacity = '1';
    };

    recognition.onerror = (event) => {
        console.error("Speech Rec Error:", event.error);
        listenBtn.innerText = 'MIC ERROR - TRY AGAIN';
    };
} else {
    alert("Speech Recognition is not supported in this browser. Please use Chrome or Edge.");
}

// Camera Access
async function initCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
        webcam.srcObject = stream;
    } catch (err) {
        console.error("Camera access denied:", err);
        document.getElementById('camStatus').className = 'status-badge status-off';
        document.getElementById('camStatus').innerText = 'CAM ERROR';
    }
}

function addMessage(text, sender) {
    const div = document.createElement('div');
    div.className = `message msg-${sender}`;
    div.innerText = text;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function speak(text) {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1;
    utterance.pitch = 1;
    window.speechSynthesis.speak(utterance);
    
    // Stop recognition while AI is speaking
    utterance.onstart = () => recognition.abort();
    utterance.onend = () => {
        listenBtn.style.display = 'inline-block';
    };
}

async function sendToAI(text) {
    listenBtn.style.display = 'none';
    const response = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: text, context: ollamaContext })
    });
    
    const data = await response.json();
    if (data.response) {
        ollamaContext = data.context;
        addMessage(data.response, 'ai');
        speak(data.response);
    }
}

startBtn.onclick = async () => {
    await initCamera();
    startBtn.style.display = 'none';
    endBtn.style.display = 'inline-block';
    
    const greeting = `Hello! I am your AI interviewer today. Thank you for joining. Let's start the interview. Can you please introduce yourself?`;
    addMessage(greeting, 'ai');
    speak(greeting);
};

listenBtn.onclick = () => {
    listenBtn.innerText = 'LISTENING...';
    listenBtn.style.opacity = '0.5';
    recognition.start();
};

endBtn.onclick = () => {
    window.location.href = '/';
};
