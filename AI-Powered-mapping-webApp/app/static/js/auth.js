document.addEventListener('DOMContentLoaded', () => {
    // Handle login/register form submission
    const forms = document.querySelectorAll('.auth-form');
    forms.forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(form);
            const action = form.getAttribute('action');
            
            try {
                const response = await fetch(action, {
                    method: 'POST',
                    body: formData
                });
                
                if (response.redirected) {
                    window.location.href = response.url;
                } else {
                    const data = await response.json();
                    alert(data.message || 'Action completed');
                }
            } catch (error) {
                alert('Error: ' + error.message);
            }
        });
    });
});