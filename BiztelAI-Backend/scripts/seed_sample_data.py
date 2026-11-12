#!/usr/bin/env python3
"""Database Seeder and Sample SOP Generator.

Initializes database schema, seeds default roles and supervisor accounts,
generates realistic manufacturing SOP PDFs, and indexes them into the vector database.
"""

import os
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv
load_dotenv(ROOT_DIR / ".env")

import pymupdf  # fitz
from app import create_app
from app.constants import DocumentStatus, IngestionStatus, UserRole
from app.extensions import db
from app.models.document import Document, DocumentChunk, DocumentPage, DocumentVersion
from app.models.ingestion import IngestionJob
from app.models.user import Permission, Role, User
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.pdf_extraction_service import PDFExtractionService
from app.services.storage_service import StorageService
from app.utils.security import compute_sha256, hash_password


SOP_DEFINITIONS = [
    {
        "filename": "SOP-101-CNC-Spindle-Maintenance.pdf",
        "title": "CNC Spindle Maintenance and Bearing Lubrication",
        "category": "Maintenance",
        "department": "Machining",
        "pages": [
            (
                "SECTION 1: PURPOSE AND SCOPE\n"
                "This Standard Operating Procedure defines the routine inspection, lubrication, and preventive maintenance "
                "for all 5-axis CNC machining center spindles (Model CNC-500).\n\n"
                "[SAFETY WARNING]\n"
                "MANDATORY PPE: Safety glasses with side shields, hearing protection (minimum NRR 25 dB), and steel-toe safety footwear. "
                "Do NOT wear gloves, loose clothing, or jewelry while operating or inspecting rotating machinery.\n\n"
                "SECTION 2: PRE-OPERATION CHECKS\n"
                "1. Verify that the pneumatic lock pressure is maintained at exactly 50 PSI (3.45 bar).\n"
                "2. Inspect spindle coolant temperature gauge. Ensure cooling fluid temperature is stabilized between 18°C and 22°C.\n"
                "3. Check the lubrication oil reservoir level. Top up with Mobil Vactra No. 2 spindle oil if below minimum mark."
            ),
            (
                "SECTION 3: DAILY SPINDLE MAINTENANCE PROCEDURE\n"
                "1. Turn off main spindle motor and wait 60 seconds for complete rotation cessation.\n"
                "2. Engage emergency stop (E-STOP) button before opening safety enclosure door.\n"
                "3. Wipe spindle taper clean using lint-free industrial wipes and approved solvent.\n"
                "4. Check runout using digital dial indicator. Total indicated runout (TIR) must not exceed 0.005 mm.\n"
                "5. Release E-STOP, close enclosure, and run spindle warmup cycle at 2000 RPM for 10 minutes.\n\n"
                "SECTION 4: VERIFICATION CHECKLIST\n"
                "• Pneumatic pressure at 50 PSI verified.\n"
                "• Spindle coolant level and temperature (18-22°C) verified.\n"
                "• Taper clean and free of metal chips.\n"
                "• Spindle runout within 0.005 mm tolerance verified."
            ),
        ],
    },
    {
        "filename": "SOP-204-Emergency-Lockout-Tagout.pdf",
        "title": "Hazardous Energy Control (Lockout / Tagout) Procedure",
        "category": "Safety",
        "department": "Plant Safety",
        "pages": [
            (
                "SECTION 1: SCOPE AND REGULATORY MANDATE\n"
                "In compliance with OSHA 1910.147 and plant safety directives, all personnel servicing electrical, pneumatic, "
                "or hydraulic machinery must execute Lockout / Tagout (LOTO) prior to servicing.\n\n"
                "[SAFETY WARNING]\n"
                "DANGER: High Voltage (480V 3-Phase). Arc flash and electrocution hazard. Never attempt maintenance without verified zero energy state!\n\n"
                "SECTION 2: LOCKOUT TAGOUT SEQUENCE\n"
                "1. Notify affected machine operators and plant supervisors before initiating shutdown.\n"
                "2. Turn off local machine operating switch and allow moving parts to coast to rest.\n"
                "3. Move to the main electrical disconnect switch located at electrical cabinet E-204.\n"
                "4. Switch disconnect handle to OFF position.\n"
                "5. Affix personal red safety padlock and completed danger tag through the lockout hasp."
            ),
            (
                "SECTION 3: STORED ENERGY DISSIPATION AND ZERO ENERGY VERIFICATION\n"
                "1. Release residual pneumatic pressure by turning the dump valve to EXHAUST.\n"
                "2. Dissipate hydraulic accumulator pressure by opening manual bleed screw.\n"
                "3. Verify zero energy state: Attempt to start machine using start push-button on operating panel.\n"
                "4. Verify machine remains completely de-energized.\n"
                "5. Return operating switch to OFF position.\n"
                "6. Test conductors using calibrated CAT-IV 600V digital multimeter to confirm zero voltage."
            ),
        ],
    },
    {
        "filename": "SOP-305-Hydraulic-Press-Safety.pdf",
        "title": "Hydraulic Stamping Press Safety and Operating Procedure",
        "category": "Operations",
        "department": "Forming",
        "pages": [
            (
                "SECTION 1: MACHINE SPECIFICATIONS\n"
                "This SOP governs the 200-ton hydraulic stamping press (Unit HP-200). "
                "Operating limits:\n"
                "- Maximum hydraulic operating pressure: 180 bar (2600 PSI).\n"
                "- Hydraulic oil grade: ISO VG 46 anti-wear hydraulic oil.\n"
                "- Maximum ambient operating temperature: 45°C.\n\n"
                "[SAFETY WARNING]\n"
                "CRUSH HAZARD: Keep hands clear of die tooling area during cycle. Dual palm anti-tie-down buttons must never be bypassed or taped down."
            ),
            (
                "SECTION 2: DAILY SAFETY INTERLOCK TEST\n"
                "1. Verify light curtain alignment. Green indicator must be steady.\n"
                "2. Obstruct light curtain beam with test rod; verify press ram stops immediately within 50 milliseconds.\n"
                "3. Test dual palm buttons: Press ram must only advance when both buttons are pressed simultaneously within 0.5 seconds.\n"
                "4. Inspect hydraulic hoses, valves, and manifold for fluid leaks. Ensure oil pressure gauge does not exceed 180 bar."
            ),
        ],
    },
    {
        "filename": "SOP-402-Quality-Inspection-Calipers.pdf",
        "title": "Digital Vernier Caliper Calibration and Quality Verification",
        "category": "Quality",
        "department": "Quality Assurance",
        "pages": [
            (
                "SECTION 1: APPLICABILITY AND STANDARDS\n"
                "Applies to all Mitutoyo digital vernier calipers used in machining inspection according to ISO-9001 standard.\n\n"
                "SECTION 2: CALIBRATION PROCEDURE\n"
                "1. Clean outside measuring jaws with isopropyl alcohol.\n"
                "2. Close jaws gently and press ZERO button to establish datum.\n"
                "3. Using Grade 0 calibration gauge blocks (10.00 mm, 25.00 mm, 50.00 mm), measure outside dimensions.\n"
                "4. Measurement tolerance limit must remain within ±0.02 mm.\n"
                "5. Record calibration log in QA database."
            ),
        ],
    },
]


