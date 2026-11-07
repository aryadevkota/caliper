"""
Caliper UI Rendering Helpers
Generates rich SVG dial gauges, hardware spec cards, and trace inspectors for the localhost interface.
"""
import math
import html
from typing import Dict, Any, List

def generate_dial_svg(title: str, value: float, min_val: float, max_val: float, unit: str = "", default_val: float = 4.0) -> str:
    """Generate a clean, high-precision SVG rotary dial."""
    val = float(value if value is not None else default_val)
    min_v = float(min_val if min_val is not None else 0.0)
    max_v = float(max_val if max_val is not None and max_val > min_v else min_v + 9.0)
    
    val_clamped = max(min_v, min(max_v, val))
    range_span = max_v - min_v if max_v > min_v else 1.0
    ratio = (val_clamped - min_v) / range_span
    
    # -135 deg to +135 deg sweep (270 degree total arc)
    angle_start = -135
    angle_end = 135
    needle_angle = angle_start + ratio * (angle_end - angle_start)
    
    # Ticks along the arc
    tick_marks = []
    num_ticks = int(min(10, max_v - min_v + 1)) if (max_v - min_v).is_integer() else 5
    for i in range(num_ticks):
        t_val = min_v + (range_span * (i / (num_ticks - 1 if num_ticks > 1 else 1)))
        t_ratio = (t_val - min_v) / range_span
        t_angle = angle_start + t_ratio * (angle_end - angle_start)
        rad = math.radians(t_angle - 90)
        
        # Outer and inner tick positions
        x1 = 65 + 46 * math.cos(rad)
        y1 = 65 + 46 * math.sin(rad)
        x2 = 65 + 40 * math.cos(rad)
        y2 = 65 + 40 * math.sin(rad)
        tick_marks.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#4b5563" stroke-width="1.5" />')
        
    # Needle vector
    needle_rad = math.radians(needle_angle - 90)
    nx = 65 + 38 * math.cos(needle_rad)
    ny = 65 + 38 * math.sin(needle_rad)
    
    formatted_val = f"{val_clamped:.1f}" if val_clamped % 1 != 0 else f"{int(val_clamped)}"
    
    svg = f'''
    <div style="display:flex; flex-direction:column; align-items:center; margin:4px;">
      <svg viewBox="0 0 130 130" width="115" height="115" style="filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));">
        <!-- Outer bezel -->
        <circle cx="65" cy="65" r="58" fill="#181d24" stroke="#2e3746" stroke-width="3" />
        <circle cx="65" cy="65" r="50" fill="#10141a" stroke="#1f2937" stroke-width="1" />
        
        <!-- Ticks -->
        {''.join(tick_marks)}
        
        <!-- Arc track -->
        <path d="M 32.5 97.5 A 46 46 0 1 1 97.5 97.5" fill="none" stroke="#252d3a" stroke-width="4" stroke-linecap="round"/>
        
        <!-- Needle -->
        <line x1="65" y1="65" x2="{nx:.1f}" y2="{ny:.1f}" stroke="#a81c25" stroke-width="3" stroke-linecap="round" />
        <circle cx="65" cy="65" r="6.5" fill="#e5e7eb" stroke="#a81c25" stroke-width="1.5"/>
        <circle cx="65" cy="65" r="2" fill="#111827" />
        
        <!-- Value Readout -->
        <text x="65" y="100" text-anchor="middle" fill="#ffffff" font-family="system-ui, sans-serif" font-size="14" font-weight="700">{formatted_val}{unit}</text>
      </svg>
      <span style="font-size:11px; font-weight:600; color:#cbd5e1; text-transform:uppercase; letter-spacing:0.04em; margin-top:2px;">{html.escape(title)}</span>
      <span style="font-size:10px; color:#64748b;">Range: {int(min_v) if min_v.is_integer() else min_v} – {int(max_v) if max_v.is_integer() else max_v}{unit}</span>
    </div>
    '''
    return svg

