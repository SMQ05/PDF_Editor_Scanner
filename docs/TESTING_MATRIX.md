# Testing Matrix

Comprehensive test cases for PDF Scanner app covering all features and edge cases.

## 1. Permission Handling

| Test ID | Scenario | Steps | Expected Result | Status |
|---------|----------|-------|-----------------|--------|
| P-01 | First launch grant | Install fresh → Open → Grant camera | Camera preview shows | ☐ |
| P-02 | First launch deny | Install fresh → Open → Deny camera | Rationale screen shows | ☐ |
| P-03 | Deny then grant | P-02 → Tap "Grant Permission" → Grant | Camera starts | ☐ |
| P-04 | Permanent denial | Deny with "Don't ask again" | "Open Settings" button shown | ☐ |
| P-05 | Settings recovery | P-04 → Tap "Open Settings" → Grant → Return | Camera works | ☐ |

## 2. Camera & Scanning

| Test ID | Scenario | Steps | Expected Result | Status |
|---------|----------|-------|-----------------|--------|
| C-01 | Basic capture | Point at document → Tap capture | Image captured, crop screen shows | ☐ |
| C-02 | Quad detection | Point at contrasting document | Quad overlay visible | ☐ |
| C-03 | No quad detected | Point at blank wall | No overlay; manual crop on capture | ☐ |
| C-04 | Low light | Cover camera in dark | Flash suggestion appears | ☐ |
| C-05 | Flash toggle | Tap flash button | Flash state changes | ☐ |
| C-06 | Multi-page | Capture 3 pages | Page counter shows 3 | ☐ |
| C-07 | Page limit | Capture 200 pages → Try 201st | Warning shown, capture blocked | ☐ |

## 3. Crop & Adjust

| Test ID | Scenario | Steps | Expected Result | Status |
|---------|----------|-------|-----------------|--------|
| A-01 | Corner drag | Drag any corner | Corner moves, lines update | ☐ |
| A-02 | All corners | Move all 4 corners | Quad updates properly | ☐ |
| A-03 | Rotation left | Tap rotate left | Image rotates CCW | ☐ |
| A-04 | Rotation right | Tap rotate right | Image rotates CW | ☐ |
| A-05 | Filter B/W | Select B/W filter | Chip selected, preview updates | ☐ |
| A-06 | Filter Grayscale | Select Grayscale | Chip selected | ☐ |
| A-07 | Filter Enhanced | Select Enhanced | Chip selected | ☐ |
| A-08 | Retake | Tap Retake | Returns to scanner | ☐ |
| A-09 | Confirm | Adjust → Confirm | Page added, back to scanner | ☐ |

## 4. Session Persistence

| Test ID | Scenario | Steps | Expected Result | Status |
|---------|----------|-------|-----------------|--------|
| S-01 | Background resume | Scan 2 pages → Home button → Return | 2 pages still there | ☐ |
| S-02 | Process death | Scan 2 pages → Force stop → Reopen | 2 pages restored | ☐ |
| S-03 | Orientation | Scan 2 pages → Rotate device | Pages preserved | ☐ |
| S-04 | Session clear | Complete export | Session cleared for next scan | ☐ |

## 5. PDF Export

| Test ID | Scenario | Steps | Expected Result | Status |
|---------|----------|-------|-----------------|--------|
| E-01 | Export small | 3 pages → Small preset → Export | PDF created < expected size | ☐ |
| E-02 | Export balanced | 3 pages → Balanced preset → Export | PDF created | ☐ |
| E-03 | Export high | 3 pages → High preset → Export | PDF created, larger size | ☐ |
| E-04 | Custom filename | Enter "MyScan" → Export | File named MyScan.pdf | ☐ |
| E-05 | Share after export | Export → Tap Share | Share sheet opens | ☐ |
| E-06 | PDF valid | Export → Open in PDF reader | PDF displays correctly | ☐ |

## 6. PDF Tools

| Test ID | Scenario | Steps | Expected Result | Status |
|---------|----------|-------|-----------------|--------|
| T-01 | Merge 2 PDFs | Select 2 PDFs → Merge | Combined PDF created | ☐ |
| T-02 | Split PDF | Select PDF → Split 1-2, 3-5 | 2 PDFs created | ☐ |
| T-03 | Encrypted detect | Import encrypted PDF → Try merge | Error message, no crash | ☐ |
| T-04 | Large PDF merge | Merge 10 PDFs | Completes without ANR | ☐ |

## 7. Privacy & Metadata

| Test ID | Scenario | Steps | Expected Result | Status |
|---------|----------|-------|-----------------|--------|
| V-01 | EXIF stripped | Scan photo with GPS → Export → Check EXIF | No GPS/device data | ☐ |
| V-02 | PDF metadata | Export → Check PDF metadata | Creator: "PDF Scanner", no personal info | ☐ |

## 8. Monetization - Ads

