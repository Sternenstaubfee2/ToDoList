/* === Task Dashboard — Frontend Logic === */

const PROJECT = document.body.dataset.project;
const API = `/api/${PROJECT}`;

// --- Drag & Drop ---
let draggedCard = null;

document.addEventListener('DOMContentLoaded', () => {
  initDragDrop();
  initCardActions();
  initAddButtons();
});

function initDragDrop() {
  document.querySelectorAll('.task-card').forEach(card => {
    card.addEventListener('dragstart', e => {
      draggedCard = card;
      card.classList.add('dragging');
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', card.dataset.id);
    });
    card.addEventListener('dragend', () => {
      card.classList.remove('dragging');
      draggedCard = null;
      document.querySelectorAll('.drag-over').forEach(el => el.classList.remove('drag-over'));
    });
  });

  document.querySelectorAll('.column-body').forEach(col => {
    col.addEventListener('dragover', e => {
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move';
      col.classList.add('drag-over');
    });
    col.addEventListener('dragleave', () => col.classList.remove('drag-over'));
    col.addEventListener('drop', e => {
      e.preventDefault();
      col.classList.remove('drag-over');
      const taskId = e.dataTransfer.getData('text/plain');
      const newStatus = col.dataset.status;
      updateTaskStatus(taskId, newStatus);
    });
  });
}

function initCardActions() {
  // Edit button
  document.querySelectorAll('.edit-btn').forEach(btn => {
    btn.addEventListener('click', e => {
      e.stopPropagation();
      const card = btn.closest('.task-card');
      openEditModal(card.dataset.id);
    });
  });

  // Delete button
  document.querySelectorAll('.delete-btn').forEach(btn => {
    btn.addEventListener('click', e => {
      e.stopPropagation();
      const card = btn.closest('.task-card');
      if (confirm('Task wirklich löschen?')) {
        deleteTask(card.dataset.id);
      }
    });
  });

  // Click card to expand description
  document.querySelectorAll('.task-card').forEach(card => {
    card.addEventListener('dblclick', () => openEditModal(card.dataset.id));
  });
}

function initAddButtons() {
  document.querySelectorAll('.add-task-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const status = btn.dataset.status;
      openAddModal(status);
    });
  });
}

// --- API Calls ---
async function updateTaskStatus(taskId, newStatus) {
  try {
    const res = await fetch(`${API}/tasks/${taskId}`, {
      method: 'PUT',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({status: newStatus}),
    });
    if (res.ok) {
      toast('Status aktualisiert', 'success');
      setTimeout(() => location.reload(), 300);
    }
  } catch (err) {
    toast('Fehler beim Aktualisieren', 'error');
  }
}

async function deleteTask(taskId) {
  try {
    const res = await fetch(`${API}/tasks/${taskId}`, {method: 'DELETE'});
    if (res.ok) {
      toast('Task gelöscht', 'success');
      const card = document.querySelector(`.task-card[data-id="${taskId}"]`);
      if (card) card.remove();
    }
  } catch (err) {
    toast('Fehler beim Löschen', 'error');
  }
}

async function createTask(data) {
  try {
    const res = await fetch(`${API}/tasks`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(data),
    });
    if (res.ok) {
      toast('Task erstellt', 'success');
      setTimeout(() => location.reload(), 300);
    } else {
      const err = await res.text();
      toast(`Fehler ${res.status}: ${err}`, 'error');
      console.error('Create failed:', res.status, err);
    }
  } catch (err) {
    toast('Fehler beim Erstellen: ' + err.message, 'error');
    console.error('Create exception:', err);
  }
}

async function saveTask(taskId, data) {
  try {
    const res = await fetch(`${API}/tasks/${taskId}`, {
      method: 'PUT',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(data),
    });
    if (res.ok) {
      toast('Task gespeichert', 'success');
      setTimeout(() => location.reload(), 300);
    }
  } catch (err) {
    toast('Fehler beim Speichern', 'error');
  }
}

async function gitSync() {
  try {
    toast('Git-Sync läuft...', 'success');
    const res = await fetch(`${API}/git-sync`, {method: 'POST'});
    const data = await res.json();
    if (data.error) {
      toast(data.error, 'error');
    } else {
      const n = data.matched?.length || 0;
      toast(`${data.scanned_commits} Commits gescannt, ${n} Tasks aktualisiert`, 'success');
      if (n > 0) setTimeout(() => location.reload(), 1000);
    }
  } catch (err) {
    toast('Git-Sync fehlgeschlagen', 'error');
  }
}

