from typing import Any, List

# ✅ LangChain Core (1.x LCEL 구조 표준)
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage


class CustomMongoChatMessageHistory(BaseChatMessageHistory):  # type: ignore[misc]
		"""LangChain ChatMessageHistory backed by custom MongoDB schema."""

		def __init__(
			self,
			manager: Any,
			user_id: str,
			session_id: str,
		):

			self._manager = manager
			self._user_id = user_id
			self._session_id = session_id
			# Request context (session_no, user_no, llm_no)
			self._context = manager.get_request_context(user_id, session_id)

		@property
		def messages(self) -> List[BaseMessage]:  # type: ignore[override]
			documents = self._manager._fetch_custom_messages(self._user_id, self._session_id)
			results: List[BaseMessage] = []
			for doc in documents:
				role_value = doc.get("ROLE") or doc.get("role") or ""
				content_value = doc.get("CONTENT") or doc.get("content") or ""
				role = str(role_value).upper()
				content = str(content_value)
				# --- Build common additional kwargs (kept inside message objects) ---
				created_at = doc.get("CREATED_AT") or doc.get("created_at")
				# Convert datetime to iso string for portability
				try:
					timestamp = created_at.isoformat() if hasattr(created_at, "isoformat") else str(created_at) if created_at else None
				except Exception:
					timestamp = str(created_at) if created_at else None

				# Normalize UUID/Binary ids to strings when present
				def _to_str(value: Any) -> str:
					try:
						# bson.binary.Binary -> bytes; uuid -> str; fallback to str
						if hasattr(value, "as_uuid"):
							return str(value.as_uuid())  # type: ignore[attr-defined]
						return str(value)
					except Exception:
						return ""

				message_id = _to_str(doc.get("MESSAGE_NO") or doc.get("message_id") or doc.get("id"))
				session_no = _to_str(doc.get("SESSION_NO") or doc.get("session_no"))
				user_no = _to_str(doc.get("USER_NO") or doc.get("user_no"))

				references = doc.get("REFERENCES") or doc.get("references") or []
				if not isinstance(references, list):
					references = []

				input_tokens = doc.get("INPUT_TOKENS")
				output_tokens = doc.get("OUTPUT_TOKENS")
				total_tokens = doc.get("TOTAL_TOKENS")
				response_time_ms = doc.get("RESPONSE_TIME_MS") or doc.get("latency_ms")
				llm_no = doc.get("LLM_NO") or doc.get("llm")

				additional_kwargs = {
					"timestamp": timestamp,
					"message_id": message_id,
					"session_no": session_no,
					"user_no": user_no,
					# Keep both keys for convenience in upstream code
					"references": references,
					"citations": references,
					"input_tokens": input_tokens,
					"output_tokens": output_tokens,
					"total_tokens": total_tokens,
					"response_time_ms": response_time_ms,
					"llm_no": llm_no,
				}

				if role == "HUMAN" and HumanMessage is not None:
					results.append(
						HumanMessage(
							content=content,
							additional_kwargs={k: v for k, v in additional_kwargs.items() if v is not None},
							id=message_id or None,
						)
					)
				elif role == "AI" and AIMessage is not None:
					# response_metadata is preferred place for usage/latency in LangChain
					response_metadata = {
						"token_usage": {
							"prompt_tokens": input_tokens,
							"completion_tokens": output_tokens,
							"total_tokens": total_tokens,
						},
						"latency_ms": response_time_ms,
						"llm_no": llm_no,
					}
					# Remove Nones from nested dicts
					response_metadata["token_usage"] = {k: v for k, v in response_metadata["token_usage"].items() if v is not None}
					if response_metadata["token_usage"] == {}:
						del response_metadata["token_usage"]
					response_metadata = {k: v for k, v in response_metadata.items() if v is not None}

					results.append(
						AIMessage(
							content=content,
							additional_kwargs={k: v for k, v in additional_kwargs.items() if v is not None},
							response_metadata=response_metadata,  # type: ignore[arg-type]
							id=message_id or None,
						)
					)
			return results

		def add_user_message(self, message: Any) -> None:  # type: ignore[override]
			content = getattr(message, "content", str(message))
			# Compute prompt tokens and store in pending AI payload for the next turn
			input_tokens = self._manager.count_tokens(content)
			self._manager.set_pending_ai_payload(
				user_id=self._user_id,
				session_id=self._session_id,
				input_tokens=input_tokens,
			)
			self._manager.save_custom_message(
				user_id=self._user_id,
				session_id=self._session_id,
				role="HUMAN",
				content=content,
				# Use router-provided context when available
				session_no=self._context.get("session_no"),
				allow_insert=True,
				allow_update=False,
			)

		def add_ai_message(self, message: Any) -> None:  # type: ignore[override]
			content = getattr(message, "content", str(message))
			references = None
			if hasattr(message, "additional_kwargs"):
				references = message.additional_kwargs.get("citations") or message.additional_kwargs.get("references")
			normalized_references = self._manager._normalize_references(references)
			if normalized_references is None:
				pending = self._manager.pop_pending_references(self._user_id, self._session_id)
				if pending is not None:
					normalized_references = pending

			ai_payload = self._manager.pop_pending_ai_payload(self._user_id, self._session_id)
			if ai_payload and normalized_references is None and ai_payload.get("references") is not None:
				normalized_references = ai_payload.get("references")

			computed_out = self._manager.count_tokens(content)
			if not ai_payload or not isinstance(ai_payload, dict):
				ai_payload = {}
			ai_payload["output_tokens"] = computed_out
			input_tok_val = ai_payload.get("input_tokens") or 0
			ai_payload["total_tokens"] = (input_tok_val or 0) + (computed_out or 0)

			self._manager.save_custom_message(
				user_id=self._user_id,
				session_id=self._session_id,
				role="AI",
				content=content,
				references=normalized_references,
				llm_no=ai_payload.get("llm_no") if isinstance(ai_payload, dict) else None,
				input_tokens=ai_payload.get("input_tokens") if isinstance(ai_payload, dict) else None,
				output_tokens=ai_payload.get("output_tokens") if isinstance(ai_payload, dict) else None,
				total_tokens=ai_payload.get("total_tokens") if isinstance(ai_payload, dict) else None,
				response_time_ms=ai_payload.get("response_time_ms") if isinstance(ai_payload, dict) else None,
				session_no=self._context.get("session_no"),
				allow_insert=True,
				allow_update=False,
			)

		def add_message(self, message: BaseMessage) -> None:  # type: ignore[override]
			if isinstance(message, HumanMessage):
				self.add_user_message(message)
			elif isinstance(message, AIMessage):
				self.add_ai_message(message)

		def clear(self) -> None:  # type: ignore[override]
			self._manager._delete_custom_messages(self._user_id, self._session_id)

