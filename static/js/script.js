/* =========================
   SEND MESSAGE
========================= */

function sendMessage() {

    let input = document.getElementById("message");
    let message = input.value.trim();

    if (message === "") {
        return;
    }

    let chatBox = document.getElementById("chat-box");

    /* Escape HTML so user input is displayed safely */
    let safeMessage = message
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");


    /* =========================
       USER MESSAGE
    ========================= */

    chatBox.innerHTML += `
        <div class="message user-message"
             style="justify-content:flex-end;">

            <div class="message-content">

                <div class="message-name"
                     style="text-align:right;">
                    You
                </div>

                <div class="bubble"
                     style="
                     background:#4f46e5;
                     color:white;
                     border-radius:15px 5px 15px 15px;">
                    ${safeMessage}
                </div>

            </div>

        </div>
    `;


    /* Clear input */

    input.value = "";


    /* =========================
       TYPING INDICATOR
    ========================= */

    chatBox.innerHTML += `
        <div id="typing"
             class="message">

            <div class="avatar ai-avatar">

                <i class="bi bi-robot"></i>

            </div>

            <div class="message-content">

                <div class="message-name">
                    SmartSupport AI
                </div>

                <div class="bubble">

                    <span class="typing-dot">●</span>
                    <span class="typing-dot">●</span>
                    <span class="typing-dot">●</span>

                    <span style="margin-left:5px;">
                        AI is thinking...
                    </span>

                </div>

            </div>

        </div>
    `;


    /* Scroll to bottom */

    chatBox.scrollTop = chatBox.scrollHeight;


    /* =========================
       SEND TO FLASK
    ========================= */

    fetch('/get_response', {

        method: 'POST',

        headers: {
            'Content-Type':
            'application/x-www-form-urlencoded'
        },

        body:
        'message=' + encodeURIComponent(message)

    })


    /* =========================
       RECEIVE RESPONSE
    ========================= */

    .then(response => {

        if (!response.ok) {
            throw new Error("Server error");
        }

        return response.text();

    })


    .then(data => {

        /* Remove typing indicator */

        let typing =
            document.getElementById("typing");

        if (typing) {
            typing.remove();
        }


        /* AI RESPONSE */

        chatBox.innerHTML += `
            <div class="message">

                <div class="avatar ai-avatar">

                    <i class="bi bi-robot"></i>

                </div>

                <div class="message-content">

                    <div class="message-name">
                        SmartSupport AI
                    </div>

                    <div class="bubble">
                        ${data}
                    </div>

                </div>

            </div>
        `;


        /* Scroll down */

        chatBox.scrollTop =
            chatBox.scrollHeight;

    })


    /* =========================
       ERROR HANDLING
    ========================= */

    .catch(error => {

        console.error(error);


        let typing =
            document.getElementById("typing");

        if (typing) {
            typing.remove();
        }


        chatBox.innerHTML += `
            <div class="message">

                <div class="avatar ai-avatar">

                    <i class="bi bi-robot"></i>

                </div>

                <div class="message-content">

                    <div class="message-name">
                        SmartSupport AI
                    </div>

                    <div class="bubble">

                        Sorry, I'm having trouble
                        connecting right now.
                        Please try again.

                    </div>

                </div>

            </div>
        `;


        chatBox.scrollTop =
            chatBox.scrollHeight;

    });

}


/* =========================
   ENTER KEY
========================= */

function handleEnter(event) {

    if (event.key === "Enter") {

        event.preventDefault();

        sendMessage();

    }

}


/* =========================
   QUICK ACTION
========================= */

function quickMessage(message) {

    document.getElementById("message").value =
        message;

    sendMessage();

}


/* =========================
   DARK MODE
========================= */

function toggleTheme() {

    document.body.classList.toggle("dark");

}