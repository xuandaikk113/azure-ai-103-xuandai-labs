"""Test chuẩn hoá intent của router — thuần, không cần LLM."""

from assistant.router import AssistantRouter


def test_normalize_known_intent():
    assert AssistantRouter.normalize_intent("sales") == "sales"
    assert AssistantRouter.normalize_intent("  Meetings\n") == "meetings"
    assert AssistantRouter.normalize_intent("web.") == "web"
    assert AssistantRouter.normalize_intent("qa please") == "qa"


def test_normalize_unknown_falls_back_to_qa():
    assert AssistantRouter.normalize_intent("khong_biet") == "qa"
    assert AssistantRouter.normalize_intent("") == "qa"
