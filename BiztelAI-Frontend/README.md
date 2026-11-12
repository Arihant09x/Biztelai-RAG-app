# PlantAssist AI — Manufacturing Knowledge Copilot (Frontend)

**PlantAssist AI** is an operational intelligence and SOP reference interface designed for manufacturing plant supervisors and shop floor operators. Grounded in factory standard operating procedures (SOPs), machinery maintenance manuals, and safety guidelines.

Built with **React 18**, **TypeScript (Strict Mode)**, **Vite**, **Tailwind CSS**, **shadcn/ui**, **TanStack Query**, **PDF.js**, **Recharts**, **Mermaid**, **Zustand**, and **Lucide Icons**.

---

## 🎨 Industrial Design System (Anti-Slop Craft)

Designed following the **Frontend Anti-Slop Principles** from `.agent/skills/frontend`:
- **Primary Color**: **Deep Precision Slate** (`#090A0F` dark / `#F8FAFC` light, `#111318` card surfaces, quiet hairlines).
- **Secondary / Accent**: **Safety Amber / Signal Gold** (`#F59E0B` dark / `#D97706` light) — the universal industrial color for machinery status, calibrated tolerances, caution alerts, and focus rings.
- **Zero AI-Slop Tells**: No purple-to-blue gradients, no sparkles icons, no glowing or pulsing blobs, no generic chatbot copy.
- **Precision Typography & Layout**: 4px baseline rhythm, tabular monospace figures for engineering specs (`SOP-305`, `±0.02 mm`, `450 bar`), and high-contrast legible typography.

---

## 🚀 Quick Start

### 1. Prerequisites
- Backend running on `http://localhost:5000` (run `python run.py` from repository root)
- Node.js v18+ and npm installed

### 2. Development Mode
From the `BiztelAI-Frontend` directory:
```bash
npm run dev
```
The application will launch at: **`http://localhost:3000`**

### 3. Production Build
```bash
npm run build
npm run preview
```

---

## 🔑 1-Click Demo Profiles

| Profile | Credentials | Scope & Permissions |
|---|---|---|
| **Supervisor** | `supervisor@biztelai.com` / `Password123!` | Full factory scope, upload SOPs, inspect pages, manage repository |
| **Admin** | `admin@biztelai.com` / `Password123!` | System administration, pgvector telemetry, audit logs |
| **Operator** | `operator@biztelai.com` / `Password123!` | Shop floor access, execute interactive checklists, view procedures |

---

## ⚡ Core Architecture & Features

### 1. assistant-ui & shadcn/ui Chat Experience
- **Grounded Message Turns**: Every response is anchored in verified SOP passages with citation cards.
- **Real-Time Telemetry Readout**: Header & status pills showing active pgvector connection, model latency, and match confidence.
- **Interactive Floor Checklists**: Line operators can check off operational verification items in real-time.
- **Critical Safety Callouts**: Industrial `DANGER`, `WARNING`, and `CAUTION` banners with hazard icons.
- **Mermaid Process Flows**: Inline decision trees and machinery troubleshooting flowcharts.
- **Feedback Loop**: Positive/negative response feedback with discrepancy reporting.

### 2. PDF.js Live Canvas Document Viewer (`PDFViewer.tsx`)
- High-fidelity PDF page rendering directly onto an HTML `<canvas>` powered by `pdfjs-dist`.
- Pan, zoom controls (60% to 250%), fit-to-width, previous/next page navigation.
- Clicking any citation in chat opens the **Source Drawer** directly on that exact cited page!

### 3. Recharts Machine Data Visualizations (`NumericalChartBlock.tsx`)
- Contextual numerical charts rendered when technical questions discuss machine tolerances or operating pressures:
  - **Operating Pressure Curves**: Line chart tracking hydraulic press HP-500 cycle pressure vs 400 bar nominal and 450 bar safety cutoff.
  - **Tolerance Deviation Bands**: Bar chart tracking caliper measurements against ±0.02 mm tolerance limits.

### 4. TanStack Query API State Management
- Automated query caching, deduplication, and background refetching for SOP documents and conversation threads.

### 5. SOP Document Management (`DocumentLibrary.tsx`)
- Drag-and-drop PDF upload with automatic category classification (`Operations`, `Safety`, `Maintenance`, `Quality`).
- Real-time ingestion progress tracking polling background Celery/Redis vectorization jobs.
