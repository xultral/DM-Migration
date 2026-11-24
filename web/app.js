'use strict';

const paths = {
  database: '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v7c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 12v7c0 1.7 3.6 3 8 3s8-1.3 8-3v-7"/>',
  shuffle: '<path d="m18 3 3 3-3 3M3 18h3c4 0 7-12 11-12h4M18 15l3 3-3 3M3 6h3c2 0 3.5 3 5 6M14 15c1 2 2 3 3 3h4"/>',
  upload: '<path d="M12 16V3m-5 5 5-5 5 5M4 16v4a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-4"/>',
  download: '<path d="M12 3v13m-5-5 5 5 5-5M4 16v4a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-4"/>',
  history: '<path d="M3 10a9 9 0 1 1 2 8M3 4v6h6M12 7v5l3 2"/>',
  settings: '<path d="m10 3-1 3-3 1-3-1-2 4 3 2v2l-3 2 2 4 3-1 3 1 1 3h4l1-3 3-1 3 1 2-4-3-2v-2l3-2-2-4-3 1-3-1-1-3Z" transform="translate(0 -1) scale(.95)"/><circle cx="12" cy="12" r="3"/>',
  help: '<circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 0 1 5 0c0 2-2.5 2-2.5 4M12 17h.01"/>',
  terminal: '<rect x="3" y="4" width="18" height="16" rx="3"/><path d="m7 9 3 3-3 3m6 0h4"/>',
  power: '<path d="M12 2v10M6 5a9 9 0 1 0 12 0"/>',
  'chevron-right': '<path d="m9 5 7 7-7 7"/>',
  'arrow-right': '<path d="M4 12h16m-6-6 6 6-6 6"/>',
  'arrow-left': '<path d="M20 12H4m6-6-6 6 6 6"/>',
  folder: '<path d="M3 7V5a2 2 0 0 1 2-2h4l3 3h7a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z"/>',
  shield: '<path d="M12 2 3 6v6c0 6 9 10 9 10s9-4 9-10V6Z"/><path d="m8 12 3 3 5-6"/>',
  server: '<rect x="3" y="3" width="18" height="7" rx="2"/><rect x="3" y="14" width="18" height="7" rx="2"/><path d="M7 6.5h.01M7 17.5h.01M11 6.5h6M11 17.5h6"/>',
  user: '<circle cx="12" cy="7" r="4"/><path d="M4 21v-2a8 8 0 0 1 16 0v2"/>',
  lock: '<rect x="4" y="10" width="16" height="12" rx="2"/><path d="M7 10V7a5 5 0 0 1 10 0v3M12 15v3"/>',
  eye: '<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/>',
  'eye-off': '<path d="m3 3 18 18M10.5 5.1A12 12 0 0 1 12 5c6 0 10 7 10 7a18 18 0 0 1-3.2 3.9M6 6a18 18 0 0 0-4 6s4 7 10 7a12 12 0 0 0 5-1M9.8 9.8a3 3 0 0 0 4.4 4.4"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7h.01"/>',
  plug: '<path d="M8 2v5M16 2v5M5 7h14v3a7 7 0 0 1-14 0ZM12 17v5"/>',
  sparkles: '<path d="m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5ZM20 2v4M18 4h4"/>',
  edit: '<path d="m16 3 5 5M4 16l13-13a2.1 2.1 0 0 1 3 3L7 19l-4 1ZM12 21h9"/>',
  file: '<path d="M14 2H5a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V9Zm0 0v7h7M7 14h10M7 18h7"/>',
  layers: '<path d="m12 2 10 5-10 5L2 7Zm-10 10 10 5 10-5M2 17l10 5 10-5"/>',
  search: '<circle cx="10.5" cy="10.5" r="7.5"/><path d="m16 16 6 6"/>',
  refresh: '<path d="M3 10a9 9 0 0 1 16-6l2 3M21 3v4h-4M21 14A9 9 0 0 1 5 20l-2-3M3 21v-4h4"/>',
  table: '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 9v12M3 15h18"/>',
  'check-circle': '<circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/>',
  check: '<path d="m5 12 4 4L19 6"/>',
  sliders: '<path d="M4 7h4m4 0h8M4 17h8m4 0h4"/><circle cx="10" cy="7" r="2"/><circle cx="14" cy="17" r="2"/>',
  copy: '<rect x="8" y="8" width="13" height="13" rx="2"/><path d="M16 8V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h3"/>',
  package: '<path d="m12 2 9 5v10l-9 5-9-5V7Zm0 10 9-5M12 12 3 7M12 12v10M7 4.5l9 5"/>',
  zap: '<path d="M13 2 3 14h8l-1 8L21 9h-8Z"/>',
  stop: '<rect x="5" y="5" width="14" height="14" rx="2"/>',
  x: '<path d="m6 6 12 12M6 18 18 6"/>',
  alert: '<path d="m10.5 3-9 16a1.7 1.7 0 0 0 1.5 2h18a1.7 1.7 0 0 0 1.5-2l-9-16a1.7 1.7 0 0 0-3 0ZM12 9v4M12 17h.01"/>',
  loader: '<path d="M12 3a9 9 0 1 1-9 9"/>',
};

