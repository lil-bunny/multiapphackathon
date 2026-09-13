from app.core.logger import get_logger
from app.domain.state import WorkflowState
from app.services.reply_classification_service import ReplyClassificationService
from app.tools import mail as mail_tools

logger = get_logger(__name__)


def classify_email_reply(state: WorkflowState) -> WorkflowState:
    data = state.data
    thread_id = str(data.get("thread_id") or "").strip()
    if not thread_id:
        state.data["workflow_error"] = "missing_thread_id"
        return state

    messages = mail_tools.fetch_thread_messages(
        thread_id=thread_id,
        account_id=data.get("account_id"),
        fixture_messages=data.get("fixture_thread_messages"),
    )
    thread_text = mail_tools.thread_text_for_llm(messages)
    result = ReplyClassificationService().classify(
        thread_text,
        fixture_result=data.get("fixture_classification"),
    )
    state.data["reply_intent"] = result["intent"]
    state.data["classification"] = result
    logger.info("classified thread_id=%s intent=%s", thread_id, result["intent"])
    return state