def render_machine_card(specs: Dict[str, Any]) -> str:
    """Render an overview card for the currently selected sewing machine."""
    if not specs:
        return "<div style='color:#94a3b8; padding:10px;'>No machine selected.</div>"
    
    brand = html.escape(str(specs.get("brand", "Generic")))
    model = html.escape(str(specs.get("model_name", "Machine")))
    cat = html.escape(str(specs.get("machine_category", "Standard")))
    bobbin = html.escape(str(specs.get("bobbin_system", "Drop-in")))
    bobbin_class = html.escape(str(specs.get("bobbin_class", "Class 15")))
    needle_sys = html.escape(str(specs.get("needle_system", "130/705 H")))
    foot_sys = html.escape(str(specs.get("presser_foot_system", "Snap-on")))
    speed = specs.get("max_speed_spm", 800)
    stitches = specs.get("total_stitch_count", "Standard")
    t_min = specs.get("tension_min", 0)
    t_max = specs.get("tension_max", 9)
    
    html_card = f'''
    <div style="background:#111827; border:1px solid #1f2937; border-radius:10px; padding:12px 16px; margin-bottom:12px; color:#f3f4f6; font-family:system-ui, sans-serif;">
      <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #1f2937; padding-bottom:8px; margin-bottom:10px;">
        <div>
          <span style="font-size:16px; font-weight:700; color:#f87171; letter-spacing:-0.01em;">{brand} {model}</span>
          <span style="background:#374151; color:#93c5fd; font-size:10px; font-weight:600; padding:2px 6px; border-radius:4px; margin-left:8px; text-transform:uppercase;">{cat}</span>
        </div>
        <div style="font-size:11px; color:#9ca3af;">
          Max: <strong style="color:#f3f4f6;">{speed} SPM</strong> · Stitches: <strong style="color:#f3f4f6;">{stitches}</strong>
        </div>
      </div>
      
      <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap:8px; font-size:11px;">
        <div style="background:#1f2937; padding:6px 10px; border-radius:6px;">
          <span style="color:#9ca3af; display:block; font-size:9px; text-transform:uppercase;">Tension Range</span>
          <strong style="color:#67e8f9;">{t_min} – {t_max}</strong>
        </div>
        <div style="background:#1f2937; padding:6px 10px; border-radius:6px;">
          <span style="color:#9ca3af; display:block; font-size:9px; text-transform:uppercase;">Bobbin System</span>
          <strong style="color:#e2e8f0;">{bobbin} ({bobbin_class})</strong>
        </div>
        <div style="background:#1f2937; padding:6px 10px; border-radius:6px;">
          <span style="color:#9ca3af; display:block; font-size:9px; text-transform:uppercase;">Needle System</span>
          <strong style="color:#e2e8f0;">{needle_sys}</strong>
        </div>
        <div style="background:#1f2937; padding:6px 10px; border-radius:6px;">
          <span style="color:#9ca3af; display:block; font-size:9px; text-transform:uppercase;">Presser Foot</span>
          <strong style="color:#e2e8f0;">{foot_sys}</strong>
        </div>
      </div>
    </div>
    '''
    return html_card

