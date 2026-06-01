import * as path from 'node:path';
import { spawn } from 'node:child_process';
import * as vscode from 'vscode';

const PARTICIPANT_ID = 'prompt-optimizer-mini.promptOptimizer';
const COMMAND_OPTIMIZE_SELECTION = 'promptOptimizerLite.optimizeSelection';
const COMMAND_CHOOSE_ROUTE = 'promptOptimizerLite.chooseModelRoute';
const COMMAND_SETUP_LOCAL = 'promptOptimizerLite.setupLocalModel';
const COMMAND_CONFIGURE_EXTERNAL = 'promptOptimizerLite.configureExternalModel';
const COMMAND_SHOW_STATUS = 'promptOptimizerLite.showModelStatus';
const COMMAND_SETUP_AGENT_ADAPTERS = 'promptOptimizerLite.setupAgentAdapters';
const EXTERNAL_API_KEY_SECRET = 'promptOptimizerLite.externalApiKey';
const ADAPTER_BEGIN = '<!-- promptopt:begin -->';
const ADAPTER_END = '<!-- promptopt:end -->';

type ModelRoute = 'auto' | 'vscode' | 'external' | 'local' | 'template';
type LocalTemplate = 'auto' | 'general' | 'variables' | 'review' | 'text2image';

interface LocalModelStatus {
  ready: boolean;
  backend: string;
  model: string;
  modelPath: string;
  modelDownloaded: boolean;
  modelBytes: number;
  ollamaCommand: string;
  ollamaModel: string;
  llamaCli: string;
  cacheDir: string;
}

interface OptimizationResult {
  prompt: string;
  routeLabel: string;
  routeId: string;
}

const SENIOR_PROMPT_ENGINEER_INSTRUCTION = `你是一位资深 Prompt 工程师。你的任务是把用户输入的粗糙需求，优化成可直接给大模型使用的高质量提示词。

必须遵守：
1. 保留用户核心意图，不改变任务目标。
2. 自动补齐执行上下文：目标、输入、约束、输出格式、验收标准。
3. 对变量化任务显式提取 {{variable}} 占位符；对审稿任务按严重程度给出审查结构；对文生图任务补齐主体、构图、光线、材质、氛围和负面约束。
4. 输出结构清晰、可执行，避免空泛措辞。
5. 不回答任务本身，只输出“优化后的提示词”。
6. 默认使用中文输出，除非用户原文明确要求英文。`;

export function activate(context: vscode.ExtensionContext): void {
  const participant = vscode.chat.createChatParticipant(
    PARTICIPANT_ID,
    async (request, _chatContext, stream, token) => {
      const sourcePrompt = request.prompt.trim();
      if (!sourcePrompt) {
        stream.markdown('请先输入你要优化的原始 prompt。');
        return;
      }
      const result = await optimizePrompt(context, sourcePrompt, token, request.model);
      stream.markdown(renderOptimizationMarkdown(sourcePrompt, result, shouldShowOptimizationTrace()));
    }
  );

  context.subscriptions.push(
    participant,
    vscode.commands.registerCommand(COMMAND_OPTIMIZE_SELECTION, () => optimizeSelection(context)),
    vscode.commands.registerCommand(COMMAND_CHOOSE_ROUTE, () => chooseModelRoute()),
    vscode.commands.registerCommand(COMMAND_SETUP_LOCAL, () => setupLocalModel(context)),
    vscode.commands.registerCommand(COMMAND_CONFIGURE_EXTERNAL, () => configureExternalModel(context)),
    vscode.commands.registerCommand(COMMAND_SHOW_STATUS, () => showModelStatus(context)),
    vscode.commands.registerCommand(COMMAND_SETUP_AGENT_ADAPTERS, () => setupAgentAdapters(context))
  );

  void offerAgentAdapterSetup(context);
}

export function deactivate(): void {
  // no-op
}

