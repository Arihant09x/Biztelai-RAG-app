"""Chat, streaming, and conversation management API endpoints."""

import json
import time
from flask import Blueprint, Response, jsonify, request, stream_with_context
from flask_jwt_extended import jwt_required
from pydantic import ValidationError as PydanticValidationError
from app.api.deps import get_current_user
from app.constants import AuditAction
from app.models.conversation import Conversation, Message
from app.schemas.chat import (
    ChatQueryRequest,
    ConversationCreateRequest,
    ConversationDetailResponse,
    ConversationResponse,
    MessageResponse,
)
from app.schemas.response_blocks import SourceCitation
from app.services.answer_service import AnswerService
from app.services.audit_service import AuditService
from app.services.conversation_service import ConversationService
from app.utils.errors import ValidationError

chat_bp = Blueprint("chat", __name__)
answer_service = AnswerService()
conv_service = ConversationService()


@chat_bp.route("/chat", methods=["POST"])
@jwt_required()
def chat_query():
    """Submit a question to the manufacturing SOP Copilot and receive structured grounded answer."""
    user = get_current_user()
    raw_data = request.get_json() or {}

    try:
        req = ChatQueryRequest.model_validate(raw_data)
    except PydanticValidationError as e:
        raise ValidationError("Chat request validation failed.", details=e.errors())

    start_time = time.time()

    # Resolve or create conversation
    if req.conversation_id:
        conversation = conv_service.get_conversation_authorized(req.conversation_id, user)
    else:
        conversation = conv_service.create_conversation(
            user_id=str(user.id),
            title=req.question[:50],
            department_filter=req.department,
            category_filter=req.category,
        )

    # Load recent conversation turns for context
    history_messages = []
    past_msgs = (
        Message.query.filter_by(conversation_id=conversation.id)
        .order_by(Message.created_at.asc())
        .limit(6)
        .all()
    )
    for m in past_msgs:
        history_messages.append({
            "role": m.sender_type,
            "content": m.content,
        })

    # Generate source-grounded answer
    answer_result = answer_service.generate_answer(
        query=req.question,
        conversation_history=history_messages,
        category=req.category or conversation.category_filter,
        department=req.department or conversation.department_filter,
        document_ids=req.document_ids,
    )

    duration_ms = round((time.time() - start_time) * 1000, 2)

    # Build complete, comprehensive readable markdown text from all blocks
    text_parts = []
    for block in answer_result.response.blocks:
        if block.type == "markdown":
            if block.content and block.content.strip():
                text_parts.append(block.content.strip())
        elif block.type == "callout":
            callout_title = f"**{block.title}**\n\n" if block.title else ""
            text_parts.append(f"> ⚠️ **{block.variant.upper()} ALERT**\n>\n> {callout_title}{block.content.strip()}")
        elif block.type == "steps":
            steps_header = f"### {block.title or 'Execution Procedure'}\n"
            steps_lines = [f"{i+1}. {item.content.strip()}" for i, item in enumerate(block.items)]
            text_parts.append(steps_header + "\n".join(steps_lines))
        elif block.type == "checklist":
            checklist_header = f"### {block.title or 'Verification Checklist'}\n"
            checklist_lines = [f"- [ ] {item.content.strip()}" for item in block.items]
            text_parts.append(checklist_header + "\n".join(checklist_lines))
        elif block.type == "table":
            table_header = f"### {block.title}\n" if block.title else ""
            hdr = "| " + " | ".join(block.headers) + " |"
            sep = "| " + " | ".join(["---"] * len(block.headers)) + " |"
            rows = ["| " + " | ".join(str(c) for c in r) + " |" for r in block.rows]
            text_parts.append(table_header + "\n".join([hdr, sep] + rows))
        elif block.type == "quote":
            text_parts.append(f"> \"{block.quote}\"\n> — *{block.source}*")

    full_answer_text = "\n\n".join(text_parts).strip()
    if not full_answer_text:
        if not answer_result.answerable:
            full_answer_text = "No standard operating procedures or maintenance manuals were found matching your inquiry. The system abstains from providing unverified machinery parameters."
        else:
            full_answer_text = "Procedure retrieved from standard operating documentation."

    answer_dict = answer_result.model_dump()
    answer_dict["answer"] = full_answer_text

    # Persist message turns
    user_msg, asst_msg = conv_service.append_message_turn(
        conversation_id=str(conversation.id),
        user_query=req.question,
        assistant_content=full_answer_text,
        structured_response=answer_dict,
        sources=answer_result.sources,
        token_usage={"total_tokens": 0},
        latency_ms=duration_ms,
        intent=answer_service.classify_intent(req.question).value,
    )

    AuditService.log_event(
        action=AuditAction.CHAT_QUERY.value,
        user_id=str(user.id),
        target_type="conversation",
        target_id=str(conversation.id),
        details={"latency_ms": duration_ms, "answerable": answer_result.answerable},
    )

    return jsonify({
        "success": True,
        "conversation_id": str(conversation.id),
        "message_id": str(asst_msg.id),
        "data": answer_dict,
        "latency_ms": duration_ms,
    }), 200


