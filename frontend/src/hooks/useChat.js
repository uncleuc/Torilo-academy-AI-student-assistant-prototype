import { useEffect, useRef, useState } from "react";

import { ApiError } from "../services/api";
import { sendChatMessage } from "../services/chatService";
import {
	CONVERSATION_ID_STORAGE_KEY,
	MAX_MESSAGE_LENGTH,
} from "../utils/constants";

function createMessage(role, content, extra = {}) {
	return {
		id: globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random()}`,
		role,
		content,
		...extra,
	};
}

function readSavedConversationId() {
	try {
		return window.sessionStorage.getItem(CONVERSATION_ID_STORAGE_KEY) || "";
	} catch {
		return "";
	}
}

export function useChat({ service = sendChatMessage } = {}) {
	const [messages, setMessages] = useState([]);
	const [conversationId, setConversationId] = useState(readSavedConversationId);
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState("");
	const [pendingMessage, setPendingMessage] = useState("");
	const activeRequest = useRef(false);

	useEffect(() => {
		try {
			if (conversationId) {
				window.sessionStorage.setItem(CONVERSATION_ID_STORAGE_KEY, conversationId);
			} else {
				window.sessionStorage.removeItem(CONVERSATION_ID_STORAGE_KEY);
			}
		} catch {
			// Session storage may be disabled; in-memory chat remains usable.
		}
	}, [conversationId]);

	async function submitMessage(rawMessage) {
		const message = typeof rawMessage === "string" ? rawMessage.trim() : "";
		if (!message || message.length > MAX_MESSAGE_LENGTH || activeRequest.current) return false;

		activeRequest.current = true;
		setError("");
		setPendingMessage(message);
		setMessages((current) => [...current, createMessage("user", message)]);
		setLoading(true);
		try {
			const result = await service(message, conversationId || null);
			setConversationId(result.conversationId);
			setMessages((current) => [
				...current,
				createMessage("assistant", result.answer, { sources: result.sources }),
			]);
			setPendingMessage("");
			return true;
		} catch (requestError) {
			const safeMessage = requestError instanceof ApiError
				? requestError.message
				: "The assistant could not process this request. Please try again.";
			setError(safeMessage);
			return false;
		} finally {
			activeRequest.current = false;
			setLoading(false);
		}
	}

	async function retryLastMessage() {
		if (!pendingMessage || loading) return false;
		// Remove the failed user bubble before retrying so it is not duplicated.
		setMessages((current) => current.slice(0, -1));
		return submitMessage(pendingMessage);
	}

	function startNewConversation() {
		if (loading) return;
		setMessages([]);
		setConversationId("");
		setPendingMessage("");
		setError("");
	}

	return {
		messages,
		conversationId,
		loading,
		error,
		submitMessage,
		retryLastMessage,
		startNewConversation,
	};
}