def render_dial_dashboard(specs: Dict[str, Any], dials: Dict[str, Any], safety_status: Dict[str, Any] = None) -> str:
    """Render the interactive visual dial dashboard with dials, badges, and safety status."""
    specs = specs or {}
    dials = dials or {}
    
    t_val = dials.get("tension", specs.get("tension_default", 4.0))
    t_min = specs.get("tension_min", 0.0)
    t_max = specs.get("tension_max", 9.0)
    
    l_val = dials.get("stitch_length", 2.5)
    l_min = specs.get("stitch_length_min_mm", 0.0)
    l_max = specs.get("stitch_length_max_mm", 4.0)
    
    w_val = dials.get("stitch_width", 0.0)
    w_min = specs.get("stitch_width_min_mm", 0.0)
    w_max = specs.get("stitch_width_max_mm", 5.0)
    
    pattern = dials.get("stitch_type", "Straight")
    needle = dials.get("needle", "80/12 Universal")
    foot = dials.get("foot", "Standard J / All-purpose")
    
    # SVG Dials
    tension_svg = generate_dial_svg("Upper Tension", t_val, t_min, t_max, default_val=specs.get("tension_default", 4.0))
    length_svg = generate_dial_svg("Stitch Length", l_val, l_min, l_max, unit="mm")
    width_svg = generate_dial_svg("Stitch Width", w_val, w_min, w_max, unit="mm")
    
    # Safety Banner
    safety_banner = ""
    if safety_status:
        severity = safety_status.get("severity", "SAFE")
        msg = html.escape(safety_status.get("message", "All physical parameters within limits."))
        if severity == "CRITICAL":
            safety_banner = f'''
            <div style="background:rgba(220, 38, 38, 0.15); border:1px solid #ef4444; border-radius:8px; padding:10px 14px; margin-bottom:12px; color:#fca5a5; font-size:12px;">
              <div style="font-weight:700; color:#f87171; text-transform:uppercase; margin-bottom:2px;">[SAFETY INTERCEPT] CRITICAL DEFLECTION RISK</div>
              <div>{msg}</div>
            </div>
            '''
        elif severity == "WARNING":
            safety_banner = f'''
            <div style="background:rgba(217, 119, 6, 0.15); border:1px solid #f59e0b; border-radius:8px; padding:10px 14px; margin-bottom:12px; color:#fde68a; font-size:12px;">
              <div style="font-weight:700; color:#fbbf24; text-transform:uppercase; margin-bottom:2px;">[SAFETY WARNING]</div>
              <div>{msg}</div>
            </div>
            '''
        else:
            safety_banner = f'''
            <div style="background:rgba(16, 185, 129, 0.12); border:1px solid #10b981; border-radius:8px; padding:8px 12px; margin-bottom:12px; color:#a7f3d0; font-size:11px;">
              <span style="font-weight:700; color:#34d399;">[PHYSICAL SAFETY VERIFIED]</span> Safe operating limits confirmed.
            </div>
            '''
            
    html_dashboard = f'''
    <div style="background:#0f172a; border:1px solid #1e293b; border-radius:12px; padding:14px; font-family:system-ui, sans-serif; color:#f8fafc;">
      {safety_banner}
      
      <!-- Rotary Dials Row -->
      <div style="display:flex; justify-content:space-around; align-items:center; background:#0b0f17; border:1px solid #1e293b; border-radius:10px; padding:10px 4px; margin-bottom:14px; flex-wrap:wrap;">
        {tension_svg}
        {length_svg}
        {width_svg}
      </div>
      
      <!-- Mechanical Readout Cards -->
      <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap:8px;">
        <div style="background:#1e293b; border-radius:8px; padding:8px 10px;">
          <span style="font-size:9px; text-transform:uppercase; color:#94a3b8; font-weight:600; display:block;">Pattern</span>
          <strong style="color:#38bdf8; font-size:12px;">{html.escape(str(pattern))}</strong>
        </div>
        <div style="background:#1e293b; border-radius:8px; padding:8px 10px;">
          <span style="font-size:9px; text-transform:uppercase; color:#94a3b8; font-weight:600; display:block;">Needle Gauge</span>
          <strong style="color:#4ade80; font-size:12px;">{html.escape(str(needle))}</strong>
        </div>
        <div style="background:#1e293b; border-radius:8px; padding:8px 10px;">
          <span style="font-size:9px; text-transform:uppercase; color:#94a3b8; font-weight:600; display:block;">Presser Foot</span>
          <strong style="color:#fbbf24; font-size:12px;">{html.escape(str(foot))}</strong>
        </div>
      </div>
    </div>
    '''
    return html_dashboard

def format_trace_html(trace: List[Dict[str, Any]]) -> str:
    """Format step-by-step execution trace into styled HTML."""
    if not trace:
        return "<div style='color:#64748b; font-size:12px; padding:8px;'>No execution trace yet. Submit an instruction or click a scenario.</div>"
    
    steps_html = []
    for step_info in trace:
        step_num = step_info.get("step", 1)
        thought = html.escape(str(step_info.get("thought", "")))
        tool_name = html.escape(str(step_info.get("tool_name", "")))
        tool_args = html.escape(str(step_info.get("tool_args", "")))
        obs = html.escape(str(step_info.get("observation", "")))
        answer = html.escape(str(step_info.get("answer", "")))
        
        step_card = f'''
        <div style="background:#111827; border:1px solid #1f2937; border-left:3px solid #ef4444; border-radius:6px; padding:8px 12px; margin-bottom:8px; font-family:monospace; font-size:11px;">
          <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
            <strong style="color:#f87171;">[Step {step_num}]</strong>
            {f'<span style="background:#1e293b; color:#38bdf8; padding:1px 6px; border-radius:3px;">{tool_name}</span>' if tool_name else '<span style="background:#1e293b; color:#4ade80; padding:1px 6px; border-radius:3px;">FINAL ANSWER</span>'}
          </div>
          {f'<div style="color:#cbd5e1; margin-bottom:4px;"><strong>Reasoning:</strong> {thought}</div>' if thought else ''}
          {f'<div style="color:#93c5fd; margin-bottom:4px;"><strong>Tool Call:</strong> <code>{tool_name}({tool_args})</code></div>' if tool_name else ''}
          {f'<div style="color:#94a3b8; background:#0b0f17; padding:6px; border-radius:4px; max-height:120px; overflow-y:auto; white-space:pre-wrap; margin-top:4px;"><strong>Observation:</strong>\n{obs}</div>' if obs else ''}
          {f'<div style="color:#4ade80; margin-top:4px;"><strong>Answer:</strong> {answer}</div>' if answer else ''}
        </div>
        '''
        steps_html.append(step_card)
        
    return f'''
    <div style="max-height:360px; overflow-y:auto; padding-right:4px;">
      {''.join(steps_html)}
    </div>
    '''