const $ = (id) => document.getElementById(id);
const all = (selector, root = document) => [...root.querySelectorAll(selector)];
const escapeHtml = (value) => String(value ?? '').replace(/[&<>"']/g, (char) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const icon = (name) => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name] || paths.info}</svg>`;
function renderIcons(root = document) { all('[data-icon]', root).forEach((node) => { node.innerHTML = icon(node.dataset.icon); }); }
renderIcons();

const fragment = new URLSearchParams(location.hash.slice(1));
const initialToken = fragment.get('token');
if (initialToken) {
  sessionStorage.setItem('dm-session-token', initialToken);
  history.replaceState(null, '', location.pathname + location.search);
}
const state = {
  token: initialToken || sessionStorage.getItem('dm-session-token') || '',
  boot: null,
  mode: 'migrate',
  page: 'migration',
  step: 0,
  connections: {source: {status:'idle', signature:null}, target: {status:'idle', signature:null}},
  tables: [],
  selected: new Set(),
  selectedSchema: '',
  tablesLoaded: false,
  tablesLoading: false,
  tableError: '',
  tableGeneration: 0,
  job: null,
  activeJobId: null,
  events: [],
  lastSequence: 0,
  pollTimer: null,
  polling: false,
  busy: false,
};

const modeLabels = {migrate:'数据库迁移', export:'导出数据', import:'导入数据'};
const statusLabels = {idle:'准备就绪', queued:'等待启动', preparing:'验证连接', exporting:'正在导出', importing:'正在导入', success:'已完成', warning:'完成 · 有警告', failed:'失败', cancelled:'已停止', interrupted:'运行中断'};
const phaseLabels = {pending:'等待', running:'进行中', completed:'完成', skipped:'跳过', failed:'失败', cancelled:'已停止'};
const activeStatuses = new Set(['queued','preparing','exporting','importing']);
const strategies = {SKIP:'跳过已存在的表', APPEND:'追加数据', TRUNCATE:'清空后导入', REPLACE:'删除并重建表'};

function toast(message, level = 'success', duration = 5500) {
  const node = document.createElement('div');
  node.className = `toast ${level}`;
  node.innerHTML = `<span>${icon(level === 'error' ? 'alert' : level === 'warning' ? 'info' : 'check-circle')}</span><div>${escapeHtml(message)}</div><button aria-label="关闭提示">${icon('x')}</button>`;
  node.querySelector('button').addEventListener('click', () => node.remove());
  $('toast-container').append(node);
  setTimeout(() => node.remove(), duration);
}

async function api(path, options = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), options.timeout || 45000);
  try {
    const response = await fetch(path, {
      method: options.body === undefined ? 'GET' : 'POST',
      headers: {'X-App-Token': state.token, ...(options.body === undefined ? {} : {'Content-Type':'application/json'})},
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
      signal: controller.signal,
    });
    if (options.blob && response.ok) return await response.blob();
    const data = await response.json();
    if (!response.ok) {
      if (data.code === 'session_expired') showStartupError(data.error);
      throw new Error(data.error || `请求失败 (${response.status})`);
    }
    return data;
  } catch (error) {
    if (error.name === 'AbortError') throw new Error('操作超时，请检查数据库地址、端口与网络后重试。');
    if (error instanceof TypeError) throw new Error('无法连接本地服务，请确认迁移工具仍在运行。');
    throw error;
  } finally { clearTimeout(timer); }
}

function getConnection(role) {
  return {host: $(`${role}-host`).value.trim(), port: Number($(`${role}-port`).value), username:$(`${role}-username`).value, password:$(`${role}-password`).value};
}
function connectionSignature(role) { return JSON.stringify(getConnection(role)); }
function setConnection(role, profile, clearPassword = true) {
  if (!profile) return;
  for (const key of ['host','port','username']) if (profile[key] !== undefined) $(`${role}-${key}`).value = profile[key];
  if (clearPassword) $(`${role}-password`).value = '';
  invalidateConnection(role);
}
function invalidateConnection(role, resetObjects = true) {
  state.connections[role] = {status:'idle', signature:null};
  updateConnection(role);
  if (role === 'source') {
    if (resetObjects) {
      state.tables = [];
      state.tablesLoaded = false;
      state.selected.clear();
    }
    state.tablesLoading = false;
    $('refresh-tables').classList.remove('spinning');
    state.tableGeneration++;
    renderTables();
    renderSelection();
  }
}
function updateConnection(role, message) {
  const connection = state.connections[role];
  const badge = $(`${role}-badge`);
  badge.className = `connection-badge ${connection.status === 'connected' ? 'connected' : connection.status === 'error' ? 'error' : connection.status === 'loading' ? 'loading' : ''}`;
  badge.innerHTML = `<i></i>${{idle:'未连接', loading:'连接中', connected:'已连接', error:'连接失败'}[connection.status]}`;
  const status = $(`${role}-message`);
  status.className = `connection-message ${connection.status === 'connected' ? 'success' : connection.status === 'error' ? 'error' : ''}`;
  const fallback = role === 'source' ? '使用有权读取所选数据表的账号。' : '目标 Schema 需存在，并具备建表与写入权限。';
  const text = message || connection.message || fallback;
  status.innerHTML = `<span>${icon(connection.status === 'connected' ? 'check-circle' : 'info')}</span><span>${escapeHtml(text)}</span>`;
  const button = document.querySelector(`[data-test="${role}"]`);
  button.disabled = connection.status === 'loading';
  button.innerHTML = `<span class="${connection.status === 'loading' ? 'spinning' : ''}">${icon(connection.status === 'loading' ? 'loader' : 'plug')}</span>${connection.status === 'loading' ? '正在连接' : '测试连接'}`;
}

async function testConnection(role, silent = false) {
  const config = getConnection(role);
  if (!config.host || !config.username || !config.password) throw new Error(`请填写${role === 'source' ? '源库' : '目标库'}地址、用户名和密码。`);
  const signature = connectionSignature(role);
  state.connections[role] = {status:'loading', signature:null};
  updateConnection(role);
  try {
    const result = await api('/api/database/test', {body:{connection:config}});
    if (signature !== connectionSignature(role)) throw new Error('连接信息已更改，请重新测试。');
    if (result.username) $(`${role}-username`).value = result.username;
    state.connections[role] = {status:'connected', signature:connectionSignature(role), message:result.version, result};
    const list = $(`${role}-schema-list`);
    list.innerHTML = result.schemas.map((schema) => `<option value="${escapeHtml(schema)}"></option>`).join('');
    const schemaInput = $(`${role}-schema`);
    if (!schemaInput.value || !result.schemas.includes(schemaInput.value)) schemaInput.value = result.schemas.includes(result.username) ? result.username : result.schemas[0] || config.username;
    updateConnection(role);
    updateMapping();
    if (!silent) toast(`${role === 'source' ? '源库' : '目标库'}连接成功。`);
    return result;
  } catch (error) {
    if (signature === connectionSignature(role)) {
      state.connections[role] = {status:'error', signature:null, message:error.message};
      updateConnection(role);
    }
    throw error;
  }
}

async function rememberProfiles() {
  if (!state.boot || state.activeJobId) return;
  const body = {bin_dir: state.boot.tools.bin_dir};
  for (const role of ['source','target']) {
    if ($(`${role}-remember`).checked) {
      const connection = getConnection(role);
      body[role] = {host:connection.host, port:connection.port, username:connection.username};
    }
  }
  const result = await api('/api/settings', {body});
  state.boot.settings = result.settings;
}

