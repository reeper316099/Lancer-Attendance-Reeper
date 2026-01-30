let users = [];

async function fetchUsers() {
    try {
        const response = await fetch('/api/get_users');
        if (!response.ok) throw new Error('Failed to fetch users');

        const jsonData = await response.json();
        users = jsonData.response;
        users.sort((a, b) => b.score - a.score);
    } catch (error) {
        console.error('Error fetching users:', error);
    }
}

async function createUserCard(user, position) {
    const card = document.createElement("div");
    card.className = "container1 inline-container";

    const critical = document.createElement("div")
    critical.className = "inline-container";
    critical.style.cssText = "width:50%";

    const header = document.createElement("div")
    header.innerHTML = "<b>#" + position + "</b> " + user.name + " <span class='lesser'>(" + user.position + ")</span>"
    if (user.admin) {
        header.innerHTML += "<i class='bi bi-person-fill-gear' style='color:#ff3737;padding:3px'></i>"
    }

    const score = document.createElement("div")
    score.innerHTML = "Score: <b>" + user.score + "</b>"

    const email = document.createElement("div")
    email.innerHTML = " <span class='lesser'>" + user.id + "@lasallehs.org</span>"

    critical.appendChild(score);
    critical.appendChild(email);

    card.appendChild(header);
    card.appendChild(critical);

    return card;
}

async function renderUsers(data) {
    const container = document.getElementById("user-container");

    const cards = await Promise.all(
        data.map((user, i) => createUserCard(user, i + 1))
    );

    cards.forEach(card => container.appendChild(card));
}

document.addEventListener("DOMContentLoaded", async () => {
    await fetchUsers();
    await renderUsers(users);

    console.log("This is an unofficial website made by La Salle students. Also, snooping around won't get you anywhere.");
});
