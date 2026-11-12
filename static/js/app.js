/**
 * Caliper: The Sewing & Calibration Atelier
 * Tactile Rotary Drag Physics, Web Audio Synthesized Mechanical Detents,
 * 6-Specimen Swatch Specimen Drawer, Dynamic Cursor Lighting & API Streaming.
 */

// Global State
let allMachines = [];
let currentMachine = null;

// Audio Synthesizer Class
class RotaryAudio {
  constructor() {
    this.ctx = null;
    this.lastClickTime = 0;
  }

  ensureContext() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) {
        this.ctx = new AudioCtx();
      }
    }
    if (this.ctx && this.ctx.state === "suspended") {
      this.ctx.resume();
    }
  }

  /**
   * Synthesize crisp mechanical dial ratchet detent click.
   * Pitch factor modulates click frequency based on dial position.
   */
  playDetent(pitch = 1.0) {
    try {
      this.ensureContext();
      if (!this.ctx) return;
      const now = this.ctx.currentTime;
      if (now - this.lastClickTime < 0.02) return; // Debounce rapid bursts
      this.lastClickTime = now;

      // 1. High-frequency metallic snap transient
      const bufferSize = Math.floor(this.ctx.sampleRate * 0.005);
      const buffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
      const output = buffer.getChannelData(0);
      for (let i = 0; i < bufferSize; i++) {
        output[i] = (Math.random() * 2 - 1) * Math.exp(-i / (bufferSize * 0.25));
      }
      const noise = this.ctx.createBufferSource();
      noise.buffer = buffer;

      const noiseFilter = this.ctx.createBiquadFilter();
      noiseFilter.type = "bandpass";
      noiseFilter.frequency.setValueAtTime(3200 * pitch, now);
      noiseFilter.Q.setValueAtTime(3.5, now);

      const noiseGain = this.ctx.createGain();
      noiseGain.gain.setValueAtTime(0.3, now);
      noiseGain.gain.exponentialRampToValueAtTime(0.001, now + 0.006);

      noise.connect(noiseFilter);
      noiseFilter.connect(noiseGain);
      noiseGain.connect(this.ctx.destination);
      noise.start(now);

      // 2. Hollow mechanical ratchet cavity resonance
      const osc = this.ctx.createOscillator();
      const oscGain = this.ctx.createGain();
      osc.type = "triangle";
      osc.frequency.setValueAtTime(940 * pitch, now);
      osc.frequency.exponentialRampToValueAtTime(420 * pitch, now + 0.022);

      oscGain.gain.setValueAtTime(0.18, now);
      oscGain.gain.exponentialRampToValueAtTime(0.0001, now + 0.028);

      osc.connect(oscGain);
      oscGain.connect(this.ctx.destination);
      osc.start(now);
      osc.stop(now + 0.03);
    } catch (_) {
      // Audio policy safe
    }
  }

  /**
   * Synthesize softer button/switch toggle click
   */
  playSwitch() {
    this.playDetent(0.78);
  }
}

const rotaryAudio = new RotaryAudio();

// Backward compatibility helper
function playTactileClick() {
  rotaryAudio.playSwitch();
}

// DOM Elements Cache
const machineSelect = document.getElementById("machineSelect");
const providerSelect = document.getElementById("providerSelect");
const apiKeyInput = document.getElementById("apiKeyInput");
const chatStream = document.getElementById("chatStream");
const chatForm = document.getElementById("chatForm");
const userInput = document.getElementById("userInput");
const btnSubmit = document.getElementById("btnSubmit");
const yarnLoader = document.getElementById("yarnLoader");
const traceDrawer = document.getElementById("traceDrawer");
const traceToggleBtn = document.getElementById("traceToggleBtn");
const traceToggleHint = document.getElementById("traceToggleHint");
const btnResetDefaults = document.getElementById("btnResetDefaults");

// Dials & Badges
const bezelTension = document.getElementById("bezelTension");
const bezelLength = document.getElementById("bezelLength");
const bezelWidth = document.getElementById("bezelWidth");
const rotorTension = document.getElementById("rotorTension");
const rotorLength = document.getElementById("rotorLength");
const rotorWidth = document.getElementById("rotorWidth");
const valTension = document.getElementById("valTension");
const valLength = document.getElementById("valLength");
const valWidth = document.getElementById("valWidth");
const rangeTension = document.getElementById("rangeTension");
const rangeLength = document.getElementById("rangeLength");
const rangeWidth = document.getElementById("rangeWidth");
const badgeStitchType = document.getElementById("badgeStitchType");
const badgeNeedle = document.getElementById("badgeNeedle");
const badgeFoot = document.getElementById("badgeFoot");
const safetyCard = document.getElementById("safetyCard");
const currentMachineLabel = document.getElementById("currentMachineLabel");