async function optimizeSelection(context: vscode.ExtensionContext): Promise<void> {
  const editor = vscode.window.activeTextEditor;
  let sourcePrompt = '';
  let selectionForReplace: vscode.Selection | undefined;

  if (editor && !editor.selection.isEmpty) {
    const selectedText = editor.document.getText(editor.selection).trim();
    if (selectedText) {
      sourcePrompt = selectedText;
      selectionForReplace = editor.selection;
    } else {
      vscode.window.showWarningMessage('选中内容为空，将改为手动输入。');
    }
  }

  if (!sourcePrompt) {
    const manualInput = await vscode.window.showInputBox({
      title: 'Prompt Optimizer Mini',
      prompt: 'Paste or type the raw prompt you want to optimize',
      placeHolder: 'Example: 帮我写一个可执行的客服机器人提示词',
      ignoreFocusOut: true
    });
    if (!manualInput?.trim()) {
      vscode.window.showWarningMessage('没有可优化的输入内容。');
      return;
    }
    sourcePrompt = manualInput.trim();
  }

  const result = await vscode.window.withProgress(
    {
      location: vscode.ProgressLocation.Notification,
      title: 'Prompt Optimizer Mini: Optimizing...',
      cancellable: true
    },
    async (_progress, token) => optimizePrompt(context, sourcePrompt, token)
  );

  const replaceSelection = vscode.workspace
    .getConfiguration('promptOptimizerLite')
    .get<boolean>('replaceSelection', false);
  const optimized = result.prompt;
  if (replaceSelection && editor && selectionForReplace) {
    await editor.edit((editBuilder) => editBuilder.replace(selectionForReplace, optimized));
    return;
  }

  const actions: string[] = [];
  if (editor && selectionForReplace) {
    actions.push('Replace Selection');
  }
  if (editor) {
    actions.push('Insert At Cursor');
  }
  actions.push('Copy To Clipboard', 'Open Preview');
  const action = await vscode.window.showQuickPick(actions, {
    placeHolder:
      selectionForReplace && editor
        ? 'Choose what to do with optimized prompt'
        : 'No selection found. Choose where to put optimized prompt'
  });

  if (action === 'Replace Selection' && editor && selectionForReplace) {
    await editor.edit((editBuilder) => editBuilder.replace(selectionForReplace, optimized));
  } else if (action === 'Insert At Cursor' && editor) {
    await editor.edit((editBuilder) => editBuilder.insert(editor.selection.active, optimized));
  } else if (action === 'Copy To Clipboard') {
    await vscode.env.clipboard.writeText(optimized);
    vscode.window.showInformationMessage('Optimized prompt copied to clipboard.');
  } else if (action === 'Open Preview') {
    const doc = await vscode.workspace.openTextDocument({
      language: 'markdown',
      content: renderOptimizationMarkdown(sourcePrompt, result, shouldShowOptimizationTrace())
    });
    await vscode.window.showTextDocument(doc, { preview: true });
  }
}

async function optimizePrompt(
  context: vscode.ExtensionContext,
  sourcePrompt: string,
  token: vscode.CancellationToken,
  currentChatModel?: vscode.LanguageModelChat
): Promise<OptimizationResult> {
  const config = vscode.workspace.getConfiguration('promptOptimizerLite');
  const route = config.get<ModelRoute>('modelRoute', 'auto');
  const failures: string[] = [];

  const attempt = async (label: string, action: () => Promise<string>): Promise<string | undefined> => {
    try {
      return await action();
    } catch (err) {
      failures.push(`${label}: ${errorMessage(err)}`);
      return undefined;
    }
  };

  if ((route === 'auto' || route === 'external') && (await externalModelIsConfigured(context))) {
    const result = await attempt('OpenAI-compatible API', () =>
      optimizeWithExternalModel(context, sourcePrompt, token)
    );
    if (result) {
      return {
        prompt: result,
        routeLabel: 'OpenAI-compatible API',
        routeId: 'external'
      };
    }
  }

  if (route === 'auto' || route === 'vscode') {
    const vscodeModel = currentChatModel ?? (await selectFirstVsCodeModel());
    if (vscodeModel) {
      const result = await attempt('VS Code chat model', () =>
        optimizeWithVsCodeModel(vscodeModel, sourcePrompt, token)
      );
      if (result) {
        return {
          prompt: result,
          routeLabel: 'VS Code Chat model',
          routeId: 'vscode'
        };
      }
    } else {
      failures.push('VS Code chat model: no model is available to extension APIs');
    }
  }

  if (route !== 'template') {
    const result = await attempt('local model', () => optimizeWithLocalModel(context.extensionUri, sourcePrompt, token));
    if (result) {
      return {
        prompt: result,
        routeLabel: 'Local GGUF model',
        routeId: 'local'
      };
    }
  }

  const fallback = await attempt('Python template fallback', () =>
    optimizeWithPythonFallback(context.extensionUri, sourcePrompt, token)
  );
  if (fallback) {
    if (failures.length > 0 && route !== 'template') {
      vscode.window.showWarningMessage(`Prompt Optimizer Mini used template fallback. ${failures.join(' | ')}`);
    }
    return {
      prompt: fallback,
      routeLabel: 'Local Python template',
      routeId: 'python-template'
    };
  }
  return {
    prompt: buildEmergencyFallback(sourcePrompt),
    routeLabel: 'Built-in emergency template',
    routeId: 'built-in-template'
  };
}

