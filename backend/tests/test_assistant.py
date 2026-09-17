import pytest
from fastapi import HTTPException

from app.config import Settings
from app.routers.assistant import OUT_OF_SCOPE_MESSAGE, chat
from app.schemas import GeneralAssistantMessage, GeneralAssistantRequest
from app.services.openai_service import (
    AssistantNavigation,
    AssistantNavigationTarget,
    GeneralAssistantAnswer,
    ModelResult,
)


def test_assistant_requires_a_user_message_at_the_end() -> None:
    payload = GeneralAssistantRequest(
        messages=[GeneralAssistantMessage(role="assistant", content="Welcome.")]
    )

    with pytest.raises(HTTPException, match="last message"):
        chat(payload, Settings())


def test_assistant_passes_conversation_and_generic_area_to_ai(monkeypatch) -> None:
    captured_messages: list[dict[str, str]] = []
    captured_areas: list[str] = []

    class FakeAssistant:
        def answer_general_question(
            self,
            messages: list[dict[str, str]],
            current_area: str,
        ) -> ModelResult[GeneralAssistantAnswer]:
            captured_messages.extend(messages)
            captured_areas.append(current_area)
            return ModelResult(
                value=GeneralAssistantAnswer(
                    answer="VendorLens requires three document categories."
                ),
                input_tokens=11,
                output_tokens=7,
            )

    monkeypatch.setattr("app.routers.assistant.get_openai_service", lambda: FakeAssistant())
    payload = GeneralAssistantRequest(
        current_area="reviewer_case",
        messages=[
            GeneralAssistantMessage(role="user", content="What should I prepare?"),
            GeneralAssistantMessage(
                role="assistant",
                content="Start with your registration records.",
            ),
            GeneralAssistantMessage(role="user", content="Anything else?"),
        ],
    )

    result = chat(payload, Settings(openai_answer_model="gpt-test"))

    assert captured_messages == [
        message.model_dump() for message in payload.messages
    ]
    assert captured_areas == ["reviewer case"]
    assert "9b043b1e" not in captured_areas[0]
    assert result.related is True
    assert result.links == []
    assert result.run.model == "gpt-test"
    assert result.run.input_tokens == 11
    assert result.run.output_tokens == 7
    assert result.run.redaction_counts == {}


def test_assistant_redacts_pii_before_ai(monkeypatch) -> None:
    captured: list[dict[str, str]] = []

    class FakeAssistant:
        def answer_general_question(
            self,
            messages: list[dict[str, str]],
            _current_area: str,
        ) -> ModelResult[GeneralAssistantAnswer]:
            captured.extend(messages)
            return ModelResult(
                value=GeneralAssistantAnswer(
                    answer="Use the portal's secure upload flow."
                ),
                input_tokens=1,
                output_tokens=1,
            )

    monkeypatch.setattr("app.routers.assistant.get_openai_service", lambda: FakeAssistant())
    payload = GeneralAssistantRequest(
        messages=[
            GeneralAssistantMessage(
                role="user",
                content="Email me at supplier@example.com",
            )
        ]
    )

    result = chat(payload, Settings())

    assert captured[0]["content"] == "Email me at [EMAIL_1]"
    assert result.run.redaction_counts == {"EMAIL": 1}


def test_assistant_rejects_an_oversized_conversation(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.routers.assistant.get_openai_service",
        lambda: pytest.fail("AI should not be called"),
    )
    payload = GeneralAssistantRequest(
        messages=[GeneralAssistantMessage(role="user", content="x" * 2000)] * 6
    )

    with pytest.raises(HTTPException, match="conversation is too long"):
        chat(payload, Settings())


def test_assistant_rejects_supplier_data_questions(monkeypatch) -> None:
    class FakeAssistant:
        def answer_general_question(
            self,
            _messages: list[dict[str, str]],
            _current_area: str,
        ) -> ModelResult[GeneralAssistantAnswer]:
            return ModelResult(
                value=GeneralAssistantAnswer(
                    answer="A model-generated supplier answer.",
                    related=False,
                    navigation=[
                        AssistantNavigation(
                            target=AssistantNavigationTarget.REVIEW_QUEUE,
                            label="Should not appear",
                        )
                    ],
                ),
                input_tokens=1,
                output_tokens=1,
            )

    monkeypatch.setattr("app.routers.assistant.get_openai_service", lambda: FakeAssistant())
    payload = GeneralAssistantRequest(
        messages=[
            GeneralAssistantMessage(
                role="user",
                content="Give me this customer's contact number.",
            )
        ]
    )

    result = chat(payload, Settings())

    assert result.answer == OUT_OF_SCOPE_MESSAGE
    assert result.related is False
    assert result.links == []


def test_assistant_rejects_unrelated_questions(monkeypatch) -> None:
    class FakeAssistant:
        def answer_general_question(
            self,
            _messages: list[dict[str, str]],
            _current_area: str,
        ) -> ModelResult[GeneralAssistantAnswer]:
            return ModelResult(
                value=GeneralAssistantAnswer(
                    answer="An unsafe off-topic answer.",
                    related=False,
                ),
                input_tokens=1,
                output_tokens=1,
            )

    monkeypatch.setattr("app.routers.assistant.get_openai_service", lambda: FakeAssistant())
    payload = GeneralAssistantRequest(
        messages=[GeneralAssistantMessage(role="user", content="Who won the match?")]
    )

    result = chat(payload, Settings())

    assert result.answer == OUT_OF_SCOPE_MESSAGE
    assert result.related is False


def test_assistant_resolves_only_static_project_navigation(monkeypatch) -> None:
    class FakeAssistant:
        def answer_general_question(
            self,
            _messages: list[dict[str, str]],
            _current_area: str,
        ) -> ModelResult[GeneralAssistantAnswer]:
            return ModelResult(
                value=GeneralAssistantAnswer(
                    answer="Use these VendorLens areas.",
                    navigation=[
                        AssistantNavigation(
                            target=AssistantNavigationTarget.CREATE_CASE,
                            label="Create case",
                        ),
                        AssistantNavigation(
                            target=AssistantNavigationTarget.REVIEW_QUEUE,
                            label="Review queue",
                        ),
                    ],
                ),
                input_tokens=1,
                output_tokens=1,
            )

    monkeypatch.setattr("app.routers.assistant.get_openai_service", lambda: FakeAssistant())
    payload = GeneralAssistantRequest(
        messages=[
            GeneralAssistantMessage(
                role="user",
                content="Where do I create and review cases?",
            )
        ]
    )

    result = chat(payload, Settings())

    assert [link.path for link in result.links] == ["/supplier/new", "/reviewer"]
