# OSINT QA log

Draft for the course QA write-up. Every row is backed by a test that exists and was run in this session. Aiman posts the results on the QA issue.

**Run (America/Chicago):** 2026-11-05 ~18:57 CST  
**Commands:**
- `.venv/osint/bin/pytest ai-brain/tests -q` → **78 passed**
- `.venv/osint/bin/pytest -m e2e tests/e2e_pipeline -v` → **5 passed**

Severity is the impact if the case failed in production (wrong activation, missed activation, or silent loss of a source). Result is the outcome of the run above. Resolution is empty when the case already matches the design; use a GitHub issue only when a defect needs a follow-up.

| Test | Edge case | Severity | Result | Resolution | Linked issue |
| --- | --- | --- | --- | --- | --- |
| `tests/e2e_pipeline/test_osint_pipeline.py::test_matching_sources_activate_camera_and_corroborate_events` | Two independent sources report the same class inside the window: camera 1 becomes Active and both threat events become Corroborated | high | pass | — | #61 |
| `tests/e2e_pipeline/test_osint_pipeline.py::test_different_classes_leave_camera_dormant` | Two sources report different classes: camera stays Dormant, events stay Pending | high | pass | — | #62 |
| `tests/e2e_pipeline/test_osint_pipeline.py::test_reports_outside_the_window_do_not_corroborate` | Second report arrives after the corroboration window: no activation | high | pass | — | #62 |
| `tests/e2e_pipeline/test_osint_pipeline.py::test_same_source_twice_does_not_corroborate` | Same source posts twice with the same class: never activates | high | pass | — | #62 |
| `tests/e2e_pipeline/test_osint_pipeline.py::test_one_source_request_error_does_not_stop_the_runner` | One source raises a request error: the other source still classifies; camera stays Dormant on a single report | medium | pass | — | #62 |
| `ai-brain/tests/test_corroboration.py::test_one_source_stays_pending` | A single report never corroborates | high | pass | — | #33 |
| `ai-brain/tests/test_corroboration.py::test_two_distinct_sources_corroborate` | Two distinct source ids with the same category inside the window agree | high | pass | — | #33 |
| `ai-brain/tests/test_corroboration.py::test_same_source_twice_does_not_corroborate` | Repeated reports from one source never count as a second source | high | pass | — | #33 |
| `ai-brain/tests/test_corroboration.py::test_reports_outside_the_window_do_not_corroborate` | A later source does not revive a report older than the window | high | pass | — | #33 |
| `ai-brain/tests/test_corroboration.py::test_report_on_the_window_edge_still_counts` | A report exactly `window_seconds` later is still inside the window | medium | pass | — | #33 |
| `ai-brain/tests/test_corroboration.py::test_corroboration_fires_only_once` | A third source does not start another corroboration for that category | medium | pass | — | #33 |
| `ai-brain/tests/test_corroboration.py::test_different_categories_do_not_corroborate` | Agreement is per classified category, not across categories | high | pass | — | #33 |
| `ai-brain/tests/test_corroboration.py::test_synonyms_of_the_same_class_corroborate` | Different person synonyms (`man` / `woman`) still corroborate as `person` | high | pass | — | #60 |
| `ai-brain/tests/test_corroboration.py::test_vehicle_synonyms_corroborate` | Different vehicle synonyms (`car` / `truck`) still corroborate as `vehicle` | high | pass | — | #60 |
| `ai-brain/tests/test_corroboration.py::test_two_unknown_reports_do_not_corroborate` | Two `unknown` classifications never activate | high | pass | — | #60 |
| `ai-brain/tests/test_corroboration.py::test_different_unmapped_labels_do_not_corroborate` | Unmapped labels collapse to `unknown` and still do not corroborate | high | pass | — | #60 |
| `ai-brain/tests/test_object_classes.py::test_normalize_maps_allowed_classes_and_synonyms` | Allowed classes and listed synonyms map to the shared vocabulary (parametrized) | medium | pass | — | #60 |
| `ai-brain/tests/test_object_classes.py::test_normalize_unknown_fallback` | Labels outside the synonym map become `unknown` (parametrized) | medium | pass | — | #60 |
| `ai-brain/tests/test_object_classes.py::test_allowed_object_classes_are_exactly_five` | Shared vocabulary is exactly person, vehicle, crowd, package, unknown | medium | pass | — | #60 |
| `ai-brain/tests/test_object_classes.py::test_threat_classification_normalizes_synonyms` | Classifier structured output coerces synonyms onto a shared class | medium | pass | — | #60 |
| `ai-brain/tests/test_object_classes.py::test_threat_classification_maps_unknown_labels` | Unrecognized classifier labels become `unknown`, not raw text | medium | pass | — | #60 |
| `ai-brain/tests/test_object_classes.py::test_threat_classification_rejects_blank_object_class` | Blank `object_class` is invalid structured output | low | pass | — | #60 |
| `ai-brain/tests/test_live_osint.py::test_keyword_match_and_case` | Keywords match case-insensitively; unrelated text is ignored | medium | pass | — | #32 |
| `ai-brain/tests/test_live_osint.py::test_keyword_miss_is_logged` | Text with no keyword is logged and dropped before classification | low | pass | — | #32 |
| `ai-brain/tests/test_live_osint.py::test_keyword_filter_drops_items_before_the_agent` | The agent runs only for items that match a keyword; camera untouched | medium | pass | — | #32 |
| `ai-brain/tests/test_live_osint.py::test_single_report_does_not_change_the_camera` | One matching report is classified and leaves the camera alone | high | pass | — | #33 |
| `ai-brain/tests/test_live_osint.py::test_activation_patches_then_puts_once` | Two sources corroborate once: PATCH events, then PUT camera Active, then one system log | high | pass | — | #33 |
| `ai-brain/tests/test_live_osint.py::test_registration_reuses_existing_sources` | Startup lists sources first and does not POST names that already exist | low | pass | — | #32 |
| `ai-brain/tests/test_live_osint.py::test_registration_posts_only_missing_sources` | A source missing from `GET /sources` is created once | low | pass | — | #32 |
| `ai-brain/tests/test_live_osint.py::test_live_flag_defaults_to_off` | Unset `FEATURE_LIVE_OSINT` keeps live polling disabled | high | pass | — | #32 |
| `ai-brain/tests/test_live_osint.py::test_flag_off_uses_the_mock_path` | Flag false processes mock JSON and does not start live polling | medium | pass | — | #32 |
| `ai-brain/tests/test_live_osint.py::test_flag_on_uses_the_live_runner` | Flag true skips mock alerts and hands control to the live runner | medium | pass | — | #32 |
| `ai-brain/tests/test_live_osint.py::test_default_adapters_poll_ntfy_and_rss` | Default live adapters poll the configured ntfy and RSS URLs (mocked HTTP) | medium | pass | — | #32 |
| `ai-brain/tests/test_live_osint.py::test_client_patch_put_and_list_use_backend_routes` | Corroboration uses threat PATCH and camera PUT routes | medium | pass | — | #33 |
| `ai-brain/tests/test_live_osint.py::test_list_sources_rejects_a_non_list` | A malformed sources payload is an API error, not a later crash | medium | pass | — | TODO |
| `ai-brain/tests/test_adapters.py::test_ntfy_keeps_messages_and_skips_other_events` | ntfy keeps message events, skips open/keepalive/junk, and deduplicates by id | medium | pass | — | #32 |
| `ai-brain/tests/test_adapters.py::test_rss_parses_guid_and_deduplicates` | RSS items need a guid; a second poll of the same guid yields nothing | medium | pass | — | #32 |
| `ai-brain/tests/test_adapters.py::test_demo_feed_form_and_rss_round_trip` | Submitted demo text is served as RSS and read back by the adapter | low | pass | — | #32 |
| `ai-brain/tests/test_adapters.py::test_rss_request_uses_the_configured_feed_url` | Adapter GETs the configured feed URL with a bounded timeout | low | pass | — | #32 |
| `ai-brain/tests/test_osint_integration.py::test_authenticate_adds_bearer_token` | Successful login stores a Bearer token on the session | medium | pass | — | #12 |
| `ai-brain/tests/test_osint_integration.py::test_authenticate_requires_credentials` | Missing OSINT credentials raise before any login attempt | medium | pass | — | #12 |
| `ai-brain/tests/test_osint_integration.py::test_alerts_are_mapped_to_registered_source_ids` | Mock alerts attach the registered source id by name | low | pass | — | #12 |
| `ai-brain/tests/test_osint_integration.py::test_unknown_alert_source_is_rejected` | An unregistered alert source is rejected | medium | pass | — | #12 |
| `ai-brain/tests/test_osint_integration.py::test_osint_event_uses_source_without_fake_camera` | Threat events post with a source id and without inventing a camera id | medium | pass | — | #12 |
| `ai-brain/tests/test_osint_logging.py::test_classify_event_has_required_fields` | Classify JSON log includes timestamp, level, request_id, user_id | low | pass | — | #64 |
| `ai-brain/tests/test_osint_logging.py::test_failed_classification_is_a_warning` | Agent error result is a classify warning with the required fields | medium | pass | — | #64 |
| `ai-brain/tests/test_osint_logging.py::test_corroborate_event_has_required_fields` | Corroborate JSON log includes category, event ids, source ids, and the required fields | low | pass | — | #64 |
| `ai-brain/tests/test_osint_logging.py::test_each_item_gets_its_own_request_id` | Two items in one poll get different request ids | low | pass | — | #64 |
| `ai-brain/tests/test_osint_logging.py::test_poll_error_event_has_required_fields` | A source request error is logged; the other source still runs | medium | pass | — | #64 |
| `ai-brain/tests/test_osint_logging.py::test_agent_error_event_has_required_fields` | An API error raised by the agent is logged as a classify-stage error | medium | pass | — | #64 |
| `ai-brain/tests/test_osint_logging.py::test_activation_error_event_has_required_fields` | A failed camera activation logs a corroborate-stage error, not a success | high | pass | — | #64 |
| `ai-brain/tests/test_osint_logging.py::test_console_banner_is_unchanged` | Source banner still prints to stdout; JSON events do not | low | pass | — | #64 |
| `ai-brain/tests/test_osint_logging.py::test_formatter_uses_bound_context_for_plain_records` | Bound request_id / user_id appear on plain records only while the context is active | low | pass | — | #64 |
| `ai-brain/tests/test_osint_logging.py::test_configure_logging_installs_json_handler` | With no handlers configured, the root logger writes JSON lines | low | pass | — | #64 |
| `ai-brain/tests/test_osint_logging.py::test_current_user_id` | `GET /auth/me` supplies user_id; auth and type failures return None (parametrized) | low | pass | — | #64 |

## Notes for the QA issue

- No failing rows in this run. Resolution is `—` for every case because the behavior already matches the design; no defect issue was opened from these results.
- The E2E suite talks only to the local API and test Postgres. Classifier and source adapters are fakes (no Groq, no ntfy.sh, no live RSS).
- Parametrized cases (`test_normalize_*`, `test_current_user_id`) are one row each; every parameter passed in the same run.
