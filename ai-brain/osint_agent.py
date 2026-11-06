"""LangGraph OSINT agent that classifies alerts and posts them to Heimdall."""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Optional, TypedDict

from langchain_groq import ChatGroq
from langgraph.graph import END, START, StateGraph
from object_classes import normalize_object_class
from osint_client import HeimdallAPIClient, HeimdallAPIError
from pydantic import BaseModel, Field, field_validator


class OsintAgentError(Exception):
    """Raised when the OSINT agent cannot be constructed or run.

    Covers a missing Groq key and unparseable model output.
    """


class ThreatClassification(BaseModel):
    """Structured LLM output for a single OSINT alert.

    Attributes:
        object_class: Normalized shared class after synonym mapping.
        confidence_score: Model confidence in the closed interval
            ``[0.0, 1.0]``.
    """

    object_class: str = Field(min_length=1, max_length=100)
    confidence_score: float = Field(ge=0, le=1)

    @field_validator("object_class")
    @classmethod
    def coerce_object_class(cls, value: str) -> str:
        """Map the predicted label onto a shared object class.

        Args:
            value: Free-form class string from the model.

        Returns:
            One of the shared object classes from
            :func:`object_classes.normalize_object_class`.

        Raises:
            ValueError: ``value`` is blank after stripping.
        """

        if not value.strip():
            raise ValueError("object_class cannot be empty.")
        return normalize_object_class(value)


class OsintAgentState(TypedDict, total=False):
    """Shared state passed between LangGraph nodes in the OSINT pipeline.

    Attributes:
        alert_text: Normalized alert body.
        object_class: Shared visual class predicted for the alert.
        confidence_score: Model confidence for ``object_class``.
        threat_event: Created threat-event record, when posted.
        system_log: Created system-log record, when posted.
        error: Failure message when a node could not finish.
        source_id: Heimdall source that produced the alert.
    """

    alert_text: str
    object_class: str
    confidence_score: float
    threat_event: Optional[Dict[str, Any]]
    system_log: Optional[Dict[str, Any]]
    error: Optional[str]
    source_id: int