async function selectFirstVsCodeModel(): Promise<vscode.LanguageModelChat | undefined> {
  const models = await vscode.lm.selectChatModels({});
  return models[0];
}

async function optimizeWithVsCodeModel(
  model: vscode.LanguageModelChat,
  sourcePrompt: string,
  token: vscode.CancellationToken
): Promise<string> {
  const messages: vscode.LanguageModelChatMessage[] = [
    vscode.LanguageModelChatMessage.User(SENIOR_PROMPT_ENGINEER_INSTRUCTION),
    vscode.LanguageModelChatMessage.User(
      `请优化以下原始 prompt，并严格只输出优化后的提示词正文，不要额外解释。\n\n原始 prompt：\n${sourcePrompt}`
    )
  ];
  const response = await model.sendRequest(messages, {}, token);
  let text = '';
  for await (const chunk of response.text) {
    text += chunk;
  }
  return requireOutput(text, 'VS Code chat model');
}

async function externalModelIsConfigured(context: vscode.ExtensionContext): Promise<boolean> {
  const config = vscode.workspace.getConfiguration('promptOptimizerLite');
  const baseUrl = config.get<string>('externalBaseUrl', '').trim();
  const model = config.get<string>('externalModel', '').trim();
  const apiKey = (await context.secrets.get(EXTERNAL_API_KEY_SECRET))?.trim() ?? '';
  return Boolean(baseUrl && model && apiKey);
}

