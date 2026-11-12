"""Integration tests for document upload, duplicate rejection, and management."""

import io
import pytest


def test_upload_pdf_success(client, supervisor_auth_headers, sample_pdf_bytes):
    data = {
        "file": (io.BytesIO(sample_pdf_bytes), "CNC_Spindle_Manual.pdf"),
        "title": "CNC Spindle Operating Guide",
        "category": "Maintenance",
        "department": "Machining",
    }
    res = client.post(
        "/api/v1/documents/upload",
        data=data,
        content_type="multipart/form-data",
        headers=supervisor_auth_headers,
    )
    assert res.status_code == 202
    resp_data = res.get_json()
    assert resp_data["success"] is True
    assert "document" in resp_data["data"]
    assert resp_data["data"]["document"]["title"] == "CNC Spindle Operating Guide"


def test_upload_duplicate_rejection(client, supervisor_auth_headers, sample_pdf_bytes):
    # First upload
    data1 = {
        "file": (io.BytesIO(sample_pdf_bytes), "File1.pdf"),
        "title": "Original Doc",
    }
    client.post("/api/v1/documents/upload", data=data1, content_type="multipart/form-data", headers=supervisor_auth_headers)

    # Second upload with identical PDF content
    data2 = {
        "file": (io.BytesIO(sample_pdf_bytes), "File2.pdf"),
        "title": "Duplicate Doc",
    }
    res = client.post("/api/v1/documents/upload", data=data2, content_type="multipart/form-data", headers=supervisor_auth_headers)
    assert res.status_code == 409
    assert "Duplicate document detected" in res.get_json()["error"]["message"]


def test_upload_non_pdf_rejection(client, supervisor_auth_headers):
    fake_file = io.BytesIO(b"Hello world, I am plain text not a PDF")
    res = client.post(
        "/api/v1/documents/upload",
        data={"file": (fake_file, "fake.pdf")},
        content_type="multipart/form-data",
        headers=supervisor_auth_headers,
    )
    assert res.status_code == 400
    assert "not a valid PDF document" in res.get_json()["error"]["message"]


def test_operator_upload_forbidden(client, operator_auth_headers, sample_pdf_bytes):
    data = {"file": (io.BytesIO(sample_pdf_bytes), "test.pdf")}
    res = client.post("/api/v1/documents/upload", data=data, content_type="multipart/form-data", headers=operator_auth_headers)
    # Operators are forbidden from uploading; supervisor or admin required
    assert res.status_code == 403


def test_get_document_file_endpoint(client, supervisor_auth_headers, sample_pdf_bytes):
    data = {
        "file": (io.BytesIO(sample_pdf_bytes), "Download_Test.pdf"),
        "title": "Download Test Document",
    }
    upload_res = client.post("/api/v1/documents/upload", data=data, content_type="multipart/form-data", headers=supervisor_auth_headers)
    assert upload_res.status_code == 202
    doc_id = upload_res.get_json()["data"]["document"]["id"]

    # Test file retrieval with Authorization header
    res = client.get(f"/api/v1/documents/{doc_id}/file", headers=supervisor_auth_headers)
    assert res.status_code == 200
    assert res.mimetype == "application/pdf"
    assert res.headers.get("Accept-Ranges") == "bytes"
    assert len(res.data) > 0

    # Test file retrieval with query token param
    token = supervisor_auth_headers["Authorization"].split(" ")[1]
    res_token = client.get(f"/api/v1/documents/{doc_id}/file?token={token}")
    assert res_token.status_code == 200
    assert res_token.mimetype == "application/pdf"
    assert len(res_token.data) > 0


def test_hard_delete_document_success(client, supervisor_auth_headers, sample_pdf_bytes):
    from app.models.document import Document, DocumentChunk, DocumentPage

    data = {
        "file": (io.BytesIO(sample_pdf_bytes), "Delete_Target.pdf"),
        "title": "Document To Hard Delete",
    }
    upload_res = client.post("/api/v1/documents/upload", data=data, content_type="multipart/form-data", headers=supervisor_auth_headers)
    assert upload_res.status_code == 202
    doc_id = upload_res.get_json()["data"]["document"]["id"]

    # Verify document exists in database
    assert Document.query.get(doc_id) is not None

    # Issue DELETE request
    del_res = client.delete(f"/api/v1/documents/{doc_id}", headers=supervisor_auth_headers)
    assert del_res.status_code == 200
    assert del_res.get_json()["success"] is True

    # Verify document is PERMANENTLY hard-deleted from DB
    assert Document.query.get(doc_id) is None
    # Verify child records cascaded
    assert DocumentChunk.query.filter_by(document_id=doc_id).count() == 0
    assert DocumentPage.query.filter_by(document_id=doc_id).count() == 0

