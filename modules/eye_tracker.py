import streamlit.components.v1 as components
import random
import json

def get_eye_tracker_html(initial_mins=25, state=None, guard_enabled=True):
    """Returns the SAMS II Engine with Mute Toggle and Balanced Night-Vision."""
    if state is None: state = {}
    v = random.randint(100, 999) 
    
    html_template = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
        
        #cam-container {
            position: relative; width: 100%; max-width: 800px; margin: 20px auto;
            aspect-ratio: 16/9; z-index: 9; border-radius: 24px; overflow: hidden;
            background: #0d1117; transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            border: 2px solid rgba(6, 182, 212, 0.5);
            box-shadow: 0 0 50px rgba(6, 182, 212, 0.3);
        }
        
        #cam-container.distracted {
            border-color: #ef4444;
            box-shadow: 0 0 70px rgba(239, 68, 68, 0.9), inset 0 0 30px rgba(239, 68, 68, 0.4);
        }
        
        video#webcam { 
            width: 100%; height: 100%; object-fit: cover; transform: scaleX(-1); 
            filter: brightness(1.1) contrast(1.1); 
            display: %%CAM_DISPLAY%%;
        }
        canvas#output_canvas { 
            position: absolute; top: 0; left: 0; width: 100%; height: 100%; 
            transform: scaleX(-1); pointer-events: none; 
            display: %%CAM_DISPLAY%%;
        }
        
        #focus-hud {
            position: absolute; top: 10px; right: 10px; z-index: 1000;
            background: rgba(15, 23, 42, 0.9); backdrop-filter: blur(15px);
            padding: 10px 20px; border-radius: 16px; border: 1px solid rgba(255, 255, 255, 0.1);
            color: white; font-family: 'Inter', sans-serif; display: flex; align-items: center; gap: 15px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
        }
        
        .hud-status { display: flex; flex-direction: column; min-width: 140px; }
        .hud-status .label { font-size: 10px; text-transform: uppercase; letter-spacing: 2px; color: #06b6d4; font-weight: 800; }
        .hud-status .val { font-size: 16px; font-weight: 800; transition: all 0.3s; }

        #timer-box { border-left: 1px solid rgba(255,255,255,0.1); padding-left: 20px; }
        #timer-val { font-size: 24px; font-weight: 900; color: #fbbf24; font-variant-numeric: tabular-nums; }
        
        .btn-group { display: flex; gap: 8px; flex-wrap: wrap; }
        .btn-ctrl { 
            background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); 
            color: white; font-size: 11px; padding: 8px 12px; border-radius: 12px; cursor: pointer;
            font-weight: 800; text-transform: uppercase; transition: 0.2s;
        }
        .btn-ctrl:hover { background: rgba(255,255,255,0.1); border-color: #06b6d4; }
        .btn-stop { color: #ef4444; border-color: rgba(239, 68, 68, 0.2); }
        .btn-stop:hover { background: rgba(239, 68, 68, 0.1); border-color: #ef4444; }
        .btn-mute { color: #a78bfa; border-color: rgba(167,139,250,0.2); font-size: 10px; padding: 6px 10px; }
        .btn-mute.muted { color: #ef4444; border-color: rgba(239,68,68,0.3); }

        #attention-ring { width: 44px; height: 44px; position: relative; display: flex; align-items: center; justify-content: center; }
        svg#progress-svg { transform: rotate(-90deg); width: 44px; height: 44px; }
        circle#progress-circle { fill: none; stroke: #06b6d4; stroke-width: 4; stroke-dasharray: 126; stroke-dashoffset: 126; transition: 0.5s; }
        
        #loading-overlay {
            position: absolute; inset: 0; background: #0d1117; 
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            z-index: 100; color: #06b6d4; font-family: 'Inter', sans-serif; text-align: center; padding: 20px;
            display: %%CAM_DISPLAY%%;
        }
        .spinner { border: 4px solid rgba(255,255,255,0.1); border-left-color: #06b6d4; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin-bottom: 20px; }
        @keyframes spin { to { transform: rotate(360deg); } }
        #error-log { color: #ef4444; font-size: 11px; margin-top: 15px; max-width: 80% ; opacity: 0.8; }
    </style>

    <div id="cam-container">
        <div id="focus-hud">
            <div id="attention-ring">
                <svg id="progress-svg"><circle cx="22" cy="22" r="20" style="stroke: rgba(255,255,255,0.05); stroke-width: 4; fill: none;"></circle><circle id="progress-circle" cx="22" cy="22" r="20"></circle></svg>
                <span id="attention-val" style="position: absolute; font-size: 10px; font-weight: 800;">100</span>
            </div>
            <div class="hud-status">
                <span class="label">GUARDIAN AI</span>
                <span id="gaze-status" class="val">🛡️ READY</span>
            </div>
            <div id="timer-box" style="display:flex; flex-direction:column; align-items:flex-end;">
                <div id="timer-val" style="line-height:1;">%%MINS%%:00</div>
                <div class="btn-group" style="margin-top:5px;">
                    <button id="main-btn" class="btn-ctrl" style="background: #06b6d4; color: #0f172a; padding: 4px 10px; font-size: 10px;">▶ START</button>
                    <button id="stop-btn" class="btn-ctrl btn-stop" style="display:none; padding: 4px 10px; font-size: 10px;">⏹ STOP</button>
                    <button id="mute-btn" class="btn-ctrl btn-mute" style="display:none; padding: 4px 10px; font-size: 10px;">🔊 MUTE</button>
                </div>
            </div>
        </div>

        <div id="loading-overlay">
            <div class="spinner"></div>
            <div id="load-text">Loading Neural Engine...</div>
            <div id="error-log"></div>
        </div>
        <video id="webcam" autoplay playsinline muted></video>
        <canvas id="output_canvas"></canvas>
        <div style="position:absolute; bottom:10px; left:10px; font-size:9px; color:#06b6d4; opacity:0.5;">SAMS CORE v3.1 • ESM LOAD</div>
    </div>

    <script type="module">
    // Direct ESM import is the most reliable way for Mediapipe Tasks today
    import { FaceLandmarker, FilesetResolver } from "https://cdn.skypack.dev/@mediapipe/tasks-vision@0.10.3";

    const video = document.getElementById('webcam');
    const canvas = document.getElementById('output_canvas');
    const ctx = canvas.getContext('2d');
    const statusEl = document.getElementById('gaze-status');
    const attentionVal = document.getElementById('attention-val');
    const progressCircle = document.getElementById('progress-circle');
    const container = document.getElementById('cam-container');
    const mainBtn = document.getElementById('main-btn');
    const stopBtn = document.getElementById('stop-btn');
    const muteBtn = document.getElementById('mute-btn');
    const timerVal = document.getElementById('timer-val');
    const loadingOverlay = document.getElementById('loading-overlay');
    const loadText = document.getElementById('load-text');
    const errorLog = document.getElementById('error-log');

    // Early error catcher
    window.onerror = function(msg, url, line) {
        errorLog.innerText = "Error: " + msg + " (at " + line + ")";
        statusEl.innerText = "❌ ERROR";
    };

    const hiddenCanvas = document.createElement('canvas');
    const hctx = hiddenCanvas.getContext('2d', { willReadFrequently: true });

    let faceLandmarker;
    let isRunning = %%IS_RUNNING%%;
    let isPaused = false, currentScore = %%SCORE%%;
    let audioCtx = null, oscillator = null, isMuted = false;
    const TOTAL_MINS = %%MINS%%;
    
    // Timer Persistence Logic
    let sessionStartTime = %%START_TIME%%; 
    if (sessionStartTime < 100000) sessionStartTime = 0; // Reset invalid 0
    
    let remainingSecs = TOTAL_MINS * 60;
    let elapsedSecs = 0, pauseCount = 0;
    let counts = %%COUNTS%%;
    
    let timerInterval = null;
    let lastVideoTime = -1;
    let distractionFrames = { phone: 0, closed: 0, away: 0 };

    function playAlarm() {
        if (isMuted) return;
        container.classList.add('distracted');
        if(!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        if(!oscillator) { 
            oscillator = audioCtx.createOscillator(); oscillator.type = 'square'; 
            oscillator.frequency.setValueAtTime(440, audioCtx.currentTime);
            const gain = audioCtx.createGain(); gain.gain.value = 0.05;
            oscillator.connect(gain); gain.connect(audioCtx.destination); oscillator.start(); 
        }
        if(audioCtx.state === 'suspended') audioCtx.resume();
    }
    function stopAlarm() { if(audioCtx && audioCtx.state === 'running') audioCtx.suspend(); container.classList.remove('distracted'); }

    function updateHUD() {
        const offset = 126 - (currentScore / 100) * 126;
        progressCircle.style.strokeDashoffset = offset;
        attentionVal.innerText = Math.round(currentScore);
        const m = Math.floor(remainingSecs / 60); const s = remainingSecs % 60;
        const timeStr = `${m}:${s < 10 ? '0' : ''}${s}`;
        timerVal.innerText = (isPaused ? "PAUSED" : timeStr);
        
        if (currentScore < 40) { progressCircle.style.stroke = "#ef4444"; statusEl.style.color = "#ef4444"; }
        else if (currentScore < 75) { progressCircle.style.stroke = "#f59e0b"; statusEl.style.color = "#f59e0b"; }
        else { progressCircle.style.stroke = "#06b6d4"; statusEl.style.color = "#06b6d4"; }
        
        // Redundant sync removed to prevent message flood. Heartbeat in startTimer covers this.
    }

    mainBtn.onclick = () => {
        if (!isRunning) {
            isRunning = true; mainBtn.innerText = "⏸ PAUSE";
            stopBtn.style.display = "block"; muteBtn.style.display = "block";
            startTimer();
            window.top.postMessage({ type: 'focus_start', startTime: sessionStartTime }, '*');
        } else {
            isPaused = !isPaused;
            if (isPaused) { 
                mainBtn.innerText = "▶ RESUME"; 
                pauseCount++; 
                if (pauseCount >= 3) {
                    statusEl.innerText = "🔥 Stay strong! You've paused " + pauseCount + " times. Every minute focused is a step closer to your goal!";
                    statusEl.style.color = "#f59e0b";
                }
                stopAlarm(); 
            } else { 
                mainBtn.innerText = "⏸ PAUSE"; 
            }
        }
        updateHUD();
    };

    muteBtn.onclick = () => {
        isMuted = !isMuted;
        muteBtn.innerText = isMuted ? "🔇 UNMUTE" : "🔊 MUTE";
        if (isMuted) stopAlarm();
    };

    stopBtn.onclick = () => {
        const result = { 
            elapsedMins: Math.max(1, Math.floor(elapsedSecs / 60)), 
            score: Math.round(currentScore), 
            counts, 
            pauses: pauseCount 
        };
        clearInterval(timerInterval);
        window.top.postMessage({ type: 'focus_stop', data: result }, '*');
        const dataStr = encodeURIComponent(JSON.stringify(result));
        const target = window.top.location.pathname + "?sams_save=" + dataStr;
        setTimeout(() => { window.top.location.href = target; }, 100);
    };

    function startTimer() {
        if (timerInterval) clearInterval(timerInterval);
        timerInterval = setInterval(() => {
            if (isRunning && !isPaused) {
                const now = Date.now();
                if (!sessionStartTime || sessionStartTime < 1000000000000) {
                    sessionStartTime = now;
                }
                
                elapsedSecs = Math.floor((now - sessionStartTime) / 1000);
                remainingSecs = Math.max(0, (TOTAL_MINS * 60) - elapsedSecs);
                
                // Break Reminder: Every 60 mins of continuous focus
                if (elapsedSecs > 0 && elapsedSecs % 3600 === 0) {
                    alert("☕ MISSION ALERT: You've been focusing for 1 hour straight! Time for a 5-minute break to stay sharp.");
                }

                if (remainingSecs <= 0 && elapsedSecs > 5) { 
                    stopBtn.click(); 
                }
                
                window.top.postMessage({ 
                    type: 'focus_sync_heartbeat', 
                    data: { score: Math.round(currentScore), counts, elapsed: elapsedSecs, startTime: sessionStartTime } 
                }, '*');
                
                updateHUD();
            }
        }, 1000);
    }
    
    // Auto-resume if already running
    if (isRunning) {
        console.log("SAMS: Resuming session from ", sessionStartTime);
        stopBtn.style.display = "block"; muteBtn.style.display = "block";
        mainBtn.innerText = "⏸ PAUSE";
        startTimer();
    }

    async function init() {
        if (!%%GUARD_ENABLED%%) {
            loadingOverlay.style.display = 'none';
            statusEl.innerText = "🛡️ HYBRID TIMER";
            // In hybrid mode without guard, we don't start the camera or landmarker
            return;
        }
        try {
            loadText.innerText = "Initializing Vision Matrix...";
            const clips = await FilesetResolver.forVisionTasks("https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.3/wasm");
            faceLandmarker = await FaceLandmarker.createFromOptions(clips, {
                baseOptions: {
                    modelAssetPath: "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task",
                    delegate: "GPU"
                },
                outputFaceBlendshapes: true,
                runningMode: "VIDEO",
                numFaces: 1,
                refineLandmarks: true
            });
            
            // Standard constraints for stability
            const stream = await navigator.mediaDevices.getUserMedia({ 
                video: { width: { ideal: 640 }, height: { ideal: 480 }, frameRate: { ideal: 30 } } 
            });
            video.srcObject = stream;
            video.onloadedmetadata = () => {
                canvas.width = video.videoWidth; canvas.height = video.videoHeight;
                hiddenCanvas.width = video.videoWidth; hiddenCanvas.height = video.videoHeight;
                loadingOverlay.style.display = 'none';
                predictLoop();
            };
        } catch (e) { 
            errorLog.innerText = "Initialization Error: " + e.message;
            console.error(e);
        }
    }

    function calculateEAR(eyeLandmarks) {
        const dist = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);
        const v1 = dist(eyeLandmarks[1], eyeLandmarks[5]);
        const v2 = dist(eyeLandmarks[2], eyeLandmarks[4]);
        const h = dist(eyeLandmarks[0], eyeLandmarks[3]);
        return (v1 + v2) / (2.0 * h);
    }

    function predictLoop() {
        if (video.currentTime !== lastVideoTime) {
            lastVideoTime = video.currentTime;
            const results = faceLandmarker.detectForVideo(video, performance.now());
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            if (results.faceLandmarks && results.faceLandmarks.length > 0) {
                const landmarks = results.faceLandmarks[0];
                
                // Draw refined mesh (subtle dots)
                ctx.fillStyle = "rgba(6, 182, 212, 0.4)";
                landmarks.forEach((p, i) => {
                    if (i % 15 === 0) { 
                        ctx.beginPath(); ctx.arc(p.x * canvas.width, p.y * canvas.height, 1, 0, 2*Math.PI); ctx.fill();
                    }
                });

                const leftEye = [362, 385, 387, 263, 373, 380].map(i => landmarks[i]);
                const rightEye = [33, 160, 158, 133, 153, 144].map(i => landmarks[i]);
                const ear = (calculateEAR(leftEye) + calculateEAR(rightEye)) / 2;

                // Gaze Calcs
                const leftIris = landmarks[468]; 
                const rightIris = landmarks[473];
                const leftGazeX = (leftIris.x - landmarks[362].x) / (landmarks[263].x - landmarks[362].x);
                const rightGazeX = (rightIris.x - landmarks[33].x) / (landmarks[133].x - landmarks[33].x);
                const avgGazeX = (leftGazeX + rightGazeX) / 2;

                // Visual Gaze Points
                ctx.fillStyle = "#fbbf24";
                [468, 473].forEach(i => {
                    const p = landmarks[i];
                    ctx.beginPath(); ctx.arc(p.x * canvas.width, p.y * canvas.height, 2.5, 0, 2*Math.PI); ctx.fill();
                });

                if (isRunning && !isPaused) {
                    let distracted = false;
                    hctx.drawImage(video, 0, 0, hiddenCanvas.width, hiddenCanvas.height);
                    let phoneSignals = [0, 0];
                    
                    const zones = [
                        // Move zones INWARD to stay strictly on the face/skin, avoiding bright background walls
                        { id: 'L-SIDE', x: (landmarks[234].x + 0.05) * canvas.width, y: (landmarks[234].y - 0.05) * canvas.height, w: 50, h: 70 },
                        { id: 'R-SIDE', x: (landmarks[454].x - 0.08) * canvas.width, y: (landmarks[454].y - 0.05) * canvas.height, w: 50, h: 70 },
                        { id: 'CHIN', x: (landmarks[152].x - 0.04) * canvas.width, y: (landmarks[152].y - 0.08) * canvas.height, w: 50, h: 50 }
                    ];

                    // Skin tone calibration (sample from forehead)
                    const forehead = landmarks[10];
                    const skinData = hctx.getImageData(forehead.x * canvas.width, forehead.y * canvas.height, 5, 5).data;
                    let avgSkin = 0; for(let i=0; i<skinData.length; i+=4) avgSkin += (skinData[i]+skinData[i+1]+skinData[i+2])/3;
                    avgSkin /= (skinData.length/4);
                    
                    zones.forEach((z, idx) => {
                        try {
                            const tx = Math.max(0, Math.min(hiddenCanvas.width - z.w, z.x));
                            const ty = Math.max(0, Math.min(hiddenCanvas.height - z.h, z.y));
                            const imgData = hctx.getImageData(tx, ty, z.w, z.h);
                            let brightCount = 0; let darkCount = 0;
                            for (let i = 0; i < imgData.data.length; i += 4) {
                                const lum = (imgData.data[i] + imgData.data[i+1] + imgData.data[i+2])/3;
                                // Detect Screen GLOW (much brighter than skin)
                                if (lum > avgSkin + 70) brightCount++;
                                // Detect SOLID OBJECT (much darker than skin/room)
                                if (lum < avgSkin - 80) darkCount++;
                            }
                            const glowDensity = brightCount/(z.w*z.h);
                            const objectDensity = darkCount/(z.w*z.h);
                            
                            // Trigger if it's either glowing OR a solid dark block is held there
                            if (glowDensity > 0.35 || objectDensity > 0.45) { phoneSignals[idx] = 1; }

                            // DRAW DEBUG ZONES
                            const isAlert = (glowDensity > 0.35 || objectDensity > 0.45);
                            ctx.strokeStyle = isAlert ? "#ef4444" : "rgba(6, 182, 212, 0.4)";
                            ctx.strokeRect(z.x, z.y, z.w, z.h);
                            ctx.fillStyle = ctx.strokeStyle;
                            ctx.font = "bold 9px Inter";
                            ctx.fillText(z.id + (glowDensity > 0.35 ? " GLOW" : (objectDensity > 0.45 ? " OBJ" : " OK")), z.x, z.y - 5);
                        } catch(e){}
                    });

                    if (phoneSignals[0] || phoneSignals[1]) {
                        distractionFrames.phone++;
                        if (distractionFrames.phone > 2) { // Ultra-fast response (approx 0.1s)
                            statusEl.innerText = "🚨 PHONE DETECTED"; distracted = true;
                            if (distractionFrames.phone % 25 === 0) counts.phone++;
                        }
                    } else { distractionFrames.phone = 0; }

                    if (!distracted && ear < 0.16) {
                        distractionFrames.closed++;
                        if (distractionFrames.closed > 6) { // Half the delay for drowsiness
                            statusEl.innerText = "🚨 EYES CLOSED"; distracted = true;
                            if (distractionFrames.closed % 25 === 0) counts.drowsy++;
                        }
                    } else { distractionFrames.closed = 0; }

                    if (!distracted && (avgGazeX < 0.1 || avgGazeX > 0.9)) {
                        distractionFrames.away++;
                        if (distractionFrames.away > 8) { // Faster gaze away detection
                            statusEl.innerText = "🚨 LOOKING AWAY"; distracted = true;
                            if (distractionFrames.away % 25 === 0) counts.zone_out++;
                        }
                    } else { distractionFrames.away = 0; }

                    if (distracted) {
                        playAlarm();
                        currentScore = Math.max(0, currentScore - 1.0);
                    } else {
                        statusEl.innerText = "✅ FOCUSING";
                        stopAlarm();
                        currentScore = Math.min(100, currentScore + 0.1);
                    }
                } else {
                    statusEl.innerText = "🛡️ READY";
                    stopAlarm();
                }
            } else if (isRunning && !isPaused) {
                distractionFrames.away++;
                if (distractionFrames.away > 20) {
                    statusEl.innerText = "🕵️‍♂️ FACE LOST";
                    playAlarm();
                    currentScore = Math.max(0, currentScore - 0.4);
                    if (distractionFrames.away % 40 === 0) counts.zone_out++;
                }
            } else { statusEl.innerText = "🛡️ READY"; }
        }
        updateHUD();
        requestAnimationFrame(predictLoop);
    }
    init();
    </script>



    """
    return html_template \
        .replace("%%MINS%%", str(initial_mins)) \
        .replace("%%IS_RUNNING%%", "true" if state.get('running') else "false") \
        .replace("%%START_TIME%%", str(state.get('start_time', 0))) \
        .replace("%%SCORE%%", str(state.get('score', 100))) \
        .replace("%%COUNTS%%", json.dumps(state.get('counts', {"phone":0,"drowsy":0,"zone_out":0}))) \
        .replace("%%GUARD_ENABLED%%", "true" if guard_enabled else "false") \
        .replace("%%CAM_DISPLAY%%", "block" if guard_enabled else "none") \
        .replace("%%VERSION%%", "3.3")

def embed_eye_tracker(initial_mins=25, state=None, guard_enabled=True):
    if state is None: state = {}
    components.html(get_eye_tracker_html(initial_mins, state, guard_enabled), height=645)