// Chassis spec elements
const chassisName = document.getElementById("chassisName");
const chassisCategory = document.getElementById("chassisCategory");
const specTension = document.getElementById("specTension");
const specBobbin = document.getElementById("specBobbin");
const specNeedle = document.getElementById("specNeedle");
const specFoot = document.getElementById("specFoot");
const specSpeed = document.getElementById("specSpeed");

// Dial State Model
const dialState = {
  tension: {
    value: 4.0,
    min: 0.0,
    max: 9.0,
    step: 0.5,
    unit: "",
    rotor: rotorTension,
    valElem: valTension,
    bezel: bezelTension
  },
  length: {
    value: 2.5,
    min: 0.0,
    max: 4.0,
    step: 0.5,
    unit: " mm",
    rotor: rotorLength,
    valElem: valLength,
    bezel: bezelLength
  },
  width: {
    value: 0.0,
    min: 0.0,
    max: 5.0,
    step: 0.5,
    unit: " mm",
    rotor: rotorWidth,
    valElem: valWidth,
    bezel: bezelWidth
  }
};

const WIDTH_WHEEL_ANGLES = [0, -65, -130, -180, -228, -295];

/**
 * Compute rotor rotation (deg) so the active value aligns with the top bezel notch.
 */
function getDialAngle(param, value) {
  if (param === "tension") {
    // 0–9 ticks span clockwise at 36deg/unit with 0 at 12 o'clock
    return -value * 36;
  }
  if (param === "width") {
    // 0–5 marks sit clockwise at [0, 65, 130, 180, 228, 295] deg
    const idx = Math.floor(value);
    const frac = value - idx;
    if (idx >= WIDTH_WHEEL_ANGLES.length - 1) {
      return WIDTH_WHEEL_ANGLES[WIDTH_WHEEL_ANGLES.length - 1];
    }
    if (idx < 0) return WIDTH_WHEEL_ANGLES[0];
    return WIDTH_WHEEL_ANGLES[idx] + frac * (WIDTH_WHEEL_ANGLES[idx + 1] - WIDTH_WHEEL_ANGLES[idx]);
  }
  if (param === "length") {
    // 0–4 marks span -137deg to +137deg at 68.5deg/unit with 2 at 12 o'clock
    return (2.0 - value) * 68.5;
  }
  const dial = dialState[param];
  const span = dial && dial.max - dial.min > 0 ? (dial.max - dial.min) : 1;
  const ratio = dial ? (value - dial.min) / span : 0;
  return -120 + ratio * 240;
}

/**
 * Set dial value, compute wheel alignment angle, and update visual/ARIA state.
 */
function setDialValue(param, value, animate = true) {
  const dial = dialState[param];
  if (!dial || !dial.rotor) return;

  const numVal = parseFloat(value);
  if (isNaN(numVal)) return;

  const clamped = Math.min(dial.max, Math.max(dial.min, numVal));
  dial.value = clamped;

  if (animate) {
    dial.rotor.classList.add("animating");
  } else {
    dial.rotor.classList.remove("animating");
  }

  const angle = getDialAngle(param, clamped);
  dial.rotor.style.transform = `rotate(${angle.toFixed(1)}deg)`;

  if (param === "width" && clamped === 0) {
    dial.valElem.textContent = "0.0 mm";
    if (dial.bezel) dial.bezel.setAttribute("aria-valuetext", "0.0 mm (Straight)");
  } else {
    dial.valElem.textContent = `${clamped.toFixed(1)}${dial.unit}`;
    if (dial.bezel) dial.bezel.setAttribute("aria-valuetext", `${clamped.toFixed(1)}${dial.unit}`);
  }

  if (dial.bezel) {
    dial.bezel.setAttribute("aria-valuenow", clamped.toFixed(1));
  }
}

/**
 * Configure circular pointer dragging and keyboard slider controls on dials.
 */
