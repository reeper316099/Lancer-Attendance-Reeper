userData = null;

const style = document.createElement("style");
style.textContent = `
  .blue-button.small {
    background-color: #007bff;
    color: white;
    border: none;
    padding: 6px 10px;
    font-size: 0.85rem;
    border-radius: 6px;
    cursor: pointer;
    transition: background-color 0.2s ease-in-out;
    margin-right: 4px;
  }
  .blue-button.small:hover {
    background-color: #0056b3;
  }
`;
document.head.appendChild(style);

style.textContent += `
  

  .inline-container button {
    transition: transform 0.1s ease;
  }

  

  .container1.inline-container {
    padding: 12px 16px;
    margin-bottom: 12px;
    background-color: #f9f9f9;
    border-radius: 12px;
    display: flex;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
  }

  .container1.inline-container div {
    min-width: 120px;
  }

  .container1.inline-container p.lesser {
    margin: 0;
    font-size: 0.8rem;
    color: #666;
  }

  .container1.inline-container p:not(.lesser) {
    margin: 4px 0 0;
    font-weight: 500;
  }

  .gray-button {
    background-color: #6c757d;
    color: white;
    border: none;
    padding: 6px 10px;
    font-size: 0.85rem;
    border-radius: 6px;
    cursor: pointer;
    transition: background-color 0.2s ease-in-out;
    margin-right: 4px;
    display: inline-flex;
    align-items: center;
    gap: 4px;
  }
  .gray-button:hover {
    background-color: #5a6268;
  }

  .card-green {
    border: 2px solid #28a745;
    border-radius: 10px;
    box-shadow: 0 0 8px rgba(40, 167, 69, 0.2);
  }
  .card-red {
    border: 2px solid #dc3545;
    border-radius: 10px;
    box-shadow: 0 0 8px rgba(220, 53, 69, 0.2);
  }
`;

async function fetchUser(id) {
    try {
        const response = await fetch('/api/get_user?id=' + id);
        if (!response.ok) throw new Error('Failed to fetch user');

        const jsonData = await response.json();
        userData = jsonData.response;

        main();
        loadUserCards(userData.id); // Fetch cards for user ID (e.g. dsachmanyan25)

    } catch (error) {
        console.error('Error fetching users:', error);
    }
}

function updateUserProfile(user) {
  var containers = document.getElementsByClassName("container1");
  var profileContainer = document.getElementsByClassName("inline-container")[1];

  profileContainer.children[0].getElementsByTagName("p")[1].textContent = user.name;
  profileContainer.children[1].getElementsByTagName("p")[1].textContent = user.id;
  profileContainer.children[2].getElementsByTagName("p")[1].textContent = user.position;
  profileContainer.children[3].getElementsByTagName("p")[1].textContent = user.score;
}

function formatTime(timestamp) {
  var date = new Date(timestamp * 1000);
  var hours = date.getHours() % 12 || 12;
  var minutes = date.getMinutes();
  return hours + ":" + (minutes < 10 ? "0" + minutes : minutes);
}

function formatDate(timestamp) {
  const date = new Date(timestamp * 1000);
  return date.toLocaleDateString("en-US");
}

function formatDuration(seconds) {
  var hrs = Math.floor(seconds / 3600);
  var mins = Math.floor((seconds % 3600) / 60);
  var hStr = hrs < 10 ? "0" + hrs : hrs;
  var mStr = mins < 10 ? "0" + mins : mins;
  return hStr + ":" + mStr;
}

function getCurrentDateFormatted() {
  var date = new Date();
  var m = date.getMonth() + 1;
  var d = date.getDate();
  var y = date.getFullYear() % 100;
  if (m < 10) m = "0" + m;
  if (d < 10) d = "0" + d;
  if (y < 10) y = "0" + y;
  return m + "/" + d + "/" + y;
}

function groupAttendance(attendanceArray) {
  var groups = {};
  attendanceArray.forEach(function(record) {
    if (!groups[record.date]) {
      groups[record.date] = [];
    }
    groups[record.date].push(record);
  });
  return groups;
}

function getRecordsForDate(date, attendance) {
  return attendance.filter(function(record) {
    return record.date === date;
  });
}

function createCardForDate(date, records) {
  var currentDate = getCurrentDateFormatted();
  var cardDiv = document.createElement("div");
  cardDiv.className = "container1 inline-container";

  var totalSeconds = 0;
  records.forEach(function(record) {
    if (record.out !== null) {
      totalSeconds += (record.out - record.in);
    } else if (date === currentDate) {
      var nowInSeconds = Math.floor(Date.now() / 1000);
      totalSeconds += (nowInSeconds - record.in);
    }
  });

  var historySpans = "";
  records.forEach(function(record) {
    var inTime = formatTime(record.in);
    var outTime = record.out ? formatTime(record.out) : "Present";
    historySpans += '<span class="check-in-out">' + inTime +
                    ' <span class="lesser">-</span> ' + outTime + '</span>';
  });

  if (date === currentDate) {
    cardDiv.innerHTML = ''
      + '<div>'
      +   '<p class="lesser">Date</p>'
      +   '<p>' + date + '</p>'
      + '</div>'
      + '<div>'
      +   '<p class="lesser">Currently Present</p>'
      +   '<p>' + formatDuration(totalSeconds) + '</p>'
      + '</div>'
      + '<div>'
      +   '<span class="lesser">Today\'s Check-in History</span>'
      +   historySpans
      + '</div>';
  } else {
    cardDiv.innerHTML = ''
      + '<div>'
      +   '<span class="lesser">Date: </span> <span>' + date + '</span>'
      + '</div>'
      + '<div>'
      +   '<span class="lesser">Time Present: </span> <span>' + formatDuration(totalSeconds) + '</span>'
      + '</div>'
      + '<div>'
      +   '<span class="lesser">History</span>'
      +   historySpans
      + '</div>';
  }
  return cardDiv;
}