class OsintAgent:
    """Classify raw OSINT alerts and post the results to Heimdall.

    The compiled LangGraph runs three nodes in order:

    1. ``ingest_alert`` — normalize the raw alert text
    2. ``classify_with_llm`` — Groq Llama predicts ``object_class`` and
       ``confidence_score`` as structured JSON
    3. ``post_to_api`` — create a threat event and a system log
    """

    MODEL_NAME = "openai/gpt-oss-20b"
    MODULE_NAME = "osint-agent"
    DEFAULT_STATUS = "Pending"

    _SYSTEM_PROMPT = (
        "You are the OSINT classifier for Project Heimdall, an "
        "edge-to-cloud surveillance system. Read a raw open-source "
        "alert and decide what a nearby camera should look for.\n\n"
        "Return structured JSON with:\n"
        '- object_class: exactly one of "person", "vehicle", "crowd", '
        '"package", or "unknown"\n'
        "- confidence_score: a float from 0.0 to 1.0\n\n"
        "Lower confidence when the report is unconfirmed, second-hand, "
        'or vague. Use object_class "unknown" when no visual object '
        "is implied."
    )

    def __init__(
        self,
        client: HeimdallAPIClient,
        groq_api_key: Optional[str] = None,
    ) -> None:
        """Build the Groq client and compile the LangGraph pipeline.

        Args:
            client: Heimdall API client used by the ``post_to_api`` node.
            groq_api_key: Groq API key. When omitted, ``GROQ_API_KEY`` is
                read from the environment.

        Raises:
            OsintAgentError: The Groq API key is missing.
        """

        api_key = groq_api_key or os.getenv("GROQ_API_KEY", "").strip()
        if not api_key:
            raise OsintAgentError(
                "GROQ_API_KEY is not set. Copy ai-brain/.env.example to "
                "ai-brain/.env and add your Groq API key."
            )

        self._client = client
        self._llm = ChatGroq(
            model=self.MODEL_NAME,
            api_key=api_key,
            temperature=0,
        )
        self._structured_llm = self._llm.with_structured_output(ThreatClassification)
        self._graph = self._build_graph()

    def run(self, alert_text: str, source_id: int) -> OsintAgentState:
        """Run the pipeline for one source-attributed OSINT alert.

        Args:
            alert_text: Raw report text to classify.
            source_id: Heimdall ``osint_sources.source_id`` for the alert.

        Returns:
            Final graph state, including classification fields and any
            ``error`` set by a node.
        """

        result = self._graph.invoke(
            {
                "alert_text": alert_text,
                "source_id": source_id,
            }
        )
        return dict(result)

    def _build_graph(self) -> Any:
        """Compile the three-node LangGraph StateGraph."""

        graph: StateGraph = StateGraph(OsintAgentState)
        graph.add_node("ingest_alert", self._ingest_alert)
        graph.add_node("classify_with_llm", self._classify_with_llm)
        graph.add_node("post_to_api", self._post_to_api)
        graph.add_edge(START, "ingest_alert")
        graph.add_edge("ingest_alert", "classify_with_llm")
        graph.add_edge("classify_with_llm", "post_to_api")
        graph.add_edge("post_to_api", END)
        return graph.compile()

    def _ingest_alert(self, state: OsintAgentState) -> Dict[str, Any]:
        """Normalize raw alert text before classification."""

        alert_text = (state.get("alert_text") or "").strip()
        if not alert_text:
            return {
                "alert_text": "",
                "error": "Alert text is empty.",
            }

        return {"alert_text": alert_text, "error": None}

    def _classify_with_llm(self, state: OsintAgentState) -> Dict[str, Any]:
        """Ask Groq to emit object_class and confidence_score as JSON."""

        if state.get("error"):
            return {}

        alert_text = state["alert_text"]
        messages = [
            ("system", self._SYSTEM_PROMPT),
            ("human", alert_text),
        ]

        try:
            classification = self._invoke_classifier(messages)
        except Exception as exc:
            return {
                "error": f"Groq classification failed: {exc}",
            }

        return {
            "object_class": classification.object_class,
            "confidence_score": classification.confidence_score,
            "error": None,
        }

    def _post_to_api(self, state: OsintAgentState) -> Dict[str, Any]:
        """Post a threat event and a system log to the Heimdall API."""

        if state.get("error") or not state.get("object_class"):
            return {}

        object_class = state["object_class"]
        confidence_score = float(state["confidence_score"])
        alert_text = state["alert_text"]

        try:
            threat_event = self._client.post_threat_event(
                {
                    "source_id": state["source_id"],
                    "object_class": object_class,
                    "confidence_score": confidence_score,
                    "status": self.DEFAULT_STATUS,
                }
            )
        except HeimdallAPIError as exc:
            return {"error": str(exc)}

        event_id = threat_event.get("event_id")
        log_message = (
            f"OSINT classified alert as {object_class} "
            f"(confidence={confidence_score:.2f}): {alert_text}"
        )

        try:
            system_log = self._client.post_system_log(
                {
                    "event_id": event_id,
                    "module": self.MODULE_NAME,
                    "message": log_message,
                }
            )
        except HeimdallAPIError as exc:
            return {
                "threat_event": threat_event,
                "error": f"Threat event stored, but system log failed: {exc}",
            }

        return {
            "threat_event": threat_event,
            "system_log": system_log,
            "error": None,
        }

    def _invoke_classifier(self, messages: list) -> ThreatClassification:
        """Return structured JSON from Groq, with a plain-JSON fallback."""

        try:
            result = self._structured_llm.invoke(messages)
            return self._coerce_classification(result)
        except Exception:
            raw = self._llm.invoke(messages)
            content = getattr(raw, "content", raw)
            return self._parse_classification_json(str(content))

    def _coerce_classification(self, result: Any) -> ThreatClassification:
        """Accept a Pydantic model or dict from structured output."""

        if isinstance(result, ThreatClassification):
            return result
        if isinstance(result, dict):
            return ThreatClassification.model_validate(result)
        return self._parse_classification_json(str(result))

    def _parse_classification_json(self, content: str) -> ThreatClassification:
        """Extract a ThreatClassification from a model text response."""

        text = content.strip()
        fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
        if fenced:
            text = fenced.group(1)

        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if not match:
                raise OsintAgentError(f"Model did not return JSON: {content!r}")
            payload = json.loads(match.group(0))

        return ThreatClassification.model_validate(payload)
