// Force polling only - instant clicks on Render free tier
const socket = io({
    transports: ['polling'],  // No WebSocket = no delay
    reconnectionAttempts: 5,
    timeout: 10000
});

// Mouse aura effect (kept)
document.querySelectorAll('.card').forEach(card => {
    card.addEventListener('mousemove', (e) => {
        const rect = card.getBoundingClientRect();
        const x = ((e.clientX - rect.left) / rect.width) * 100;
        const y = ((e.clientY - rect.top) / rect.height) * 100;
        card.style.setProperty('--mouse-x', `${x}%`);
        card.style.setProperty('--mouse-y', `${y}%`);
    });
});

// Update with aura pulse
function updateWithAura(el, newText) {
    el.classList.remove('updating');
    void el.offsetWidth;
    el.textContent = newText;
    el.classList.add('updating');
    setTimeout(() => el.classList.remove('updating'), 1000);
}

// Real-time updates
socket.on('attendance_update', data => {
    const el = document.getElementById('att-' + data.service);
    if (el) updateWithAura(el, data.total.toLocaleString());
});

socket.on('offering_update', data => {
    const el = document.getElementById('off-' + data.service);
    if (el) updateWithAura(el, 'GH₵' + data.total.toFixed(2));
});

// Optional: monthly
socket.on('monthly_att_update', data => {
    const el = document.getElementById('monthly-att-' + data.service);
    if (el) updateWithAura(el, data.total.toLocaleString());
});
socket.on('monthly_off_update', data => {
    const el = document.getElementById('monthly-off-' + data.service);
    if (el) updateWithAura(el, 'GH₵' + data.total.toFixed(2));
});