function setupKnobInteractions(param) {
  const dial = dialState[param];
  if (!dial || !dial.bezel) return;

  let isDragging = false;
  let lastDetentVal = dial.value;

  function updateFromPointer(e) {
    const rect = dial.bezel.getBoundingClientRect();
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;
    const dx = e.clientX - cx;
    const dy = e.clientY - cy;

    // Angle relative to 3 o'clock in degrees
    const degFromEast = Math.atan2(dy, dx) * (180 / Math.PI);
    // Convert to dial angle where 12 o'clock is 0deg (-180 to +180)
    let dialAngle = degFromEast + 90;
    if (dialAngle > 180) dialAngle -= 360;

    // Clamping to active arc [-120, +120]
    // The bottom dead zone is between 120 and 180 (right) and -180 and -120 (left)
    if (dialAngle > 120) {
      dialAngle = 120;
    } else if (dialAngle < -120) {
      dialAngle = -120;
    }

    const ratio = (dialAngle - (-120)) / 240;
    const rawVal = dial.min + ratio * (dial.max - dial.min);
    const snappedVal = Math.round(rawVal / dial.step) * dial.step;
    const clampedVal = Math.min(dial.max, Math.max(dial.min, snappedVal));

    if (Math.abs(clampedVal - lastDetentVal) >= dial.step / 2) {
      const pitch = 0.85 + 0.35 * ratio;
      rotaryAudio.playDetent(pitch);
      lastDetentVal = clampedVal;
    }

    setDialValue(param, clampedVal, false);
  }

  dial.bezel.addEventListener("pointerdown", (e) => {
    if (e.button !== 0 && e.pointerType === "mouse") return;
    isDragging = true;
    try {
      dial.bezel.setPointerCapture(e.pointerId);
    } catch (_) {}
    dial.bezel.classList.add("dragging");
    dial.rotor.classList.remove("animating");
    updateFromPointer(e);
  });

  dial.bezel.addEventListener("pointermove", (e) => {
    if (!isDragging) return;
    updateFromPointer(e);
  });

  const stopDrag = (e) => {
    if (!isDragging) return;
    isDragging = false;
    try {
      dial.bezel.releasePointerCapture(e.pointerId);
    } catch (_) {}
    dial.bezel.classList.remove("dragging");
    dial.rotor.classList.add("animating");
  };

  dial.bezel.addEventListener("pointerup", stopDrag);
  dial.bezel.addEventListener("pointercancel", stopDrag);

  // Full ARIA 1.2 Slider Keyboard Access
  dial.bezel.addEventListener("keydown", (e) => {
    let delta = 0;
    if (e.key === "ArrowRight" || e.key === "ArrowUp") {
      delta = dial.step;
    } else if (e.key === "ArrowLeft" || e.key === "ArrowDown") {
      delta = -dial.step;
    } else if (e.key === "PageUp") {
      delta = dial.step * 2;
    } else if (e.key === "PageDown") {
      delta = -dial.step * 2;
    } else if (e.key === "Home") {
      e.preventDefault();
      setDialValue(param, dial.min, true);
      rotaryAudio.playDetent(0.8);
      return;
    } else if (e.key === "End") {
      e.preventDefault();
      setDialValue(param, dial.max, true);
      rotaryAudio.playDetent(1.2);
      return;
    } else {
      return;
    }

    e.preventDefault();
    const nextVal = Math.min(dial.max, Math.max(dial.min, dial.value + delta));
    if (nextVal !== dial.value) {
      const ratio = (nextVal - dial.min) / (dial.max - dial.min);
      rotaryAudio.playDetent(0.85 + 0.35 * ratio);
      setDialValue(param, nextVal, true);
    }
  });
}

/**
 * Setup dynamic cursor lighting occlusion on workspace cards.
 */
function setupDynamicLighting() {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  const workspace = document.querySelector(".atelier-workspace");
  if (!workspace) return;

  let ticking = false;
  workspace.addEventListener("mousemove", (e) => {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(() => {
      const rect = workspace.getBoundingClientRect();
      const xRatio = (e.clientX - rect.left) / rect.width - 0.5; // -0.5 to +0.5
      const yRatio = (e.clientY - rect.top) / rect.height - 0.5;

      const shadowX = (-xRatio * 14).toFixed(1);
      const shadowY = (12 - yRatio * 8).toFixed(1);

      document.documentElement.style.setProperty(
        "--shadow-paper-dynamic",
        `${shadowX}px ${shadowY}px 28px rgba(61, 30, 40, 0.09), 0 3px 6px rgba(61, 30, 40, 0.05)`
      );
      ticking = false;
    });
  });
}

