let users = [];

function refresh() {
    window.open("/");
}

function createUser() {
    name_input = document.getElementById("create-name");
    email_input = document.getElementById("create-email");
    position_input = document.getElementById("create-position");

    fetch("/api/create_user", {
        method: "POST",
        body: JSON.stringify({
            name: name_input.value,
            id: email_input.value,
            position: position_input.value
        }),
        headers: {
            "Content-type": "application/json; charset=UTF-8"
        }
    })
    .then(response => response.json())
    .then(data => {
        name_input.value = "";
        email_input.value = "";
        position_input.value = "";

        renderUsers();
        window.alert(data.response);
    });
}

function saveUser(email, position, score) {
    fetch("/api/update_user", {
        method: "PUT",
        body: JSON.stringify({
            id: email,
            position: position,
            score: score,
            admin: false
        }),
        headers: {
            "Content-type": "application/json; charset=UTF-8"
        }
    })
    .then(response => response.json())
    .then(data => {
        window.alert(data.response);
    });
}

function deleteUser(email) {
    fetch("/api/delete_user", {
        method: "DELETE",
        body: JSON.stringify({
            id: email
        }),
        headers: {
            "Content-type": "application/json; charset=UTF-8"
        }
    })
    .then(response => response.json())
    .then(data => {
        window.alert(data.response);
    });
}

async function fetchUsers() {
    try {
        const response = await fetch("/api/get_users");
        if (!response.ok) throw new Error("Failed to fetch users");

        const jsonData = await response.json();
        users = jsonData.response;
    } catch (error) {
        console.error("Error getting users", error);
    }
}

function hasCheckedIn(email) {
    return fetch("/api/is_present?id=" + email)
        .then(response => response.json())
        .then(data => data.response);
}

function createUserCard(userData) {
    // Create container div
    let container = document.createElement("div");
    container.className = "container1 inline-container";
    container.id = "user-container";

    // Create user info paragraph
    let userInfo = document.createElement("p");
    userInfo.innerHTML = `${userData.name} <span class="lesser">(<a href="../admin/profile/${userData.id}">${userData.id}</a>)</span>`;
    container.appendChild(userInfo);

    // Position section
    let positionDiv = document.createElement("div");
    let positionLabel = document.createElement("p");
    positionLabel.textContent = "Position";
    let positionInput = document.createElement("input");
    positionInput.type = "text";
    positionInput.className = "input";
    positionInput.value = userData.position;

    positionDiv.appendChild(positionLabel);
    positionDiv.appendChild(positionInput);
    container.appendChild(positionDiv);

    // Score section
    let scoreDiv = document.createElement("div");
    let scoreLabel = document.createElement("p");
    scoreLabel.innerHTML = `Score
        <button class="tiny-gray-button" onclick="updateScore(this, 5)">+5</button>
        <button class="tiny-gray-button" onclick="updateScore(this, 10)">+10</button>
        <button class="tiny-gray-button" onclick="updateScore(this, 25)">+25</button>`;

    let scoreInput = document.createElement("input");
    scoreInput.type = "text";
    scoreInput.className = "input";
    scoreInput.value = userData.score;

    scoreDiv.appendChild(scoreLabel);
    scoreDiv.appendChild(scoreInput);
    container.appendChild(scoreDiv);

    let attendanceDiv = document.createElement("div");
    let attendanceLabel = document.createElement("p");
    let attendanceMarker = document.createElement("h1");
    attendanceLabel.innerHTML = "<span class='lesser'>Present</span>"

    hasCheckedIn(userData.id).then(result => {
        if (result) {
            attendanceMarker.innerHTML = "<i class='bi bi-check' style='color:#3acc00'></i>"
        } else {
            attendanceMarker.innerHTML = "<i class='bi bi-x' style='color:#e00000'></i>"
        }
    })

    attendanceDiv.appendChild(attendanceLabel);
    attendanceDiv.appendChild(attendanceMarker);
    container.appendChild(attendanceDiv);

    let buttonDiv = document.createElement("div");

    let deleteButton = document.createElement("button");
    deleteButton.className = "red-button";
    deleteButton.innerHTML = '<i class="bi bi-trash3-fill"></i>';
    deleteButton.onclick = () => {
        container.remove();
        deleteUser(userData.id);
    }

    let saveButton = document.createElement("button");
    saveButton.className = "green-button";
    saveButton.textContent = "Save";
    saveButton.onclick = () => {
        saveUser(userData.id, positionInput.value, Number(scoreInput.value));
    };

    buttonDiv.appendChild(deleteButton);
    buttonDiv.appendChild(saveButton);
    container.appendChild(buttonDiv);

    return container;
}

function updateScore(button, amount) {
    let scoreInput = button.closest("div").querySelector(".input");
    scoreInput.value = parseInt(scoreInput.value) + amount;
}

async function renderUsers() {
    let container = document.getElementById("users-container");
    container.innerHTML = "";

    users.forEach(user => {
        container.appendChild(createUserCard(user));
    });
}

document.addEventListener("DOMContentLoaded", async () => {
    await fetchUsers();
    await renderUsers();
});