function setPage(page) {
  state.page = page;
  $('migration-page').classList.toggle('hidden', page !== 'migration');
  $('history-page').classList.toggle('hidden', page !== 'history');
  $('settings-page').classList.toggle('hidden', page !== 'settings');
  all('.nav-item').forEach((node) => node.classList.toggle('active', page === 'migration' ? node.dataset.mode === state.mode : node.dataset.page === page));
  $('breadcrumb-current').textContent = page === 'migration' ? modeLabels[state.mode] : page === 'history' ? '任务记录' : '环境设置';
  $('page-title').textContent = page === 'history' ? '任务记录' : page === 'settings' ? '准备好环境，即可出发。' : state.mode === 'export' ? '把数据，妥善保存。' : state.mode === 'import' ? '让数据，在新库就位。' : '让数据，顺利抵达。';
  $('page-description').textContent = page === 'history' ? '每次任务的执行结果、转储文件和运行日志，都在这里。' : page === 'settings' ? '检测达梦官方工具，配置本机运行环境。' : state.mode === 'export' ? '将指定数据表导出为达梦转储文件，保存在本机。' : state.mode === 'import' ? '选择本机的达梦转储文件，导入目标数据库。' : '选择源库中的数据表，迁移至目标达梦数据库。';
  document.querySelector('.eyebrow').textContent = page === 'history' ? 'TASK HISTORY' : page === 'settings' ? 'LOCAL ENVIRONMENT' : 'DATABASE TRANSFER';
  if (page === 'history') loadHistory().catch((error) => toast(error.message, 'error'));
}

function setMode(mode, reset = true) {
  state.mode = mode;
  if (reset) {
    clearTimeout(state.pollTimer);
    state.job = null;
    state.events = [];
    state.lastSequence = 0;
  }
  all('.target-only').forEach((node) => node.classList.toggle('hidden', mode === 'export'));
  all('.export-only').forEach((node) => node.classList.toggle('hidden', mode === 'import'));
  all('.import-only').forEach((node) => node.classList.toggle('hidden', mode !== 'import'));
  $('source-card').classList.toggle('hidden', mode === 'import');
  $('target-card').classList.toggle('hidden', mode === 'export');
  document.querySelector('.connection-bridge').classList.toggle('hidden', mode !== 'migrate');
  $('connection-grid').classList.toggle('single', mode !== 'migrate');
  $('connection-description').textContent = mode === 'export' ? '连接源数据库，准备导出指定表。' : mode === 'import' ? '连接目标数据库，准备导入转储文件。' : '建立两端连接，开始一次新的迁移。';
  $('table-section-title').textContent = mode === 'import' ? '选择文件与源 Schema' : '选择数据表';
  $('table-section-description').textContent = mode === 'import' ? '填写文件中的原始 Schema；可手动指定表，留空则导入整个文件。' : '选择源 Schema，然后勾选需要迁移的表。';
  $('refresh-tables').disabled = mode === 'import';
  $('manual-hint').textContent = mode === 'import' ? '不指定表时导入文件中的全部对象。筛选表时请使用文件中的原始表名。' : '手动输入与勾选的表会合并，重复表名自动去重。';
  if (mode === 'import') { state.tables = []; state.tablesLoaded = false; if (reset) { state.selected.clear(); state.selectedSchema = ''; } }
  setPage('migration');
  gotoStep(reset ? 0 : state.step);
}

function gotoStep(step) {
  state.step = Math.max(0, Math.min(3, step));
  for (let index = 0; index < 4; index++) $('step-' + index).classList.toggle('hidden', index !== state.step);
  all('.step').forEach((node) => {
    const index = Number(node.dataset.step);
    node.classList.toggle('active', index === state.step);
    node.classList.toggle('complete', index < state.step);
    node.setAttribute('aria-current', index === state.step ? 'step' : 'false');
    node.querySelector('.step-number').innerHTML = index < state.step ? icon('check') : String(index + 1);
  });
  if (state.step === 1) { renderTables(); renderSelection(); }
  if (state.step === 2) updateMapping();
  if (state.step === 3) { renderJob(); renderLogs(); }
  updateFooter();
}

function updateFooter() {
  const running = state.job && activeStatuses.has(state.job.status);
  $('previous-step').classList.toggle('hidden', state.step === 0 || Boolean(running));
  $('cancel-job').classList.toggle('hidden', !(state.step === 3 && running));
  $('next-step').disabled = state.busy || Boolean(state.step === 3 && running);
  const label = state.step === 0 ? '连接并继续' : state.step === 1 ? '配置迁移选项' : state.step === 2 ? '确认执行配置' : running ? '任务运行中' : state.job ? '创建新任务' : state.mode === 'export' ? '开始导出' : state.mode === 'import' ? '开始导入' : '开始迁移';
  $('next-step').innerHTML = `${state.busy ? `<span class="spinning">${icon('loader')}</span>` : ''}${label}<span>${icon(state.step === 3 && !state.job ? 'zap' : 'arrow-right')}</span>`;
  $('footer-note').textContent = state.step === 1 ? `${state.selected.size} 张表已选${state.mode === 'import' && !state.selected.size ? '，将导入文件中的全部对象' : '，可随时调整迁移清单'}` : state.step === 2 ? '执行前可查看参数，清空或替换表需要明确确认。' : state.step === 3 && running ? '关闭浏览器不会中断任务，请通过“停止任务”结束。' : '连接信息在本机处理，密码仅用于本次连接。';
}

async function nextStep() {
  if (state.busy) return;
  state.busy = true;
  updateFooter();
  try {
    if (state.step === 0) {
      const roles = state.mode === 'export' ? ['source'] : state.mode === 'import' ? ['target'] : ['source','target'];
      const results = await Promise.allSettled(roles.map((role) => state.connections[role].signature === connectionSignature(role) && state.connections[role].status === 'connected' ? Promise.resolve() : testConnection(role, true)));
      const failure = results.find((result) => result.status === 'rejected');
      if (failure) throw failure.reason;
      await rememberProfiles();
      gotoStep(1);
      if (state.mode !== 'import') await loadTables();
    } else if (state.step === 1) {
      validateTables();
      gotoStep(2);
    } else if (state.step === 2) {
      validateDraft();
      gotoStep(3);
    } else if (state.job) {
      state.job = null;
      state.events = [];
      state.lastSequence = 0;
      gotoStep(0);
    } else {
      validateDraft();
      await confirmStart();
    }
  } catch (error) { toast(error.message, 'error', 8000); }
  finally { state.busy = false; updateFooter(); }
}

function validateTables() {
  if (!$('source-schema').value.trim()) throw new Error(state.mode === 'import' ? '请填写转储文件中的原始 Schema。' : '请选择或输入源 Schema。');
  if (state.mode === 'import' && !$('dump-file').value.trim()) throw new Error('请选择需要导入的 .dmp 文件。');
  if (state.mode !== 'import' && !state.selected.size) throw new Error('请至少勾选一张表，或手动输入表名后添加到清单。');
}
function validateDraft() {
  validateTables();
  for (const role of state.mode === 'export' ? ['source'] : state.mode === 'import' ? ['target'] : ['source','target']) {
    const connection = getConnection(role);
    if (!connection.host || !connection.username || !connection.password) throw new Error(`请先配置${role === 'source' ? '源库' : '目标库'}连接并输入密码。`);
  }
  if (state.mode !== 'export' && !$('target-schema').value.trim()) throw new Error('请选择或输入目标 Schema。');
  if (!$('output-dir').value.trim()) throw new Error('请选择保存转储文件与日志的工作目录。');
  const parallel = Number($('option-parallel').value);
  const tableParallel = Number($('option-table-parallel').value);
  if (!Number.isInteger(parallel) || parallel < 1 || parallel > 100) throw new Error('并行线程数应为 1–100 的整数。');
  if (!Number.isInteger(tableParallel) || tableParallel < 1 || tableParallel > 50) throw new Error('单表导出线程数应为 1–50 的整数。');
}

