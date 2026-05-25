# Notability to ChatGPT/OpenAI Migration Todo

Goal: replace Claude Vision extraction with OpenAI API vision extraction while keeping the existing upload, review, and ServiceM8 workflow unchanged.

## 1. Confirm Target Behaviour

- [x] Keep the current user flow: upload Notability PDF, extract structured data, review/edit, approve, push to ServiceM8.
- [x] Keep the existing `ExtractedData` schema so the frontend does not need major changes.
- [x] Decide whether the app should use OpenAI only, or support both OpenAI and Claude behind a provider setting.
- [x] Confirm target OpenAI model for vision extraction.
- [ ] Confirm expected extraction quality on handwritten DDK job sheets, sketches, diagrams, and photos.

## 2. Configuration

- [x] Add `OPENAI_API_KEY` to backend environment configuration.
- [x] Add `OPENAI_MODEL` with a sensible vision-capable default.
- [x] Add OpenAI variables to `backend/.env.example`.
- [ ] Consider adding `LLM_PROVIDER=openai` if keeping Claude as an optional fallback.
- [ ] Remove or deprecate `CLAUDE_API_KEY` and `CLAUDE_MODEL` once OpenAI extraction is verified.
- [x] Update local `backend/.env` with the OpenAI key.
- [ ] Update deployment environment variables.

## 3. Backend Extraction Service

- [x] Rename `extract_with_claude()` to a provider-neutral name, such as `extract_with_vision_model()`.
- [x] Rename `_extract_with_anthropic_vision()` to `_extract_with_openai_vision()` or add a new OpenAI function beside it.
- [x] Keep `pdf_to_images()` unchanged unless image size or quality needs adjustment.
- [x] Convert rendered PDF page PNGs to base64 data URLs for OpenAI image input.
- [x] Replace the Anthropic `/v1/messages` call with the OpenAI `/v1/responses` call.
- [x] Change request headers from Anthropic headers to `Authorization: Bearer <OPENAI_API_KEY>`.
- [x] Change content blocks:
  - [x] Prompt text: `{"type": "input_text", "text": "..."}`
  - [x] Images: `{"type": "input_image", "image_url": "data:image/png;base64,..."}`
- [x] Parse OpenAI response output text.
- [x] Pass parsed JSON through `validate_extracted_data()` as currently done.
- [x] Keep timeout handling through `external_timeout_seconds`.

## 4. Structured Output

- [x] Decide whether to keep prompt-only JSON extraction for the first migration pass.
- [x] Prefer adding OpenAI Structured Outputs after the basic API call works.
- [x] Create a JSON schema matching `ExtractedData`.
- [x] Use structured output to reduce fragile manual JSON parsing.
- [x] Keep `_extract_json()` temporarily as a fallback while testing.

## 5. Fallback Behaviour

- [x] Update fallback text from "Claude Vision is not configured" to "OpenAI vision extraction is not configured".
- [x] Update recommendation action from "Configure Claude Vision" to "Configure OpenAI vision extraction".
- [x] Ensure handwritten-note limitations are still clearly explained when no API key is configured.
- [x] Ensure re-extraction feedback is still included.

## 6. Tests and Smoke Checks

- [x] Rename `backend/test_claude_extract.py` to something like `backend/test_vision_extract.py`.
- [x] Update imports and function names in the test script.
- [ ] Run extraction against `files/Anne Donohoe.pdf`.
- [ ] Resolve OpenAI `insufficient_quota` response for the configured API key.
- [ ] Verify handwritten content appears in `raw_text`.
- [ ] Verify `client_details`, `job_details`, `findings`, `recommendations`, `follow_up_actions`, and `visual_notes` validate correctly.
- [x] Test the no-key fallback path.
- [x] Test re-extraction with feedback.
- [x] Test backend upload smoke path with no external API key configured.
- [x] Confirm frontend production build succeeds.
- [x] Confirm frontend dev server serves the app.
- [ ] Test upload through the frontend and confirm the review page still renders.
- [x] Push a reviewed consultation to ServiceM8 mock or real API depending on environment.

## 7. Documentation

- [x] Update README environment variable list.
- [x] Replace Claude references in README MVP notes.
- [x] Update `files/spec.md` if it should reflect the new OpenAI architecture.
- [x] Update `files/todo.md` historical Claude tasks or add an OpenAI migration note.
- [x] Document which OpenAI model is used and why.
- [ ] Document expected costs and upload/page-size constraints once tested.

## 8. Cleanup

- [x] Search the repo for remaining `Claude`, `claude`, `Anthropic`, and `anthropic` references.
- [x] Remove obsolete Claude-only test names after migration.
- [ ] Remove unused config fields if Claude support is fully dropped.
- [ ] Confirm no API keys are committed.
- [x] Confirm `.env` files remain ignored.

## Suggested Implementation Order

1. [x] Add OpenAI config.
2. [x] Add `_extract_with_openai_vision()` using `httpx`.
3. [x] Switch extraction function to use OpenAI when `OPENAI_API_KEY` is set.
4. [x] Update fallback messages.
5. Run one real PDF extraction.
6. Add Structured Outputs if the basic OpenAI call works.
7. Update README and cleanup old Claude references.