@chat_bp.route("/chat/stream", methods=["POST"])
@jwt_required()
def chat_stream():
    """Stream response tokens using Server-Sent Events (SSE)."""
    user = get_current_user()
    raw_data = request.get_json() or {}

    try:
        req = ChatQueryRequest.model_validate(raw_data)
    except PydanticValidationError as e:
        raise ValidationError("Chat request validation failed.", details=e.errors())

    def event_stream():
        # First yield status event
        yield f"event: status\ndata: {json.dumps({'stage': 'retrieving_documents'})}\n\n"

        candidates = answer_service.retrieval_service.hybrid_search(
            query=req.question,
            top_k=5,
            department=req.department,
            category=req.category,
        )

        context = answer_service.context_service.engineer_context(chunks=candidates, query=req.question)
        is_answerable, reason = answer_service.validation_service.check_answerability(context, req.question)

        if not is_answerable:
            abstain_res = answer_service.validation_service.create_abstention_response(reason or "Insufficient evidence", req.question)
            yield f"event: result\ndata: {json.dumps(abstain_res.model_dump())}\n\n"
            return

        yield f"event: status\ndata: {json.dumps({'stage': 'generating_answer'})}\n\n"

        # Stream LLM tokens
        provider = answer_service._get_provider()
        prompt_msgs = [
            {"role": "system", "content": "You are BiztelAI Copilot. Answer concisely based on evidence."},
            {"role": "user", "content": f"EVIDENCE:\n{context.context_text}\n\nQUESTION: {req.question}"},
        ]

        try:
            for token in provider.stream_chat_completion(prompt_msgs):
                yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

        yield "event: done\ndata: [DONE]\n\n"

    return Response(stream_with_context(event_stream()), mimetype="text/event-stream")


@chat_bp.route("/conversations", methods=["GET"])
@jwt_required()
def list_conversations():
    """List recent conversation threads for current user."""
    user = get_current_user()
    skip = int(request.args.get("skip", 0))
    limit = min(int(request.args.get("limit", 20)), 50)

    convs = conv_service.list_user_conversations(str(user.id), skip=skip, limit=limit)
    return jsonify({
        "success": True,
        "data": [c.model_dump() for c in convs],
    }), 200


@chat_bp.route("/conversations", methods=["POST"])
@jwt_required()
def create_conversation():
    """Explicitly initialize a new conversation thread."""
    user = get_current_user()
    raw = request.get_json() or {}
    try:
        req = ConversationCreateRequest.model_validate(raw)
    except PydanticValidationError as e:
        raise ValidationError("Conversation creation validation failed.", details=e.errors())

    conv = conv_service.create_conversation(
        user_id=str(user.id),
        title=req.title,
        department_filter=req.department_filter,
        category_filter=req.category_filter,
    )

    return jsonify({
        "success": True,
        "data": {
            "id": str(conv.id),
            "title": conv.title,
            "department_filter": conv.department_filter,
            "category_filter": conv.category_filter,
            "created_at": conv.created_at,
        },
    }), 201


@chat_bp.route("/conversations/<conversation_id>", methods=["GET"])
@jwt_required()
def get_conversation(conversation_id: str):
    """Retrieve full conversation history with message turn details and citations."""
    user = get_current_user()
    conv = conv_service.get_conversation_authorized(conversation_id, user)

    messages = (
        Message.query.filter_by(conversation_id=conv.id)
        .order_by(Message.created_at.asc())
        .all()
    )

    msg_items = []
    for m in messages:
        src_items = []
        for s in m.sources:
            src_items.append(
                SourceCitation(
                    id=s.citation_label or "source",
                    document_id=str(s.document_id),
                    document_title=s.document.original_filename if s.document else "SOP Reference",
                    page_number=s.page_number or 1,
                    snippet=s.snippet,
                    relevance_score=s.relevance_score,
                )
            )
        msg_items.append(
            MessageResponse(
                id=str(m.id),
                sender_type=m.sender_type,
                content=m.content,
                structured_response=m.structured_response_json or {},
                sources=src_items,
                intent=m.intent,
                latency_ms=m.latency_ms,
                created_at=m.created_at,
            )
        )

    return jsonify({
        "success": True,
        "data": {
            "id": str(conv.id),
            "title": conv.title,
            "department_filter": conv.department_filter,
            "category_filter": conv.category_filter,
            "created_at": conv.created_at,
            "messages": [m.model_dump() for m in msg_items],
        },
    }), 200


@chat_bp.route("/conversations/<conversation_id>", methods=["DELETE"])
@jwt_required()
def delete_conversation(conversation_id: str):
    """Archive or soft delete a conversation thread."""
    user = get_current_user()
    conv_service.archive_conversation(conversation_id, user)
    return jsonify({
        "success": True,
        "message": f"Conversation '{conversation_id}' archived.",
    }), 200

