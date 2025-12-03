let currentConversation = null;
let autodestructTimer = null;
const navbar = document.querySelector("nav.navbar");
const currentUser = navbar.dataset.username;


function getCookie(cookie_name) {
    const cookies = document.cookie ? document.cookie.split("; ") : [];
    for (const cookie of cookies) {
        const [key, ...rest] = cookie.split("=");
        if (key === cookie_name) {
            return decodeURIComponent(rest.join("="));
        }
    }
    return null;
}

async function fetchJSON(url, opts = {}) {
    const csrftoken = getCookie("csrftoken")

    const re = await fetch(url, Object.assign({
        headers: {
            "Content-type": "application/json",
            "X-Requested-With": "fetch",
            "X-CSRFToken": csrftoken,
        },
        credentials: "same-origin"
    }, opts));
    if (!re.ok) throw new Error(await re.text());
    return await re.json();
}

async function loadConversations() {
    const fetched_data = await fetchJSON("api/conversations/");
    const list = document.getElementById("conv-list");
    list.innerHTML = "";
    //If no conversations exist
    if (!fetched_data.conversations || fetched_data.conversations.length === 0) {
        const empty = document.createElement("li");
        empty.className = "list-group-item text-muted";
        empty.textContent = "No conversations yet."
        list.appendChild(empty);
        return;
    }
    //Display conversations
    fetched_data.conversations.forEach(c => {
        const el_list = document.createElement("li");
        el_list.className = "list-group-item list-group-item-action";
        el_list.textContent = `${c.title}`;

        if (currentConversation && currentConversation.id === c.id) {
            el_list.classList.add("conv-selected");
        }

        el_list.onclick = () => chooseConversation(c);
        list.appendChild(el_list);
    });
}

async function chooseConversation(c) {
    currentConversation = c;
    document.getElementById("conv-title").textContent = c.title;
    document.getElementById("send-btn").disabled = false;

    //unhide autodestruct
    const autodestructBtn = document.getElementById("autodestruct-btn");
    const autodestructSelect = document.getElementById('autodestruct-select');

    if (autodestructBtn && autodestructSelect) {
        autodestructBtn.hidden = false;
        autodestructSelect.hidden = false;
    }

    // Countdown status
    startAutodestructTimer(c);

    await loadMessages();
    await loadConversations();
    document.getElementById("message-input").focus();
}


async function loadMessages() {
    if (!currentConversation || !currentConversation.id) return;
    console.log("Polling messages for", currentConversation.id);
    const fetched_data = await fetchJSON(`/api/conversations/${currentConversation.id}/messages/`);
    const message_box = document.getElementById("messages");
    message_box.innerHTML = "";
    fetched_data.messages.forEach(m => {
        const chat_bubble = document.createElement("div");
        if (m.sender === currentUser) {
            //align right
            chat_bubble.className = "p-2 rounded border bg-primary-subtle text-white ms-auto"
        } else {
            //align left
            chat_bubble.className = "p-2 rounded border bg-light-subtle text-white me-auto"
        }

        const sender_date = document.createElement("div")
        sender_date.className = "small text-muted";
        sender_date.textContent = `${m.sender} - ${new Date(m.created_at).toLocaleString()}`;

        const msg_txt = document.createElement("div")
        msg_txt.textContent = m.text;

        message_box.appendChild(chat_bubble)
        chat_bubble.appendChild(sender_date);
        chat_bubble.appendChild(msg_txt)
    });
    message_box.scrollTop = message_box.scrollHeight;
}

async function sendMessage() {
    if (!currentConversation) return;
    const csrftoken = getCookie("csrftoken")
    const input = document.getElementById("message-input");
    const text = input.value.trim();
    if (!text) return;
    await fetchJSON(`/api/conversations/${currentConversation.id}/messages/`, {
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        method: "POST",
        body: JSON.stringify({text})
    });
    input.value = "";
    await loadMessages();
    input.focus();
}

