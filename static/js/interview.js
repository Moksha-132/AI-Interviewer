const webcam = document.getElementById('webcam');
const chatMessages = document.getElementById('chatMessages');
const startBtn = document.getElementById('startBtn');
const listenBtn = document.getElementById('listenBtn');
const endBtn = document.getElementById('endBtn');
const interviewControls = document.getElementById('interviewControls');
const textInput = document.getElementById('textInput');
const sendTextBtn = document.getElementById('sendTextBtn');

let recognition;
let ollamaContext = [];
let startTime = null;
let isMicActive = false;

// Initialize Speech Recognition
if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false; // We use restart logic for better turn management
    recognition.lang = 'en-US';
    recognition.interimResults = false;

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        handleUserMessage(transcript);
    };

    recognition.onend = () => {
        // If mic is still supposed to be active (and not aborted for AI speech), restart it
        if (isMicActive && !window.speechSynthesis.speaking) {
            try { recognition.start(); } catch(e) {}
        } else if (!window.speechSynthesis.speaking) {
            listenBtn.innerText = 'SPEAK';
            listenBtn.style.background = '#10b981';
        }
    };

    recognition.onerror = (event) => {
        if (event.error === 'no-speech') {
             // Just restart if no speech was detected
             return;
        }
        console.error("Speech Rec Error:", event.error);
        isMicActive = false;
        listenBtn.innerText = 'SPEAK';
    };
}

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
    
    utterance.onstart = () => {
        if (recognition) {
            recognition.abort(); // Stop listening while AI speaks
        }
    };

    utterance.onend = () => {
        // AI finished speaking, resume listening if it was active
        if (isMicActive && recognition) {
            listenBtn.innerText = 'LISTENING...';
            listenBtn.style.background = '#ef4444'; // Red for listening
            try { recognition.start(); } catch(e) {}
        } else {
            listenBtn.innerText = 'SPEAK';
        }
    };
    
    window.speechSynthesis.speak(utterance);
}

async function handleUserMessage(text) {
    if (!text.trim()) return;
    addMessage(text, 'user');
    textInput.value = '';
    await sendToAI(text);
}

async function sendToAI(text, isInitial = false) {
    const controls = [textInput, sendTextBtn, listenBtn];
    controls.forEach(c => c.disabled = true);
    
    // If it's the user's turn (not initial), we keep the mic active flag
    // so it restarts after the AI replies

    const response = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            prompt: text, 
            context: ollamaContext,
            elapsed_minutes: startTime ? (Date.now() - startTime) / 60000 : 0,
            is_initial: isInitial,
            technology: document.getElementById('techData').value,
            difficulty: document.getElementById('diffData').value
        })
    });
    
    const data = await response.json();
    
    if (data.error) {
        addMessage(`Error: ${data.error}`, 'ai');
    } else {
        let aiResponse = data.response || "";
        const isConcluding = aiResponse.includes('[CONCLUDE]');
        if (isConcluding) aiResponse = aiResponse.replace('[CONCLUDE]', '').trim();

        if (aiResponse) {
            ollamaContext = data.context;
            addMessage(aiResponse, 'ai');
            speak(aiResponse);
            
            if (isConcluding) endInterviewInternally();
        }
    }
    
    controls.forEach(c => c.disabled = false);
}

function endInterviewInternally() {
    isMicActive = false;
    if (recognition) recognition.abort();
    interviewControls.style.display = 'none';
    const msg = document.createElement('div');
    msg.className = 'glass-card';
    msg.style.textAlign = 'center';
    msg.style.padding = '2rem';
    msg.style.marginTop = '2rem';
    msg.style.border = '1px solid #4ade80';
    msg.innerHTML = "<h2 style='color: #4ade80'>Interview Completed</h2><p>Thank you for your time.</p><button onclick='window.location.href=\"/\"' style='margin-top: 1rem;'>Back to Home</button>";
    chatMessages.appendChild(msg);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

startBtn.onclick = async () => {
    startBtn.disabled = true;
    startBtn.innerText = 'Initializing...';
    await initCamera();
    startTime = Date.now();
    startBtn.style.display = 'none';
    interviewControls.style.display = 'flex';
    
    // For the very first question, we can enable auto-listening
    isMicActive = true; 
    await sendToAI("START_INTERVIEW", true);
};

listenBtn.onclick = () => {
    if (recognition) {
        if (isMicActive) {
            // Toggle off
            isMicActive = false;
            recognition.abort();
            listenBtn.innerText = 'SPEAK';
            listenBtn.style.background = '#10b981';
        } else {
            // Toggle on
            isMicActive = true;
            listenBtn.innerText = 'LISTENING...';
            listenBtn.style.background = '#ef4444';
            try { recognition.start(); } catch(e) {}
        }
    } else {
        alert("Speech recognition not supported.");
    }
};

sendTextBtn.onclick = () => handleUserMessage(textInput.value);
textInput.onkeypress = (e) => {
    if (e.key === 'Enter') handleUserMessage(textInput.value);
};

endBtn.onclick = () => {
    if (confirm("Are you sure?")) window.location.href = '/';
};
