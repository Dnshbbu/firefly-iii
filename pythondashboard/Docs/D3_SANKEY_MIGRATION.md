# D3 Sankey Migration

## Overview

The Cash Flow Sankey diagram has been migrated from **Plotly** to **D3.js** to resolve label visibility issues during hover interactions and provide more robust, professional visualization capabilities.

## Problem Statement

The original Plotly implementation had custom JavaScript hover effects that attempted to dim unconnected nodes and their labels. However, this caused issues where:

- **Connected node labels were incorrectly dimmed** during hover
- Text element indices didn't align with node data indices
- Labels would disappear when they should remain visible
- The custom implementation was fragile and difficult to maintain

## Solution: D3-Sankey

We migrated to D3.js with the official d3-sankey plugin, which provides:

✅ **Reliable hover interactions** with proper highlighting
✅ **Professional tooltip display** with formatted amounts
✅ **All labels remain visible** with proper opacity control
✅ **Better performance** with native D3 event handling
✅ **Easier customization** through standard D3 patterns
✅ **No dependency on Plotly's complex internals**

## Implementation Details

### New Files

**`utils/d3_sankey_helper.py`**
- `prepare_sankey_data()`: Transforms Firefly III transaction data into D3 Sankey format
- `generate_d3_sankey_html()`: Generates complete HTML with embedded D3 visualization

### Modified Files

**`pages/20_🌊_Cash_Flow_Sankey.py`**
- Replaced `create_sankey_with_destinations()` (Plotly) with `prepare_sankey_data()` (D3)
- Removed 180+ lines of custom hover JavaScript
- Simplified to ~25 lines of clean implementation

### Key Features

**5-Tier Cash Flow Visualization:**
1. Income Sources (green)
2. Total Income (blue)
3. Remaining + Total Expenses (green/orange)
4. Destination Accounts (yellow)
5. Expense Categories (red)

**Hover Interactions:**
- Hover over any **node** → highlights all connected nodes and links
- Hover over any **link** → highlights source and target nodes
- All other nodes/links are dimmed to 20% opacity
- **Labels remain fully visible at all times**
- Smooth tooltip shows: Name, Amount (€), Percentage

**Visual Design:**
- Dark mode compatible with transparent background
- Consistent color scheme matching the existing dashboard
- Professional typography with proper spacing
- Formatted currency (€) with thousand separators
- Percentage calculations relative to income/expenses

## Testing

A test script (`test_d3_sankey.py`) is included to verify:
- Data preparation logic
- Node and link generation
- HTML output generation
- Proper formatting

Run with:
```bash
./venv/Scripts/python.exe test_d3_sankey.py
```

## Usage in Streamlit

The D3 Sankey diagram is embedded using `streamlit.components.v1.html()`:

```python
import streamlit.components.v1 as components
from utils.d3_sankey_helper import prepare_sankey_data, generate_d3_sankey_html

# Prepare data
sankey_data = prepare_sankey_data(
    income_df=income_sources,
    destination_df=destination_accounts,
    destination_category_mapping_df=destination_category_mapping,
    top_n_income=10,
    top_n_destination=15,
    top_n_category=30
)

# Generate HTML
sankey_html = generate_d3_sankey_html(
    data=sankey_data,
    title="Cash Flow Sankey Diagram",
    height=700
)

# Display
components.html(sankey_html, height=750, scrolling=False)
```

## Dependencies

The implementation uses CDN-hosted libraries (no installation required):
- **D3.js v7** - Core visualization library
- **d3-sankey v0.12.3** - Official Sankey diagram plugin

These are loaded via CDN in the generated HTML, so no additional Python packages are needed.

## Benefits Over Plotly

| Feature | Plotly | D3-Sankey |
|---------|--------|-----------|
| Label visibility | ❌ Issues with dimming | ✅ Always visible |
| Hover interactions | ⚠️ Custom/fragile | ✅ Native/robust |
| Customization | ⚠️ Limited by Plotly API | ✅ Full D3 flexibility |
| Performance | ⚠️ Heavy library | ✅ Lightweight |
| Code complexity | ❌ 180+ lines JS | ✅ Clean D3 patterns |
| Maintenance | ❌ High | ✅ Low |

## Future Enhancements

Possible improvements with D3:
- [ ] Animated transitions when data changes
- [ ] Drag-and-drop node repositioning
- [ ] Click to expand/collapse node groups
- [ ] Export as SVG or PNG
- [ ] Responsive sizing based on viewport
- [ ] Custom color schemes per category

## Backward Compatibility

The old Plotly implementation (`utils/sankey_helper.py`) remains in the codebase for reference but is no longer used. It can be safely removed if no other pages depend on it.

## Migration Notes

If you need to migrate other Sankey diagrams:

1. Use `prepare_sankey_data()` to transform your data
2. Call `generate_d3_sankey_html()` to create the visualization
3. Display with `components.html()`
4. Customize colors/styling in the HTML template as needed

The data format is straightforward:
- **Nodes**: Array of objects with `name`, `amount`, `percentage`, `layer`, `type`
- **Links**: Array of objects with `source`, `target`, `value` (indices into nodes array)

---

**Created:** 2025-11-07
**Author:** Claude Code
**Version:** 1.0
