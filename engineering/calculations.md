# Rev B dynamics, structures and cost verification

Authoritative inputs: `design_parameters.json`. Reproduce using
`python -m engineering.review_sizing` or the compatible `python engineering/sizing.py`.
Both result filenames receive the same data; old holding-torque approvals are gone.
Run `python -m unittest discover -s tests -p 'test_engineering*.py'` for the independent
integration, conservation, reaction-equilibrium, cost and invalid-input checks.
This is a desk screening model. It explicitly does not certify the final assembly.

## Geometry, masses and reference

The fixed square outer tube is38.1mm side ×1.5875mm wall ×770mm, axial interval
[-250,+520]mm relative to pitch. The inner tube is25.4mm side ×1.5875mm wall ×805mm,
interval[-220+s,+585+s]mm. Here s spans0–500mm. The claw mouth is700+s mm;
the assumed catcher/ball center of mass is60mm behind that plane. Ball seating is
not the same point as interception. Four wear shoes at the moving rear center
-200+s mm and fixed front center490mm provide190mm minimum guide spacing;
physical tube overlap is240mm at maximum extension. The pads remain inside the
outer at retraction. The root extension drive was shifted behind the tube, hence its
signed COM=-275mm is included. This helps gravity but adds pitch/yaw inertia.

Tube properties use A=b²-(b-2t)²; I_section=(b⁴-(b-2t)⁴)/12; density2700kg/m³.
Calculated outer mass0.4820kg and inner0.3287kg include full stock lengths; corner
radii are neglected. The actual vendor outer stock is labelled0.062in rather than
exactly1/16in: measure dimensions and update the parameter before release.
6061 properties E=69GPa, G=26GPa, yield240MPa are conservative *design assumptions*,
not a mill certificate. All printed/assembled masses are allowances needing weighing.
The catcher including servo, hardware and wiring has a170g allowance, not the old
130g unverified target; weigh the complete assembly. Ball-loaded pitch-moving mass
is2.411kg; the complete robot is heavier because the
yaw-carried motor/frame and fixed base are separate.

## Independent rigid-body equations

Let r_i(s) be each component's signed axial center of mass, ell_i its fixed length,
and m_i its mass. A translating inner tube remains the same physical length:

I(s) = sum m_i [r_i(s)² + ell_i²/12].
I'(s) = 2 sum_moving m_i r_i(s); I_dot=I'(s)*s_dot.
S(s)=sum m_i r_i(s), and gravity pitch torque=g*S*cos(p).

Using yaw y, pitch p measured up from horizontal, and extension s, the line-boom
kinetic energy is T=0.5I(s)[p_dot²+cos²(p)y_dot²]+0.5m_s*s_dot². The stationary-on-yaw
turret contributes I_t*y_dot²/2. Inverse dynamics from Euler–Lagrange is:

tau_p = (I+J_p*n_p²)*p_ddot + I'*s_dot*p_dot
        + I*y_dot²*sin(p)*cos(p) + g*S*cos(p).
