'use strict';
document.getElementById('review').addEventListener('submit', function (event) {
  event.preventDefault();
  const title = document.getElementById('title').value.trim();
  const description = document.getElementById('description').value.trim();
  const audience = document.getElementById('audience').value;
  const quality = document.getElementById('quality').checked;
  const rights = document.getElementById('rights').checked;
  const ok = title && description && audience && quality && rights;
  document.getElementById('summary').textContent = ok
    ? 'Local fields complete. No file, account, channel or permissions are verified. Nothing uploaded.'
    : 'Complete the local fields and acknowledgements. Nothing uploaded.';
});