async function loadTables() {
  if (state.mode === 'import') return;
  const schema = $('source-schema').value;
  if (!schema.trim()) throw new Error('请先选择或输入源 Schema。');
  const generation = ++state.tableGeneration;
  state.tablesLoading = true;
  state.tableError = '';
  $('refresh-tables').classList.add('spinning');
  renderTables();
  try {
    const result = await api('/api/database/tables', {body:{connection:getConnection('source'), schema}});
    if (generation !== state.tableGeneration) return;
    if (state.selectedSchema && state.selectedSchema !== schema) state.selected.clear();
    state.selectedSchema = schema;
    state.tables = result.tables;
    state.tablesLoaded = true;
  } catch (error) {
    if (generation !== state.tableGeneration) return;
    state.tableError = error.message; state.tables = []; state.tablesLoaded = false;
    throw error;
  } finally {
    if (generation === state.tableGeneration) {
      state.tablesLoading = false;
      $('refresh-tables').classList.remove('spinning');
      renderTables();
      renderSelection();
    }
  }
}

function filteredTables() {
  const term = $('table-search').value.trim().toLocaleLowerCase();
  return state.tables.filter((table) => !term || `${table.name} ${table.comment || ''}`.toLocaleLowerCase().includes(term));
}
function renderTables() {
  const tables = filteredTables();
  const body = $('tables-body');
  body.innerHTML = tables.map((table, index) => `<tr class="${state.selected.has(table.name) ? 'selected' : ''}"><td class="check-cell"><input type="checkbox" data-table-index="${index}" aria-label="选择 ${escapeHtml(table.name)}" ${state.selected.has(table.name) ? 'checked' : ''}></td><td><span class="table-name"><span>${icon('table')}</span>${escapeHtml(table.name)}</span></td><td class="rows-column">${table.estimated_rows == null ? '—' : Number(table.estimated_rows).toLocaleString('zh-CN')}</td><td class="comment-column" title="${escapeHtml(table.comment || '')}">${escapeHtml(table.comment || '—')}</td></tr>`).join('');
  body.querySelectorAll('[data-table-index]').forEach((input) => input.addEventListener('change', () => {
    const name = tables[Number(input.dataset.tableIndex)].name;
    if (input.checked) state.selected.add(name); else state.selected.delete(name);
    state.selectedSchema = $('source-schema').value;
    renderTables(); renderSelection();
  }));
  const count = tables.filter((table) => state.selected.has(table.name)).length;
  $('select-all').checked = tables.length > 0 && count === tables.length;
  $('select-all').indeterminate = count > 0 && count < tables.length;
  $('select-all').disabled = tables.length === 0;
  $('table-count').textContent = state.tablesLoading ? '正在加载…' : $('table-search').value ? `筛选 ${tables.length} / ${state.tables.length} 张表` : `共 ${state.tables.length} 张表`;
  const empty = $('table-empty');
  empty.classList.toggle('hidden', tables.length > 0);
  const heading = empty.querySelector('h3');
  const description = empty.querySelector('p');
  const action = $('empty-table-action');
  if (state.tablesLoading) {
    heading.textContent = '正在读取数据表'; description.textContent = '正在向源数据库请求当前 Schema 的表清单。'; action.classList.add('hidden');
  } else if (state.mode === 'import') {
    heading.textContent = '按需筛选文件中的表'; description.textContent = '通过“手动输入表名”指定表；也可以留空，导入全部对象。'; action.textContent = '手动输入表名'; action.classList.remove('hidden');
  } else if (state.tableError) {
    heading.textContent = '读取表清单失败'; description.textContent = state.tableError; action.textContent = '手动输入表名'; action.classList.remove('hidden');
  } else if (state.tablesLoaded) {
    heading.textContent = state.tables.length ? '没有匹配的数据表' : '当前 Schema 下没有可访问的数据表'; description.textContent = state.tables.length ? '试试其他表名或清空搜索条件。' : '请检查 Schema 名称和账号权限。'; action.textContent = '重新加载'; action.classList.remove('hidden');
  } else {
    heading.textContent = '等待读取数据表'; description.textContent = '连接源库后，选择 Schema 并加载表清单。'; action.textContent = '返回连接配置'; action.classList.remove('hidden');
  }
}
function renderSelection() {
  $('selected-count').textContent = state.selected.size;
  $('selected-description').textContent = state.selected.size ? `${state.selected.size} 张表将加入本次任务` : state.mode === 'import' ? '未筛选，将导入文件中的全部对象' : '从左侧表清单中勾选';
  $('selection-schema').textContent = state.selected.size ? $('source-schema').value : '';
  const names = [...state.selected];
  $('selected-tables').innerHTML = names.length ? names.slice(0,200).map((name, index) => `<div class="selected-item"><span>${icon('table')}</span><span>${escapeHtml(name)}</span><button data-remove-index="${index}" aria-label="移除 ${escapeHtml(name)}">${icon('x')}</button></div>`).join('') + (names.length > 200 ? `<div class="selection-empty">还有 ${names.length - 200} 张表</div>` : '') : `<div class="selection-empty">${state.mode === 'import' ? '将导入文件中的全部对象' : '你的迁移清单会显示在这里'}</div>`;
  $('selected-tables').querySelectorAll('[data-remove-index]').forEach((button) => button.addEventListener('click', () => { state.selected.delete(names[Number(button.dataset.removeIndex)]); renderTables(); renderSelection(); }));
  updateFooter();
}
function applyManualTables() {
  if (!$('source-schema').value.trim()) { toast('请先填写源 Schema，再添加表名。', 'error'); return; }
  const names = $('manual-tables').value.split(/\r?\n/).map((name) => name.trim()).filter(Boolean);
  if (!names.length) { toast('每行输入一个表名，再添加到清单。', 'warning'); return; }
  if (names.some((name) => name.length > 128 || /[\x00-\x1f]/.test(name))) { toast('表名不能超过 128 个字符或包含控制字符。', 'error'); return; }
  const before = state.selected.size;
  names.forEach((name) => state.selected.add(name));
  state.selectedSchema = $('source-schema').value;
  $('manual-tables').value = '';
  renderTables(); renderSelection();
  toast(`已添加 ${state.selected.size - before} 张表，重复表名已去重。`);
}

