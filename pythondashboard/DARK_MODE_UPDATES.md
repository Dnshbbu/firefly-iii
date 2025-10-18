# Dark Mode Updates - Net Worth Dashboard

## Changes Made

### 1. **Gridstack.js Widget Styling (Dark Mode)**
Updated `pages/1_📊_Net_Worth.py` to support dark mode theme:

#### Widget Backgrounds
- Changed from `background: white` to `background: rgba(38, 39, 48, 0.4)` with backdrop blur
- Added semi-transparent dark background for glass-morphism effect

#### Colors Updated
- **Widget borders:** `rgba(250, 250, 250, 0.1)` - subtle light borders
- **Text colors:**
  - Headers: `#fafafa` (off-white)
  - Body text: `#e0e0e0` (light gray)
  - Labels: `#b0b0b0` (medium gray)
- **Tables:**
  - Header background: `rgba(250, 250, 250, 0.05)`
  - Row borders: `rgba(250, 250, 250, 0.1)`
- **Positive/Negative values:**
  - Green (positive): `#4ade80` (Tailwind green-400)
  - Red (negative): `#f87171` (Tailwind red-400)

#### Shadows
- Normal: `0 2px 8px rgba(0,0,0,0.3)`
- Moving/dragging: `0 4px 16px rgba(0,0,0,0.5)`

### 2. **Backdrop Filter**
Added `backdrop-filter: blur(10px)` for modern glass effect on widgets

### 3. **Interactive Elements**
- Header borders: `rgba(250, 250, 250, 0.1)` separator line
- Drag handles: `#b0b0b0` color
- Hover states on table rows: `rgba(250, 250, 250, 0.03)`

## Features

### Visual Elements
- ✅ Dark semi-transparent widget cards
- ✅ Glass-morphism effect with backdrop blur
- ✅ Bright, readable text on dark backgrounds
- ✅ Subtle borders and separators
- ✅ Appropriate color contrast for accessibility
- ✅ Consistent color scheme across all widgets

### Widget Types
1. **Net Worth Metrics** - Large value display with colored amounts
2. **Account Type Summary** - Dark-themed table
3. **Top Accounts** - Scrollable list with colored balances
4. **Account Statistics** - Information panel

## Color Palette

```
Background:     rgba(38, 39, 48, 0.4)
Text Primary:   #fafafa
Text Secondary: #e0e0e0
Text Muted:     #b0b0b0
Borders:        rgba(250, 250, 250, 0.1)
Positive:       #4ade80 (green)
Negative:       #f87171 (red)
```

## Testing

To test the dark mode:
1. Run `streamlit run Home.py`
2. Navigate to "📊 Net Worth" page
3. Connect to your Firefly III instance
4. Enable "🎨 Use Draggable Dashboard Layout" in the sidebar
5. Verify all widgets have dark backgrounds with light text
6. Test drag and drop functionality
7. Check color contrast and readability

## Browser Compatibility

The `backdrop-filter` property is supported in:
- Chrome/Edge 76+
- Safari 9+
- Firefox 103+

For older browsers, widgets will still display correctly without the blur effect.
