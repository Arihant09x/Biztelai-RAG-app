# PlantAssist SOP Copilot — Design Thinking & Reflection

> **Assessment:** BiztelAI Technologies  
> **Stack:** FastAPI, React/Frontend, Neon PostgreSQL (pgvector), Groq LLM  

---

## 1. Understand the User

### Who the Supervisor Is
The primary user is a **Shift Supervisor** on the machining floor (such as the shaft machining line at Kaveri Precision Components' Hosur plant). They manage 6–15 machine operators, keep production on schedule, handle minor machine alarms, verify incoming quality holds, and enforce safety rules like Lockout/Tagout (LOTO).

### What They Are Trying to Do
During an 8-to-12 hour shift, supervisors rarely sit at a desk. They are walking the floor with a phone or tablet and need **fast, exact answers** to unblock work safely:
- Confirming operating limits (e.g., coolant concentration or spindle runout on a TX-200 CNC)[cite: 1].
- Checking what an alarm code means so they know whether an operator can reset it or if maintenance must be called[cite: 1, 2].
- Verifying latest inspection rules (like sampling counts for BH-220 bearing housings) or LOTO escalation steps when a lock owner goes home[cite: 4, 6].

### What Frustrates Them Today
- **Hunting through binders and shared drives:** Printed copies on the floor get greasy or outdated (the PDFs literally warn *"Uncontrolled copy when printed"*[cite: 1, 3, 4, 6]), while searching folders on a phone is slow.
- **Outdated document revisions:** Having both `QC-SOP-014 Rev 03` and `Rev 04` in circulation creates real risk—using Rev 03's old rule (5 samples for every lot[cite: 3]) instead of Rev 04's lot-size table[cite: 4] causes audit failures.
- **No patience for long answers:** Standing beside a noisy CNC machine wearing gloves, a supervisor doesn't want three paragraphs of polite AI fluff. They want the exact number, step, or warning, plus proof of which SOP it came from.

### Explicit Assumptions Made
- **Mobile-first ergonomics:** Supervisors use phones/tablets with gloved or oily hands, so buttons and citations need large tap targets (≥44px) and high-contrast text.
- **Spotty shop-floor Wi-Fi:** Metal machinery and concrete walls cause brief signal drops, so payloads must stay lightweight and failures must fail gracefully.
- **Zero-guesswork rule:** Guessing a torque spec or safety step on a factory floor can injure someone. If the answer isn't in the uploaded SOPs, the app must strictly refuse to guess.

---

## 2. User Journey

### Step-by-Step Flow (First Draft)
1. **Trigger:** During the morning shift on the shaft machining line, CNC-05 stops with alarm **AL-104**[cite: 1, 2].
2. **Open App:** The supervisor pulls out their phone on plant Wi-Fi and opens the copilot web app.
3. **Ask Question:** They tap a quick-prompt chip or type: *"TX-200 alarm AL-104 what should operator do?"*
4. **Search & Grounding:** The backend embeds the query, searches `pgvector` across the indexed SOPs, and retrieves Page 2 of `MNT-MAN-CNC-02`[cite: 2].
5. **Read Answer:** The screen shows a direct answer: *AL-104 means Way lube oil level low. Top up with ISO VG 68 oil to the MAX mark, then press RESET[cite: 2].*
6. **Verify Source:** The supervisor taps the source citation (`MNT-MAN-CNC-02, Rev 02, Page 2`) to verify the exact text before instructing the operator[cite: 2].
7. **Action:** The operator tops up the ISO VG 68 oil, resets the alarm, and resumes production[cite: 2].

### What Could Go Wrong
- **Asking about undocumented equipment:** The supervisor asks about a machine or PPE rule not in the 4 PDFs (e.g., shop-floor decibel limits). If the LLM relies on pretraining data, it will hallucinate a plausible-sounding OSHA number.
- **Retrieving a superseded revision:** The supervisor asks where to put rejected incoming parts. If the retriever pulls `QC-SOP-014 Rev 03` (*"Red Bin area near Gate 2"*[cite: 3]) instead of `Rev 04` (*"Quarantine Cage Q1, Stores Bay 3"*[cite: 4, 5]), the floor team follows an obsolete procedure.
- **Ambiguous questions:** Typing *"What is the normal pressure?"* could refer to TX-200 hydraulic pressure (`3.5–4.0 MPa`), chuck clamping pressure (`2.0–2.5 MPa`), or compressed air (`5.5–6.5 bar`)[cite: 1].
- **Tiny UI on a phone screen:** Multi-megabyte PDFs crashing mobile browsers or tiny citation links being hard to tap with gloves.

---

## 3. AI Challenge

I asked an AI acting as a skeptical plant operations manager to critique my initial user journey.

### Key Conversation Excerpts
> **Skeptical PM:** *"Your journey assumes the supervisor reads a chat paragraph and trusts it. On a loud shop floor, nobody reads walls of text. Also, you have both Rev 03 and Rev 04 of QC-SOP-014 in the folder—what happens when a supervisor asks about incoming inspection? And if you load full PDFs on a phone over weak Wi-Fi, it's going to lag."*

> **My Response:** *"Good catch on the revisions—if both are indexed equally, cosine search might pull Rev 03 because the phrasing matches closely. I should track document revisions at ingestion or enforce latest-version priority, and format answers as scannable steps/callouts instead of chat paragraphs."*

> **Skeptical PM:** *"What if they need to see the actual table or drawing in the PDF, not just extracted text?"*

> **My Response:** *"Instead of removing PDF viewing or downloading the whole file upfront, I can stream only the requested page on demand when they tap 'Inspect PDF'."*

### Reflection: Agreed, Disagreed & Changed
- **What I Agreed With:**
  1. Conversational paragraphs don't work on a factory floor—answers need structured blocks (Safety Alerts, numbered steps, and spec tables).
  2. Superseded documents (`Rev 03` vs `Rev 04`[cite: 3, 4]) are a real trap that retrieval must handle explicitly.
  3. Strict similarity thresholds (`≥ 0.55`) plus an abstention state are mandatory so the bot never guesses.
- **What I Disagreed With:**
  - The AI suggested stripping out PDF viewing completely on mobile and only showing raw text snippets. I disagreed because quality specs (like the BH-220 dimension table in `QC-SOP-014 Rev 04`[cite: 5]) lose alignment in plain text, and supervisors need to visually confirm the signed document header. Instead, I kept the PDF viewer but used HTTP byte-range streaming so phones only load the single page needed.
- **What I Changed in the Journey:**
  - Added an **evidence-check gate** before rendering answers (triggering a clear *"Insufficient Document Grounding"* warning when similarity is too low).
  - Replaced plain text replies with **Guided Procedure cards** and interactive verification checkboxes.

---

## 4. The Improvement Added & Why I Chose It

### What I Built: Guided Procedure Mode + Interactive Checklists
Instead of a standard chatbot bubble, responses are parsed into structured industrial cards:
1. **Safety / PPE Callout Banner:** Highlights mandatory warnings (such as LOTO isolation[cite: 1, 6]) at the top of the answer.
2. **Interactive Step Checklists:** Procedural steps render with large, tap-friendly checkboxes so a supervisor can tick off each check physically at the machine (e.g., confirming pressure gauge reads zero before loosening a hydraulic fitting[cite: 2]).
3. **One-Tap Audit & Handover Copy:** A **"Copy Procedure"** button formats the verified steps and source document citation so it can be pasted directly into a shift handover log.
4. **Page-Level PDF Citation Drawer:** Tapping a citation opens the exact source PDF page right inside the app to verify tables and revision numbers.

### Why I Chose It
In manufacturing, reading an SOP is only half the job—making sure no step gets skipped under time pressure is what prevents accidents and scrap parts. Turning static PDF text into a checkable, source-linked workflow directly solves the supervisor's need for speed, glove-friendly interaction, and audit traceability.

---

## 5. Final Reflection

### What I'd Build Next
- **Automatic Revision Archiving:** Parse `Document No.` and `Revision` on upload so newer revisions (like `Rev 04`) automatically mark older revisions (`Rev 03`) inactive during search while keeping them archived for audit history[cite: 3, 4].
- **Offline PWA Caching:** Cache the top 20 critical SOPs and LOTO procedures in the browser's Service Worker so supervisors can still view them in Wi-Fi dead zones.
- **Voice-to-Text Input:** Add push-to-talk speech input for hands-free queries when holding tools or gauges.

### What I'm Unsure About
- **Complex Engineering Drawings:** `PyMuPDF` extracts text and basic tables well, but dense CAD schematics or multi-column tolerance callouts in larger OEM manuals may require layout-aware vision parsing.
- **Multilingual Queries:** Many shop-floor teams switch between English and local languages (e.g., Tamil/Kannada/Hindi); translating technical terms without distorting tolerances needs careful testing.

### Questions I Would Ask the Customer
1. *"How are SOP revisions currently managed—do filenames always follow a standard convention like `Rev04`, or do we need to parse revision tables inside the PDF?"*
2. *"Do supervisors need role-based views (e.g., Operator vs. Maintenance Technician vs. Shift Supervisor) for actions like LOTO lock removal?"*
3. *"What does the plant's Wi-Fi coverage look like near heavy CNC bays, and do devices stay on an internal LAN without internet access?"*

### Biggest Challenges Faced & How I Handled Them
1. **Windows IPv6 DNS Timeout with Cloud PostgreSQL:**
   - *Challenge:* Connecting from my Windows laptop to Neon PostgreSQL intermittently failed with `getaddrinfo failed` due to IPv6 DNS resolution delays.
   - *Fix:* Added an IPv4 socket pre-resolution hook (`socket.AF_INET`) during app startup so database connections resolve reliably every time.
2. **Keeping LLM JSON Outputs Crash-Proof:**
   - *Challenge:* Requiring structured blocks (`callout`, `steps`, `checklist`, `table`) occasionally caused frontend errors when the LLM omitted a field or renamed a key.
   - *Fix:* Built a defensive block normalizer on the backend and a safe fallback renderer in the UI so malformed JSON never breaks the supervisor's screen.
3. **Mobile PDF Loading over Local Wi-Fi:**
   - *Challenge:* Testing from my phone over local Wi-Fi (`0.0.0.0`) initially struggled with loading full PDFs inside PDF.js.
   - *Fix:* Enabled HTTP `Accept-Ranges: bytes` streaming on the document endpoint so mobile browsers only fetch the specific page requested.