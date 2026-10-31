---
name: Kinfolk Care Portal
colors:
  surface: '#f8f9ff'
  surface-dim: '#cbdbf5'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e5eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d3e4fe'
  on-surface: '#0b1c30'
  on-surface-variant: '#42474f'
  inverse-surface: '#213145'
  inverse-on-surface: '#eaf1ff'
  outline: '#727780'
  outline-variant: '#c2c7d1'
  surface-tint: '#2d6197'
  primary: '#00355f'
  on-primary: '#ffffff'
  primary-container: '#0f4c81'
  on-primary-container: '#8ebdf9'
  inverse-primary: '#a0c9ff'
  secondary: '#006398'
  on-secondary: '#ffffff'
  secondary-container: '#5bb8fe'
  on-secondary-container: '#00476e'
  tertiary: '#003c27'
  on-tertiary: '#ffffff'
  tertiary-container: '#005539'
  on-tertiary-container: '#3dd197'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d2e4ff'
  primary-fixed-dim: '#a0c9ff'
  on-primary-fixed: '#001c37'
  on-primary-fixed-variant: '#07497d'
  secondary-fixed: '#cce5ff'
  secondary-fixed-dim: '#93ccff'
  on-secondary-fixed: '#001d31'
  on-secondary-fixed-variant: '#004b73'
  tertiary-fixed: '#6ffbbe'
  tertiary-fixed-dim: '#4edea3'
  on-tertiary-fixed: '#002113'
  on-tertiary-fixed-variant: '#005236'
  background: '#f8f9ff'
  on-background: '#0b1c30'
  surface-variant: '#d3e4fe'
typography:
  display:
    fontFamily: Plus Jakarta Sans
    fontSize: 40px
    fontWeight: '700'
    lineHeight: 48px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 26px
    fontWeight: '700'
    lineHeight: 34px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  title-md:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  label-lg:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '700'
    lineHeight: 14px
    letterSpacing: 0.04em
  metric-number:
    fontFamily: Plus Jakarta Sans
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 32px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1.25rem
  gutter-mobile: 0.75rem
  margin: 2rem
  margin-mobile: 1rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
---

## Brand & Style

This design system is engineered for daycare directors, early childhood educators, and anxious parents who navigate busy morning drop-offs and hectic classroom schedules. The interface must communicate unwavering institutional safety, clarity under duress, and warm domestic approachable care. 

The aesthetic is **Modern Friendly Functionalism**—a fusion of clean, Scandinavian clarity with soft, tactile warmth:
- **Calm & Stabilizing:** Clutter-free interfaces reduce cognitive strain during high-tempo transitions (sign-in rushes, allergy checks, emergency handoffs).
- **Legible & High-Contrast:** Large touch targets, immediate visual anchors, and crisp distinctions allow one-handed operation on tablets by educators carrying infants or moving between classrooms.
- **Approachable Professionalism:** Gentle rounded forms and warm accents dismantle bureaucratic coldness while preserving regulatory diligence and absolute administrative rigor.

## Colors

The palette balances clinical legibility with domestic warmth, calibrated to pass WCAG AAA standards for ambient classroom tablets.

- **Primary Deep Teal-Navy (`#0F4C81`):** Represents institutional accountability, administrative depth, and quiet authority. Used for core brand elements, primary actions, and key table headers.
- **Secondary Sky Accent (`#0284C7`):** A friendly, light-hearted blue for active tabs, secondary links, and neutral activity tags (e.g., naps, diaper logs, sensory activities).
- **Status & Operational Accents:**
  - **Present / Checked-in Emerald (`#10B981`):** Signals active attendance, completed health checks, and verified pickups. Always paired with deep forest text (`#065F46`) on light green washes (`#ECFDF5`).
  - **Care Alert Amber (`#F59E0B`):** Denotes dietary alerts, medication due times, and approaching pickup deadlines. Rendered with dark amber text (`#92400E`) on warm pale amber (`#FFFBEB`).
  - **Urgent / Absent Crimson (`#EF4444`):** Flags unverified absences, severe allergies, and urgent incident logs. Paired with deep crimson text (`#991B1B`) on soft rose surfaces (`#FEF2F2`).
- **Surface & Neutrals:**
  - App canvas sits on a gentle warm paper white (`#F8FAFC`), separating cleanly from crisp elevated white (`#FFFFFF`) cards.
  - Borders use subtle slate (`#E2E8F0`), maintaining crisp tabular bounds without harsh visual noise.

## Typography

Typography pairs the human-centric, rounded warmth of **Plus Jakarta Sans** for titles with the strict, pixel-precise legibility of **Inter** for rosters, medical charts, and dense administrative feeds.

- **Headlines:** Display and Headline roles leverage Plus Jakarta Sans to infuse approachability and optimism into the daily greeting, classroom nameplates, and key hub summaries.
- **Rosters & Records:** Inter drives all data tables, student profile attributes, and incident logs. Its high x-height and distinctive tabular figures prevent transcription errors in check-in times and guardian contact numbers.
- **Status Metrics:** Numbers within live classroom capacity badges utilize Plus Jakarta Sans Bold (`metric-number`) to deliver instantaneous awareness of child-to-staff compliance ratios.