tau_y = [I*cos²(p)+I_t+J_y*n_y²]*y_ddot
        + [I'*s_dot*cos²(p)-2I*sin(p)*cos(p)*p_dot]*y_dot.
F_s = [m_s+J_ext/r_pulley²]*s_ddot
      -0.5I'*(p_dot²+y_dot²*cos²(p)) + m_s*g*sin(p) + friction.

This accounts for extension Coriolis/centrifugal terms; a fixed-inertia PD controller
does not. Axis reflected rotor inertias are estimated50e-6kgm² for major steppers
and5e-6kgm² extension, pending exact part data. Cross-section transverse inertias,
motor gyroscopic effects, geometric offsets, flexible joints and backlash are omitted
and must be revisited with the final mass model. Within this approximation the
energy-conservation tests are independent of the inverse-dynamics implementation.

The outputs report min/mid/max extension, gravity, I, I', analytic motion demand
bounds and separate commissioning caps. The loaded pitch I rises from0.2008 to0.5408kgm²
(2.69×); horizontal gravity rises from1.507 to4.394Nm. Target simultaneous motion
screening produces11.65Nm pitch and9.61Nm yaw at maximum extension, before impact.
An8:1/6:1 reduction at120deg/s means160/120motor rpm, not motor speed120deg/s.
With0.90 belt efficiency and1.5 torque margin the motor must provide2.43/2.67Nm
at those respective speeds. These requirements exceed the candidate2Nm **holding**
rating even before any speed derating. High-speed targets are therefore not approved.

## Guides, drive force and binding

Guide loads include both pitch-plane and yaw-plane distributed inertial acceleration.
For a member acceleration a(r)=k*r+c, integrate F=m(k*r_com+c) and
M_about_rear=m[k(r_com²+ell²/12-r_rear*r_com)+c(r_com-r_rear)]. Then
R_front=M/span and R_rear=F-R_front, in each plane. Friction is modeled as
mu*(abs(R_front_pitch)+abs(R_front_yaw)+abs(R_rear_pitch)+abs(R_rear_yaw)+preload)
+cable_drag. Orthogonal square-pad face normals add; their vector resultant alone
would understate friction by up to sqrt(2). The nominal mu=0.15 and12N
total preload are measurements to obtain, not known properties of the finished guides.
`guide_bound` uses absolute integrands and independent acceleration bounds to avoid
underestimating simultaneous rotation/extension normal force. Printed carriers must
permit alignment; more motor torque cannot fix a skewed, wedging telescope.
[igus design notes](https://www.igus.com/linear-bearings/linear-guides-drylin-w-design-notes-com)
explain eccentric-force friction and overconstraint. Its specific2:1 rule is not
treated as a universal pass/fail rule for our custom shoe geometry.

The outer bore34.925mm gives4.7625mm nominal radial gap to the25.4mm inner. This
space is intentional for the top belt/clamp and corner-cleared shoes. It is not all
filled with soft tape. Physical extruded corner radii/straightness and30mm pad
length must be checked; drive line should remain close to the section center to
avoid self-induced wedging. Use rigid carriers plus thin replaceable wear faces.
Two fixed guide stations alone cannot support this full stroke; the rear must move.

## Bending, torsion, guides and shafts

Tip compliance follows integral[(L-x)²/(E I_section(x))]dx. The screening section
is outer to the moving rear-guide position, then the weaker inner. Overlap is not
assumed adhesively bonded. This deliberately understates tube EI through overlap,
but the final115mm claw attachment is modeled with inner-tube EI and may actually
be more compliant. The resulting number is **not an upper bound on actual assembled
tip deflection**. It excludes root, pad, hub, belt and finger stiffness. Tip-load
screens conservatively relocate all pitch-moving gravity mass to the mouth; actual
distributed gravity is used in dynamics. Compare the generated static/dynamic yield
factors to a target >=2.5 after local stress concentrations and fatigue allowances.
Do not approve a printed clamp from tube yield factor.

Torsional J≈t*(b-t)³ is the thin-wall closed-square Bredt approximation, and twist
=integral[T/(G*J)]dx. Tube bending polar inertia is not a valid torsion constant
for this section. Torsional clearance at pad faces, clamp slip and belt strain may
dominate. A0.20mm total guide clearance alone corresponds to about0.95mm mouth
lost motion at maximum reach. Film/shims should set fit after measured coupon tests.
The frequency output uses beam-only equivalent stiffness and all moving mass as
modal mass. It is a low-order sensitivity screen, **not a predicted measured resonance**.

Shaft/belt screen includes80T HTD5 pitch pulley127.3mm pitch diameter,100N assumed
preload per strand,12mm steel shaft and20mm overhang. It calculates tight/slack belt
tension, bearing radial load, bending plus torsion von Mises stress and a2× local
stress allowance. An arbitrary pretension is not a vendor belt rating. Actual drive
shaft geometry, keyways/clamping hubs, yaw bearing separation, axial retention,
trunnion fatigue and mounting plates still need the full assembly dimensions.
Two short supported trunnions must leave the telescope bore clear. Loads and shafts
for the unmatched impact screen can be far above the ordinary motion screen.

## Claws, impact and active retraction

The user requires fingers/claws: no net. Use three compliant fingers around a
lightweight mount. The25mm effective stopping stroke is presently an **assumption**
for claw bending plus foam compression, not finger length. The energy screen uses
E=0.5*m*v_rel², F_average=E/d and an explicitly assumed2× peak shape factor.
For50g at4m/s, E=0.4J and25mm stroke gives16N average/32N assumed peak. At1m/s
relative velocity the same stroke yields1N average/2N assumed peak. A32N transverse
catch at1.2m adds38.4Nm shoulder torque, exceeding the candidate drive. Foam-contact
time at4m/s is about12.5ms in a constant-deceleration model. A tiny servo cannot
close reliably from first touch on that timescale: geometry needs passive contact
compliance/retention and closing prepositioned from prediction. Verify bounce-out
and finger-root fatigue using controlled drop tests before launches.

v_rel = v_ball - v_hand is a vector. Positive radial velocity points outward.
Retraction helps an inward ball: -4 -(-1.2)=-2.8m/s instead of-4m/s. It makes an
outward ball worse: +4 -(-1.2)=+5.2m/s. Telescope retraction does not cancel tangential
ball velocity; coordinate yaw/pitch velocity matching and verify approach cone.
After contact, follow the ball along its velocity subject to retention, available
stroke, friction, actuator current and workspace. Do not always retract on contact.
At minimum physical length there is no reserve retraction stroke; claw compliance
must work there or planning must reserve stroke before the event. No impact credit
is taken for active retraction in the structural screen.

## Power, energy, duty and thermal

Target simultaneous mechanical demands are summed as |tau*w|+|F*v|, then divided
by an assumed0.65 conversion efficiency. Additional40W major-motor copper bound,
35W extension/driver loss and15W logic are disclosed allowances, not a validated
thermal model. Stepper phase current is not the same as DC-bus current. The final
bus current figure is generated from those assumptions; log actual simultaneous
acceleration and holding currents and check each fuse/wire/connector rating.

For any chosen cycle compute tau_RMS=sqrt(sum(t_i*tau_i²)/sum(t_i)), winding copper
heat=sum(I_phase_RMS²*R(T)), and average regenerated energy per cycle. A full horizontal
hold phase must be included. Without torque constant/current mapping, winding
resistance-temperature correction, thermal impedance and cooling measurements the
model intentionally cannot report a defensible continuous torque/temperature.
Use60s moving/holding/logging tests then a30minute worst-duty soak, starting at the
commissioning envelope with conservative current. Measure motor case, driver and
printed mount temperatures; stay below the lower of supplier limits and coupon-based
creep/softening limit, with a planned15C margin. Stop on temperature rise that fails
to stabilize; surface temperature alone does not prove winding temperature.

Regeneration includes both rotation axes, translation, reflected rotors and full
pitch gravity descent. Output estimates capacitor bus rise using
V_final=sqrt(V_initial²+2E/C), with4700uF. This exceeds ordinary driver limits; use
a verified dump circuit rather than assuming the PSU absorbs energy. A10ohm resistor
at28V dissipates78.4W while conducting, but its pulse-energy/repetition rating and
chopper electronics must be selected. Average DC consumption does not size that
resistor. Retain dump downstream of the contactor.

Extension hard-stop energy includes moving mass plus reflected motor J at1.2m/s.
Force over5mm is output as an average only; continued motor pushing is additional.
Physical stops, guarded stroke, hardware disable and matched current limits are
necessary. Never demonstrate the target speed by intentionally hitting hard stops.

## Cost and evidence

`bom.csv` has exact qty×unit calculations and no hand-entered TOTAL row. The tool
adds12% shipping/tax allowance and15% reserve. These are planning allowances, not
quotes or local tax advice. Complete machine total is above the$500 objective.
Restrained rig stages can be purchased separately, and existing owned parts should
be inventoried before purchases. Currency USD; price date2026-09-07. See
`selections.md` for manufacturer sources and `docs/mechanical_analysis.md` for
print/purchase decisions and physical gates.