async function optimizeWithExternalModel(
  context: vscode.ExtensionContext,
  sourcePrompt: string,
  token: vscode.CancellationToken
): Promise<string> {
  const config = vscode.workspace.getConfiguration('promptOptimizerLite');
  const baseUrl = config.get<string>('externalBaseUrl', '').trim().replace(/\/+$/, '');
  const model = config.get<string>('externalModel', '').trim();
  const apiKey = (await context.secrets.get(EXTERNAL_API_KEY_SECRET))?.trim() ?? '';
  if (!baseUrl || !model || !apiKey) {
    throw new Error('base URL, model name, or API key is missing');
  }
  const endpoint = baseUrl.endsWith('/chat/completions') ? baseUrl : `${baseUrl}/chat/completions`;
  const controller = new AbortController();
  const subscription = token.onCancellationRequested(() => controller.abort());
  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model,
        messages: [
          { role: 'system', content: SENIOR_PROMPT_ENGINEER_INSTRUCTION },
          {
            role: 'user',
            content: `请优化以下原始 prompt，并严格只输出优化后的提示词正文，不要额外解释。\n\n原始 prompt：\n${sourcePrompt}`
          }
        ]
      }),
      signal: controller.signal
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${(await response.text()).slice(0, 240)}`);
    }
    const payload = (await response.json()) as {
      choices?: Array<{ message?: { content?: string } }>;
    };
    return requireOutput(payload.choices?.[0]?.message?.content ?? '', 'OpenAI-compatible API');
  } finally {
    subscription.dispose();
  }
}

async function optimizeWithLocalModel(
  extensionUri: vscode.Uri,
  sourcePrompt: string,
  token: vscode.CancellationToken
): Promise<string> {
  const config = vscode.workspace.getConfiguration('promptOptimizerLite');
  const autoDownload = config.get<boolean>('autoDownloadLocalModel', true);
  const template = config.get<LocalTemplate>('localTemplate', 'auto');
  if (!autoDownload) {
    const status = await readLocalModelStatus(extensionUri, token);
    if (!status.ready) {
      throw new Error('local model is missing and automatic download is disabled');
    }
  }
  return runBundledPython(
    extensionUri,
    'local_model_manager.py',
    ['optimize', '--stdin', '--template', template],
    sourcePrompt,
    token
  );
}

async function chooseModelRoute(): Promise<void> {
  const config = vscode.workspace.getConfiguration('promptOptimizerLite');
  const current = config.get<ModelRoute>('modelRoute', 'auto');
  const choices: Array<vscode.QuickPickItem & { route: ModelRoute }> = [
    { route: 'auto', label: '$(wand) Auto', description: 'External API if configured, then VS Code, local model, template' },
    { route: 'local', label: '$(device-desktop) Local model', description: 'Private GGUF model via Ollama or llama.cpp' },
    { route: 'external', label: '$(cloud) OpenAI-compatible API', description: 'Your configured base URL, API key, and model' },
    { route: 'vscode', label: '$(comment-discussion) VS Code chat model', description: 'Use the model exposed by VS Code Chat' },
    { route: 'template', label: '$(symbol-structure) Offline template', description: 'Fast dependency-free formatter without model inference' }
  ];
  const picked = await vscode.window.showQuickPick(choices, {
    title: `Prompt Optimizer Mini: Model Router (current: ${current})`,
    placeHolder: 'Choose the optimization route'
  });
  if (picked) {
    await config.update('modelRoute', picked.route, vscode.ConfigurationTarget.Global);
    vscode.window.showInformationMessage(`Prompt Optimizer Mini route: ${picked.route}`);
  }
}

async function setupLocalModel(context: vscode.ExtensionContext): Promise<void> {
  const status = await vscode.window.withProgress(
    {
      location: vscode.ProgressLocation.Notification,
      title: 'Prompt Optimizer Mini: preparing local model...',
      cancellable: true
    },
    async (_progress, token) => {
      const output = await runBundledPython(context.extensionUri, 'local_model_manager.py', ['ensure'], '', token);
      return JSON.parse(output) as LocalModelStatus;
    }
  );
  vscode.window.showInformationMessage(`Local model ready: ${status.backend} / ${status.model}`);
}

async function configureExternalModel(context: vscode.ExtensionContext): Promise<void> {
  const config = vscode.workspace.getConfiguration('promptOptimizerLite');
  const baseUrl = await vscode.window.showInputBox({
    title: 'OpenAI-compatible model: Base URL',
    value: config.get<string>('externalBaseUrl', ''),
    placeHolder: 'https://api.example.com/v1',
    ignoreFocusOut: true
  });
  if (baseUrl === undefined) {
    return;
  }
  const model = await vscode.window.showInputBox({
    title: 'OpenAI-compatible model: Model name',
    value: config.get<string>('externalModel', ''),
    placeHolder: 'your-model-name',
    ignoreFocusOut: true
  });
  if (model === undefined) {
    return;
  }
  const apiKey = await vscode.window.showInputBox({
    title: 'OpenAI-compatible model: API key',
    prompt: 'Stored in VS Code SecretStorage. Enter DELETE to clear the saved key.',
    password: true,
    ignoreFocusOut: true
  });
  if (apiKey === undefined) {
    return;
  }
  await config.update('externalBaseUrl', baseUrl.trim(), vscode.ConfigurationTarget.Global);
  await config.update('externalModel', model.trim(), vscode.ConfigurationTarget.Global);
  if (apiKey === 'DELETE') {
    await context.secrets.delete(EXTERNAL_API_KEY_SECRET);
  } else if (apiKey.trim()) {
    await context.secrets.store(EXTERNAL_API_KEY_SECRET, apiKey.trim());
  }
  vscode.window.showInformationMessage('OpenAI-compatible model configuration updated.');
}

async function showModelStatus(context: vscode.ExtensionContext): Promise<void> {
  const config = vscode.workspace.getConfiguration('promptOptimizerLite');
  const route = config.get<ModelRoute>('modelRoute', 'auto');
  const externalConfigured = await externalModelIsConfigured(context);
  try {
    const status = await readLocalModelStatus(context.extensionUri);
    vscode.window.showInformationMessage(
      `Route: ${route} | External API: ${externalConfigured ? 'configured' : 'not configured'} | Local: ${
        status.ready ? `${status.backend} / ${status.model}` : 'not installed'
      }`
    );
  } catch (err) {
    vscode.window.showWarningMessage(`Route: ${route} | Local status unavailable: ${errorMessage(err)}`);
  }
}

async function offerAgentAdapterSetup(context: vscode.ExtensionContext): Promise<void> {
  const config = vscode.workspace.getConfiguration('promptOptimizerLite');
  if (!config.get<boolean>('offerAgentAdapterSetup', true)) {
    return;
  }
  const folders = vscode.workspace.workspaceFolders;
  if (!folders?.length) {
    return;
  }
  const root = folders[0].uri;
  const stateKey = adapterOfferStateKey(root);
  if (context.workspaceState.get<boolean>(stateKey, false) || (await agentAdaptersAreInstalled(root))) {
    return;
  }
  const choice = await vscode.window.showInformationMessage(
    'Enable PromptOpt in Codex and Claude Code for this workspace? This adds small managed adapter blocks to AGENTS.md and CLAUDE.md.',
    'Enable Adapters',
    'Not Now',
    'Do Not Ask Again'
  );
  if (choice === 'Enable Adapters') {
    await setupAgentAdapters(context, root);
  } else if (choice === 'Do Not Ask Again') {
    await context.workspaceState.update(stateKey, true);
  }
}

async function setupAgentAdapters(context: vscode.ExtensionContext, preferredRoot?: vscode.Uri): Promise<void> {
  const root = preferredRoot ?? (await chooseWorkspaceRoot());
  if (!root) {
    vscode.window.showWarningMessage('Open a workspace folder before enabling PromptOpt agent adapters.');
    return;
  }

  const cliPath = path.join(context.extensionUri.fsPath, 'bin', 'promptopt');
  const replacements = new Map([['{{PROMPTOPT_CLI}}', shellQuote(cliPath)]]);
  const agentsBlock = replaceTemplateValues(
    await readExtensionText(context, 'resources', 'agent-adapters', 'AGENTS.promptopt.md'),
    replacements
  );
  const claudeBlock = replaceTemplateValues(
    await readExtensionText(context, 'resources', 'agent-adapters', 'CLAUDE.promptopt.md'),
    replacements
  );
  const claudeCommand = await readExtensionText(context, 'resources', 'agent-adapters', 'promptopt-command.md');

  await upsertManagedBlock(vscode.Uri.joinPath(root, 'AGENTS.md'), agentsBlock);
  await upsertManagedBlock(vscode.Uri.joinPath(root, 'CLAUDE.md'), claudeBlock);
  await installClaudeCommand(vscode.Uri.joinPath(root, '.claude', 'commands', 'promptopt.md'), claudeCommand);
  await context.workspaceState.update(adapterOfferStateKey(root), true);
  vscode.window.showInformationMessage(
    'PromptOpt adapters enabled. Reopen Codex or Claude Code chats, then use: @promptopt <your request>'
  );
}

async function chooseWorkspaceRoot(): Promise<vscode.Uri | undefined> {
  const folders = vscode.workspace.workspaceFolders;
  if (!folders?.length) {
    return undefined;
  }
  if (folders.length === 1) {
    return folders[0].uri;
  }
  const picked = await vscode.window.showQuickPick(
    folders.map((folder) => ({ label: folder.name, description: folder.uri.fsPath, uri: folder.uri })),
    { title: 'Prompt Optimizer Mini: Choose workspace for Codex / Claude Code adapters' }
  );
  return picked?.uri;
}

async function agentAdaptersAreInstalled(root: vscode.Uri): Promise<boolean> {
  const agents = await readWorkspaceText(vscode.Uri.joinPath(root, 'AGENTS.md'));
  const claude = await readWorkspaceText(vscode.Uri.joinPath(root, 'CLAUDE.md'));
  const command = await readWorkspaceText(vscode.Uri.joinPath(root, '.claude', 'commands', 'promptopt.md'));
  return agents.includes(ADAPTER_BEGIN) && claude.includes(ADAPTER_BEGIN) && command.includes(ADAPTER_BEGIN);
}

async function upsertManagedBlock(target: vscode.Uri, block: string): Promise<void> {
  const existing = await readWorkspaceText(target);
  const updated = mergeManagedBlock(existing, block);
  await writeWorkspaceText(target, updated);
}

async function installClaudeCommand(target: vscode.Uri, command: string): Promise<void> {
  const existing = await readWorkspaceText(target);
  if (existing.trim() && !existing.includes(ADAPTER_BEGIN)) {
    const choice = await vscode.window.showWarningMessage(
      `${target.fsPath} already exists. Replace it with the PromptOpt command adapter?`,
      { modal: true },
      'Replace',
      'Keep Existing'
    );
    if (choice !== 'Replace') {
      return;
    }
  }
  await writeWorkspaceText(target, command.trimEnd() + '\n');
}

function mergeManagedBlock(existing: string, block: string): string {
  const normalizedBlock = block.trim();
  const begin = escapeRegExp(ADAPTER_BEGIN);
  const end = escapeRegExp(ADAPTER_END);
  const managedBlock = new RegExp(`${begin}[\\s\\S]*?${end}`);
  if (managedBlock.test(existing)) {
    return existing.replace(managedBlock, normalizedBlock);
  }
  const prefix = existing.trimEnd();
  return `${prefix}${prefix ? '\n\n' : ''}${normalizedBlock}\n`;
}

async function readExtensionText(context: vscode.ExtensionContext, ...segments: string[]): Promise<string> {
  return readWorkspaceText(vscode.Uri.joinPath(context.extensionUri, ...segments));
}

async function readWorkspaceText(target: vscode.Uri): Promise<string> {
  try {
    return new TextDecoder().decode(await vscode.workspace.fs.readFile(target));
  } catch (err) {
    if (err instanceof vscode.FileSystemError && err.code === 'FileNotFound') {
      return '';
    }
    throw err;
  }
}

async function writeWorkspaceText(target: vscode.Uri, text: string): Promise<void> {
  await vscode.workspace.fs.createDirectory(vscode.Uri.joinPath(target, '..'));
  await vscode.workspace.fs.writeFile(target, new TextEncoder().encode(text));
}

function adapterOfferStateKey(root: vscode.Uri): string {
  return `agentAdaptersOffer:${root.toString()}`;
}

function replaceTemplateValues(template: string, replacements: Map<string, string>): string {
  let result = template;
  for (const [needle, replacement] of replacements) {
    result = result.replaceAll(needle, replacement);
  }
  return result;
}

function shellQuote(value: string): string {
  return `'${value.replace(/'/g, `'\"'\"'`)}'`;
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

