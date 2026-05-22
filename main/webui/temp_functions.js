// 在 cancelLongTask 函数后添加以下函数

async function startEditLongTask() {
  const contentEl = document.getElementById('longtask-content');
  const editEl = document.getElementById('longtask-edit');
  const editorEl = document.getElementById('longtask-editor');
  const textEl = document.getElementById('longtask-text');
  
  // 将当前内容填入编辑器
  editorEl.value = textEl.textContent || '';
  
  // 切换显示
  contentEl.style.display = 'none';
  editEl.style.display = 'block';
  
  showNotification('进入编辑模式', 'info');
}

async function saveLongTask() {
  const editorEl = document.getElementById('longtask-editor');
  const content = editorEl.value;
  
  try {
    const response = await fetch(`${API_BASE}/longtask/update`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content })
    });
    if (!response.ok) throw new Error('API 请求失败');
    const data = await response.json();
    
    showNotification(data.message || '长期任务已更新', 'success');
    
    // 退出编辑模式并刷新
    document.getElementById('longtask-edit').style.display = 'none';
    await loadLongTask();
  } catch (error) {
    console.error('保存长期任务失败:', error);
    showNotification('保存失败: ' + error.message, 'error');
  }
}

function cancelEditLongTask() {
  document.getElementById('longtask-edit').style.display = 'none';
  document.getElementById('longtask-content').style.display = 'block';
  showNotification('已取消编辑', 'info');
}