def create_pdf(file_path: Path, pages: list[str], title: str) -> None:
    """Generate a valid PDF file with multiple pages using PyMuPDF."""
    doc = pymupdf.open()
    for text_content in pages:
        page = doc.new_page(width=595, height=842)  # A4 size
        # Add Header banner
        page.draw_rect(pymupdf.Rect(40, 30, 555, 60), color=(0.2, 0.4, 0.7), fill=(0.9, 0.95, 1.0))
        page.insert_text((50, 50), title, fontsize=12, fontname="helv", color=(0.1, 0.2, 0.5))
        # Insert body text
        page.insert_textbox(pymupdf.Rect(40, 80, 555, 780), text_content, fontsize=10, fontname="helv")
    doc.save(str(file_path))
    doc.close()


def seed_database(use_sqlite: bool = False):
    if use_sqlite:
        sqlite_path = (ROOT_DIR / "data" / "biztelai_sop.db").resolve()
        os.environ["DATABASE_URL"] = f"sqlite:///{sqlite_path}"
        os.environ["APP_ENV"] = "development"

    app = create_app()

    with app.app_context():
        import app.models  # Ensure all model tables are registered
        print("Creating database tables...")
        db.create_all()

        # 1. Seed Roles
        roles_data = [
            (UserRole.ADMIN.value, "System Administrator with full access"),
            (UserRole.SUPERVISOR.value, "Manufacturing Supervisor with upload & procedure rights"),
            (UserRole.OPERATOR.value, "Plant Operator with read and query rights"),
            (UserRole.AUDITOR.value, "Compliance Auditor with read-only audit access"),
        ]
        role_map = {}
        for r_name, r_desc in roles_data:
            role = Role.query.filter_by(name=r_name).first()
            if not role:
                role = Role(name=r_name, description=r_desc)
                db.session.add(role)
                db.session.flush()
            role_map[r_name] = role

        # 2. Seed Default Users
        supervisor = User.query.filter_by(email="supervisor@biztelai.com").first()
        if not supervisor:
            supervisor = User(
                email="supervisor@biztelai.com",
                password_hash=hash_password("Password123!"),
                full_name="John Doe (Supervisor)",
                department="Machining",
                role_id=role_map[UserRole.SUPERVISOR.value].id,
                is_active=True,
            )
            db.session.add(supervisor)

        admin = User.query.filter_by(email="admin@biztelai.com").first()
        if not admin:
            admin = User(
                email="admin@biztelai.com",
                password_hash=hash_password("AdminSecret123!"),
                full_name="System Administrator",
                department="IT",
                role_id=role_map[UserRole.ADMIN.value].id,
                is_active=True,
            )
            db.session.add(admin)

        db.session.commit()
        print("Default roles and users seeded.")

        # 3. Generate and Ingest Sample SOP PDFs
        sops_dir = ROOT_DIR / "sample_data" / "sops"
        sops_dir.mkdir(parents=True, exist_ok=True)

        storage = StorageService()
        pdf_extractor = PDFExtractionService()
        chunker = ChunkingService(target_chunk_tokens=700, overlap_tokens=100)
        embedding_service = EmbeddingService()

        for sop in SOP_DEFINITIONS:
            pdf_path = sops_dir / sop["filename"]
            create_pdf(pdf_path, sop["pages"], sop["title"])
            print(f"Generated PDF: {sop['filename']}")

            with open(pdf_path, "rb") as f:
                sha256 = compute_sha256(pdf_path)
                existing_doc = Document.query.filter_by(sha256_hash=sha256, is_deleted=False).first()
                if existing_doc:
                    print(f"Document '{sop['title']}' already indexed. Skipping.")
                    continue

                stored_fn, clean_name, file_size, _ = storage.save_file(f, sop["filename"])

                doc = Document(
                    title=sop["title"],
                    original_filename=clean_name,
                    stored_filename=stored_fn,
                    file_size_bytes=file_size,
                    sha256_hash=sha256,
                    category=sop["category"],
                    department=sop["department"],
                    status=DocumentStatus.INDEXED.value,
                    created_by_id=supervisor.id,
                )
                db.session.add(doc)
                db.session.flush()

                # Extract and chunk
                extraction_res = pdf_extractor.extract(pdf_path)
                page_id_map = {}
                for p in extraction_res.pages:
                    dp = DocumentPage(
                        document_id=doc.id,
                        page_number=p.page_number,
                        raw_text=p.text,
                        has_ocr=False,
                    )
                    db.session.add(dp)
                    db.session.flush()
                    page_id_map[p.page_number] = dp.id

                chunks = chunker.chunk_document(
                    extraction_res.pages,
                    document_id=str(doc.id),
                    document_title=doc.title,
                    category=doc.category,
                    department=doc.department,
                )

                chunk_texts = [c.content for c in chunks]
                embeddings = embedding_service.provider.embed_texts(chunk_texts)

                for c_obj, emb in zip(chunks, embeddings):
                    dc = DocumentChunk(
                        document_id=doc.id,
                        page_id=page_id_map.get(c_obj.page_number),
                        chunk_index=c_obj.chunk_index,
                        section_heading=c_obj.section_heading,
                        subheading=c_obj.subheading,
                        content=c_obj.content,
                        token_count=c_obj.token_count,
                        embedding=emb,
                        is_active=True,
                        metadata_json=c_obj.metadata,
                    )
                    db.session.add(dc)

                db.session.commit()
                print(f"Successfully indexed '{doc.title}' ({len(chunks)} chunks).")

        print("\n[SUCCESS] Sample manufacturing database seeded successfully!")


if __name__ == "__main__":
    use_sqlite_arg = "--sqlite" in sys.argv or "--local" in sys.argv
    seed_database(use_sqlite=use_sqlite_arg)
