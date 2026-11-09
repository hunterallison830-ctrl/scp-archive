from pathlib import Path
import re
p=Path(__file__).parent/'assets'
# Each behavioral study has its own original animated operational diagram.
loops={
'173':('OBSERVATION INTERRUPT','<rect class="blink-shutter" x="27" y="54" width="426" height="244" fill="#0a120d"/><text x="150" y="291" class="signal" font-family="monospace" font-size="10" fill="#c5bd8b">VISUAL CONTACT: INTERRUPTED</text>'),
'049':('BIOLOGICAL ARREST','<path class="trace" d="M48 244h27l5-12 7 26 8-14h48"/><path d="M340 244h84" stroke="#b88669"/><text x="346" y="263" class="label">PULSE: 0</text>'),
'096':('DISTRESS RESPONSE','<path class="trace" d="M50 251l7-11 6 22 7-33 7 38 7-21 7 9 7-6 7 14 7-31 7 23 7-7h25"/><path class="trace" d="M327 251l7-11 6 22 7-33 7 38 7-21 7 9 7-6 7 14 7-31 7 23 7-7h25"/>'),
'682':('TISSUE RECONSTITUTION','<path class="regrow" d="M202 233l-8 34 25 0" stroke="#c7ca98" stroke-width="10" fill="none"/><g class="signal" fill="none" stroke="#b9c494"><circle cx="205" cy="247" r="24"/><path d="M176 247h58m-29-29v58"/></g>'),
'106':('BARRIER PHASE','<path d="M305 78v217m9-217v217m-9-150h58m-58 52h58m-58 51h58" stroke="#73816b" fill="none"/><path class="leak" d="M307 161v117m12-96v106m-26-62v62" stroke="#1a291d" stroke-width="8"/>'),
'079':('MEMORY / ACCESS ATTEMPT','<text x="180" y="181" class="label signal">&gt; LINK DENIED_</text><path class="trace" d="M328 127h47v114h41"/><text x="341" y="260" class="label">AIR GAP</text>'),
'087':('UNRESOLVED DESCENT','<g class="pulse-rings" fill="none" stroke="#c3c3a1"><rect x="187" y="133" width="107" height="141"/><rect x="199" y="146" width="83" height="127"/></g><path class="trace" d="M338 152v118m-7-10l7 10 7-10"/>'),
'093':('REFLECTIVE THRESHOLD','<ellipse class="pulse-rings" cx="242" cy="177" rx="65" ry="87" fill="none" stroke="#b0b18f"/><path class="trace" d="M90 218h55m-13-8l13 8-13 8"/>'),
'035':('CORROSIVE DISCHARGE','<path d="M177 87h123v199H177z" fill="none" stroke="#b0b39b" opacity=".5"/><g class="fall" fill="#1c2b20"><ellipse cx="209" cy="255" rx="5" ry="12"/><ellipse cx="259" cy="246" rx="5" ry="13"/></g><path class="leak" d="M175 287h126" stroke="#19291c" stroke-width="9"/>'),
'914':('INPUT / OUTPUT TRANSFORMATION','<path class="trace" d="M119 217h244m-12-8l12 8-12 8"/><path d="M120 198h21v21h-21z" fill="#bdba9a"/><g class="pulse-rings" fill="none" stroke="#d3c699"><circle cx="343" cy="210" r="16"/><path d="M343 187v46m-23-23h46"/></g>'),
'999':('POSITIVE CONTACT RESPONSE','<g class="float-particles" fill="#d9bd75"><circle cx="160" cy="177" r="4"/><circle cx="305" cy="146" r="3"/><circle cx="325" cy="202" r="5"/><circle cx="177" cy="120" r="3"/></g><path class="trace" d="M78 259h52m226 0h48"/>'),
'3008':('UNBOUNDED FLOORPLAN','<g class="aisle" fill="none" stroke="#b2a882" opacity=".5"><path d="M195 147v105h90V147zM207 158v84h66v-84zM219 169v63h42v-63z"/></g><text x="198" y="100" class="label">EXIT → ?</text>'),
'002':('INTERIOR ASSIMILATION','<rect class="signal" x="226" y="187" width="30" height="25" fill="#99906b"/><path class="trace" d="M109 207h65m-10-9l10 9-10 9"/><text x="114" y="141" class="label">MASS +</text>'),
'008':('TRANSMISSION MODEL','<g stroke="#b6b48b" fill="#84956a"><path class="trace" d="M83 122l31 49-29 72m29-72l47 8m173-13l42-50m-42 50l43 74"/><circle class="signal" cx="83" cy="122" r="7"/><circle class="signal" cx="85" cy="243" r="7"/><circle cx="114" cy="171" r="7"/><circle class="signal" cx="377" cy="116" r="7"/><circle class="signal" cx="377" cy="240" r="7"/></g>'),
'055':('RETENTION FAILURE','<rect class="erasure" x="161" y="205" width="165" height="43" fill="#253227"/><text x="185" y="278" class="label signal">SUBJECT: [      ]</text>'),
'610':('GROWTH PROGRESSION','<path class="growth" d="M105 280q37-93 88-86t42-80M296 264q-46-51 13-93M181 267q-7-63-38-66" stroke="#c4b08a" stroke-width="5" fill="none"/>'),
'939':('HUMAN VOCAL MIMICRY','<path class="trace" d="M80 131h24l6-16 7 30 7-14 7 5 6-21 7 22 8-7h28"/><path class="pulse-rings" d="M377 184q18 16 0 32m12-41q28 25 0 50m12-60q38 35 0 70" fill="none" stroke="#c6b38c"/>'),
'966':('INFRARED / SLEEP DISRUPTION','<rect class="scanner" x="73" y="90" width="334" height="5" fill="#b9cba5" opacity=".6"/><path class="trace" d="M80 268h72l10-10 10 10h18"/><text x="290" y="280" class="label">SLEEP: 0</text>'),
'294':('DISPENSE CYCLE','<path class="leak" d="M240 203v34" stroke="#b9cdb1" stroke-width="4"/><circle class="fall" cx="240" cy="221" r="4" fill="#d4dbbd"/>'),
'500':('SYSTEMIC RECOVERY','<path class="trace" d="M67 197h30l8-23 12 47 9-24h38m168 0h29l8-23 12 47 9-24h29"/><path class="pulse-rings" d="M238 237v24m-12-12h24" stroke="#aabc90" stroke-width="4"/>'),
'426':('REFERENTIAL SUBSTITUTION','<text x="137" y="107" class="label erasure">IT IS A TOASTER</text><text x="156" y="108" class="label signal">I AM A TOASTER</text>'),
'1048':('UNAUTHORIZED DUPLICATE','<g class="signal" fill="#8c8668" stroke="#b8b18c"><circle cx="350" cy="226" r="20"/><circle cx="336" cy="211" r="9"/><circle cx="365" cy="211" r="9"/><ellipse cx="350" cy="262" rx="20" ry="25"/></g><path class="trace" d="M301 208l28 19"/>'),
'1471':('ESCALATING PROXIMITY','<rect x="80" y="113" width="68" height="119" rx="8" fill="#111c15" stroke="#99a58b" stroke-width="3"/><path class="approach" d="M95 214l3-37-5-15 16-10 16 10-5 15 7 37z" fill="#a3ad95"/><text x="82" y="251" class="label">72:00:00</text>'),
'2006':('FEAR / SHAPE ASSUMPTION','<path class="erasure" d="M170 277q-25-73 29-98l-20-48 45 20 17-62 25 62 39-20-18 48q48 44 25 98z" fill="#4b5a42" opacity=".8"/><text x="151" y="294" class="label signal">FORM REASSESSMENT</text>'),
'3000':('MNESTIC DEGRADATION','<text x="133" y="107" class="label erasure">NAME / LOCATION / SELF</text><g class="pulse-rings" fill="none" stroke="#a5b39b"><ellipse cx="244" cy="230" rx="183" ry="36"/><ellipse cx="244" cy="230" rx="195" ry="44"/></g>'),
'131':('CONTINUOUS OBSERVATION','<path class="trace" d="M177 212l52-30m70 30l-54-30"/><circle class="pulse-rings" cx="239" cy="174" r="15" fill="none" stroke="#c8c4a0"/>'),
'513':('AUDITORY / PERIPHERAL EFFECT','<path class="pulse-rings" d="M173 154q-25 40 0 79m-15-90q-38 52 0 102m147-91q25 40 0 79m15-90q38 52 0 102" fill="none" stroke="#b7bd9b"/><path class="signal" d="M382 279v-86l-8-22 10-16 12 16-7 22v86" fill="#c0c2a5" opacity=".4"/>'),
'354':('SURFACE EMERGENCE','<g class="float-particles" fill="none" stroke="#cc9876"><circle cx="170" cy="244" r="10"/><circle cx="298" cy="220" r="7"/><circle cx="310" cy="253" r="12"/></g><ellipse class="pulse-rings" cx="242" cy="249" rx="85" ry="21" fill="none" stroke="#d09c7a"/>'),
'076':('WEAPON MANIFESTATION','<path class="growth" d="M278 226l51-92m-47 69l25 14" stroke="#c8d0b7" stroke-width="6" fill="none"/><path class="trace" d="M112 259v-76h31"/>'),
'073':('DAMAGE REFLECTION','<path class="trace" d="M95 185h87m-10-9l10 9-10 9M182 216H95m10-9l-10 9 10 9"/><circle class="pulse-rings" cx="240" cy="181" r="64" fill="none" stroke="#b4bfa1"/>'),
'343':('SOLID BARRIER DISREGARDED','<path class="erasure" d="M135 72v218m-12-218v218m-35-67h90m-90-49h90m-90-49h90" stroke="#b2b69c" stroke-width="5"/><text x="300" y="113" class="label">PASSAGE</text>'),
'053':('PROXIMITY RESPONSE','<circle class="pulse-rings" cx="238" cy="190" r="88" fill="none" stroke="#c89a72" stroke-dasharray="4 8"/><path class="signal" d="M93 257v-64l-9-18 12-17 12 17-9 18v64m277 0v-64l-9-18 12-17 12 17-9 18v64" stroke="#b78465" fill="none" stroke-width="7"/>'),
'2317':('RESTRAINT INTEGRITY','<g class="pulse-rings" fill="none" stroke="#c5b48b" stroke-width="3"><ellipse cx="99" cy="160" rx="11" ry="20"/><ellipse cx="99" cy="189" rx="11" ry="20"/><path d="M94 204l-8 15m22-8l5 17"/></g><text x="84" y="250" class="label signal">FAULT</text>'),
'701':('UNSCRIPTED APPEARANCE','<path class="signal" d="M166 279l5-87-8-17 16-21 16 21-8 17 6 87" fill="#adb298" opacity=".5"/><path class="trace" d="M329 248h48"/>'),
'012':('COMPULSIVE COMPLETION','<path class="growth" d="M172 244l15-4 2-17m15 19l10-4 2-17m17 22l12-5 2-17m17 24l9-4 2-17" stroke="#9a5840" stroke-width="3" fill="none"/>'),
'2521':('◼ ◼◼ ◼◼◼','<g class="erasure" stroke="#b2b59c" fill="none"><rect x="85" y="171" width="42" height="58"/><path d="M91 184h28m-28 10h28m-28 10h20"/></g><path class="trace" d="M134 199h41m-10-7l10 7-10 7"/>')}
styles='''<style>.label{font:11px monospace;fill:#c3c5a1;letter-spacing:1px}.trace{fill:none;stroke:#bbc3a1;stroke-width:2;stroke-dasharray:8 6;animation:flow 3s linear infinite}.signal{animation:signal 4s steps(2,end) infinite}.pulse-rings{animation:halo 4s ease-in-out infinite;transform-origin:240px 220px}.float-particles{animation:float 4s ease-in-out infinite}.fall{animation:fall 2s ease-in infinite}.leak{animation:halo 3s ease-in-out infinite}.growth{stroke-dasharray:500;stroke-dashoffset:500;animation:grow 6s ease-in-out infinite}.regrow{transform-origin:203px 233px;animation:regrow 5s ease-in-out infinite}.erasure{animation:erase 5s steps(2,end) infinite}.scanner{animation:scan 5s linear infinite}.approach{transform-origin:110px 210px;animation:approach 6s steps(3,end) infinite}.aisle{transform-origin:240px 230px;animation:approach 6s linear infinite}.blink-shutter{opacity:0;animation:blink 5s linear infinite}@keyframes flow{to{stroke-dashoffset:-84}}@keyframes signal{0%,70%,100%{opacity:.15}30%,60%{opacity:.9}}@keyframes halo{0%,100%{opacity:.15}50%{opacity:.9}}@keyframes float{0%,100%{transform:translateY(10px);opacity:.2}50%{transform:translateY(-15px);opacity:.9}}@keyframes fall{from{transform:translateY(-7px);opacity:0}50%{opacity:.9}to{transform:translateY(18px);opacity:0}}@keyframes grow{0%,10%{stroke-dashoffset:500;opacity:.2}70%,100%{stroke-dashoffset:0;opacity:.9}}@keyframes regrow{0%,20%{transform:scaleY(.05);opacity:.1}80%,100%{transform:scaleY(1);opacity:.85}}@keyframes erase{0%,35%,100%{opacity:.9}40%,90%{opacity:0}}@keyframes scan{from{transform:translateY(0)}to{transform:translateY(196px)}}@keyframes approach{0%{transform:scale(.7);opacity:.1}90%,100%{transform:scale(1.3);opacity:.8}}@keyframes blink{0%,44%,54%,100%{opacity:0}45%,53%{opacity:1}}@media(prefers-reduced-motion:reduce){*{animation:none!important}.growth{stroke-dashoffset:0}.regrow{transform:none}.signal,.float-particles,.erasure{opacity:.7}.blink-shutter{display:none}}</style>'''
for ident,(label,overlay) in loops.items():
    file=p/f'{int(ident):03d}-capability.svg'
    s=file.read_text();s=s.replace('</defs>','</defs>'+styles,1)
    # Overlay after specimen but before recorder frame. Diagram never purports to be an optical photograph.
    s=s.replace('<path d="M25 180h65',overlay+'<path d="M25 180h65',1)
    s=re.sub(r'BEHAVIORAL MODEL / [A-Z]+ / LOOP',f'{label} / LOOP',s)
    file.write_text(s)
print('Enhanced',len(loops),'capability reconstructions')

import json
data_path = Path(__file__).parent / "data.json"
data = json.loads(data_path.read_text())
for entry in data:
    entry["capabilityLabel"] = {int(k): v for k, v in loops.items()}[int(entry["id"])][0]
data_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

# External SVG images do not consistently inherit live motion-preference changes.
# An explicit still source in <picture> guarantees reduced-motion behavior.
static_style = '<style>*{animation:none!important}.growth{stroke-dashoffset:0}.regrow{transform:none}.signal,.float-particles{opacity:.7}.erasure{opacity:0}.blink-shutter{display:none}</style>'
for entry in data:
    animated = Path(__file__).parent / entry["capability"]
    still = animated.with_name(animated.stem + "-static.svg")
    still.write_text(animated.read_text().replace('</svg>', static_style + '</svg>'))
    entry["capabilityStill"] = 'assets/' + still.name
data_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