// Initialize Application
async function init() {
  // Setup Dial Interactions
  setupKnobInteractions("tension");
  setupKnobInteractions("length");
  setupKnobInteractions("width");

  // Setup Dynamic Lighting Occlusion
  setupDynamicLighting();

  try {
    const res = await fetch("/api/machines");
    const data = await res.json();
    allMachines = data.machines || [];

    // Populate dropdown
    machineSelect.innerHTML = allMachines.map(m => `
      <option value="${m.machine_id}">
        ${m.brand} ${m.model_name} (${m.category})
      </option>
    `).join("");

    // Set default to brother_sm3701
    const defaultM = allMachines.find(m => m.machine_id === "brother_sm3701") || allMachines[0];
    if (defaultM) {
      machineSelect.value = defaultM.machine_id;
      await selectMachine(defaultM.machine_id);
    }
  } catch (err) {
    console.error("Failed to load machine catalog:", err);
  }

  // Event Listeners
  machineSelect.addEventListener("change", (e) => {
    rotaryAudio.playSwitch();
    selectMachine(e.target.value);
  });

  chatForm.addEventListener("submit", handleSubmit);

  // Collapsible Sample Prompts Drawer
  const samplePromptsToggle = document.getElementById("samplePromptsToggle");
  const samplePromptsGrid = document.getElementById("samplePromptsGrid");
  const promptsToggleHint = document.getElementById("promptsToggleHint");

  if (samplePromptsToggle && samplePromptsGrid) {
    const togglePrompts = () => {
      rotaryAudio.playSwitch();
      const isCollapsed = samplePromptsGrid.classList.toggle("collapsed");
      samplePromptsToggle.setAttribute("aria-expanded", !isCollapsed);
      if (promptsToggleHint) {
        promptsToggleHint.textContent = isCollapsed ? "Expand ▸" : "Collapse ▾";
      }
    };

    samplePromptsToggle.addEventListener("click", togglePrompts);
    samplePromptsToggle.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        togglePrompts();
      }
    });
  }

  // Expandable Chat View Toggle
  const btnExpandChat = document.getElementById("btnExpandChat");
  const chatCard = document.querySelector(".chat-atelier-card");
  const expandChatText = document.getElementById("expandChatText");

  if (btnExpandChat && chatCard) {
    btnExpandChat.addEventListener("click", () => {
      rotaryAudio.playSwitch();
      const isExpanded = chatCard.classList.toggle("expanded");
      btnExpandChat.setAttribute("aria-expanded", isExpanded);
      if (expandChatText) {
        expandChatText.textContent = isExpanded ? "Collapse View" : "Expand View";
      }
    });
  }

  // Trace Drawer Toggle
  if (traceToggleBtn) {
    traceToggleBtn.addEventListener("click", () => {
      rotaryAudio.playSwitch();
      const isHidden = traceDrawer.style.display === "none";
      traceDrawer.style.display = isHidden ? "flex" : "none";
      traceToggleBtn.setAttribute("aria-expanded", isHidden ? "true" : "false");
      if (traceToggleHint) {
        traceToggleHint.textContent = isHidden ? "Click to Collapse ▴" : "Click to Inspect ▾";
      }
    });

    traceToggleBtn.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        traceToggleBtn.click();
      }
    });
  }

  // Reset to Baseline Defaults Button
  if (btnResetDefaults) {
    btnResetDefaults.addEventListener("click", () => {
      rotaryAudio.playSwitch();
      setTimeout(() => rotaryAudio.playDetent(1.15), 110);

      if (currentMachine) {
        const defTension = currentMachine.tension_default !== undefined ? currentMachine.tension_default : 4.0;
        const defLength = currentMachine.stitch_length_default !== undefined ? currentMachine.stitch_length_default : 2.5;
        const defWidth = currentMachine.stitch_width_default !== undefined ? currentMachine.stitch_width_default : 0.0;

        setDialValue("tension", defTension, true);
        setDialValue("length", defLength, true);
        setDialValue("width", defWidth, true);

        badgeStitchType.textContent = "Straight";
        badgeNeedle.textContent = `${currentMachine.min_needle_size_eu || 75}/${currentMachine.min_needle_size_us || 11} Universal`;
        badgeFoot.textContent = currentMachine.presser_foot_system || "Snap-on Foot";
        updateSafety({ severity: "SAFE", message: "Physical Safety Verified: Reset to catalog baseline." });

        // Clear active chip states
        document.querySelectorAll(".swatch-chip").forEach(c => c.classList.remove("active"));
      }
    });
  }

  // Preset Swatch Chip Clicks
  document.querySelectorAll(".swatch-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      handleScenarioClick(chip.dataset.scenario);
    });
  });
}