async function createConversation() {
    const csrftoken = getCookie("csrftoken")
    const membersInpt = document.getElementById("new-members");
    const allmembers = membersInpt.value.trim();

    // input not empty
    if (!allmembers) {
        showAlert("error", "The field cannot be empty.")
        membersInpt.focus();
        return;
    }

    const members = allmembers ? allmembers.split(",").map(s => s.trim()).filter(Boolean) : [];

    // protect input from commas/spaces
    if (members.length ===0) {
        showAlert("error", "Please enter at least one valid username.");
        membersInpt.focus();
        return;
    }

    let fetched_data;

    try {
        fetched_data = await fetchJSON("/api/conversations/", {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken,
            },
            method: "POST",
            body: JSON.stringify({members})
        });
        showAlert("success", "Conversation created successfully!");
    } catch (error) {
        // JSON invalid_usernames
        const e = JSON.parse(error.message);
        showAlert("error", e.message);
        return;
    }

    membersInpt.value = "";

    await loadConversations();
    await chooseConversation(fetched_data);
}

function showAlert(type, message) {
    const success = document.querySelector(".alert-success");
    const error = document.querySelector(".alert-danger");

    //Both hidden
    success.hidden = true;
    error.hidden = true;

    let element;

    if (type === "success") {
        success.textContent = message;
        success.hidden = false;
        element = success;
    } else if (type === "error") {
        error.textContent = message;
        error.hidden = false;
        element = error;
    }
    // Hide after 3 seconds
    setTimeout(() => {
        element.hidden = true;
    }, 3000);
}

async function setAutodestruct() {
    if (!currentConversation) return;
    const select = document.getElementById("autodestruct-select")
    const value = select.value;

    if (!value) {
        showAlert("error", "Please select a self-destruct time.");
        return;
    }

    const delay_minutes = parseInt(value, 10)
    if (![1, 3, 5].includes(delay_minutes)) {
        showAlert("error", "Invalid self-destruct value.");
        return;
    }

    try {

        const upd_conv = await fetchJSON(`/api/conversations/${currentConversation.id}/autodestruct/`, {
            method: "POST",
            body: JSON.stringify({delay_minutes})
        });

        // Update autodestruct_at time from Back End
        if (upd_conv.autodestruct_at) {
            currentConversation.autodestruct_at = upd_conv.autodestruct_at;
        }
        startAutodestructTimer(currentConversation);

        showAlert("success", `Self-destruct set for ${delay_minutes} minutes.`);
    } catch (error) {
        showAlert("error", "Failed to set self-destruct timer");
    }
}


function startAutodestructTimer(conv) {
    const statusElement = document.getElementById("autodestruct-status");
    if (!statusElement) return;

    // Wipe previous timer
    if (autodestructTimer !== null) {
        clearInterval(autodestructTimer);
        autodestructTimer = null;
    }

    // If not set
    if (!conv.autodestruct_at) {
        statusElement.textContent = "Self-destruct: OFF"
        return;
    }

    const deadline = new Date(conv.autodestruct_at);

    function countdown() {
        const now = new Date();
        const difference = deadline - now;

        if (difference <= 0) {
            statusElement.textContent = "Self-destruct: OFF"
            clearInterval(autodestructTimer);
            autodestructTimer = null;
            return;
        }
        const differenceInSeconds = Math.floor(difference / 1000);
        const minutes = Math.floor(differenceInSeconds / 60);
        const seconds = differenceInSeconds % 60;

        statusElement.textContent = `Self-destruct in ${minutes}:${seconds.toString().padStart(2, "0")}`;
    }

    countdown();
    autodestructTimer = setInterval(countdown, 1000);

}

async function getAutodestructStatus() {
    if (!currentConversation) return;
    try {

        const fetched_data = await fetchJSON(`/api/conversations/`);

        const upd = fetched_data.conversations.find(
            c => c.id === currentConversation.id
        );
        if (!upd) return;

        currentConversation.autodestruct_at = upd.autodestruct_at;
        startAutodestructTimer(currentConversation);
    } catch (error) {
        showAlert("error", "Failed to sync self-destruct timer");
    }
}


document.addEventListener("DOMContentLoaded", () => {
    document.getElementById('create-conv').addEventListener("click", createConversation);
    document.getElementById('send-btn').addEventListener("click", sendMessage);

    const autodestructBtn = document.getElementById("autodestruct-btn");
    if (autodestructBtn) {
        autodestructBtn.addEventListener("click", setAutodestruct);
    }

    loadConversations();
    setInterval(loadMessages, 2000);
    setInterval(getAutodestructStatus, 2000)
    setInterval(loadConversations, 2000);

})