function getOptions() {
  const values = {};
  for (const key of ['rows','indexes','constraints','triggers','grants','compress']) values[key] = $('option-' + key).checked;
  return {...values, parallel:Number($('option-parallel').value), table_parallel:Number($('option-table-parallel').value), table_exists:document.querySelector('input[name="table-exists"]:checked').value};
}
function buildRequest(confirmation = '') {
  return {
    mode:state.mode,
    source:state.mode === 'import' ? null : getConnection('source'),
    target:state.mode === 'export' ? null : getConnection('target'),
    source_schema:$('source-schema').value,
    target_schema:$('target-schema').value,
    tables:[...state.selected],
    output_dir:$('output-dir').value.trim(),
    dump_file:$('dump-file').value.trim(),
    options:getOptions(),
    destructive_confirmation:confirmation,
  };
}
function updateMapping() {
  $('mapping-source').textContent = $('source-schema').value || '源 Schema';
  $('mapping-target').textContent = $('target-schema').value || '目标 Schema';
}

function openDialog(title, html, actions) {
  const dialog = $('app-dialog');
  if (dialog.open) dialog.close('cancel');
  $('dialog-title').textContent = title;
  $('dialog-body').innerHTML = html;
  $('dialog-footer').innerHTML = '';
  renderIcons($('dialog-body'));
  return new Promise((resolve) => {
    let result = null;
    const close = () => { dialog.removeEventListener('close', close); resolve(result); };
    dialog.addEventListener('close', close);
    actions.forEach((action) => {
      const button = document.createElement('button');
      button.className = `button ${action.style || 'secondary'}`;
      button.textContent = action.label;
      if (action.id) button.id = action.id;
      button.disabled = Boolean(action.disabled);
      button.addEventListener('click', () => { result = action.value === undefined ? action.label : action.value; if (action.result) result = action.result(); dialog.close('action'); });
      $('dialog-footer').append(button);
    });
    dialog.showModal();
  });
}

async function confirmStart() {
  const request = buildRequest();
  const destructive = request.mode !== 'export' && ['TRUNCATE','REPLACE'].includes(request.options.table_exists);
  const sourceName = request.mode === 'import' ? '转储文件' : `${request.source.host}:${request.source.port}`;
  const targetName = request.mode === 'export' ? '本机工作目录' : `${request.target.host}:${request.target.port}`;
  const names = request.tables.slice(0,8).map(escapeHtml).join('、');
  const html = `<p>请确认本次${modeLabels[request.mode]}的执行范围。</p><div class="review-route"><div><small>${request.mode === 'import' ? 'FILE' : 'SOURCE'}</small><strong>${escapeHtml(sourceName)}</strong><br>${escapeHtml(request.source_schema)}</div><span>${icon('arrow-right')}</span><div><small>${request.mode === 'export' ? 'LOCAL' : 'TARGET'}</small><strong>${escapeHtml(targetName)}</strong><br>${escapeHtml(request.mode === 'export' ? request.output_dir : request.target_schema)}</div></div><div class="review-detail"><span>数据表</span><strong>${request.tables.length ? `${request.tables.length} 张指定表` : '文件中的全部对象'}</strong></div>${request.tables.length ? `<p class="field-note">${names}${request.tables.length > 8 ? ` 等 ${request.tables.length} 张表` : ''}</p>` : ''}<div class="review-detail"><span>迁移内容</span><strong>${request.options.rows ? '表结构与数据' : '表结构与对象，不含表数据'}</strong></div>${request.mode !== 'export' ? `<div class="review-detail"><span>目标表已存在时</span><strong>${escapeHtml(strategies[request.options.table_exists])}</strong></div>` : ''}${destructive ? `<div class="dialog-warning">${request.options.table_exists === 'REPLACE' ? '已有目标表将被删除后重建，包括其现有数据与表结构。' : '已有目标表的数据将被清空后重新导入。'} 此操作无法通过本工具撤销。</div><label class="field"><span>输入目标 Schema「${escapeHtml(request.target_schema)}」确认</span><input id="destructive-confirmation" autocomplete="off" placeholder="输入目标 Schema"></label>` : request.options.table_exists === 'APPEND' && request.mode !== 'export' ? '<div class="dialog-warning">追加会保留原有数据，重复执行可能产生重复行或主键冲突。</div>' : '<p class="field-note">任务会先验证连接与所选表。转储文件和日志会保留在独立工作目录中。</p>'}`;
  const promise = openDialog('确认' + modeLabels[request.mode], html, [{label:'返回检查',value:null},{label:request.mode === 'export' ? '确认导出' : request.mode === 'import' ? '确认导入' : '确认迁移', style:destructive ? 'danger' : 'primary', value:'start', id:'confirm-start', disabled:destructive, result:() => ({confirmation:$('destructive-confirmation')?.value || ''})}]);
  if (destructive) $('destructive-confirmation').addEventListener('input', () => { $('confirm-start').disabled = $('destructive-confirmation').value !== request.target_schema; });
  const result = await promise;
  if (!result) return;
  const job = await api('/api/jobs', {body:{...request, destructive_confirmation:result.confirmation}});
  state.job = job;
  state.activeJobId = job.id;
  state.events = [];
  state.lastSequence = 0;
  gotoStep(3);
  toast('任务已启动，可在日志中查看执行情况。');
  pollJob();
  loadHistoryCount();
}

async function showPreview() {
  validateDraft();
  const data = await api('/api/preview', {body:buildRequest()});
  const html = '<p>密码通过标准输入传给官方工具，不包含在以下命令与参数文件中。</p>' + data.commands.map((command) => `<h3>${command.phase === 'export' ? '导出 · dexp' : '导入 · dimp'}</h3><pre class="preview-command">${escapeHtml(command.command)}\n\n${escapeHtml(command.parameters)}</pre>`).join('');
  await openDialog('执行参数', html, [{label:'关闭',style:'primary'}]);
}