// Update UI when a machine is chosen
async function selectMachine(machineId) {
  try {
    const res = await fetch(`/api/machine/${machineId}`);
    currentMachine = await res.json();

    chassisName.textContent = `${currentMachine.brand} ${currentMachine.model_name}`;
    chassisCategory.textContent = currentMachine.machine_category.toUpperCase();
    specTension.textContent = `${currentMachine.tension_min} – ${currentMachine.tension_max}`;
    specBobbin.textContent = `${currentMachine.bobbin_system} (${currentMachine.bobbin_class})`;
    specNeedle.textContent = `${currentMachine.needle_system} (${currentMachine.min_needle_size_eu}-${currentMachine.max_needle_size_eu})`;
    specFoot.textContent = currentMachine.presser_foot_system;
    specSpeed.textContent = `${currentMachine.max_speed_spm} SPM`;
    currentMachineLabel.textContent = `${currentMachine.brand} ${currentMachine.model_name}`;

    rangeTension.textContent = `Range: ${currentMachine.tension_min} – ${currentMachine.tension_max}`;
    rangeLength.textContent = `Range: ${currentMachine.stitch_length_min_mm} – ${currentMachine.stitch_length_max_mm}mm`;
    rangeWidth.textContent = `Range: ${currentMachine.stitch_width_min_mm} – ${currentMachine.stitch_width_max_mm}mm`;

    // Update Dial Min/Max Bounds
    dialState.tension.min = currentMachine.tension_min || 0;
    dialState.tension.max = currentMachine.tension_max || 9;
    dialState.length.min = currentMachine.stitch_length_min_mm || 0;
    dialState.length.max = currentMachine.stitch_length_max_mm || 4;
    dialState.width.min = currentMachine.stitch_width_min_mm || 0;
    dialState.width.max = currentMachine.stitch_width_max_mm || 5;

    // Update ARIA Bounds
    if (bezelTension) {
      bezelTension.setAttribute("aria-valuemin", dialState.tension.min);
      bezelTension.setAttribute("aria-valuemax", dialState.tension.max);
    }
    if (bezelLength) {
      bezelLength.setAttribute("aria-valuemin", dialState.length.min);
      bezelLength.setAttribute("aria-valuemax", dialState.length.max);
    }
    if (bezelWidth) {
      bezelWidth.setAttribute("aria-valuemin", dialState.width.min);
      bezelWidth.setAttribute("aria-valuemax", dialState.width.max);
    }

    // Reset baseline knob positions with smooth physical spin
    const baseTension = currentMachine.tension_default || 4.0;
    setDialValue("tension", baseTension, true);

    const baseLength = currentMachine.stitch_length_default !== undefined ? currentMachine.stitch_length_default : 2.5;
    setDialValue("length", baseLength, true);

    const baseWidth = currentMachine.stitch_width_default !== undefined ? currentMachine.stitch_width_default : 0.0;
    setDialValue("width", baseWidth, true);

  } catch (err) {
    console.error("Error selecting machine:", err);
  }
}

