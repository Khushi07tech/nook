document.addEventListener("DOMContentLoaded", () => {
  const chatForm = document.querySelector(".chat-form");
  const chatTextarea = document.querySelector(".chat-textarea, textarea[name='msg']");
  const chatMessages = document.getElementById("chatMessages") || document.querySelector(".chat-messages");
  const chatContainer = document.querySelector(".chat-container");

  if (!chatForm || !chatTextarea || !chatMessages) return;

  chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const text = chatTextarea.value.trim();
    if (!text) return;

    // Dynamically choose endpoint (/chat/:id vs /chat)
    const projectId = chatContainer?.dataset?.projectId || chatForm.dataset?.projectId;
    const endpoint = projectId ? `/chat/${projectId}` : (chatForm.getAttribute("action") || "/chat");

    // Helper function to append message bubbles
    const appendBubble = (content, role) => {
      const wrapper = document.createElement("div");
      wrapper.className = `chat-bubble-wrapper ${role}-wrapper`;

      const bubble = document.createElement("div");
      bubble.className = `chat-bubble ${role}-bubble`;

      const messageContent = document.createElement("div");
      messageContent.className = "message-content";
      messageContent.textContent = content;

      bubble.appendChild(messageContent);
      wrapper.appendChild(bubble);
      chatMessages.appendChild(wrapper);

      // Auto-scroll to the latest message
      chatMessages.scrollTop = chatMessages.scrollHeight;
    };

    // 1. Instantly show user message & clear input box
    appendBubble(text, "user");
    chatTextarea.value = "";

    try {
      // 2. Build form data payload
      const formData = new FormData();
      formData.append("msg", text);

      // 3. Send request to Flask backend
      const response = await fetch(endpoint, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) throw new Error("Failed to send message");

      const data = await response.json();

      // 4. Show AI companion response
      appendBubble(data.response, "assistant");
    } catch (err) {
      console.error("Chat Error:", err);
      appendBubble("Sorry, something went wrong. Please try again.", "assistant");
    }
  });
});