async function readLocalModelStatus(
  extensionUri: vscode.Uri,
  token?: vscode.CancellationToken
): Promise<LocalModelStatus> {
  const output = await runBundledPython(extensionUri, 'local_model_manager.py', ['status'], '', token);
  return JSON.parse(output) as LocalModelStatus;
}

async function optimizeWithPythonFallback(
  extensionUri: vscode.Uri,
  sourcePrompt: string,
  token?: vscode.CancellationToken
): Promise<string> {
  return runBundledPython(extensionUri, 'fallback_optimize.py', ['--stdin'], sourcePrompt, token);
}

async function runBundledPython(
  extensionUri: vscode.Uri,
  scriptName: string,
  args: string[],
  stdin: string,
  token?: vscode.CancellationToken
): Promise<string> {
  const scriptPath = path.join(extensionUri.fsPath, 'scripts', scriptName);
  const configuredPython = vscode.workspace
    .getConfiguration('promptOptimizerLite')
    .get<string>('fallbackPythonCommand', '')
    .trim();
  const candidates = configuredPython ? [configuredPython] : ['python3', 'python'];
  const failures: string[] = [];
  for (const command of candidates) {
    try {
      return requireOutput(await runProcess(command, [scriptPath, ...args], stdin, token), scriptName);
    } catch (err) {
      failures.push(`${command}: ${errorMessage(err)}`);
    }
  }
  throw new Error(failures.join(' | '));
}

