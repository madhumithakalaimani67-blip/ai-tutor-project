import streamlit.components.v1 as components
import json

def get_eye_tracker_html(initial_mins=25, state=None, guard_enabled=True, duration_source="settings", is_background=False, remaining_secs=None):
    if state is None:
        state = {"running": False, "start_time": 0, "score": 100, "counts": {"phone": 0, "drowsy": 0, "zone_out": 0}}

    html_template = """
<!DOCTYPE html>
<html>
<head>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: transparent; font-family: 'Inter', sans-serif; }

  #cam-container {
    position: relative; width: 100%; max-width: 660px; margin: 0 auto;
    border-radius: 18px; overflow: hidden; background: #050d1a;
    border: 2px solid rgba(99,102,241,0.25);
    box-shadow: 0 0 40px rgba(0,0,0,0.6);
    display: %%DISPLAY%%;
    height: 490px;
    transition: border-color 0.3s ease, box-shadow 0.3s ease;
  }
  #cam-container.alert-red {
    border-color: #ef4444 !important;
    box-shadow: 0 0 0 3px rgba(239,68,68,0.35), 0 0 40px rgba(239,68,68,0.2) !important;
    animation: pulse-border 0.8s ease infinite;
  }
  @keyframes pulse-border {
    0%,100% { box-shadow: 0 0 0 3px rgba(239,68,68,0.35), 0 0 40px rgba(239,68,68,0.2); }
    50% { box-shadow: 0 0 0 6px rgba(239,68,68,0.6), 0 0 60px rgba(239,68,68,0.35); }
  }

  /* ---- HUD ---- */
  #focus-hud {
    position: absolute; top: 12px; left: 10px; right: 10px; z-index: 200;
    display: flex; align-items: center; gap: 12px;
    background: rgba(6,12,28,0.88); backdrop-filter: blur(16px);
    padding: 8px 14px; border-radius: 50px;
    border: 1px solid rgba(255,255,255,0.07);
    box-shadow: 0 4px 24px rgba(0,0,0,0.5);
    color: white;
  }

  /* Score ring */
  #score-ring { position: relative; width: 42px; height: 42px; flex-shrink: 0; }
  #score-ring svg { transform: rotate(-90deg); width:42px; height:42px; }
  #ring-track { stroke: rgba(255,255,255,0.08); stroke-width: 4.5; fill: none; }
  #ring-fill {
    stroke: #ef4444; stroke-width: 4.5; fill: none;
    stroke-dasharray: 119; stroke-dashoffset: 0;
    transition: stroke-dashoffset 0.5s ease, stroke 0.4s ease;
  }
  #score-num {
    position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%);
    font-size: 12px; font-weight: 800; color: white;
  }

  /* Status */
  #hud-center { display: flex; flex-direction: column; gap: 1px; flex: 1; min-width: 0; }
  #hud-label { font-size: 7.5px; font-weight: 800; letter-spacing: 2px; color: #06b6d4; opacity: 0.8; text-transform: uppercase; }
  #hud-status { font-size: 13px; font-weight: 700; color: white; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

  /* Timer + buttons — SINGLE ROW */
  #hud-right { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
  #timer-val { font-size: 24px; font-weight: 800; color: #fbbf24; font-variant-numeric: tabular-nums; letter-spacing: 1.5px; white-space: nowrap; }
  .btn-row { display: flex; gap: 5px; }
  .btn-ctrl {
    border: none; border-radius: 20px; cursor: pointer;
    font-weight: 700; font-size: 10px; padding: 5px 13px;
    transition: all 0.18s; font-family: 'Inter', sans-serif;
    letter-spacing: 0.4px; white-space: nowrap;
  }
  #btn-start { background: #06b6d4; color: #050d1a; }
  #btn-start:hover { background: #22d3ee; }
  #btn-pause { background: rgba(99,102,241,0.85); color: white; display: none; }
  #btn-pause:hover { background: #6366f1; }
  #btn-stop  { background: rgba(239,68,68,0.8); color: white; display: none; }
  #btn-stop:hover { background: #ef4444; }
  #btn-restart { background: rgba(16,185,129,0.8); color: white; display: none; }
  #btn-restart:hover { background: #10b981; }
  #btn-mute  { background: rgba(255,255,255,0.13); color: rgba(255,255,255,0.8); display: none; }
  #btn-mute:hover { background: rgba(255,255,255,0.25); }
  #btn-pip   { background: rgba(255,255,255,0.13); color: rgba(255,255,255,0.8); display: none; font-size: 14px; padding: 5px 10px; }
  #btn-cam   { background: rgba(255,255,255,0.13); color: rgba(255,255,255,0.8); display: inline-block; font-size: 14px; padding: 5px 10px; }

  /* Canvas / Video */
  #webcam { position: absolute; top:0; left:0; width:1px; height:1px; opacity:0; pointer-events:none; }
  #output_canvas { width: 100%; height: 100%; transform: scaleX(-1); display: block; }
  #pip-video { position: absolute; top:0; left:0; width:1px; height:1px; opacity:0; pointer-events:none; }

  /* Loading overlay */
  #loading-overlay {
    position: absolute; inset: 0; z-index: 100;
    background: #050d1a; display: flex; flex-direction: column;
    align-items: center; justify-content: center; gap: 14px;
  }
  .spinner {
    width: 42px; height: 42px; border-radius: 50%;
    border: 4px solid rgba(6,182,212,0.1); border-top-color: #06b6d4;
    animation: spin 0.9s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  #load-text { color: rgba(255,255,255,0.6); font-size: 12px; font-weight: 600; letter-spacing: 0.5px; }

  /* Standby */
  #standby-screen {
    position: absolute; inset: 0; background: #050d1a;
    display: none; flex-direction: column; align-items: center; justify-content: center; gap: 10px;
  }
  #standby-screen .st-icon { font-size: 3rem; }
  #standby-screen .st-txt { color: rgba(99,102,241,0.9); font-weight: 700; font-size: 1rem; letter-spacing: 1.5px; }

  /* PiP Overlay Styles */
  #pip-overlay #timer-val,
  #pip-window #timer-val,
  #pip-timer {
    display: block !important;
    font-size: 2rem !important;
    color: #fbbf24 !important;
    font-weight: 800 !important;
    text-align: center !important;
  }
  #pip-overlay #hud-status,
  #hud-status-pip {
    display: block !important;
    font-size: 0.85rem !important;
    color: white !important;
    text-align: center !important;
  }
</style>

</head>
<body>

<div id="cam-container">
  <!-- HUD -->
  <div id="focus-hud">
    <div id="score-ring">
      <svg width="46" height="46" viewBox="0 0 46 46">
        <circle id="ring-track" cx="23" cy="23" r="20"/>
        <circle id="ring-fill"  cx="23" cy="23" r="20"/>
      </svg>
      <span id="score-num">100</span>
    </div>
    <div id="hud-center">
      <span id="hud-label">GUARDIAN AI</span>
      <span id="hud-status">🛡️ INITIALIZING</span>
    </div>
    <div id="hud-right">
      <div id="timer-val">%%MINS%%:00</div>
      <div class="btn-row">
        <button id="btn-cam"     class="btn-ctrl" title="Toggle Camera">📷</button>
        <button id="btn-pip"     class="btn-ctrl" title="PiP Mode">📺</button>
        <button id="btn-mute"    class="btn-ctrl">🔇 MUTE</button>
        <button id="btn-restart" class="btn-ctrl">🔄 RESTART</button>
        <button id="btn-pause"   class="btn-ctrl">⏸ PAUSE</button>
        <button id="btn-stop"    class="btn-ctrl">⏹ STOP</button>

        <button id="btn-start"   class="btn-ctrl">▶ START</button>

      </div>
    </div>
  </div>

  <video id="pip-video" autoplay playsinline></video>

  <!-- Loading -->
  <div id="loading-overlay">
    <div class="spinner"></div>
    <div id="load-text">Loading Vision Engine...</div>
  </div>

  <!-- Standby (guard off) -->
  <div id="standby-screen">
    <div class="st-icon">🛰️</div>
    <div class="st-txt">AI STANDBY MODE</div>
  </div>

  <!-- Camera -->
  <video id="webcam" autoplay playsinline muted></video>
  <canvas id="output_canvas"></canvas>

  <!-- PiP Overlay (Simulated) -->
  <div id="pip-overlay" style="display:none; position:absolute; bottom:15px; right:15px; width:160px; background:rgba(6,12,28,0.92); backdrop-filter:blur(10px); border-radius:20px; border:1px solid #fbbf24; padding:15px; z-index:1000; flex-direction:column; align-items:center; box-shadow:0 10px 30px rgba(0,0,0,0.5);">
    <div id="hud-status-pip" style="margin-bottom:2px; opacity:0.8;">FOCUSING</div>
    <div id="pip-timer" data-pip-timer>00:00</div>
    <div style="font-size:0.6rem; color:rgba(255,255,255,0.4); margin-top:5px; letter-spacing:1px; font-weight:700;">PIP MODE</div>
  </div>

  <script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs"></script>
<script src="https://cdn.jsdelivr.net/npm/@tensorflow-models/coco-ssd"></script>

<script type="module">
import { FaceLandmarker, FilesetResolver, DrawingUtils } from "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.3";

// ── DOM refs ──────────────────────────────────────────────────────────────
const video       = document.getElementById('webcam');
const canvas      = document.getElementById('output_canvas');
const ctx         = canvas.getContext('2d');
const container   = document.getElementById('cam-container');
const hudStatus   = document.getElementById('hud-status');
const scoreNum    = document.getElementById('score-num');
const ringFill    = document.getElementById('ring-fill');
const timerVal    = document.getElementById('timer-val');
const loadOverlay = document.getElementById('loading-overlay');
const loadText    = document.getElementById('load-text');
const standby     = document.getElementById('standby-screen');
const btnStart    = document.getElementById('btn-start');
const btnPause    = document.getElementById('btn-pause');
const btnStop     = document.getElementById('btn-stop');
const btnMute     = document.getElementById('btn-mute');

const btnRestart  = document.getElementById('btn-restart');
const btnPip      = document.getElementById('btn-pip');
const btnCam      = document.getElementById('btn-cam');
const pipVideo    = document.getElementById('pip-video');

// ── Config ────────────────────────────────────────────────────────────────
const TOTAL_MINS    = %%MINS%%;
const IS_BG         = %%IS_BG%%;
const GUARD_ENABLED = %%GUARD_ENABLED%%;
const OVERRIDE_SECS = %%REMAINING_SECS%%;

// ── State ─────────────────────────────────────────────────────────────────
let objectDetector = null;
let faceLandmarker = null;
let isRunning = false, isPaused = false, isMuted = false;
let currentScore = 100;
let sessionStartTime = 0, timerTargetTime = 0, lastTimerUpdate = 0;
let remainingSecs = OVERRIDE_SECS !== null ? OVERRIDE_SECS : TOTAL_MINS * 60;
let fixedDuration = TOTAL_MINS * 60;
let lookDownCtr = 0, closedEyeCtr = 0, phoneCtr = 0, awayCtr = 0;
let sessionTel = { phone: 0, drowsy: 0, zone_out: 0, pauses: 0 };
let audioCtx = null;
let isCurrentlyDistracted = false;
let isCameraOn = true;

// ── Resume prev session ───────────────────────────────────────────────────
const prev = %%STATE%%;
if (prev && prev.running) {
  isRunning = true;
  sessionStartTime = prev.start_time || Date.now();
  sessionTel = prev.counts || sessionTel;
  currentScore = prev.score || 100;
  isPaused = prev.isPaused || false;
  fixedDuration = prev.fixed_duration || (TOTAL_MINS * 60);
  
  if (isPaused) {
    remainingSecs = prev.remaining_secs || (fixedDuration);
    timerTargetTime = Date.now() + (remainingSecs * 1000);
  } else if (prev.target_time) {
    timerTargetTime = prev.target_time;
    remainingSecs = Math.max(0, Math.ceil((timerTargetTime - Date.now()) / 1000));
  } else {
    const elapsed = (Date.now() - sessionStartTime) / 1000;
    remainingSecs = Math.max(0, fixedDuration - elapsed);
    timerTargetTime = Date.now() + (remainingSecs * 1000);
  }
  
  lastTimerUpdate = Date.now();
  showRunningButtons();
  if (isPaused) {
    btnPause.innerText = "▶ RESUME";
    btnRestart.style.display = 'inline-block';
  }
}

function showRunningButtons() {
  btnStart.style.display   = 'none';
  btnPause.style.display   = 'inline-block';
  btnStop.style.display    = 'inline-block';
  btnMute.style.display    = 'inline-block';
  btnPip.style.display     = 'inline-block';
  btnCam.style.display     = 'inline-block';
  btnRestart.style.display = 'none';
}
function showIdleButtons() {
  btnStart.style.display   = 'inline-block';
  btnPause.style.display   = 'none';
  btnStop.style.display    = 'none';
  btnMute.style.display    = 'none';
  btnPip.style.display     = 'none';
  btnRestart.style.display = 'none';
}

// ── Alarm — CONTINUOUS BEEP ──────────────────────────────────────────────
let alarmOsc = null, alarmGain = null;
function playAlarm() {
  container.classList.add('alert-red');
  if (IS_BG || isMuted || alarmOsc) return;
  if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  if (audioCtx.state === 'suspended') audioCtx.resume();
  alarmOsc  = audioCtx.createOscillator();
  alarmGain = audioCtx.createGain();
  alarmOsc.type = 'sine';
  alarmOsc.frequency.setValueAtTime(880, audioCtx.currentTime);
  alarmGain.gain.setValueAtTime(0.18, audioCtx.currentTime);
  alarmOsc.connect(alarmGain);
  alarmGain.connect(audioCtx.destination);
  alarmOsc.start();
}
function stopAlarm() {
  container.classList.remove('alert-red');
  if (alarmOsc) {
    try { alarmGain.gain.setValueAtTime(0, audioCtx.currentTime); alarmOsc.stop(); } catch(e) {}
    alarmOsc = null; alarmGain = null;
  }
}

// ── HUD updater ───────────────────────────────────────────────────────────
function updateHUD() {
  const offset = 119 - (currentScore / 100) * 119;
  ringFill.style.strokeDashoffset = offset;
  scoreNum.innerText = Math.round(currentScore);
  if (currentScore < 40) ringFill.style.stroke = '#ef4444';
  else if (currentScore < 72) ringFill.style.stroke = '#f59e0b';
  else ringFill.style.stroke = '#10b981';

  if (isRunning && !isPaused) {
    if (isCurrentlyDistracted) {
        timerTargetTime += (Date.now() - lastTimerUpdate);
    }
    lastTimerUpdate = Date.now();
    remainingSecs = Math.max(0, Math.ceil((timerTargetTime - Date.now()) / 1000));
    if (remainingSecs <= 0) { isRunning = false; btnStop.click(); return; }
  }
  if (!isPaused) {
    const m = Math.floor(remainingSecs / 60);
    const s = remainingSecs % 60;
    timerVal.innerText = `${m}:${s < 10 ? '0' : ''}${s}`;
  } else {
    timerVal.innerText = 'PAUSED';
  }
}

// ── INIT ──────────────────────────────────────────────────────────────────
async function init() {
  if (!GUARD_ENABLED) {
    loadOverlay.style.display = 'none';
    standby.style.display = 'flex';
    hudStatus.innerText = '🛰️ STANDBY';
    predictLoop();
    return;
  }
  try {
    loadText.innerText = 'Loading 3D Face Mesh...';
    const vision = await FilesetResolver.forVisionTasks("https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.3/wasm");
    faceLandmarker = await FaceLandmarker.createFromOptions(vision, {
      baseOptions: {
        modelAssetPath: "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task",
        delegate: "GPU"
      },
      outputFaceBlendshapes: true,
      outputFacialTransformationMatrixes: true,
      runningMode: "VIDEO",
      numFaces: 1
    });

    loadText.innerText = 'Loading Object Model...';
    try {
      objectDetector = await cocoSsd.load({base: 'lite_mobilenet_v2'});
    } catch(e) { console.warn('coco-ssd fallback or failed'); }

    loadText.innerText = 'Starting Camera...';
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 640 }, height: { ideal: 480 }, frameRate: { ideal: 30 } }
    });
    video.srcObject = stream;
    video.onloadedmetadata = () => {
      canvas.width  = video.videoWidth  || 640;
      canvas.height = video.videoHeight || 480;
    };
    video.onloadeddata = () => {
      canvas.width  = video.videoWidth  || 640;
      canvas.height = video.videoHeight || 480;
      loadOverlay.style.display = 'none';
      hudStatus.innerText = '🛡️ READY';
      predictLoop();
    };
  } catch(e) {
    loadText.innerText = '❌ Error: ' + e.message;
    console.error(e);
  }
}

// ── PREDICT LOOP ──────────────────────────────────────────────────────────
async function predictLoop() {
  if (GUARD_ENABLED && video.videoWidth > 0 &&
      (canvas.width !== video.videoWidth || canvas.width === 300)) {
    canvas.width  = video.videoWidth;
    canvas.height = video.videoHeight;
  }

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  if (!GUARD_ENABLED || !isCameraOn) {
    updateHUD();
    requestAnimationFrame(predictLoop);
    return;
  }


  if (!IS_BG && video.readyState >= 2) {
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  }

  // 1. Phone Detection via COCO-SSD
  let phoneOnScreen = false;
  if (objectDetector && video.readyState >= 2) {
    try {
      const predictions = await objectDetector.detect(video);
      predictions.forEach(p => {
        if (p.class === 'cell phone' && p.score > 0.30) {
          phoneOnScreen = true;
          if (!IS_BG) {
            const [x, y, width, height] = p.bbox;
            ctx.save();
            ctx.strokeStyle = '#ef4444'; ctx.lineWidth = 3;
            ctx.shadowColor = '#ef4444'; ctx.shadowBlur = 10;
            ctx.strokeRect(x, y, width, height);
            ctx.fillStyle = 'rgba(239,68,68,0.15)';
            ctx.fillRect(x, y, width, height);
            ctx.scale(-1, 1);
            ctx.fillStyle = '#ef4444'; ctx.font = 'bold 14px Inter';
            ctx.fillText('📵 PHONE', -(x + width), y - 8);
            ctx.restore();
          }
        }
      });
    } catch(e) {}
  }

  // 2. Face Detection via MediaPipe
  let faceDetected = false;
  if (faceLandmarker && video.readyState >= 2) {
    try {
        const results = faceLandmarker.detectForVideo(video, performance.now());
        
        if (results.faceLandmarks && results.faceLandmarks.length > 0) {
          faceDetected = true;
          
          if (!IS_BG) {
            const drawingUtils = new DrawingUtils(ctx);
            drawingUtils.drawConnectors(
                results.faceLandmarks[0],
                FaceLandmarker.FACE_LANDMARKS_CONTOURS,
                { color: "#06b6d4aa", lineWidth: 2 }
            );
          }
    
          if (isRunning && !isPaused) {
            awayCtr = 0;
    
            // Timer independence: If camera is off, we just focused on timer.
            // If camera is on, we do AI detection.
            if (isCameraOn) {
                // Phone logic
                if (phoneOnScreen) { 
                    phoneCtr += 2; 
                    if (phoneCtr > 60) phoneCtr = 60;
                    if (phoneCtr === 6) { sessionTel.phone++; } 
                } else { 
                    phoneCtr = 0; // Instant clear
                }
            }
    
            // Drowsy detection initialization
            let isDrowsy = false;
            let eyeLookingDown = false;
            let eyeLookingSideways = false;
            
            if (results.faceBlendshapes && results.faceBlendshapes.length > 0) {
                const categories = results.faceBlendshapes[0].categories;
                const lookDownL = categories.find(c => c.categoryName === 'eyeLookDownLeft')?.score || 0;
                const lookDownR = categories.find(c => c.categoryName === 'eyeLookDownRight')?.score || 0;
                const lookOutL = categories.find(c => c.categoryName === 'eyeLookOutLeft')?.score || 0;
                const lookInL = categories.find(c => c.categoryName === 'eyeLookInLeft')?.score || 0;
                const lookOutR = categories.find(c => c.categoryName === 'eyeLookOutRight')?.score || 0;
                const lookInR = categories.find(c => c.categoryName === 'eyeLookInRight')?.score || 0;

                eyeLookingDown = lookDownL > 0.50 && lookDownR > 0.50;
                eyeLookingSideways = (lookOutL > 0.65 && lookInR > 0.65) || (lookOutR > 0.65 && lookInL > 0.65);
            }
            
            // 3D Landmarks for Looking Away and Drowsiness (EAR)
            const lm = results.faceLandmarks[0];
            const nose = lm[1];
            const leftJaw = lm[234];
            const rightJaw = lm[454];
            const chin = lm[152];
            const topNose = lm[8];

            const faceWidth = Math.abs(rightJaw.x - leftJaw.x);
            const noseToCenter = Math.abs(nose.x - (leftJaw.x + rightJaw.x)/2);
            const headTurnedSideways = (noseToCenter / (faceWidth + 1e-6)) > 0.32; 

            const faceHeight = Math.abs(chin.y - topNose.y);
            const noseToChin = Math.abs(chin.y - nose.y);
            const headTurnedDown = (noseToChin / (faceHeight + 1e-6)) < 0.28; 

            const isLookingDown = headTurnedDown || eyeLookingDown;

            // 4. Iris-based Gaze Tracking (Eyes Center Ball)
            let eyeGazeSideways = false;
            if (lm[468] && lm[473]) {
                const rIris = lm[468], lIris = lm[473];
                // Right Eye: 33 (Outer), 133 (Inner)
                const rRatio = (rIris.x - lm[33].x) / (lm[133].x - lm[33].x + 1e-6);
                // Left Eye: 362 (Inner), 263 (Outer)
                const lRatio = (lIris.x - lm[362].x) / (lm[263].x - lm[362].x + 1e-6);
                
                // If iris is too close to either corner (looking too far left or right)
                if (rRatio < 0.22 || rRatio > 0.78 || lRatio < 0.22 || lRatio > 0.78) {
                    eyeGazeSideways = true;
                }

                if (!IS_BG && eyeGazeSideways) {
                    ctx.fillStyle = '#ef4444';
                    [rIris, lIris].forEach(pt => {
                        ctx.beginPath();
                        ctx.arc(pt.x * canvas.width, pt.y * canvas.height, 3, 0, 2 * Math.PI);
                        ctx.fill();
                    });
                }
            }

            const isLookingSideways = headTurnedSideways || eyeLookingSideways || eyeGazeSideways;
            const lookingAway = isLookingSideways;

            // EAR Calculation
            const dist = (p1, p2) => Math.sqrt(Math.pow(p1.x - p2.x, 2) + Math.pow(p1.y - p2.y, 2));
            const rWidth = dist(lm[33], lm[133]);
            const rHeight = (dist(lm[160], lm[144]) + dist(lm[158], lm[153])) / 2.0;
            const rightEAR = rHeight / (rWidth + 1e-6);
            const lWidth = dist(lm[263], lm[362]);
            const lHeight = (dist(lm[385], lm[380]) + dist(lm[387], lm[373])) / 2.0;
            const leftEAR = lHeight / (lWidth + 1e-6);
            const avgEAR = (rightEAR + leftEAR) / 2.0;
            
            if (!IS_BG) {
              ctx.save();
              ctx.scale(-1, 1);
              ctx.fillStyle = 'yellow';
              ctx.font = 'bold 13px Inter';
              ctx.fillText('EAR: ' + avgEAR.toFixed(3), -canvas.width + 10, canvas.height - 10);
              ctx.restore();
            }
            
            isDrowsy = avgEAR < 0.20;
            
            if (lookingAway) { 
                lookDownCtr++; 
                if (lookDownCtr > 60) lookDownCtr = 60;
                if (lookDownCtr === 15) { sessionTel.zone_out++; } 
            } else { 
                lookDownCtr = 0; // Instant clear
            }
            
            // 3. Allow drowsy detection even when looking down (to catch sleep), but with the ultra-strict 0.05 threshold
            if (isDrowsy) { 
                closedEyeCtr++; 
                if (closedEyeCtr > 60) closedEyeCtr = 60;
                if (closedEyeCtr === 20) { sessionTel.drowsy++; } 
            } else { 
                closedEyeCtr = 0;
            }
    
            // Alarm priority and timer pausing
            if (phoneCtr > 5) {
              hudStatus.innerText = '📵 PHONE DETECTED';
              playAlarm();
              currentScore = Math.max(0, currentScore - 0.6);
              isCurrentlyDistracted = true;
            } else if (lookDownCtr > 20) { 
              hudStatus.innerText = '👀 LOOKING AROUND';
              playAlarm();
              currentScore = Math.max(0, currentScore - 0.25);
              isCurrentlyDistracted = true;
            } else if (closedEyeCtr > 20) { 
              hudStatus.innerText = '😴 DROWSY DETECTED';
              playAlarm();
              currentScore = Math.max(0, currentScore - 0.45);
              isCurrentlyDistracted = true;
            } else {
              hudStatus.innerText = '✅ FOCUSING';
              stopAlarm();
              currentScore = Math.min(100, currentScore + 0.055);
              isCurrentlyDistracted = false;
            }
          } else if (!isRunning) {
            hudStatus.innerText = '🛡️ READY';
            isCurrentlyDistracted = false;
          }
        }
    } catch(e) {}
  }

  // User Lost (No face detected)
  if (!faceDetected) {
    if (isRunning && !isPaused) {
      awayCtr++;
      hudStatus.innerText = '❌ USER LOST';
      if (awayCtr > 15) {
        playAlarm();
        currentScore = Math.max(0, currentScore - 0.35);
        isCurrentlyDistracted = true;
      }
    } else if (!isRunning) {
      hudStatus.innerText = '🛡️ READY';
      isCurrentlyDistracted = false;
    }
  }

  updateHUD();
  drawCanvasHUD();
  
  // Predict again
  requestAnimationFrame(predictLoop);
}

function drawCanvasHUD() {
  ctx.save();

  // Distraction Warning Frame (Pulsing Red)
  if (isRunning && !isPaused && isCurrentlyDistracted) {
    ctx.strokeStyle = '#ef4444';
    ctx.lineWidth = 10;
    ctx.strokeRect(0, 0, canvas.width, canvas.height);
    
    // Translucent warning fill
    const pulse = Math.abs(Math.sin(Date.now() / 150));
    ctx.fillStyle = `rgba(239, 68, 68, ${0.05 + pulse * 0.12})`;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  }

  // Background bar
  ctx.fillStyle = 'rgba(6, 12, 28, 0.8)';
  ctx.fillRect(10, 10, 200, 60);
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
  ctx.strokeRect(10, 10, 200, 60);

  // Timer Text
  ctx.fillStyle = '#fbbf24';
  ctx.font = 'bold 28px Inter';
  ctx.fillText(timerVal.innerText, 25, 45);

  // Status Text
  ctx.fillStyle = '#ffffff';
  ctx.font = 'bold 12px Inter';
  ctx.fillText(hudStatus.innerText, 25, 62);

  // Score
  ctx.fillStyle = '#06b6d4';
  ctx.font = 'bold 16px Inter';
  ctx.fillText('SCORE: ' + Math.round(currentScore), 110, 45);

  ctx.restore();
}

// ── Telemetry sync ────────────────────────────────────────────────────────
// ── Telemetry sync ────────────────────────────────────────────────────────
function syncTel() {
  // Syncing telemetry is handled by heartbeat
}
// Track when session was stopped for post-stop heartbeat window
let sessionStoppedAt = 0;

// Write heartbeat to localStorage every 2s while running



// ── Button handlers ───────────────────────────────────────────────────────
// btnStart.onclick
btnStart.onclick = () => {
    isRunning        = true;
    isPaused         = false;
    fixedDuration    = TOTAL_MINS * 60;
    sessionStartTime = Date.now();
    timerTargetTime  = sessionStartTime + (fixedDuration * 1000);
    lastTimerUpdate  = Date.now();
    showRunningButtons();

    // Write to localStorage (same-origin iframe CAN do this)
    try {
        localStorage.removeItem('sams_final_tel');
        localStorage.setItem('sams_start_signal', JSON.stringify({
            startTime: sessionStartTime
        }));
    } catch(e) {}
    
    // Set hash via postMessage to parent
    window.parent.postMessage({
        type: 'sams_nav',
        hash: 'sams=start_' + sessionStartTime
    }, '*');
};


btnPause.onclick = () => {
  isPaused = !isPaused;
  btnPause.innerText = isPaused ? '▶ RESUME' : '⏸ PAUSE';
  btnRestart.style.display = isPaused ? 'inline-block' : 'none';
  if (isPaused) {
    sessionTel.pauses++;
    if (sessionTel.pauses >= 3) {
      alert("3 pauses. Try to focus on the session!");
    }
    syncTel();
    stopAlarm();
  } else {
    timerTargetTime = Date.now() + (remainingSecs * 1000);
    lastTimerUpdate = Date.now();
  }
};

btnRestart.onclick = () => {
  if (!confirm("Restart session? Current progress will be reset.")) return;
  remainingSecs = TOTAL_MINS * 60;
  sessionStartTime = Date.now();
  timerTargetTime = sessionStartTime + (remainingSecs * 1000);
  lastTimerUpdate = Date.now();
  isPaused = false;
  btnPause.innerText = '⏸ PAUSE';
  btnRestart.style.display = 'none';
};


btnStop.onclick = () => {
    isRunning        = false;
    isPaused         = false;
    sessionStoppedAt = Date.now();
    stopAlarm();
    hudStatus.innerText = 'MISSION COMPLETE';

    const elapsedMins = parseFloat(
        ((sessionStoppedAt - sessionStartTime) / 60000).toFixed(2)
    );

    const finalTel = {
        phone:       sessionTel.phone,
        drowsy:      sessionTel.drowsy,
        zone_out:    sessionTel.zone_out,
        pauses:      sessionTel.pauses,
        score:       Math.round(currentScore),
        elapsedMins: elapsedMins > 0 ? elapsedMins : 1,
        startTime:   sessionStartTime
    };

    // Write to localStorage
    try { localStorage.setItem('sams_final_tel', JSON.stringify(finalTel)); } catch(e) {}

    // Send hash nav request to parent via postMessage
    const payload = 'stop_' + btoa(JSON.stringify(finalTel));
    window.parent.postMessage({ type: 'sams_nav', hash: 'sams=' + payload }, '*');

    btnStop.style.display    = 'none';
    btnPause.style.display   = 'none';
    btnMute.style.display    = 'none';
    btnPip.style.display     = 'none';
    btnRestart.style.display = 'none';
    btnStart.style.display   = 'none';
};


// btnSave is removed as sessions now auto-save on Stop.



btnCam.onclick = () => {
  isCameraOn = !isCameraOn;
  btnCam.innerText = isCameraOn ? '📷' : '🚫';
  btnCam.title = isCameraOn ? 'Camera On' : 'Camera Off';
  if (!isCameraOn) {
    stopAlarm();
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    hudStatus.innerText = '📷 CAMERA OFF';
    standby.style.display = 'flex';
  } else {
    standby.style.display = 'none';
    hudStatus.innerText = '🛡️ READY';
  }
};

btnPip.onclick = async () => {
  try {
    if (document.pictureInPictureElement) {
      await document.exitPictureInPicture();
    } else {
      if (!pipVideo.srcObject) {
        // Capture stream from canvas at 30 FPS
        const stream = canvas.captureStream ? canvas.captureStream(30) : (canvas.mozCaptureStream ? canvas.mozCaptureStream(30) : null);
        if (stream) {
          pipVideo.srcObject = stream;
        } else {
          throw new Error("Canvas captureStream not supported in this browser.");
        }
      }
      await pipVideo.play();
      await pipVideo.requestPictureInPicture();
    }
  } catch (e) {
    console.error("PiP error:", e);
    // Fallback: use simulated overlay if native PiP is blocked/unsupported
    const pip = document.getElementById('pip-overlay');
    if (pip) {
      const isShowing = pip.style.display !== 'none';
      pip.style.display = isShowing ? 'none' : 'flex';
    }
  }
};

// Event listeners to toggle button styling when entering/leaving native PiP
pipVideo.addEventListener('enterpictureinpicture', () => {
  btnPip.style.background = '#fbbf24';
  btnPip.style.color = '#050d1a';
  btnPip.title = "Exit PiP Mode";
});

pipVideo.addEventListener('leavepictureinpicture', () => {
  btnPip.style.background = 'rgba(255,255,255,0.13)';
  btnPip.style.color = 'rgba(255,255,255,0.8)';
  btnPip.title = "PiP Mode";
});


btnMute.onclick = () => {
  isMuted = !isMuted;
  btnMute.innerText = isMuted ? '🔊 UNMUTE' : '🔇 MUTE';
  if (isMuted && alarmOsc) {
    try { alarmGain.gain.setValueAtTime(0, audioCtx.currentTime); alarmOsc.stop(); } catch(e) {}
    alarmOsc = null; alarmGain = null;
  }
};

// Continuous telemetry sync to localStorage
setInterval(() => {
    try {
        window.top.localStorage.setItem('sams_final_tel', JSON.stringify({
            phone:       sessionTel.phone,
            drowsy:      sessionTel.drowsy,
            zone_out:    sessionTel.zone_out,
            pauses:      sessionTel.pauses,
            score:       Math.round(currentScore),
            elapsedMins: sessionStartTime > 0 ? parseFloat(((Date.now() - sessionStartTime) / 60000).toFixed(2)) : 0,
            startTime:   sessionStartTime
        }));
    } catch(e) {}
}, 2000);

init();
</script>
</body>
</html>
"""

    final_html = html_template.replace("%%MINS%%", str(initial_mins))
    final_html = final_html.replace("%%STATE%%", json.dumps(state))
    final_html = final_html.replace("%%DISPLAY%%", "none" if is_background else "block")
    final_html = final_html.replace("%%IS_BG%%", "true" if is_background else "false")
    final_html = final_html.replace("%%GUARD_ENABLED%%", "true" if guard_enabled else "false")
    final_html = final_html.replace("%%REMAINING_SECS%%", str(remaining_secs) if remaining_secs else "null")

    components.html(final_html, height=0 if is_background else 560)


def embed_eye_tracker(initial_mins=25, state=None, guard_enabled=True, duration_source="settings", is_background=False, remaining_secs=None):
    """Embeds the Guardian AI focus tracker."""
    get_eye_tracker_html(initial_mins, state, guard_enabled, duration_source, is_background, remaining_secs)
