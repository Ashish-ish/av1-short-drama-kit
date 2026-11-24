"""
Generates high-fidelity visual mockups / screenshots for Android, iOS, React Native,
and the mid-stream fallback transition in docs/screenshots/.
"""

import os


def generate_android_screenshot(output_path: str):
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 840" width="100%" height="100%" style="background:#090d16; font-family:-apple-system,BlinkMacSystemFont,Roboto,Helvetica,sans-serif;">
  <defs>
    <linearGradient id="bg-grad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#1e1b4b"/>
      <stop offset="40%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#020617"/>
    </linearGradient>
    <linearGradient id="hud-glass" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#1e293bcc" />
      <stop offset="100%" stop-color="#0f172ae6" />
    </linearGradient>
    <filter id="shadow" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#000" flood-opacity="0.6"/>
    </filter>
  </defs>

  <!-- Device Frame (Android) -->
  <rect x="10" y="10" width="400" height="820" rx="42" fill="none" stroke="#334155" stroke-width="4"/>
  <rect x="14" y="14" width="392" height="812" rx="38" fill="url(#bg-grad)"/>

  <!-- Top Camera Punchhole -->
  <circle cx="210" cy="36" r="8" fill="#020617" stroke="#1e293b" stroke-width="1.5"/>

  <!-- Status Bar Icons -->
  <text x="36" y="40" fill="#94a3b8" font-size="12" font-weight="600">09:41</text>
  <text x="340" y="40" fill="#94a3b8" font-size="11" font-weight="600">5G 98%</text>

  <!-- Dramatic Scene Artwork Simulation (Vertical Drama) -->
  <g opacity="0.65">
    <circle cx="210" cy="340" r="130" fill="#4338ca" filter="url(#shadow)" opacity="0.4"/>
    <ellipse cx="210" cy="300" rx="65" ry="85" fill="#6366f1" opacity="0.5"/>
    <!-- Silhouette of actors in close dialogue -->
    <path d="M 170 380 Q 210 320 250 380 Z" fill="#0f172a"/>
    <circle cx="210" cy="270" r="42" fill="#1e293b"/>
    <!-- Subtitles in 9:16 frame -->
    <rect x="50" y="580" width="320" height="36" rx="6" fill="#000000a6"/>
    <text x="210" y="603" fill="#facc15" font-size="14" font-weight="600" text-anchor="middle">"You never told me the truth about that night."</text>
  </g>

  <!-- Floating Diagnostic HUD (Android / Media3) -->
  <g filter="url(#shadow)">
    <rect x="28" y="70" width="364" height="175" rx="14" fill="url(#hud-glass)" stroke="#38bdf8" stroke-width="1.2"/>

    <!-- Header badge -->
    <rect x="42" y="84" width="95" height="22" rx="4" fill="#065f46"/>
    <text x="89" y="99" fill="#34d399" font-size="11" font-weight="bold" text-anchor="middle">ACTIVE: AV1</text>
    <text x="146" y="99" fill="#94a3b8" font-size="11">c2.android.av1-dav1d.decoder</text>

    <!-- Metrics Grid -->
    <line x1="42" y1="116" x2="378" y2="116" stroke="#334155" stroke-width="0.8"/>

    <text x="42" y="134" fill="#64748b" font-size="10">RESOLUTION &amp; FPS</text>
    <text x="42" y="150" fill="#f8fafc" font-size="13" font-weight="bold">540x960 @ 30 fps</text>

    <text x="210" y="134" fill="#64748b" font-size="10">BITRATE &amp; PAPR</text>
    <text x="210" y="150" fill="#38bdf8" font-size="13" font-weight="bold">322 kbps (PAPR 1.26)</text>

    <text x="42" y="174" fill="#64748b" font-size="10">STARTUP LATENCY</text>
    <text x="42" y="190" fill="#10b981" font-size="13" font-weight="bold">TTFF: 140ms (Init: 18ms)</text>

    <text x="210" y="174" fill="#64748b" font-size="10">DROPPED FRAMES</text>
    <text x="210" y="190" fill="#10b981" font-size="13" font-weight="bold">0 drops (0.0/min)</text>

    <text x="42" y="214" fill="#94a3b8" font-size="9.5">Policy: SOFTWARE_DAV1D_PROBE_PASSED (1.82x Real-Time)</text>
    <circle cx="368" cy="95" r="5" fill="#10b981"/>
  </g>

  <!-- Interactive Test Fallback Button -->
  <g filter="url(#shadow)">
    <rect x="28" y="260" width="364" height="38" rx="8" fill="#dc2626" stroke="#ef4444" stroke-width="1"/>
    <text x="210" y="284" fill="#ffffff" font-size="12" font-weight="bold" text-anchor="middle">⚡ Force Decoder Failure (Test Guaranteed Fallback)</text>
  </g>

  <!-- Right-side Engagement Column (TikTok / DramaFeed Style) -->
  <g transform="translate(350, 420)">
    <circle cx="20" cy="0" r="20" fill="#1e293bcc" stroke="#475569" stroke-width="1"/>
    <text x="20" y="5" fill="#f43f5e" font-size="18" text-anchor="middle">♥</text>
    <text x="20" y="28" fill="#94a3b8" font-size="10" text-anchor="middle">24.5k</text>

    <circle cx="20" cy="65" r="20" fill="#1e293bcc" stroke="#475569" stroke-width="1"/>
    <text x="20" y="70" fill="#cbd5e1" font-size="16" text-anchor="middle">💬</text>
    <text x="20" y="93" fill="#94a3b8" font-size="10" text-anchor="middle">1,420</text>

    <circle cx="20" cy="130" r="20" fill="#1e293bcc" stroke="#475569" stroke-width="1"/>
    <text x="20" y="135" fill="#cbd5e1" font-size="16" text-anchor="middle">↗</text>
    <text x="20" y="158" fill="#94a3b8" font-size="10" text-anchor="middle">Share</text>
  </g>

  <!-- Bottom Navigation / Episode Scrubber -->
  <rect x="28" y="750" width="364" height="4" rx="2" fill="#334155"/>
  <rect x="28" y="750" width="130" height="4" rx="2" fill="#38bdf8"/>
  <circle cx="158" cy="752" r="6" fill="#f8fafc"/>
  <text x="28" y="776" fill="#f8fafc" font-size="12" font-weight="600">CEO's Secret Heir - Ep. 14/80</text>
  <text x="392" y="776" fill="#94a3b8" font-size="11" text-anchor="end">00:14 / 01:12</text>
