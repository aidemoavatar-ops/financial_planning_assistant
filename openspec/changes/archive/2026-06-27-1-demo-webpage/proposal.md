# Proposal: Demo Webpage with Embedded Atlas Chat Widget

**Issue:** #1
**Branch:** `feature/1-demo-webpage`

## Problem

Atlas has no web interface. Stakeholders cannot demonstrate or evaluate the assistant without custom development.

## Solution

A single-file `demo/index.html` that loads the CCAI Chat Messenger SDK (v1.16) and initializes the Atlas widget with the existing GECX deployment. No build process required.

## Non-goals

- Mobile optimisation
- Backend changes
- Authentication beyond the token broker already configured on the deployment

## Implementation

- `demo/index.html` — self-contained HTML file embedding the Chat Messenger widget
- SDK loaded from Google's CDN at v1.16
- Region `eu`, deployment ID `e882a97d-e670-4e73-954e-11532b79f0cc`
- Display name: "Financial Advisor"; Conversational Agents branding
- Features enabled: file upload, audio input
- Titlebar controls: Reset, Expand/Collapse, Close
- URL allowlist set permissively for demo use
