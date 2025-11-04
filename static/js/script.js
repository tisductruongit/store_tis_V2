document.addEventListener('DOMContentLoaded', function() {
    console.log('JavaScript is running!');

    const messages = document.querySelector('.messages');
    if (messages) {
        setTimeout(() => {
            messages.style.transition = 'opacity 1s ease-out';
            messages.style.opacity = '0';
            setTimeout(() => messages.remove(), 1000); 
        }, 5000); // Ẩn sau 5 giây
    }
});