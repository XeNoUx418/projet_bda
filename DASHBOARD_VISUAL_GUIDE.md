# Dashboard Visual Layout Reference

## Page Structure

```
┌──────────────────────────────────────────────────────────────┐
│                        TOPBAR                                │
│  [Logo] Vice Doyen • Strategic Dashboard & Analytics [← Back]│
└──────────────────────────────────────────────────────────────┘

┌──────────────┬──────────────┬──────────────┬──────────────┐
│              │              │              │              │
│  📋 Exams    │ 🏛️ Merged   │ ✂️ Split     │ 👨‍🏫 Professors│
│              │              │              │              │
│    [1234]    │ [567] / 46%  │ [234] / 19%  │    [89]      │
│ ↑ Complete   │              │              │ All assigned │
│              │              │              │              │
└──────────────┴──────────────┴──────────────┴──────────────┘

┌─────────────────────────────────┬─────────────────────────────────┐
│                                 │                                 │
│     Room Type Distribution      │   Group Handling Summary        │
│     [Doughnut Chart]            │   [Horizontal Bar Chart]        │
│     • Salle: 45%                │   Regular: [████] 45%          │
│     • Amphi: 30%                │   Merged:  [████] 30%          │
│     • Labo: 20%                 │   Split:   [██] 25%            │
│     • Other: 5%                 │                                 │
│                                 │                                 │
└─────────────────────────────────┴─────────────────────────────────┘

┌─────────────────────────────────┬─────────────────────────────────┐
│                                 │                                 │
│   Top Utilized Rooms            │   Professor Workload            │
│                                 │                                 │
│ 🏠 Room A101      [Salle]    45 │ Dr. Smith      [IT]   78 / 100% │
│ 🏠 Room B202      [Salle]    42 │ Dr. Johnson    [CS]   65 / 83%  │
│ 🏛️  Amph. 1       [Amphi]    38 │ Dr. Williams   [ENG]  52 / 67%  │
│ 🏛️  Amph. 2       [Amphi]    35 │ Dr. Brown      [BIO]  48 / 62%  │
│ 🏠 Room C303      [Salle]    32 │ Dr. Davis      [PHY]  42 / 54%  │
│                                 │                                 │
└─────────────────────────────────┴─────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│          🚨 Critical Alerts & Conflicts                      │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ✅ No professor overlaps detected. System is optimal.      │
│                                                              │
│  Professor        │ Date       │ Time  │ Overlaps          │
│  ─────────────────┼────────────┼───────┼──────────         │
│  (empty if clean) │            │       │                   │
│                                                              │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                Dashboard • Real-time academic planning      │
└──────────────────────────────────────────────────────────────┘
```

## Color Coding

### KPI Cards
- **Blue**: Primary accent (#2563eb)
- **Green**: Merged/Amphi (#10b981)
- **Amber**: Split (#f59e0b)
- **Purple**: Professors (#8b5cf6)

### Status Colors
- **Green**: ✅ All systems optimal
- **Red**: ⚠️ Conflicts detected
- **Amber**: ⚡ Warnings/splits

### Charts
- **Room Distribution**: Multiple colors (blue, green, amber, red)
- **Group Summary**: Cyan (regular), Green (merged), Amber (split)

## Responsive Breakpoints

### Desktop (1200px+)
- KPI Cards: 4 columns
- Charts: 2 columns
- Tables: 2 columns side-by-side

### Tablet (768-1199px)
- KPI Cards: 2 columns
- Charts: Full width (stacked)
- Tables: Full width

### Mobile (< 768px)
- KPI Cards: 1 column
- Charts: Full width, smaller height
- Tables: Full width, horizontal scroll

## Interaction Patterns

### KPI Cards
- **Hover**: Lift up 4px, enhanced shadow
- **Animation**: 0.2s ease transition
- **Clickable**: No action (displays only)

### Charts
- **Chart.js Interactive**:
  - Hover over segments/bars → shows value
  - Click legend → toggle data
  - Zoom possible on some charts

### Tables
- **Row Hover**: Light background highlight
- **Scroll**: Horizontal on mobile
- **Sorting**: Not implemented (sorted by backend)

### Buttons
- **Hover**: Color shift + subtle lift
- **Active**: Darker shade
- **Disabled**: Grayed out

## Data Updates

**Real-time**: 
- KPI cards update on page load
- Charts render dynamically
- Tables populate from API
- Conflicts checked automatically

**Refresh**:
- Manual: F5 or browser refresh
- Auto: No auto-refresh (design choice)
- Future: Could add real-time WebSocket

## Accessibility

✅ Color contrast ratios meet WCAG AA  
✅ Semantic HTML structure  
✅ Keyboard navigation support  
✅ ARIA labels on icons  
✅ Responsive text sizing  

## Mobile Experience

```
┌─────────────────┐
│   TOPBAR        │
├─────────────────┤
│ 📋 Exams        │
│ [1234]          │
├─────────────────┤
│ 🏛️ Merged      │
│ [567] / 46%     │
├─────────────────┤
│ ✂️ Split        │
│ [234] / 19%     │
├─────────────────┤
│ 👨‍🏫 Professors  │
│ [89]            │
├─────────────────┤
│ [Room Chart]    │
├─────────────────┤
│ [Group Chart]   │
├─────────────────┤
│ [Top Rooms]     │
├─────────────────┤
│ [Prof Load]     │
├─────────────────┤
│ [Conflicts]     │
└─────────────────┘
```

## Print Friendly

Dashboard is optimized for screen viewing. 
For printing, recommend:
- Use browser Print to PDF
- Select "Fit to page"
- Disable background colors optional
- Save as PDF for archiving

## Dark Mode (Future)

Prepared infrastructure for dark mode:
- CSS variables use semantic names
- Can easily invert colors
- Would need `prefers-color-scheme` media query

---

**Reference Version**: 1.0  
**Created**: January 6, 2026
