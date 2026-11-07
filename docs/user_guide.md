# NEXUS AI - User Guide

## For Citizens

### Reporting an Issue

1. **Sign in** (or create an account via the Register page)
2. Click **"Report an Issue"** from the navigation
3. Fill in the form:
   - **Title**: Brief description, e.g. "Large pothole near bus stop"
   - **Description**: Details – how long, how big, safety risk
   - **Category**: Select the most relevant type
   - **Photo**: Upload 1–3 images (JPEG/PNG; max 20MB each)
   - **Location**: Allow browser GPS access, or enter pincode/landmark
4. Click **"Submit Report"**

The AI processes your report in ~3-5 seconds:
- Detects and classifies the issue
- Assigns a severity level
- Finds any nearby duplicates
- Generates a public action report

### Tracking Your Report

- Go to **Dashboard** → see all your reports with status badges
- Click any report to open **Issue Details**:
  - Status timeline (Open → In Progress → Resolved)
  - AI analysis results
  - Duplicate reports at the same location
  - Officer notes and resolution date

### Understanding Severity Levels

| Level | Meaning | Expected Response Time |
|---|---|---|
| LOW | Minor; can wait for routine maintenance | 14 days |
| MEDIUM | Moderate impact on daily life | 7 days |
| HIGH | Significant risk; urgent action needed | 72 hours |
| CRITICAL | Immediate safety risk; emergency response | 24 hours |

### Verifying Repairs

After an officer marks your issue as resolved:
1. Visit the **Issue Details** page
2. Click **"Upload After Photo"** – take a fresh photo of the repaired spot
3. The AI compares before/after automatically
4. If the comparison is uncertain, an officer will review manually
5. Final verdict: LIKELY FIXED / PARTIALLY FIXED / NOT FIXED

---

## For Officers

### Daily Workflow

1. **Dashboard** → filter by your ward, sort by severity (CRITICAL first)
2. **Open issues** → review AI-detected category and severity confidence
3. **Assign** → change status to "In Progress" and add a work order note
4. **Verify** → when a repair photo is submitted, check the before/after comparison
5. **Approve or Reject** → AI verdicts above 0.75 are auto-approved; below go to your review queue

### Verification Review Queue

Navigate to **Repair Verification** → "Human Review Queue"

For each pending item:
- Slide the Before/After viewer to compare
- Check the SSIM score and edge reduction metrics
- Add your officer note explaining the decision
- Click **Approve** (marks as confirmed_fixed) or **Reject** (reopens the issue)

### Geographic Intelligence

- **Map view**: All issues plotted on the city map
- **Hotspots**: Clusters where issues are frequent (high risk score)
- **Ward performance**: Resolution rate by ward; average days to fix
- **Nearby search**: Click any point to see issues within 300m radius

---

## Tips for Better AI Accuracy

- Take photos from a similar angle as the original report (for after-photos)
- Include a recognizable landmark in the frame
- Avoid blurry images or strong backlighting
- Write descriptive titles – not just "Pothole"
- Include the approximate size if you know it (e.g. "60cm wide depression")

---

## Privacy and Data

- Images: EXIF metadata (including GPS) is stripped automatically on upload
- Location: Public map shows coordinates rounded to ~111m precision
- Reports: Never identify or accuse individuals
- Your data is never sold or shared with third parties
