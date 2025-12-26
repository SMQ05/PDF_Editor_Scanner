# Release Checklist

## Pre-Release Verification

### 1. Code Quality
- [ ] All Python files pass syntax check (`python -m py_compile`)
- [ ] No import errors when loading main modules
- [ ] No TODO placeholders in production code
- [ ] Logging is appropriate (no sensitive data logged)

### 2. Configuration
- [ ] `buildozer.spec` version updated
- [ ] Package name is unique and final
- [ ] AdMob App ID in buildozer.spec meta-data (production, not test)
- [ ] All test ad unit IDs replaced with production IDs in Java files

### 3. Assets
- [ ] App icon (512x512) in `assets/icons/icon.png`
- [ ] Presplash image in `assets/images/presplash.png`
- [ ] Feature graphic prepared (1024x500) for Play Store

### 4. Build Verification
- [ ] Clean build succeeds: `buildozer android clean && buildozer android release`
- [ ] APK size is reasonable (target < 50MB)
- [ ] APK installs on test devices

### 5. Functional Testing
- [ ] First launch permission flow works
- [ ] Camera preview displays correctly
- [ ] Document scanning captures image
- [ ] Manual crop corners are draggable
- [ ] All filters apply correctly
- [ ] PDF export creates valid PDF
- [ ] Share intent works
- [ ] Session persists across app background
- [ ] Session survives process death

### 6. Edge Cases
- [ ] Permission denied shows rationale
- [ ] Permission denied permanently shows "Open Settings"
- [ ] Low light shows flash suggestion
- [ ] No contour detected shows full-frame fallback
- [ ] Maximum page limit prevents additional captures
- [ ] Encrypted PDF shows user-friendly error
- [ ] Empty session handled gracefully

### 7. Monetization
- [ ] Banner ad displays on home (when not purchased)
- [ ] Interstitial shows after export (respects frequency cap)
- [ ] No interstitial on app launch or exit
- [ ] Remove Ads purchase flow works
- [ ] Restore purchases works
- [ ] After purchase, all ads disabled
- [ ] After refund, purchase state correctly updates

### 8. Privacy & Compliance
- [ ] EXIF stripping verified (check with ExifTool)
- [ ] PDF metadata is neutral
- [ ] Privacy policy URL is live and accessible
- [ ] Privacy policy linked in Settings screen
- [ ] No sensitive permissions requested beyond CAMERA/INTERNET

### 9. Performance
- [ ] App launches in < 3 seconds
- [ ] Camera preview is smooth (no dropped frames)
- [ ] PDF export completes in reasonable time
- [ ] Memory usage stable during multi-page scan (200 pages)
- [ ] No ANR on export of large documents

### 10. Signing & Security
- [ ] Release keystore created and secured
- [ ] APK properly signed
- [ ] APK passes Google Play upload validation
- [ ] Keystore password stored securely (not in repo)

---

## Google Play Store Preparation

### Store Listing
- [ ] App title (30 chars max)
- [ ] Short description (80 chars max)
- [ ] Full description (4000 chars max)
- [ ] Feature graphic (1024x500)
- [ ] Icon (512x512)
- [ ] Screenshots (min 2, recommended 8)
- [ ] Phone screenshots
- [ ] Tablet screenshots (if supporting)
- [ ] Category: Productivity
- [ ] Content rating questionnaire completed

### Privacy & Data Safety
- [ ] Data safety form completed
- [ ] Camera permission justified
- [ ] Ad SDK data collection disclosed
- [ ] Privacy policy URL entered

### Pricing & Distribution
- [ ] Countries selected
- [ ] Pricing confirmed (Free with IAP)
- [ ] In-app product "remove_ads" created in Play Console
- [ ] In-app product activated

### Review
- [ ] Test on multiple devices (different screen sizes)
- [ ] Test on Android 10, 11, 12, 13
- [ ] App content complies with Play policies
- [ ] No trademarked content

---

## Post-Release

- [ ] Monitor crash reports in Play Console
- [ ] Monitor reviews and respond
- [ ] Verify ad revenue appearing in AdMob
- [ ] Verify IAP revenue in Play Console
- [ ] Prepare for first update based on feedback
