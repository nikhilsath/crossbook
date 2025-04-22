export function initRichTextEditor(field) {
    const editor = document.getElementById(`editor_${field}`);
    const hidden = document.getElementById(`hidden_${field}`);
  
    if (!editor || !hidden) return;
  
    const container = editor.closest('.mb-4');
    const buttons = container.querySelectorAll('[data-command]');
  
    buttons.forEach(btn => {
      btn.addEventListener("click", () => {
        const cmd = btn.getAttribute("data-command");
        document.execCommand(cmd, false, null);
        editor.focus();
      });
    });
  
    editor.addEventListener("input", () => {
      hidden.value = editor.innerHTML;
    });
  
    hidden.value = editor.innerHTML;
  }
  