function formatElapsed(job) {
  if (!job?.started_at) return '尚未开始';
  const end = job.finished_at ? Date.parse(job.finished_at) : Date.now();
  const seconds = Math.max(0, Math.floor((end - Date.parse(job.started_at)) / 1000));
  return seconds < 60 ? `耗时 ${seconds} 秒` : seconds < 3600 ? `耗时 ${Math.floor(seconds / 60)} 分 ${seconds % 60} 秒` : `耗时 ${Math.floor(seconds / 3600)} 时 ${Math.floor(seconds / 60) % 60} 分`;
}
function renderJob() {
  const job = state.job;
  const status = job?.status || 'idle';
  const running = activeStatuses.has(status);
  const mode = job?.request.mode || state.mode;
  $('job-status-badge').className = `status-badge ${status}`;
  $('job-status-badge').textContent = statusLabels[status] || status;
  $('job-overview-icon').className = `job-overview-icon ${running ? 'active' : status === 'failed' ? 'failed' : ''}`;
  $('job-overview-icon').innerHTML = icon(running ? 'refresh' : status === 'success' || status === 'warning' ? 'check-circle' : status === 'failed' ? 'alert' : 'shuffle');
  const titles = {idle:mode === 'export' ? '等待开始导出' : mode === 'import' ? '等待开始导入' : '等待开始迁移', queued:'任务已创建', preparing:'正在验证连接与迁移范围', exporting:'正在导出所选数据表', importing:'正在导入目标数据库', success:mode === 'export' ? '数据导出完成' : '数据迁移完成', warning:'任务完成，请检查警告', failed:'任务执行失败', cancelled:'任务已停止', interrupted:'任务上次运行时中断'};
  $('job-title').textContent = titles[status] || status;
  const request = job?.request || buildRequest();
  const route = mode === 'export' ? `${request.source_schema} → 本机转储文件` : mode === 'import' ? `${request.source_schema} → ${request.target_schema}` : `${request.source_schema || '源 Schema'} → ${request.target_schema || '目标 Schema'}`;
  $('job-subtitle').textContent = job ? `${route} · ${job.id}${job.native_progress == null ? '' : ` · 工具报告进度 ${job.native_progress}%`}` : mode === 'export' ? '所选表将导出为 .dmp 文件，保存在本机。' : mode === 'import' ? '转储文件将按配置导入目标数据库。' : '所选表会先导出到本机，再导入目标库。';
  $('job-table-count').textContent = request.tables.length ? `${request.tables.length} 张表` : mode === 'import' ? '全部对象' : '0 张表';
  $('job-elapsed').textContent = formatElapsed(job);
  $('job-description').textContent = job ? running ? '任务正在运行。日志与文件会自动保留。' : '任务已结束，可下载日志或打开工作目录检查结果。' : '确认迁移配置，启动任务后在这里查看进度。';
  all('.task-phase').forEach((node) => {
    const phase = node.dataset.phase;
    const value = job ? job.phases[phase] : phase === 'export' && mode === 'import' || phase === 'import' && mode === 'export' ? 'skipped' : 'pending';
    node.className = `task-phase ${value}`;
    node.querySelector('.phase-state').textContent = phaseLabels[value] || value;
    node.querySelector('.phase-icon').innerHTML = icon(value === 'completed' ? 'check' : phase === 'validate' ? 'plug' : phase === 'export' ? 'upload' : 'download');
  });
  $('activity-track').className = `activity-track ${running ? 'active' : status === 'success' || status === 'warning' ? 'completed' : status === 'failed' ? 'failed' : ''}`;
  $('job-error').classList.toggle('hidden', !job?.error);
  $('job-error').textContent = job?.error || '';
  $('log-status').textContent = job ? running ? '实时接收官方工具输出' : '任务日志已保存' : '等待任务启动';
  $('log-indicator').classList.toggle('active', running);
  $('download-log').disabled = !job;
  $('open-job-dir').disabled = !job;
  updateFooter();
}
function renderLogs() {
  const filter = $('log-filter').value;
  const events = state.events.filter((event) => filter === 'all' || filter === 'error' && event.level === 'error' || filter === 'warning' && ['warning','error'].includes(event.level));
  $('log-line-count').textContent = `${state.lastSequence} 行`;
  const content = $('log-content');
  const oldScroll = content.scrollTop;
  content.innerHTML = events.length ? events.slice(-2000).map((event) => `<div class="log-line ${escapeHtml(event.level)}"><span class="log-time">${new Date(event.time).toLocaleTimeString('zh-CN',{hour12:false})}</span><span class="log-phase">${{export:'DEXP',import:'DIMP',validate:'CHECK',done:'DONE'}[event.phase] || 'TASK'}</span><span class="log-text">${escapeHtml(event.message)}</span></div>`).join('') : `<div class="log-placeholder"><span>${icon('terminal')}</span><p>${filter === 'all' ? '任务日志将在这里实时显示' : '当前没有匹配的日志'}</p><small>${filter === 'all' ? '运行期间可以离开此页面，任务会继续执行。' : '完整日志可以通过右上角的下载按钮保存。'}</small></div>`;
  content.scrollTop = $('log-autoscroll').checked ? content.scrollHeight : oldScroll;
}
async function pollJob() {
  clearTimeout(state.pollTimer);
  if (!state.job || state.polling) return;
  const jobId = state.job.id;
  state.polling = true;
  try {
    const record = await api(`/api/jobs/${jobId}?after=${state.lastSequence}`);
    if (!state.job || state.job.id !== jobId) return;
    state.job = record;
    const previousSequence = state.lastSequence;
    for (const event of record.events || []) {
      if (event.sequence > state.lastSequence) { state.events.push(event); state.lastSequence = event.sequence; }
    }
    if (state.events.length > 10000) state.events.splice(0,state.events.length - 10000);
    state.activeJobId = activeStatuses.has(record.status) ? record.id : state.activeJobId === record.id ? null : state.activeJobId;
    if (state.step === 3 && state.page === 'migration') { renderJob(); if (state.lastSequence !== previousSequence) renderLogs(); }
    if (activeStatuses.has(record.status) || state.lastSequence < record.last_sequence) state.pollTimer = setTimeout(pollJob, state.lastSequence < record.last_sequence ? 100 : 900);
    else loadHistoryCount();
  } catch (error) {
    if (state.job?.id === jobId) {
      $('log-status').textContent = '连接暂时中断，正在重试…';
      state.pollTimer = setTimeout(pollJob, 3000);
    }
  } finally { state.polling = false; }
}

async function viewJob(jobId) {
  clearTimeout(state.pollTimer);
  const record = await api(`/api/jobs/${jobId}?after=0`);
  state.job = record;
  state.events = record.events || [];
  state.lastSequence = state.events.at(-1)?.sequence || 0;
  if (activeStatuses.has(record.status)) state.activeJobId = record.id;
  setMode(record.request.mode, false);
  gotoStep(3);
  pollJob();
}
async function downloadLog() {
  if (!state.job) return;
  const blob = await api(`/api/jobs/${state.job.id}/log`, {blob:true});
  const address = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = address;
  link.download = `${state.job.id}.log`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(address), 1000);
}
async function cancelJob() {
  if (!state.job || !activeStatuses.has(state.job.status)) return;
  const result = await openDialog('停止当前任务', '<p>官方工具进程将被结束。已经导入的数据会保留，停止操作不会回滚目标库。</p><p>重试前请检查目标表，选择合适的已有表处理策略。</p>', [{label:'继续运行',value:null},{label:'停止任务',style:'danger',value:'stop'}]);
  if (!result) return;
  await api(`/api/jobs/${state.job.id}/cancel`, {body:{}});
  toast('已发送停止请求，正在结束当前任务。', 'warning');
  pollJob();
}