| Test ID | Scenario | Steps | Expected Result | Status |
|---------|----------|-------|-----------------|--------|
| M-01 | Banner on home | Open app (no purchase) | Banner visible at bottom | ☐ |
| M-02 | No banner if purchased | Purchase → Restart → Home | No banner | ☐ |
| M-03 | Interstitial on export | Export PDF | Interstitial may show | ☐ |
| M-04 | Interstitial on share | Share PDF | Interstitial may show | ☐ |
| M-05 | Frequency cap | Export 3x in 30s | Max 1 interstitial | ☐ |
| M-06 | No interstitial launch | Open app | No interstitial | ☐ |
| M-07 | No interstitial exit | Close app | No interstitial | ☐ |

## 9. Monetization - IAP

| Test ID | Scenario | Steps | Expected Result | Status |
|---------|----------|-------|-----------------|--------|
| I-01 | Purchase flow | Settings → Purchase Remove Ads | Play billing dialog shows | ☐ |
| I-02 | Purchase success | Complete purchase | Ads removed confirmation | ☐ |
| I-03 | Purchase cancel | Start purchase → Cancel | No change, button enabled | ☐ |
| I-04 | Restore success | Reinstall → Restore | Ads removed if purchased | ☐ |
| I-05 | Restore none | Fresh install → Restore | "No purchases" message | ☐ |
| I-06 | Refund handling | Purchase → Refund → Reopen | Ads re-enabled | ☐ |

## 10. PDF Viewer & Editor

| Test ID | Scenario | Steps | Expected Result | Status |
|---------|----------|-------|-----------------|--------|
| V-01 | Open from recents | Tap doc in recents | PDF viewer opens | ☐ |
| V-02 | Import PDF | Home → Import → Select PDF | Viewer opens with PDF | ☐ |
| V-03 | Open from file manager | Files app → Tap PDF → "Open with DocScanner" | Viewer opens | ☐ |
| V-04 | Zoom/pan | Pinch zoom, drag | Zoom and pan work | ☐ |
| V-05 | Page navigation | Swipe left/right | Pages change | ☐ |
| V-06 | Highlight | Select highlight → Drag | Yellow overlay | ☐ |
| V-07 | Underline | Select underline → Drag | Line below rect | ☐ |
| V-08 | Strikeout | Select strikeout → Drag | Line through rect | ☐ |
| V-09 | Pen/ink | Select pen → Draw | Strokes visible | ☐ |
| V-10 | Redact black | Select redact black → Drag | Black rectangle | ☐ |
| V-11 | Redact white | Select redact white → Drag | White rectangle | ☐ |
| V-12 | Add text | Select text → Tap → Type | Text appears | ☐ |
| V-13 | Signature | Select sig → Draw → Place | Signature on page | ☐ |
| V-14 | Undo/redo | Add highlight → Undo → Redo | Annotation removed/restored | ☐ |
| V-15 | Save new file | Annotate → Save As | New PDF created | ☐ |
| V-16 | Saved PDF valid | Open saved PDF in other reader | Annotations visible | ☐ |
| V-17 | Share from viewer | Save → Share | Share sheet opens | ☐ |
| V-18 | Encrypted PDF | Open password PDF | Error message shown | ☐ |
| V-19 | Unsaved changes | Annotate → Back | Confirm dialog | ☐ |

## 11. File Management

| Test ID | Scenario | Steps | Expected Result | Status |
|---------|----------|-------|-----------------|--------|
| F-01 | Recent list | Export 3 docs → Home | 3 docs in recents | ☐ |
| F-02 | Open recent | Tap recent doc | PDF viewer opens | ☐ |
| F-03 | Delete doc | Long press → Delete | Removed from list | ☐ |
| F-04 | Rename doc | Long press → Rename → Save | Name updated | ☐ |

## 11. Performance

| Test ID | Scenario | Steps | Expected Result | Status |
|---------|----------|-------|-----------------|--------|
| F-01 | Cold start | Force stop → Launch | App visible < 3s | ☐ |
| F-02 | Camera FPS | Open scanner | Preview smooth (30fps+) | ☐ |
| F-03 | Export 50 pages | Scan 50 → Export | Completes < 60s | ☐ |
| F-04 | Memory 200 pages | Scan 200 pages | No OOM crash | ☐ |
| F-05 | No ANR | Export 100 pages | No ANR dialog | ☐ |

## 12. Device Compatibility

| Test ID | Device | Android | Notes | Status |
|---------|--------|---------|-------|--------|
| D-01 | Low-end (2GB RAM) | 10 | Basic functionality | ☐ |
| D-02 | Mid-range (4GB) | 12 | Full performance | ☐ |
| D-03 | High-end | 13 | All features | ☐ |
| D-04 | Tablet | 11+ | Layout adapts | ☐ |

---

## Test Execution Notes

- Run on physical devices (camera testing)
- Use test AdMob IDs during development
- Test with license testing accounts for IAP
- Document any failures with screenshots/logs