function runProcess(
  command: string,
  args: string[],
  stdin: string,
  token?: vscode.CancellationToken
): Promise<string> {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, { stdio: ['pipe', 'pipe', 'pipe'] });
    let stdout = '';
    let stderr = '';
    let settled = false;
    const subscription = token?.onCancellationRequested(() => {
      child.kill();
      if (!settled) {
        settled = true;
        reject(new Error('cancelled'));
      }
    });
    child.stdout.on('data', (chunk: Buffer) => {
      stdout += chunk.toString('utf8');
    });
    child.stderr.on('data', (chunk: Buffer) => {
      stderr += chunk.toString('utf8');
    });
    child.on('error', (err) => {
      if (!settled) {
        settled = true;
        subscription?.dispose();
        reject(err);
      }
    });
    child.on('close', (code) => {
      if (settled) {
        return;
      }
      settled = true;
      subscription?.dispose();
      if (code === 0) {
        resolve(stdout);
      } else {
        reject(new Error(stderr.trim() || `exit code ${code ?? 'unknown'}`));
      }
    });
    child.stdin.write(stdin);
    child.stdin.end();
  });
}

function requireOutput(text: string, source: string): string {
  const normalized = text.trim();
  if (!normalized) {
    throw new Error(`${source} returned an empty response`);
  }
  return normalized;
}