async function loadHistory() {
  const result = await api('/api/jobs');
  $('history-count').textContent = result.jobs.length;
  $('history-empty').classList.toggle('hidden', result.jobs.length > 0);
  $('history-body').innerHTML = result.jobs.map((job, index) => {
    const request = job.request;
    const source = request.mode === 'import' ? '本机转储文件' : `${request.source.host}:${request.source.port} / ${request.source_schema}`;
    const target = request.mode === 'export' ? '本机工作目录' : `${request.target.host}:${request.target.port} / ${request.target_schema}`;
    return `<tr><td><span class="history-task-name">${modeLabels[request.mode]} · ${request.tables.length ? `${request.tables.length} 张表` : '全部对象'}</span><span class="history-task-id">${escapeHtml(job.id)}</span></td><td><div class="history-route"><span>${escapeHtml(source)}</span><span>→ ${escapeHtml(target)}</span></div></td><td><span class="status-badge ${escapeHtml(job.status)}">${escapeHtml(statusLabels[job.status] || job.status)}</span></td><td>${new Date(job.created_at).toLocaleString('zh-CN',{hour12:false})}</td><td><div class="history-actions"><button class="text-button" data-view="${index}">查看</button><button class="text-button" data-reuse="${index}">复用配置</button></div></td></tr>`;
  }).join('');
  $('history-body').querySelectorAll('[data-view]').forEach((button) => button.addEventListener('click', () => viewJob(result.jobs[Number(button.dataset.view)].id).catch((error) => toast(error.message,'error'))));
  $('history-body').querySelectorAll('[data-reuse]').forEach((button) => button.addEventListener('click', () => reuseJob(result.jobs[Number(button.dataset.reuse)])));
  return result;
}
async function loadHistoryCount() {
  try { const result = await api('/api/jobs'); $('history-count').textContent = result.jobs.length; }
  catch (_) { /* The active task poll handles temporary loss of service. */ }
}
function reuseJob(job) {
  const request = job.request;
  setMode(request.mode);
  setConnection('source',request.source);
  setConnection('target',request.target);
  $('source-schema').value = request.source_schema;
  $('target-schema').value = request.target_schema;
  $('output-dir').value = request.output_dir;
  $('dump-file').value = request.dump_file || '';
  for (const key of ['rows','indexes','constraints','triggers','grants','compress']) $('option-' + key).checked = request.options[key];
  $('option-parallel').value = request.options.parallel;
  $('option-table-parallel').value = request.options.table_parallel;
  document.querySelector(`input[name="table-exists"][value="${request.options.table_exists}"]`).checked = true;
  updateStrategies();
  state.selected = new Set(request.tables);
  state.selectedSchema = request.source_schema;
  renderSelection(); updateMapping();
  toast('配置已复用，请重新输入数据库密码后开始。');
}

function updateTools(tools) {
  if (state.boot) state.boot.tools = tools;
  $('tool-health-dot').className = `health-dot ${tools.ready ? 'ready' : 'error'}`;
  $('tool-health-title').textContent = tools.ready ? '迁移环境已就绪' : '工具或依赖待检查';
  $('tool-health-subtitle').textContent = tools.ready ? '官方 dexp / dimp 可用' : '前往环境设置查看';
  $('bin-dir').value = tools.bin_dir;
  $('tools-list').innerHTML = tools.tools.map((tool) => {
    const ready = tool.available && tool.runnable !== false;
    return `<div class="tool-item"><span>${icon(tool.name.endsWith('.dll') ? 'plug' : 'terminal')}</span><div><strong>${escapeHtml(tool.name)}</strong><small>${escapeHtml(tool.error || tool.version || (tool.available ? '附带驱动 · 无需注册' : '未找到文件'))}</small></div><span class="status-badge ${ready ? 'success' : 'failed'}">${ready ? '可用' : '异常'}</span></div>`;
  }).join('');
}
async function saveSettings() {
  const body = {bin_dir:$('bin-dir').value};
  for (const role of ['source','target']) {
    if ($(`${role}-remember`).checked) {
      const config = getConnection(role);
      body[role] = {host:config.host,port:config.port,username:config.username};
    }
  }
  const result = await api('/api/settings',{body});
  state.boot = result;
  invalidateConnection('source'); invalidateConnection('target');
  updateTools(result.tools);
  toast(result.tools.ready ? '环境设置已保存，工具检测通过。' : '设置已保存，请检查工具或配套依赖。', result.tools.ready ? 'success' : 'warning');
}
async function browse(kind, inputId) {
  const result = await api('/api/dialog',{body:{kind,initial:$(inputId).value},timeout:310000});
  if (result.path) { $(inputId).value = result.path.replaceAll('/','\\'); $(inputId).dispatchEvent(new Event('input')); }
}
async function openDirectory(jobId) {
  await api('/api/open-directory',{body:jobId ? {job_id:jobId} : {kind:'output'}});
}
function updateStrategies() { all('.strategy-card').forEach((label) => label.classList.toggle('selected',label.querySelector('input').checked)); }

function showHelp() {
  openDialog('使用指南', `<div class="guide-step"><span>1</span><div><h3>连接源库与目标库</h3><p>填写主机地址、端口、用户名和密码，点击测试连接。默认端口为 5236。源账号需能读取所选表，目标账号需具备建表和写入权限。</p></div></div><div class="guide-step"><span>2</span><div><h3>选择指定数据表</h3><p>选择源 Schema 并加载真实表清单，支持搜索和批量勾选。也可手动添加表名，每行一个，并保留大小写。统计行数来自数据库统计信息。</p></div></div><div class="guide-step"><span>3</span><div><h3>确认目标 Schema 与策略</h3><p>目标 Schema 需要事先存在。默认跳过已存在的表。追加、清空、替换对已有数据的影响不同，请按实际需求选择。</p></div></div><div class="guide-step"><span>4</span><div><h3>执行并核对结果</h3><p>任务先验证连接，再通过官方 dexp 导出、dimp 导入。每次任务保留独立的 .dmp 文件和日志。停止任务不会回滚已导入数据。</p></div></div><div class="dialog-warning">迁移前请准备目标库备份。迁移工具不会自动创建账号、Schema 或表空间，也不会自动解决外键依赖；只选部分表时请考虑关联表。</div><p class="field-note">只导出时选择“导出数据”；已有 .dmp 文件时选择“导入数据”，填写文件中的原始 Schema。关闭浏览器不会停止服务，退出请使用左下角的“退出”。</p>`,[{label:'开始使用',style:'primary'}]);
}
async function quitApplication() {
  const result = await openDialog('退出迁移工作台', '<p>退出后本地界面服务会停止，已保存的任务记录与转储文件会保留。</p>', [{label:'取消',value:null},{label:'退出应用',style:'primary',value:'quit'}]);
  if (!result) return;
  await api('/api/quit',{body:{}});
  clearTimeout(state.pollTimer);
  showStartupError('应用已退出。双击迁移程序或 start.bat 可以再次打开。');
  $('startup-error').querySelector('h2').textContent = '工作台已退出';
}
function showStartupError(message) { $('startup-error-message').textContent = message; $('startup-error').classList.remove('hidden'); }

