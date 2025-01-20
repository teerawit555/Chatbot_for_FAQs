document.addEventListener("DOMContentLoaded", () => {
    const chatBox = document.getElementById("chat-box");
    const userInput = document.getElementById("user-input");
    const sendBtn = document.getElementById("send-btn");
    let isSending = false; // ป้องกันการส่งข้อความซ้ำ

    // ฟังก์ชันเพิ่มข้อความในกล่องแชท
    function addMessage(message, sender) {
        const messageDiv = document.createElement("div");
        messageDiv.className = sender === "user" ? "user-message" : "bot-message";
        messageDiv.textContent = message;
        chatBox.appendChild(messageDiv);
        chatBox.scrollTop = chatBox.scrollHeight; // เลื่อนกล่องแชทลงล่างสุด
    }

    // ฟังก์ชันส่งข้อความ
    async function sendMessage() {
        const userMessage = userInput.value.trim();
        if (!userMessage || isSending) return;

        isSending = true; // ล็อคการส่งข้อความซ้ำ
        addMessage(userMessage, "user");
        userInput.value = "";

        // แสดงสถานะกำลังส่ง
        const loadingMessage = "Loading...";
        const loadingDiv = document.createElement("div");
        loadingDiv.className = "bot-message";
        loadingDiv.textContent = loadingMessage;
        chatBox.appendChild(loadingDiv);
        chatBox.scrollTop = chatBox.scrollHeight;

        try {
            const response = await fetch("/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ message: userMessage }),
            });

            if (!response.ok) {
                throw new Error("Failed to connect to the server");
            }

            const result = await response.json();
            loadingDiv.remove(); // ลบข้อความ "Loading..."
            addMessage(result.response, "bot");
        } catch (error) {
            console.error("[Error]:", error);
            loadingDiv.remove(); // ลบข้อความ "Loading..."
            addMessage("Sorry, there was an error. Please try again.", "bot");
        } finally {
            isSending = false; // ปลดล็อคการส่งข้อความ
        }
    }

    async function addFAQ(question, answer) {
        if (!question || !answer) {
            alert("Please fill out both the question and the answer.");
            return;
        }
        try {
            const response = await fetch("/add-faq", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ question, answer }),
            });

            const result = await response.json();

            if (response.ok) {
                console.log("FAQ added successfully:", result.message);
                alert("FAQ added successfully!");
            } else {
                console.error("Error adding FAQ:", result.message);
                alert("Failed to add FAQ: " + result.message);
            }
        } catch (error) {
            console.error("Error:", error);
            alert("An error occurred while adding the FAQ.");
        }
    }

    // เมื่อคลิกปุ่ม Send
    sendBtn.addEventListener("click", sendMessage);

    // เมื่อกดปุ่ม Enter ในช่องข้อความ
    userInput.addEventListener("keypress", (event) => {
        if (event.key === "Enter") {
            event.preventDefault(); // ป้องกันการขึ้นบรรทัดใหม่
            sendMessage();
        }
    });
});

