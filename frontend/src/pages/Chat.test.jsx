import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../services/api";
import { sendChatMessage } from "../services/chatService";
import Chat from "./Chat";

vi.mock("../services/chatService", () => ({
	sendChatMessage: vi.fn(),
}));

afterEach(() => {
	cleanup();
	window.sessionStorage.clear();
});

describe("Chat API integration", () => {
	it("renders backend answers and sources and reuses the returned conversation ID", async () => {
		const user = userEvent.setup();
		sendChatMessage
			.mockResolvedValueOnce({
				answer: "Backend answer from approved context.",
				sources: [{ title: "Attendance Policy", document: "attendance.md" }],
				conversationId: "server-conversation-1",
			})
			.mockResolvedValueOnce({
				answer: "Second backend answer.",
				sources: [],
				conversationId: "server-conversation-1",
			});

		render(<Chat />);
		await user.type(screen.getByRole("textbox", { name: "Ask a question" }), "attendance policy");
		await user.click(screen.getByRole("button", { name: "Send message" }));

		expect(await screen.findByText("Backend answer from approved context.")).toBeTruthy();
		expect(screen.getByText("Attendance Policy")).toBeTruthy();
		await user.type(screen.getByRole("textbox", { name: "Ask a question" }), "what about exceptions");
		await user.click(screen.getByRole("button", { name: "Send message" }));

		expect(await screen.findByText("Second backend answer.")).toBeTruthy();
		expect(sendChatMessage).toHaveBeenNthCalledWith(1, "attendance policy", null);
		expect(sendChatMessage).toHaveBeenNthCalledWith(
			2,
			"what about exceptions",
			"server-conversation-1",
		);
	});

	it("does not create an assistant answer on failure and retries the same question", async () => {
		const user = userEvent.setup();
		sendChatMessage
			.mockRejectedValueOnce(new ApiError("Assistant service unavailable", 503))
			.mockResolvedValueOnce({
				answer: "Backend answer after retry.",
				sources: [],
				conversationId: "server-conversation-2",
			});

		render(<Chat />);
		await user.type(screen.getByRole("textbox", { name: "Ask a question" }), "refund policy");
		await user.click(screen.getByRole("button", { name: "Send message" }));

		expect(await screen.findByRole("alert")).toBeTruthy();
		expect(screen.queryByText("Torilo Assistant")).toBeNull();
		await user.click(screen.getByRole("button", { name: "Retry" }));

		expect(await screen.findByText("Backend answer after retry.")).toBeTruthy();
		await waitFor(() => expect(sendChatMessage).toHaveBeenCalledTimes(2));
		expect(sendChatMessage).toHaveBeenNthCalledWith(2, "refund policy", null);
	});
});