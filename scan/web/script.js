let users = [];

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

eel.expose(reloadPage);
function reloadPage() {
  window.location.reload();
}

async function fetchUsers() {
  try {
    const response = await fetch("http://0.0.0.0:8080/api/get_users");
    if (!response.ok) throw new Error("Failed to fetch users");
    const jsonData = await response.json();
    users = jsonData.response;
  } catch (error) {
    console.error("Error getting users", error);
  }
}

function hasCheckedIn(email) {
  return fetch("http://0.0.0.0:8080/api/is_present?id=" + email)
    .then(response => response.json())
    .then(data => data.response);
}

async function renderUsers() {
  await fetchUsers();
  const tableBody = document.getElementById("table-body");
  if (!tableBody) {
    console.error("Table body not found");
    return;
  }
  tableBody.innerHTML = "";
  for (const user of users) {
    try {
      const present = await hasCheckedIn(user.id);
      const iconHtml = present
        ? "<i class='bi bi-check' style='color:#3acc00'></i>"
        : "<i class='bi bi-x' style='color:#e00000'></i>";
      const tr = document.createElement("tr");
      const td = document.createElement("td");
      td.innerHTML =
        "<div class='container1 inline-container'>" +
          "<p>" + user.name + " <span class='lesser'>(" + user.id + ")</span></p>" +
          "<div class='inline-container'>" +
            "<p>Checked in</p>" +
            "<h1>" + iconHtml + "</h1>" +
          "</div>" +
        "</div>";
      tr.appendChild(td);
      tableBody.appendChild(tr);
    } catch (error) {
      console.error("Error processing user", user, error);
    }
  }
}

document.addEventListener("DOMContentLoaded", renderUsers);
