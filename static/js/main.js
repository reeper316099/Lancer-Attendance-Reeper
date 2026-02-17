// Main JavaScript file for RFID Attendance System

// Close modals when clicking outside
window.onclick = function(event) {
    const modals = document.getElementsByClassName('modal');
    for (let modal of modals) {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    }
}

// Utility functions
function formatTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
    });
}

function formatDate(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
    });
}

function formatDateTime(timestamp) {
    return `${formatDate(timestamp)} ${formatTime(timestamp)}`;
}

// Show notification
function showNotification(message, type = 'info') {
    // This is a placeholder for future notification system
    console.log(`[${type.toUpperCase()}] ${message}`);
}

// Handle AJAX errors
function handleError(error) {
    console.error('Error:', error);
    showNotification('An error occurred. Please try again.', 'error');
}

console.log('RFID Attendance System loaded');
