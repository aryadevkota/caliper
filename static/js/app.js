/**
 * Caliper Atelier Frontend Application
 * Interactivity, Tactile Knob Physics, Rolling Yarn Loader, and API Streaming
 */

let allMachines = [];
let currentMachine = null;

// DOM Elements
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

// Dials & Badges
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
const safetyCardText = document.getElementById("safetyCardText");
const currentMachineLabel = document.getElementById("currentMachineLabel");

// Chassis spec elements
const chassisName = document.getElementById("chassisName");
const chassisCategory = document.getElementById("chassisCategory");
const specTension = document.getElementById("specTension");
const specBobbin = document.getElementById("specBobbin");
const specNeedle = document.getElementById("specNeedle");
const specFoot = document.getElementById("specFoot");
const specSpeed = document.getElementById("specSpeed");

// Initialize application
async function init() {
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
      selectMachine(defaultM.machine_id);
    }
  } catch (err) {
    console.error("Failed to load machine catalog:", err);
  }

  // Setup Event Listeners
  machineSelect.addEventListener("change", (e) => selectMachine(e.target.value));
  chatForm.addEventListener("submit", handleSubmit);
  
  // Trace drawer toggle
  traceToggleBtn.addEventListener("click", () => {
    const isHidden = traceDrawer.style.display === "none";
    traceDrawer.style.display = isHidden ? "flex" : "none";
  });

  // Preset chip clicks
  document.querySelectorAll(".swatch-chip").forEach(chip => {
    chip.addEventListener("click", () => handleScenarioClick(chip.dataset.scenario));
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

    // Reset baseline knob positions
    rotateKnob(rotorTension, currentMachine.tension_default || 4.0, currentMachine.tension_min, currentMachine.tension_max);
    valTension.textContent = (currentMachine.tension_default || 4.0).toFixed(1);
  } catch (err) {
    console.error("Error selecting machine:", err);
  }
}

// Calculate angle and rotate the physical knob smoothly
function rotateKnob(rotorElem, value, minVal, maxVal) {
  const val = parseFloat(value) || 0;
  const min = parseFloat(minVal) || 0;
  const max = parseFloat(maxVal) || (min + 9);
  const clamped = Math.max(min, Math.min(max, val));
  const span = max - min > 0 ? (max - min) : 1;
  const ratio = (clamped - min) / span;

  // -120deg to +120deg mechanical sweep
  const angle = -120 + ratio * 240;
  rotorElem.style.transform = `rotate(${angle.toFixed(1)}deg)`;
}

// Form Submit Handler
async function handleSubmit(e) {
  if (e) e.preventDefault();
  const text = userInput.value.trim();
  if (!text) return;

  // Add user bubble
  appendMessage("user", text);
  userInput.value = "";
  
  // Show the rolling yarn ball loader! 🧶
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

    // Update Dials & Knobs
    if (data.dials) {
      updateDials(data.dials, currentMachine);
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
    appendMessage("assistant", "⚠️ I encountered an error communicating with the agent. Please verify your local connection.");
  } finally {
    showYarnLoader(false);
    btnSubmit.disabled = false;
    userInput.focus();
  }
}

// Update Dials with Smooth Physics Spin
function updateDials(dials, machine) {
  const minT = machine ? machine.tension_min : 0;
  const maxT = machine ? machine.tension_max : 9;
  const minL = machine ? machine.stitch_length_min_mm : 0;
  const maxL = machine ? machine.stitch_length_max_mm : 4;
  const minW = machine ? machine.stitch_width_min_mm : 0;
  const maxW = machine ? machine.stitch_width_max_mm : 6;

  if (dials.tension !== undefined && dials.tension !== null) {
    rotateKnob(rotorTension, dials.tension, minT, maxT);
    valTension.textContent = parseFloat(dials.tension).toFixed(1);
  }

  if (dials.stitch_length !== undefined && dials.stitch_length !== null) {
    rotateKnob(rotorLength, dials.stitch_length, minL, maxL);
    valLength.textContent = `${parseFloat(dials.stitch_length).toFixed(1)} mm`;
  }

  if (dials.stitch_width !== undefined && dials.stitch_width !== null) {
    rotateKnob(rotorWidth, dials.stitch_width, minW, maxW);
    valWidth.textContent = `${parseFloat(dials.stitch_width).toFixed(1)} mm`;
  }

  if (dials.stitch_type) badgeStitchType.textContent = dials.stitch_type;
  if (dials.needle) badgeNeedle.textContent = dials.needle;
  if (dials.foot) badgeFoot.textContent = dials.foot;
}

// Update Safety Card
function updateSafety(safety) {
  const severity = safety.severity || "SAFE";
  safetyCard.className = `safety-indicator-card ${severity.toLowerCase()}`;
  
  if (severity === "CRITICAL") {
    safetyCardText.innerHTML = `<strong>🚨 HAZARD INTERCEPTED:</strong> ${safety.message || "Fabric density exceeds needle limits. Needle upgraded to prevent snapping."}`;
  } else if (severity === "WARNING") {
    safetyCardText.innerHTML = `<strong>⚠️ CAUTION:</strong> ${safety.message || "Delicate fabric fiber piercing risk."}`;
  } else {
    safetyCardText.innerHTML = `✓ <strong>Physical Safety Verified:</strong> All parameters within safe operating thresholds.`;
  }
}

// Render Step-by-Step Execution Trace
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
        ${step.thought ? `<div class="step-thought">💭 <strong>Reasoning:</strong> ${escapeHtml(step.thought)}</div>` : ""}
        ${step.tool_name ? `<div class="step-tool">🛠️ <code>${step.tool_name}(${JSON.stringify(step.tool_args || {})})</code></div>` : ""}
        ${step.observation ? `<div class="step-obs">📥 <strong>Observation:</strong>\n${escapeHtml(step.observation)}</div>` : ""}
        ${step.answer ? `<div style="color:var(--brand-burgundy); margin-top:4px;">✨ <strong>Answer:</strong> ${escapeHtml(step.answer.slice(0, 140))}...</div>` : ""}
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
    meta.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="#8E1B26"><path d="M7 2h10v3H7zm0 17h10v3H7zm2-14h6v14H9z"/></svg> Caliper Atelier Assistant`;
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

// Preset Scenario Handler
async function handleScenarioClick(scenarioId) {
  if (scenarioId === "1") {
    // Scenario 1: Stretch Jersey on Brother SM3701
    machineSelect.value = "brother_sm3701";
    await selectMachine("brother_sm3701");
    userInput.value = "Brother SM3701, polyester spandex jersey knit 200 GSM 50% stretch, side seam";
    handleSubmit();
  } else if (scenarioId === "2") {
    // Scenario 2: Bird-nesting defect on Singer 4423
    machineSelect.value = "singer_hd_4423";
    await selectMachine("singer_hd_4423");
    userInput.value = "Severe bird-nesting and looping on underside of fabric on Singer 4423";
    handleSubmit();
  } else if (scenarioId === "3") {
    // Scenario 3: Safety Intercept on Brother SM3701
    machineSelect.value = "brother_sm3701";
    await selectMachine("brother_sm3701");
    userInput.value = "14oz heavy denim flat-felled seam with 70/10 needle on Brother SM3701";
    handleSubmit();
  } else if (scenarioId === "4") {
    // Scenario 4: Silk chiffon rolled hem on Janome HD1000
    machineSelect.value = "janome_hd1000";
    await selectMachine("janome_hd1000");
    userInput.value = "Janome HD1000, silk chiffon 45 GSM rolled hem";
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

// Start app
document.addEventListener("DOMContentLoaded", init);