</svg>"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)


def generate_ios_screenshot(output_path: str):
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 840" width="100%" height="100%" style="background:#000000; font-family:-apple-system,BlinkMacSystemFont,SF Pro Display,sans-serif;">
  <defs>
    <linearGradient id="ios-hud" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#18181bcc"/>
      <stop offset="100%" stop-color="#09090be6"/>
    </linearGradient>
    <filter id="ios-blur">
      <feGaussianBlur stdDeviation="8"/>
    </filter>
  </defs>

  <!-- iPhone Rounded Bezel -->
  <rect x="10" y="10" width="400" height="820" rx="48" fill="none" stroke="#27272a" stroke-width="3"/>
  <rect x="14" y="14" width="392" height="812" rx="44" fill="#09090b"/>

  <!-- Dynamic Island -->
  <rect x="145" y="24" width="130" height="30" rx="15" fill="#000000"/>
  <circle cx="165" cy="39" r="5" fill="#18181b"/>
  <circle cx="255" cy="39" r="4.5" fill="#0284c7" opacity="0.7"/>

  <!-- iOS Status Bar -->
  <text x="42" y="44" fill="#ffffff" font-size="13" font-weight="600">9:41</text>
  <text x="375" y="44" fill="#ffffff" font-size="11" font-weight="500" text-anchor="end">5G 􀛨</text>

  <!-- Video Background Simulation -->
  <g opacity="0.6">
    <rect x="14" y="60" width="392" height="766" fill="#0c0a09"/>
    <circle cx="210" cy="400" r="140" fill="#7c2d12" opacity="0.3"/>
    <text x="210" y="620" fill="#ffffff" font-size="15" font-weight="500" text-anchor="middle" letter-spacing="0.5">"I knew who you were from the beginning."</text>
  </g>

  <!-- iOS AV1Policy Glassmorphic HUD -->
  <g transform="translate(24, 75)">
    <rect width="372" height="165" rx="20" fill="url(#ios-hud)" stroke="#27272a" stroke-width="1"/>

    <rect x="16" y="16" width="135" height="24" rx="12" fill="#047857"/>
    <text x="83" y="32" fill="#ffffff" font-size="11" font-weight="bold" text-anchor="middle">HARDWARE AV1</text>

    <text x="165" y="32" fill="#a1a1aa" font-size="11">VTIsHardwareDecode: YES</text>
    <circle cx="350" cy="28" r="4.5" fill="#10b981"/>

    <line x1="16" y1="52" x2="356" y2="52" stroke="#27272a" stroke-width="1"/>

    <text x="16" y="74" fill="#71717a" font-size="10">MASTER PLAYLIST</text>
    <text x="16" y="90" fill="#fafafa" font-size="13" font-weight="600">master_av1.m3u8 (720p)</text>

    <text x="200" y="74" fill="#71717a" font-size="10">STARTUP TIME (TTFF)</text>
    <text x="200" y="90" fill="#34d399" font-size="13" font-weight="600">105 ms</text>

    <text x="16" y="118" fill="#71717a" font-size="10">DROPPED FRAMES</text>
    <text x="16" y="134" fill="#fafafa" font-size="13" font-weight="600">0 (AVPlayerItemAccessLog)</text>

    <text x="200" y="118" fill="#71717a" font-size="10">REBUFFER STALLS</text>
    <text x="200" y="134" fill="#fafafa" font-size="13" font-weight="600">0 stalls</text>

    <text x="16" y="152" fill="#a1a1aa" font-size="9.5">Policy: IOS_HARDWARE_AV1_SUPPORTED (Future-Proof Path)</text>
  </g>

  <!-- Manual Fallback Trigger Pill -->
  <g transform="translate(24, 255)">
    <rect width="372" height="38" rx="12" fill="#ef444433" stroke="#ef4444" stroke-width="1"/>
    <text x="186" y="24" fill="#fca5a5" font-size="12" font-weight="600" text-anchor="middle">⚡ Simulate Playback Error (Mid-Stream Fallback)</text>
  </g>

  <!-- iOS Home Bar Indicator -->
  <rect x="140" y="812" width="140" height="4" rx="2" fill="#ffffff" opacity="0.6"/>