// Form Submit Handler
async function handleSubmit(e) {
  if (e) e.preventDefault();
  const text = userInput.value.trim();
  if (!text) return;

  rotaryAudio.playSwitch();

  // Add user bubble (Confectioner's Blush memo note)
  appendMessage("user", text);
  userInput.value = "";
  
  // Show the rolling yarn ball loader
  showYarnLoader(true);
  btnSubmit.disabled = true;

  try {
    const payload = {
      message: text,
      machine_id: machineSelect.value,
      provider: providerSelect.value,
      api_key: apiKeyInput.value.trim()
    };

    const res = await fetch("/api/calibrate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    
    // Add assistant bubble
    appendMessage("assistant", data.final_answer || "Calibration complete.");

    // Update Dials & Knobs with smooth physical spin
    if (data.dials) {
      updateDials(data.dials);
    }

    // Update Safety Status
    if (data.safety) {
      updateSafety(data.safety);
    }

    // Update Trace Drawer
    if (data.trace) {
      renderTrace(data.trace);
    }

  } catch (err) {
    console.error("Calibration error:", err);
    appendMessage("assistant", "I encountered an error communicating with the agent. Please verify your local connection or model selection.");
  } finally {
    showYarnLoader(false);
    btnSubmit.disabled = false;
    userInput.focus();
  }
}

// Update Dials with Smooth Physics Spin
function updateDials(dials) {
  if (dials.tension !== undefined && dials.tension !== null) {
    setDialValue("tension", dials.tension, true);
  }

  if (dials.stitch_length !== undefined && dials.stitch_length !== null) {
    setDialValue("length", dials.stitch_length, true);
  }

  if (dials.stitch_width !== undefined && dials.stitch_width !== null) {
    setDialValue("width", dials.stitch_width, true);
  }

  if (dials.stitch_type) badgeStitchType.textContent = dials.stitch_type;
  if (dials.needle) badgeNeedle.textContent = dials.needle;
  if (dials.foot) badgeFoot.textContent = dials.foot;
}

// Update Safety Card
function updateSafety(safety) {
  const severity = safety.severity || "SAFE";
  safetyCard.className = `safety-indicator-card ${severity.toLowerCase()}`;
  
  if (severity === "CRITICAL" || severity === "HAZARD") {
    safetyCard.innerHTML = `
      <img src="/newbrandkit/AccentsGraphicsElements/AssetsSVGs/82.svg" class="safety-badge-icon" alt="Hazard">
      <div><strong>HAZARD INTERCEPTED:</strong> ${escapeHtml(safety.message || "Fabric density exceeds needle limits. Needle upgraded to prevent snapping.")}</div>
    `;
  } else if (severity === "WARNING") {
    safetyCard.innerHTML = `
      <img src="/newbrandkit/AccentsGraphicsElements/AssetsSVGs/82.svg" class="safety-badge-icon" alt="Caution">
      <div><strong>CAUTION:</strong> ${escapeHtml(safety.message || "Delicate fabric fiber piercing risk.")}</div>
    `;
  } else {
    safetyCard.innerHTML = `
      <img src="/newbrandkit/AccentsGraphicsElements/AssetsSVGs/30.svg" class="safety-badge-icon" alt="Safe">
      <div><strong>Physical Safety Verified:</strong> ${escapeHtml(safety.message || "All parameters within safe operating thresholds.")}</div>
    `;
  }
}

// Render Step-by-Step Execution Trace in Deep Plum Cardstock Drawer
function renderTrace(trace) {
  if (!trace || trace.length === 0) return;

  traceDrawer.innerHTML = trace.map(step => {
    const isAnswer = !step.tool_name && step.answer;
    return `
      <div class="trace-step-item">
        <div class="step-header">
          <span>[Step ${step.step}]</span>
          <span>${isAnswer ? "FINAL ANSWER" : (step.tool_name || "REASONING")}</span>
        </div>
        ${step.thought ? `<div class="step-thought"><img src="/newbrandkit/AccentsGraphicsElements/AssetsSVGs/94.svg" class="trace-icon" alt="" aria-hidden="true"><strong>Reasoning:</strong> ${escapeHtml(step.thought)}</div>` : ""}
        ${step.tool_name ? `<div class="step-tool"><img src="/newbrandkit/AccentsGraphicsElements/AssetsSVGs/1.svg" class="trace-icon" alt="" aria-hidden="true"><code>${step.tool_name}(${JSON.stringify(step.tool_args || {})})</code></div>` : ""}
        ${step.observation ? `<div class="step-obs"><img src="/newbrandkit/AccentsGraphicsElements/AssetsSVGs/15.svg" class="trace-icon" alt="" aria-hidden="true"><strong>Observation:</strong>\n${escapeHtml(step.observation)}</div>` : ""}
        ${step.answer ? `<div class="step-answer"><img src="/newbrandkit/AccentsGraphicsElements/AssetsSVGs/23.svg" class="trace-icon" alt="" aria-hidden="true"><strong>Answer:</strong> ${escapeHtml(step.answer.slice(0, 160))}...</div>` : ""}
      </div>
    `;
  }).join("");
}

// Append Chat Bubble
function appendMessage(sender, text) {
  const bubble = document.createElement("div");
  bubble.className = `chat-bubble ${sender}`;

  const meta = document.createElement("div");
  meta.className = "bubble-meta";
  if (sender === "user") {
    meta.textContent = "You";
  } else {
    meta.innerHTML = `<img src="/newbrandkit/AccentsGraphicsElements/AssetsSVGs/81.svg" class="bubble-notion-icon" style="width:14px; height:14px; object-fit:contain; vertical-align:middle; margin-right:4px;" alt=""> Caliper Atelier Assistant`;
  }

  const content = document.createElement("div");
  content.className = "bubble-content";
  content.innerHTML = formatMarkdown(text);

  bubble.appendChild(meta);
  bubble.appendChild(content);
  chatStream.appendChild(bubble);

  // Scroll to bottom
  chatStream.scrollTop = chatStream.scrollHeight;
}

// Show/Hide Rolling Yarn Ball
function showYarnLoader(show) {
  if (show) {
    yarnLoader.classList.add("active");
    chatStream.scrollTop = chatStream.scrollHeight;
  } else {
    yarnLoader.classList.remove("active");
  }
}

// 6-Specimen Preset Scenario Handler
async function handleScenarioClick(scenarioId) {
  rotaryAudio.playSwitch();

  // Mark clicked chip as active
  document.querySelectorAll(".swatch-chip").forEach(chip => {
    if (chip.dataset.scenario === scenarioId) {
      chip.classList.add("active");
    } else {
      chip.classList.remove("active");
    }
  });

  if (scenarioId === "1") {
    // 1. Stretch Jersey on Brother SM3701
    machineSelect.value = "brother_sm3701";
    await selectMachine("brother_sm3701");
    userInput.value = "Brother SM3701, polyester spandex jersey knit 200 GSM 50% stretch, side seam";
    handleSubmit();
  } else if (scenarioId === "2") {
    // 2. Bird-Nesting Defect on Singer 4423
    machineSelect.value = "singer_hd_4423";
    await selectMachine("singer_hd_4423");
    userInput.value = "Severe bird-nesting and looping on underside of fabric on Singer 4423";
    handleSubmit();
  } else if (scenarioId === "3") {
    // 3. Denim Hazard Intercept on Brother SM3701
    machineSelect.value = "brother_sm3701";
    await selectMachine("brother_sm3701");
    userInput.value = "14oz heavy denim flat-felled seam with 70/10 needle on Brother SM3701";
    handleSubmit();
  } else if (scenarioId === "4") {
    // 4. Silk Chiffon Rolled Hem on Janome HD1000
    machineSelect.value = "janome_hd1000";
    await selectMachine("janome_hd1000");
    userInput.value = "Janome HD1000, silk chiffon 45 GSM rolled hem";
    handleSubmit();
  } else if (scenarioId === "5") {
    // 5. Heavy Duck Canvas on Singer 4423
    machineSelect.value = "singer_hd_4423";
    await selectMachine("singer_hd_4423");
    userInput.value = "Singer 4423, heavy duck canvas 450 GSM, reinforced structural seam with #16/100 needle";
    handleSubmit();
  } else if (scenarioId === "6") {
    // 6. Fine Wool Flannel on Janome HD1000
    machineSelect.value = "janome_hd1000";
    await selectMachine("janome_hd1000");
    userInput.value = "Janome HD1000, fine wool flannel 280 GSM, tailored bound seam";
    handleSubmit();
  }
}

// Simple Markdown Formatter
function formatMarkdown(text) {
  if (!text) return "";
  let out = escapeHtml(text);
  
  // Headers
  out = out.replace(/### (.*?)\n/g, "<h3>$1</h3>");
  out = out.replace(/## (.*?)\n/g, "<h2>$1</h2>");
  
  // Bold
  out = out.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
  
  // Italics
  out = out.replace(/\*(.*?)\*/g, "<em>$1</em>");
  
  // Bullet points
  out = out.replace(/^- (.*?)$/gm, "<li>$1</li>");
  out = out.replace(/(<li>.*?<\/li>)/gs, "<ul>$1</ul>");
  
  // Line breaks
  out = out.replace(/\n\n/g, "<p></p>");
  out = out.replace(/\n/g, "<br>");
  
  return out;
}

function escapeHtml(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// Start app when DOM ready
document.addEventListener("DOMContentLoaded", init);