function renderUsers(user) {
  var container = document.getElementById("attendanceCards");
  if (!container) {
    console.error("Element with id='attendanceCards' not found in the DOM.");
    return;
  }

  container.innerHTML = "";
  var currentDate = getCurrentDateFormatted();

  var recordsForToday = getRecordsForDate(currentDate, user.attendance);
  var todayCard = createCardForDate(currentDate, recordsForToday);
  container.appendChild(todayCard);

  var groups = groupAttendance(user.attendance);
  for (var date in groups) {
    if (groups.hasOwnProperty(date) && date !== currentDate) {
      var card = createCardForDate(date, groups[date]);
      container.appendChild(card);
    }
  }
}

function downloadJSON(jsonData) {
    if (!jsonData) {
        console.error('Invalid JSON data');
        return;
    }

    const jsonString = JSON.stringify(jsonData, null, 2);
    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = jsonData.name.replace(" ", "");
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    URL.revokeObjectURL(url);
}

async function generateCardImage(card) {
  const userRes = await fetch(`/api/get_user?id=${card.user_id}`);
  const userJson = await userRes.json();
  const user = userJson.response;

  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");
  const base = new Image();
  base.src = "/static/id.png";

  await new Promise(resolve => base.onload = resolve);

  // Wait for fonts to load
  await document.fonts.load("45px 'Work Sans'");
  await document.fonts.load("35px 'JetBrains Mono'");

  canvas.width = base.width;
  canvas.height = base.height;
  ctx.drawImage(base, 0, 0);

  ctx.fillStyle = "black";
  ctx.font = "45px 'Work Sans'";
  ctx.fillText(user.name, 60, 430);
  ctx.fillText(user.id, 60, 580);
  ctx.fillText(user.position, 60, 730);

  ctx.fillStyle = "#555555";
  ctx.font = "35px 'JetBrains Mono'";
  ctx.fillText(`#${String(card.id).padStart(6, '0')}`, 385, 872);
  ctx.fillText(card.academic_year, 345, 915);

  const link = document.createElement("a");
  link.download = `${user.name.replace(/\\s/g, '')}-${card.id}.png`;
  link.href = canvas.toDataURL("image/png");
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

async function loadUserCards(userId) {
  const res = await fetch(`/api/get_cards_from?user_id=${userId}`);
  const data = await res.json();
  const cards = data.response;

  const container = document.getElementById("cardDisplay");
  if (!container) return;
  container.innerHTML = "";

  const header = document.createElement("div");
  header.className = "inline-container";
  header.innerHTML = `
    <p><b>Center ID Cards</b></p>
    <button class="green-button" onclick="createNewCard()">Create New</button>
  `;

  container.appendChild(header);
  container.appendChild(document.createElement("hr"));

  cards.slice().reverse().forEach(card => {
    const year = card.academic_year;
    const endYear = parseInt(year.split("-")[1]);
    const expiresDate = new Date(`${endYear}-05-22T00:00:00`);
    const today = new Date();
    const diffDays = Math.ceil((expiresDate - today) / (1000 * 60 * 60 * 24));
    const expiresStr = expiresDate.toLocaleDateString("en-US") + ` (in ${diffDays} days)`;

    const issuedStr = formatDate(card.issued);
    const toggleText = card.enabled ? "Deactivate" : "Activate";
    const toggleClass = card.enabled ? "red-button" : "green-button";

    const div = document.createElement("div");
    const isExpired = today > expiresDate;
    const cardStatusClass = (card.enabled && !isExpired) ? "card-green" : "card-red";
    div.className = `container1 inline-container ${cardStatusClass}`;
    div.innerHTML = `
        <div>
            <p class="lesser">Card ID</p>
            <p><b>${String(card.id).padStart(6, '0')}</b></p>
        </div>
        <div>
            <p class="lesser">Academic Year</p>
            <p>${year}</p>
        </div>
        <div>
            <p class="lesser">Expires</p>
            <p>${expiresStr}</p>
        </div>
        <div>
            <p class="lesser">Issued</p>
            <p>${issuedStr}</p>
        </div>
        <div>
            <button class="gray-button" onclick='generateCardImage(${JSON.stringify(card)})'>Download</button>
            <button class="${toggleClass}" onclick="toggleCard('${card.id}', ${!card.enabled})">
                ${toggleText}
            </button>
            <button class="red-button" onclick="deleteCard('${card.id}')">
                <i class="bi bi-trash3-fill"></i>
            </button>
        </div>
    `;
    container.appendChild(div);
  });
}

async function toggleCard(id, enabled) {
    await fetch("/api/update_card", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id, enabled })
    });
    location.reload();
}

async function deleteCard(id) {
    await fetch("/api/delete_card", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id })
    });
    location.reload();
}

async function createNewCard() {
    const year = "2024-2025";
    const endYear = parseInt(year.split("-")[1]);
    const expires = `05/22/${String(endYear).slice(-2)}`;

    const res = await fetch("/api/create_card", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            user_id: userData.id,
            year: year,
            expires: expires
        })
    });

    const result = await res.json();
    if (result.status === 201) {
        location.reload();
    } else {
        alert("Failed to create card: " + result.response);
    }
}

function main() {
  updateUserProfile(userData);
  renderUsers(userData);
}