// --- Modal ---
function openAddModal(status = 'todo') {
  const overlay = document.getElementById('modal-overlay');
  const form = document.getElementById('task-form');
  document.getElementById('modal-title').textContent = 'Neuer Task';
  form.reset();
  document.getElementById('field-status').value = status;
  document.getElementById('field-task-id').value = '';
  document.getElementById('field-effort').value = '';
  document.getElementById('field-time-estimate').value = '';
  document.getElementById('field-assignee').value = 'Julia';
  document.getElementById('btn-delete-task').style.display = 'none';
  overlay.classList.add('active');
}

function openEditModal(taskId) {
  fetch(`${API}/tasks`).then(r => r.json()).then(tasks => {
    const task = tasks.find(t => t.id === taskId);
    if (!task) return;
    const overlay = document.getElementById('modal-overlay');
    document.getElementById('modal-title').textContent = 'Task bearbeiten';
    document.getElementById('field-task-id').value = task.id;
    document.getElementById('field-title').value = task.title;
    document.getElementById('field-description').value = task.description || '';
    document.getElementById('field-category').value = task.category;
    document.getElementById('field-priority').value = task.priority;
    document.getElementById('field-status').value = task.status;
    document.getElementById('field-effort').value = task.effort || '';
    document.getElementById('field-time-estimate').value = task.time_estimate || '';
    document.getElementById('field-assignee').value = task.assignee || 'Julia';
    document.getElementById('field-notes').value = task.notes || '';
    document.getElementById('btn-delete-task').style.display = 'block';
    overlay.classList.add('active');
  });
}

function closeModal() {
  document.getElementById('modal-overlay').classList.remove('active');
}

function submitModal() {
  const taskId = document.getElementById('field-task-id').value;
  const data = {
    title: document.getElementById('field-title').value,
    description: document.getElementById('field-description').value,
    category: document.getElementById('field-category').value,
    priority: parseInt(document.getElementById('field-priority').value) || 2,
    status: document.getElementById('field-status').value,
    effort: document.getElementById('field-effort').value,
    time_estimate: document.getElementById('field-time-estimate').value,
    assignee: document.getElementById('field-assignee').value,
    notes: document.getElementById('field-notes').value,
  };
  if (!data.title) { toast('Titel ist erforderlich', 'error'); return; }
  if (taskId) {
    saveTask(taskId, data);
  } else {
    createTask(data);
  }
  closeModal();
}

function deleteFromModal() {
  const taskId = document.getElementById('field-task-id').value;
  if (taskId && confirm('Task wirklich löschen?')) {
    deleteTask(taskId);
    closeModal();
  }
}

// --- Member management ---
async function addMemberPrompt() {
  const name = prompt('Name der neuen Person:');
  if (!name || !name.trim()) return;
  try {
    const res = await fetch(`${API}/members`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({name: name.trim()}),
    });
    if (res.ok) {
      const members = await res.json();
      const select = document.getElementById('field-assignee');
      // Rebuild options
      select.innerHTML = '';
      members.forEach(m => {
        const opt = document.createElement('option');
        opt.value = m;
        opt.textContent = m;
        if (m === name.trim()) opt.selected = true;
        select.appendChild(opt);
      });
      toast(`${name.trim()} hinzugefügt`, 'success');
    }
  } catch (err) {
    toast('Fehler beim Hinzufügen', 'error');
  }
}

// Close on overlay click
document.addEventListener('click', e => {
  if (e.target.id === 'modal-overlay') closeModal();
});

// Close on Escape
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeModal();
});

// --- Toast ---
function toast(message, type = 'success') {
  const container = document.querySelector('.toast-container') || createToastContainer();
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.innerHTML = `${type === 'success' ? '&#10003;' : '&#10007;'} ${message}`;
  container.appendChild(t);
  setTimeout(() => t.remove(), 3000);
}

function createToastContainer() {
  const c = document.createElement('div');
  c.className = 'toast-container';
  document.body.appendChild(c);
  return c;
}