</svg>"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)


def generate_react_native_screenshot(output_path: str):
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 840" width="100%" height="100%" style="background:#090d16; font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;">
  <defs>
    <linearGradient id="rn-card" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#1e293bfa"/>
      <stop offset="100%" stop-color="#0f172ae6"/>
    </linearGradient>
  </defs>

  <!-- Device Frame -->
  <rect x="10" y="10" width="400" height="820" rx="40" fill="none" stroke="#334155" stroke-width="3"/>
  <rect x="14" y="14" width="392" height="812" rx="36" fill="#020617"/>

  <!-- React Native / Expo Video Badge Header -->
  <g transform="translate(24, 50)">
    <rect width="372" height="195" rx="16" fill="url(#rn-card)" stroke="#60a5fa" stroke-width="1.2"/>

    <text x="18" y="28" fill="#60a5fa" font-size="12" font-weight="bold">REACT NATIVE &amp; EXPO BRIDGE</text>
    <text x="354" y="28" fill="#94a3b8" font-size="11" text-anchor="end">av1-vertical-drama-bridge</text>

    <line x1="18" y1="40" x2="354" y2="40" stroke="#334155" stroke-width="0.8"/>

    <!-- Codec & Profile Output -->
    <rect x="18" y="52" width="110" height="24" rx="6" fill="#10b981"/>
    <text x="73" y="68" fill="#064e3b" font-size="11" font-weight="bold" text-anchor="middle">ACTIVE: AV1</text>
    <text x="140" y="69" fill="#f8fafc" font-size="12" font-weight="600">540x960 (Mid Rung)</text>

    <!-- Buffer details -->
    <text x="18" y="102" fill="#94a3b8" font-size="10">BUFFER CONFIG (DRAMA TUNED)</text>
    <text x="18" y="118" fill="#38bdf8" font-size="12" font-weight="600">bufferForPlaybackMs: 800ms</text>
    <text x="210" y="118" fill="#38bdf8" font-size="12" font-weight="600">forwardBuffer: 4.0s</text>

    <text x="18" y="144" fill="#94a3b8" font-size="10">REASON CODE</text>
    <text x="18" y="160" fill="#a7f3d0" font-size="11.5" font-weight="600">ANDROID_DAV1D_ELIGIBLE_JS_FALLBACK</text>

    <text x="18" y="180" fill="#64748b" font-size="9.5">Adaptive Bitrate: Segment Peak Bandwidth 440 kbps</text>
  </g>

  <!-- Video Playback Container -->
  <rect x="24" y="260" width="372" height="460" rx="16" fill="#1e1b4b" stroke="#312e81" stroke-width="1"/>
  <circle cx="210" cy="460" r="90" fill="#4338ca" opacity="0.5"/>
  <polygon points="195,430 240,460 195,490" fill="#ffffff" opacity="0.8"/>
  <text x="210" y="530" fill="#c7d2fe" font-size="13" font-weight="500" text-anchor="middle">&lt;Video bufferConfig={DRAMA_BUFFER_CONFIG} /&gt;</text>

  <!-- Test Trigger Button -->
  <g transform="translate(24, 740)">
    <rect width="372" height="42" rx="10" fill="#dc2626" stroke="#f87171" stroke-width="1"/>
    <text x="186" y="26" fill="#ffffff" font-size="12" font-weight="bold" text-anchor="middle">⚡ Test Fallback: Switch to master_h264.m3u8</text>
  </g>
</svg>"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)