all('[data-mode]').forEach((button) => button.addEventListener('click', () => setMode(button.dataset.mode)));
all('[data-page]').forEach((button) => button.addEventListener('click', () => setPage(button.dataset.page)));
all('[data-step]').forEach((button) => button.addEventListener('click', () => { setPage('migration'); gotoStep(Number(button.dataset.step)); }));
all('[data-test]').forEach((button) => button.addEventListener('click', async () => { try { await testConnection(button.dataset.test); await rememberProfiles(); } catch (error) { toast(error.message,'error',8000); } }));
for (const role of ['source','target']) for (const key of ['host','port','username','password']) $(`${role}-${key}`).addEventListener('input', () => invalidateConnection(role, key !== 'password'));
all('.password-toggle').forEach((button) => button.addEventListener('click', () => { const input = $(button.dataset.role + '-password'); const visible = input.type === 'password'; input.type = visible ? 'text' : 'password'; input.classList.toggle('password-visible',visible); button.setAttribute('aria-label',`${visible ? '隐藏' : '显示'}${button.dataset.role === 'source' ? '源库' : '目标库'}密码`); button.innerHTML = icon(visible ? 'eye-off' : 'eye'); }));
$('next-step').addEventListener('click',nextStep);
$('previous-step').addEventListener('click',() => gotoStep(state.step - 1));
$('swap-connections').addEventListener('click',() => { const source = getConnection('source'); const target = getConnection('target'); setConnection('source',target,false); setConnection('target',source,false); $('source-password').value = target.password; $('target-password').value = source.password; $('source-schema').value = ''; $('target-schema').value = ''; toast('源库与目标库连接信息已交换，请重新验证。'); });
$('table-search').addEventListener('input',renderTables);
$('refresh-tables').addEventListener('click',() => loadTables().catch((error) => toast(error.message,'error')));
$('source-schema').addEventListener('change',() => { if (state.selectedSchema && state.selectedSchema !== $('source-schema').value) { state.selected.clear(); state.selectedSchema = $('source-schema').value; renderSelection(); } updateMapping(); if (state.mode !== 'import' && state.connections.source.status === 'connected') loadTables().catch((error) => toast(error.message,'error')); });
$('target-schema').addEventListener('input',updateMapping);
$('select-all').addEventListener('change',() => { const checked = $('select-all').checked; filteredTables().forEach((table) => checked ? state.selected.add(table.name) : state.selected.delete(table.name)); state.selectedSchema = $('source-schema').value; renderTables(); renderSelection(); });
$('clear-selection').addEventListener('click',() => { state.selected.clear(); renderTables(); renderSelection(); });
$('manual-toggle').addEventListener('click',() => { $('manual-entry').classList.toggle('hidden'); if (!$('manual-entry').classList.contains('hidden')) $('manual-tables').focus(); });
$('apply-manual').addEventListener('click',applyManualTables);
$('empty-table-action').addEventListener('click',() => { if (state.mode === 'import' || state.tableError) { $('manual-entry').classList.remove('hidden'); $('manual-tables').focus(); } else if (state.tablesLoaded) { $('table-search').value = ''; loadTables().catch((error) => toast(error.message,'error')); } else gotoStep(0); });
all('input[name="table-exists"]').forEach((input) => input.addEventListener('change',updateStrategies));
$('preview-button').addEventListener('click',() => showPreview().catch((error) => toast(error.message,'error')));
$('browse-output').addEventListener('click',() => browse('directory','output-dir').catch((error) => toast(error.message,'error')));
$('browse-bin').addEventListener('click',() => browse('directory','bin-dir').catch((error) => toast(error.message,'error')));
$('browse-dump').addEventListener('click',() => browse('file','dump-file').catch((error) => toast(error.message,'error')));
$('log-filter').addEventListener('change',renderLogs);
$('download-log').addEventListener('click',() => downloadLog().catch((error) => toast(error.message,'error')));
$('cancel-job').addEventListener('click',() => cancelJob().catch((error) => toast(error.message,'error')));
$('open-job-dir').addEventListener('click',() => { if (state.job) openDirectory(state.job.id).catch((error) => toast(error.message,'error')); });
$('open-output').addEventListener('click',() => openDirectory().catch((error) => toast(error.message,'error')));
$('refresh-history').addEventListener('click',() => loadHistory().catch((error) => toast(error.message,'error')));
$('new-migration').addEventListener('click',() => setMode('migrate'));
$('save-settings').addEventListener('click',() => saveSettings().catch((error) => toast(error.message,'error')));
$('refresh-tools').addEventListener('click',async () => { try { const result = await api('/api/tools'); updateTools(result); toast(result.ready ? '官方工具检测通过。' : '工具检测存在问题，请检查文件和依赖。',result.ready ? 'success' : 'warning'); } catch (error) { toast(error.message,'error'); } });
$('help-button').addEventListener('click',showHelp);
$('help-nav').addEventListener('click',showHelp);
$('quit-button').addEventListener('click',() => quitApplication().catch((error) => toast(error.message,'error')));
$('dialog-close').addEventListener('click',() => $('app-dialog').close('cancel'));
$('reload-page').addEventListener('click',() => location.reload());
document.querySelector('.brand').addEventListener('click',(event) => { event.preventDefault(); setPage('migration'); });
setInterval(() => { if (state.job && activeStatuses.has(state.job.status)) $('job-elapsed').textContent = formatElapsed(state.job); },1000);

async function boot() {
  if (!state.token) throw new Error('请双击迁移程序或 start.bat 启动工具，并使用程序自动打开的本地地址。');
  const result = await api('/api/bootstrap');
  state.boot = result;
  $('app-version').textContent = result.version;
  $('output-dir').value = result.output_dir;
  for (const role of ['source','target']) setConnection(role,result.settings[role]);
  updateTools(result.tools);
  setMode('migrate');
  loadHistoryCount();
  if (result.active_job) {
    state.activeJobId = result.active_job.id;
    await viewJob(result.active_job.id);
    toast('已恢复正在运行的任务。');
  }
}
boot().catch((error) => showStartupError(error.message));