## Layout & Spacing

The portal runs on a responsive fluid layout structured for tablet kiosk stands, handheld educator tablets, and desktop administrative workstations.

- **Grid Structure:**
  - **Desktop (Admin & Directors):** 12-column layout with 2rem page margins and 1.25rem gutters. Facilitates split views: active classroom roster on the left (8 cols), real-time child detail and guardian verification feed on the right (4 cols).
  - **Tablet (Educator In-Room Hub):** 8-column layout with 1.5rem margins and 1rem gutters. Optimized for horizontal 2-up card feeds or multi-child grid attendance check-in.
  - **Mobile (Parent Handheld):** 4-column layout with 1rem margins and 0.75rem gutters, stacking child attendance timelines linearly.
- **Spacing Rhythm:** 8px baseline rhythm across all element gaps. Actionable touch boundaries inside attendance grids never fall below 48px square to ensure flawless one-touch check-ins during drop-off congestion.

## Elevation & Depth

Visual hierarchy prioritizes surface clarity over heavy dramatic dimensionality, preventing interface mud under classroom fluorescent lighting or outdoor sunlight.

- **Level 0 (Canvas Base):** Tinted foundational slate (`#F8FAFC`).
- **Level 1 (Card & Roster Surface):** Pure white (`#FFFFFF`) with a delicate hairline boundary (`1px solid #E2E8F0`) and an ambient tinted drop: `0px 1px 3px rgba(15, 76, 129, 0.04), 0px 4px 12px rgba(15, 76, 129, 0.02)`.
- **Level 2 (Active Interactions & Dropdowns):** Subtle lift with `0px 4px 16px rgba(15, 76, 129, 0.08)`. Applied to active popovers, guardian signature pads, and classroom switcher menus.
- **Level 3 (Emergency Modals & Critical Overlays):** Grounded by a dim scrim (`rgba(15, 23, 42, 0.45)`) with an elevated card shadow: `0px 12px 32px rgba(15, 23, 42, 0.16)`.
- **Active State Highlights:** Selected child attendance tiles do not elevate higher; instead, they receive an energetic 2px inner border using Primary Teal (`#0F4C81`) alongside an emerald check indicator.

## Shapes

The design uses a consistent medium-soft curvature (`roundedness: 2`) that establishes an inviting, child-friendly sensibility while maintaining enterprise software alignment.

- **Container Radii:** Standard cards, child profiles, and attendance panels adhere to `rounded-lg` (16px / 1rem) to soften clinical dashboards.
- **Interactive Controls:** Buttons, text input fields, and search bars employ `rounded` (8px / 0.5rem), providing unmistakable interactive affordability without feeling toy-like.
- **Pills:** Status badges, age-group chips, allergy flags, and quick-filter pills utilize full pill curvature (`rounded-full` / 9999px) for distinct visual contrast against rectangular roster cards.
- **Avatars:** Student and guardian headshots sit inside circular crops with optional status-ring borders (green ring for present, grey ring for checked out).

## Components

### Buttons
- **Primary:** Solid `#0F4C81` with white text, 8px border radius, 44px min height for tablets. Hover shifts to `#0D3F6B`.
- **Secondary:** Clean white background, 1px `#E2E8F0` border, `#0F4C81` text. On hover, background shifts to `#F1F5F9`.
- **Attendance Action Buttons:**
  - *Check In:* Emerald solid (`#10B981`) text white, bold, prominent tactile press state (`scale(0.98)`).
  - *Check Out:* Gentle slate-crimson outline (`#EF4444`), preventing accidental taps.

### Badges & Status Chips
- Full pill format (`py-1 px-3`, `text-xs`, font weight 600).
- **Checked In / Present:** Background `#ECFDF5`, text `#065F46`, paired with a solid 6px emerald dot.
- **Alert / Care Note:** Background `#FFFBEB`, text `#92400E`, with an amber exclamation icon.
- **Absent / Not Checked In:** Background `#F1F5F9`, text `#64748B`.
- **Urgent / Medical Warning:** Background `#FEF2F2`, text `#991B1B`, uppercase label styling.

### Child Roster Cards & Grid Tiles
- White surface, 16px corner radius, 1px `#E2E8F0` border.
- Layout features child avatar (48px circle), bold name, room assignment, and prominent status pill.
- Includes quick-access allergy badge in the top right corner with high-visibility icon.
- Split footer with instant action triggers: "Check In", "Log Meal", "Add Nap".

### Input Fields & Search Bars
- Background `#FFFFFF`, 1px solid border `#CBD5E1`, 8px radius.
- Height: 44px with 16px horizontal padding.
- Focused state: Border transitions to `#0F4C81` with a `0 0 0 3px rgba(15, 76, 129, 0.15)` focus ring.
- Search rosters include a sticky quick-scan QR/PIN icon embedded within the trailing input edge.

### Ratio Compliance Bar (Daycare Specific)
- Horizontal header component displaying real-time Teacher-to-Child ratio (e.g., "Infants: 1:4 (Compliant)").
- Uses a pill progress tracker that shifts from green (`#10B981`) to amber (`#F59E0B`) as classroom approaches maximum statutory limits.