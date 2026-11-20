// The directory uses ordinary GET forms; this script handles sign-out only.
const guestLogout = document.getElementById('logout');
guestLogout.addEventListener('click', async () => {
  guestLogout.disabled = true;
  const feedback = document.getElementById('feedback');
  feedback.textContent = '';
  try {
    const {csrf} = JSON.parse(document.getElementById('config').textContent);
    const response = await fetch('/api/logout', {
      method: 'POST', headers: {'Content-Type': 'application/json', 'X-CSRF-Token': csrf}, body: '{}'
    });
    if (!response.ok) throw new Error('Could not sign out. Reload the page and try again.');
    location.assign('/login');
  } catch (error) {
    feedback.textContent = error.message || 'Could not sign out. Please try again.';
    guestLogout.disabled = false;
  }
});