function buildEmergencyFallback(sourcePrompt: string): string {
  return `# 角色
你是一名资深领域专家，面向有经验的执行者提供可落地方案。

# 任务
基于以下需求完成高质量输出：
${sourcePrompt}

# 上下文
- 如信息缺失，先列出关键假设并继续完成任务。
- 优先使用可验证、可执行、可复现的方法。

# 约束
- 不偏离用户核心目标。
- 结论要有依据，避免空泛表述。
- 输出中显式给出边界条件与风险点。

# 输出格式
1. 结果摘要（3-5条）
2. 详细方案（按步骤）
3. 可执行清单（含优先级）
4. 验收标准

# 质量检查
- 是否保留原始意图
- 是否可直接执行
- 是否包含验收标准`;
}

function shouldShowOptimizationTrace(): boolean {
  return vscode.workspace
    .getConfiguration('promptOptimizerLite')
    .get<boolean>('showOptimizationTrace', true);
}

function renderOptimizationMarkdown(
  sourcePrompt: string,
  result: OptimizationResult,
  showTrace: boolean
): string {
  if (!showTrace) {
    return result.prompt;
  }
  return `## 优化后的 Prompt

${result.prompt}

---

<details>
<summary>Prompt Optimizer Mini 对比与路由</summary>

### 原始 Prompt

${fencedMarkdown(sourcePrompt)}

### 优化路由

\`${escapeInlineCode(result.routeLabel)}\`

</details>`;
}

function fencedMarkdown(text: string): string {
  const backtickRuns = text.match(/`+/g) ?? [];
  const longestRun = backtickRuns.reduce((max, run) => Math.max(max, run.length), 2);
  const fence = '`'.repeat(longestRun + 1);
  return `${fence}text\n${text.trim()}\n${fence}`;
}

function errorMessage(err: unknown): string {
  return err instanceof Error ? err.message : String(err);
}

function escapeInlineCode(text: string): string {
  return text.replace(/`/g, '\\`');
}
