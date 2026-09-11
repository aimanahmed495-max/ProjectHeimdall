"""LangGraph OSINT agent that classifies alerts and posts them to Heimdall."""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Optional, TypedDict

from langchain_groq import ChatGroq
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field, field_validator

from osint_client import HeimdallAPIClient, HeimdallAPIError


class OsintAgentError(Exception):
    """Raised when the OSINT agent cannot be constructed or run."""


class ThreatClassification(BaseModel):
    """Structured LLM output for a single OSINT alert."""

    object_class: str = Field(min_length=1, max_length=100)
    confidence_score: float = Field(ge=0, le=1)

    @field_validator("object_class")
    @classmethod
    def normalize_object_class(cls, value: str) -> str:
        """Trim and lowercase the predicted visual object class."""

        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("object_class cannot be empty.")
        return normalized


class OsintAgentState(TypedDict, total=False):
    """Shared state passed between LangGraph nodes in the OSINT pipeline."""

    alert_text: str
    object_class: str
    confidence_score: float
    threat_event: Optional[Dict[str, Any]]
    system_log: Optional[Dict[str, Any]]
    error: Optional[str]


class OsintAgent:
    """Classify raw OSINT alerts and post the results to Heimdall.

    The compiled LangGraph runs three nodes in order:

    1. ``ingest_alert`` — normalize the raw alert text
    2. ``classify_with_llm`` — Groq Llama predicts ``object_class`` and
       ``confidence_score`` as structured JSON
    3. ``post_to_api`` — create a threat event and a system log
    """

    MODEL_NAME = "openai/gpt-oss-20b"
    CAMERA_ID = 1
    MODULE_NAME = "osint-agent"
    DEFAULT_STATUS = "Pending"

    _SYSTEM_PROMPT = (
        "You are the OSINT classifier for Project Heimdall, an "
        "edge-to-cloud surveillance system. Read a raw open-source "
        "alert and decide what a nearby camera should look for.\n\n"
        "Return structured JSON with:\n"
        '- object_class: a short lowercase noun such as "person", '
        '"vehicle", "crowd", "package", or "unknown"\n'
        "- confidence_score: a float from 0.0 to 1.0\n\n"
        "Lower confidence when the report is unconfirmed, second-hand, "
        "or vague. Use object_class \"unknown\" when no visual object "
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
        self._structured_llm = self._llm.with_structured_output(
            ThreatClassification
        )
        self._graph = self._build_graph()

    def run(self, alert_text: str) -> OsintAgentState:
        """Run the ingest → classify → post pipeline for one alert.

        Args:
            alert_text: Raw OSINT alert string.

        Returns:
            Final graph state, including classification, API responses,
            and any per-alert ``error`` message.
        """

        result = self._graph.invoke({"alert_text": alert_text})
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
                    "object_class": object_class,
                    "confidence_score": confidence_score,
                    "camera_id": self.CAMERA_ID,
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
                raise OsintAgentError(
                    f"Model did not return JSON: {content!r}"
                )
            payload = json.loads(match.group(0))

        return ThreatClassification.model_validate(payload)
