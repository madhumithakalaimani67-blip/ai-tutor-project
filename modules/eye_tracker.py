import streamlit.components.v1 as components

def get_eye_tracker_html():
    """Returns the HTML/JS for advanced eye tracking via MediaPipe Face Landmarker."""
    return """
    <div id="focus-hud" style="position: fixed; top: 10px; right: 10px; z-index: 10000; 
         background: rgba(15, 23, 42, 0.9); backdrop-filter: blur(10px); 
         padding: 10px 20px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);
         color: white; font-family: 'Inter', sans-serif; box-shadow: 0 4px 20px rgba(0,0,0,0.5);
         display: flex; align-items: center; gap: 15px;">
        <div style="display: flex; flex-direction: column;">
            <span style="font-size: 9px; text-transform: uppercase; letter-spacing: 1px; color: #6366f1; font-weight: 800;">OpenCV Focus Guard</span>
            <span id="gaze-status" style="font-size: 14px; font-weight: 700;">🔄 Initializing...</span>
        </div>
        <button id="pip-btn" style="background: #6366f1; border: none; color: white; padding: 6px 12px; 
                border-radius: 8px; cursor: pointer; font-size: 11px; font-weight: 600;">📽 View PiP</button>
    </div>

    <div id="cam-container" style="display: none; position: fixed; bottom: 20px; right: 20px; 
         width: 400px; height: 300px; z-index: 9999; border-radius: 16px; overflow: hidden;
         border: 3px solid #6366f1; background: black; cursor: move; box-shadow: 0 20px 60px rgba(0,0,0,0.8);">
        <video id="webcam" style="display: none;" autoplay playsinline muted></video>
        <canvas id="output_canvas" style="width: 100%; height: 100%; transform: scaleX(-1);"></canvas>
        <div style="position: absolute; top: 5px; right: 10px; color: white; font-size: 20px; cursor: pointer;" onclick="document.getElementById('cam-container').style.display='none'">×</div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.3/vision_bundle.js" crossorigin="anonymous"></script>
    
    <script>
    const video = document.getElementById('webcam');
    const canvas = document.getElementById('output_canvas');
    const ctx = canvas.getContext('2d');
    const container = document.getElementById('cam-container');
    const statusEl = document.getElementById('gaze-status');
    const pipBtn = document.getElementById('pip-btn');
    
    let faceLandmarker;
    let objectDetector;
    let lastVideoTime = -1;
    let lookDownCounter = 0, closedEyeCounter = 0, phoneCounter = 0;
    
    let audioCtx = null, oscillator = null;
    function playAlarm() {
        if(!audioCtx) { audioCtx = new (window.AudioContext || window.webkitAudioContext)(); }
        if(!oscillator) { 
            oscillator = audioCtx.createOscillator(); oscillator.type = 'square'; 
            oscillator.frequency.setValueAtTime(880, audioCtx.currentTime);
            const gain = audioCtx.createGain(); gain.gain.value = 0.1;
            oscillator.connect(gain); gain.connect(audioCtx.destination); 
            oscillator.start(); 
        }
        if(audioCtx.state === 'suspended') audioCtx.resume();
    }
    function stopAlarm() { if(audioCtx && audioCtx.state === 'running') audioCtx.suspend(); }

    function getEAR(lm, idxs) {
        const a = Math.hypot(lm[idxs[1]].x - lm[idxs[5]].x, lm[idxs[1]].y - lm[idxs[5]].y);
        const b = Math.hypot(lm[idxs[2]].x - lm[idxs[4]].x, lm[idxs[2]].y - lm[idxs[4]].y);
        const c = Math.hypot(lm[idxs[0]].x - lm[idxs[3]].x, lm[idxs[0]].y - lm[idxs[3]].y);
        return (a + b) / (2.0 * c);
    }

    async function init() {
        const clips = await vision.FilesetResolver.forVisionTasks("https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.3/wasm");
        faceLandmarker = await vision.FaceLandmarker.createFromOptions(clips, {
            baseOptions: { modelAssetPath: "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task", delegate: "GPU" },
            outputFaceBlendshapes: true, runningMode: "VIDEO", numFaces: 1
        });
        objectDetector = await vision.ObjectDetector.createFromOptions(clips, {
            baseOptions: { modelAssetPath: "https://storage.googleapis.com/mediapipe-models/object_detector/efficientdet_lite0/float16/1/efficientdet_lite0.tflite", delegate: "GPU" },
            scoreThreshold: 0.5, runningMode: "VIDEO"
        });
        const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } });
        video.srcObject = stream;
        video.onloadeddata = () => { predictWebcam(); };
    }

    function drawLandmarks(landmarks) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        ctx.strokeStyle = "#00FF00"; ctx.lineWidth = 1;
        landmarks.forEach(point => { ctx.beginPath(); ctx.arc(point.x * canvas.width, point.y * canvas.height, 1, 0, 2 * Math.PI); ctx.stroke(); });
    }

    async function predictWebcam() {
        canvas.width = video.videoWidth; canvas.height = video.videoHeight;
        if (lastVideoTime !== video.currentTime) {
            lastVideoTime = video.currentTime;
            const resFace = faceLandmarker.detectForVideo(video, Date.now());
            const resObj = objectDetector.detectForVideo(video, Date.now());
            
            let phoneDetected = false;
            if(resObj.detections) resObj.detections.forEach(d => { if(d.categories[0].categoryName === "cell phone") phoneDetected = true; });
            if(phoneDetected) phoneCounter++; else phoneCounter = 0;

            if (resFace.faceLandmarks && resFace.faceLandmarks.length > 0) {
                drawLandmarks(resFace.faceLandmarks[0]);
                const lm = resFace.faceLandmarks[0];
                
                const avgEar = (getEAR(lm, [362,385,387,263,373,380]) + getEAR(lm, [33,160,158,133,153,144])) / 2.0;
                if (avgEar < 0.22) closedEyeCounter++; else closedEyeCounter = 0;
                
                if (lm[1].y - lm[10].y > 0.16) lookDownCounter++; else lookDownCounter = 0;
                
                if (phoneCounter > 20) { statusEl.innerText = "📵 Phone!"; statusEl.style.color = "#ef4444"; playAlarm(); }
                else if (closedEyeCounter > 30) { statusEl.innerText = "😴 Wake up!"; statusEl.style.color = "#ef4444"; playAlarm(); }
                else if (lookDownCounter > 60) { statusEl.innerText = "🤔 Distracted!"; statusEl.style.color = "#f59e0b"; playAlarm(); }
                else { statusEl.innerText = "✅ Focused"; statusEl.style.color = "#10b981"; stopAlarm(); }
            } else { statusEl.innerText = "❌ Away"; statusEl.style.color = "#94a3b8"; stopAlarm(); }
        }
        requestAnimationFrame(predictWebcam);
    }

    pipBtn.onclick = () => { container.style.display = container.style.display === 'none' ? 'block' : 'none'; };
    let isDragging = false, offset = [0, 0];
    container.onmousedown = (e) => { isDragging = true; offset = [container.offsetLeft - e.clientX, container.offsetTop - e.clientY]; };
    document.onmousemove = (e) => { if (isDragging) { container.style.left = (e.clientX + offset[0]) + 'px'; container.style.top = (e.clientY + offset[1]) + 'px'; container.style.bottom = 'auto'; container.style.right = 'auto'; } };
    document.onmouseup = () => isDragging = false;

    init();
    </script>
    """

def embed_eye_tracker():
    """Embeds the advanced eye tracker component."""
    components.html(get_eye_tracker_html(), height=100)