def generate_fallback_transition_diagram(output_path: str):
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 840 420" width="100%" height="100%" style="background:#090d16; font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;">
  <defs>
    <linearGradient id="card-before" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#064e3b" />
      <stop offset="100%" stop-color="#022c22" />
    </linearGradient>
    <linearGradient id="card-after" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#7f1d1d" />
      <stop offset="100%" stop-color="#450a0a" />
    </linearGradient>
  </defs>

  <text x="420" y="38" fill="#f8fafc" font-size="18" font-weight="bold" text-anchor="middle">Runtime Guaranteed Fallback: Seamless Mid-Stream Transition</text>
  <text x="420" y="60" fill="#94a3b8" font-size="12" text-anchor="middle">Any decoder error or sustained &gt;5% frame drop switches to H.264 at the exact PTS without stall</text>

  <!-- State 1: Active AV1 Playback -->
  <g transform="translate(40, 90)">
    <rect width="340" height="280" rx="14" fill="url(#card-before)" stroke="#10b981" stroke-width="1.5"/>
    <rect x="20" y="20" width="120" height="26" rx="6" fill="#047857"/>
    <text x="80" y="37" fill="#ffffff" font-size="12" font-weight="bold" text-anchor="middle">1. PLAYING AV1</text>

    <text x="20" y="76" fill="#6ee7b7" font-size="11" font-weight="bold">STREAM MANIFEST:</text>
    <text x="20" y="94" fill="#f8fafc" font-size="13">master_av1.m3u8</text>

    <text x="20" y="128" fill="#6ee7b7" font-size="11" font-weight="bold">CURRENT PTS POSITION:</text>
    <text x="20" y="146" fill="#f8fafc" font-size="15" font-weight="bold">00:14.280 (Episode 1)</text>

    <text x="20" y="180" fill="#6ee7b7" font-size="11" font-weight="bold">DECODER IN USE:</text>
    <text x="20" y="198" fill="#f8fafc" font-size="12">c2.android.av1-dav1d.decoder</text>

    <rect x="20" y="226" width="300" height="34" rx="6" fill="#022c22" stroke="#059669" stroke-width="1"/>
    <text x="170" y="247" fill="#34d399" font-size="11" font-weight="bold" text-anchor="middle">STATUS: EFFICIENT (-54% BANDWIDTH)</text>
  </g>

  <!-- Transition Arrow & Trigger -->
  <g transform="translate(395, 190)">
    <circle cx="25" cy="20" r="28" fill="#dc2626" stroke="#f87171" stroke-width="2"/>
    <text x="25" y="26" fill="#ffffff" font-size="16" font-weight="bold" text-anchor="middle">⚡</text>
    <text x="25" y="65" fill="#f87171" font-size="11" font-weight="bold" text-anchor="middle">ERROR / DROP</text>
    <text x="25" y="80" fill="#94a3b8" font-size="9" text-anchor="middle">&gt;5% drops over 10s</text>
  </g>

  <!-- State 2: Seamless Fallback H.264 Playback -->
  <g transform="translate(460, 90)">
    <rect width="340" height="280" rx="14" fill="url(#card-after)" stroke="#ef4444" stroke-width="1.5"/>
    <rect x="20" y="20" width="140" height="26" rx="6" fill="#991b1b"/>
    <text x="90" y="37" fill="#ffffff" font-size="12" font-weight="bold" text-anchor="middle">2. FALLBACK H.264</text>

    <text x="20" y="76" fill="#fca5a5" font-size="11" font-weight="bold">NEW STREAM MANIFEST:</text>
    <text x="20" y="94" fill="#f8fafc" font-size="13">master_h264.m3u8</text>

    <text x="20" y="128" fill="#fca5a5" font-size="11" font-weight="bold">RESUME PTS (SEAMLESS SEEK):</text>
    <text x="20" y="146" fill="#f8fafc" font-size="15" font-weight="bold">00:14.280 (Zero Disruption)</text>

    <text x="20" y="180" fill="#fca5a5" font-size="11" font-weight="bold">DECODER SWITCHED TO:</text>
    <text x="20" y="198" fill="#f8fafc" font-size="12">c2.android.avc.decoder (Hardware)</text>

    <rect x="20" y="226" width="300" height="34" rx="6" fill="#450a0a" stroke="#b91c1c" stroke-width="1"/>
    <text x="170" y="247" fill="#fca5a5" font-size="11" font-weight="bold" text-anchor="middle">PENALTY: RECORD REASON &amp; LOWER RUNG</text>
  </g>
</svg>"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)


def main():
    target_dir = "docs/screenshots"
    generate_android_screenshot(os.path.join(target_dir, "android_player_hud.svg"))
    generate_ios_screenshot(os.path.join(target_dir, "ios_player_hud.svg"))
    generate_react_native_screenshot(os.path.join(target_dir, "react_native_player_hud.svg"))
    generate_fallback_transition_diagram(os.path.join(target_dir, "fallback_transition.svg"))
    print(f"Generated 4 screenshots and mockups in {target_dir}")


if __name__ == "__main__":
    main()
