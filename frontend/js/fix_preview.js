let activeFix = null;
let activeFinding = null;
let originalCode = null;
let fixedCode = null;

document.addEventListener("DOMContentLoaded", async () => {
  if (!(await App.setupPage("findings"))) return;
  const findingId = App.query("finding");
  if (!findingId) { App.msg("No finding selected.", "error"); return; }

  try {
    const { finding } = await App.api(`/api/findings/${findingId}`);
    activeFinding = finding;
    document.querySelector("#findingTitle").textContent = finding.title;
    document.querySelector("#findingMeta").innerHTML =
      `${App.badge(finding.severity)} &nbsp; <span style="color:var(--muted);font-size:13px">${App.escape(finding.file_path)}${finding.line_number ? `:${finding.line_number}` : ""}</span>`;
    document.querySelector("#recommendation").textContent = finding.recommendation || "No recommendation available.";
    document.querySelector("#lineText").textContent = finding.line_text || "(line not available)";
    document.querySelector("#category").textContent = finding.category;
    document.querySelector("#cvss").textContent = finding.cvss_score ? finding.cvss_score.toFixed(1) : "N/A";
    document.querySelector("#ruleId").textContent = finding.rule_id;
    document.querySelector("#status").innerHTML = 
      `<span style="color:${finding.status === 'fixed' ? '#7debb3' : '#ffaa00'}">${finding.status.toUpperCase()}</span>`;

    if (!finding.fixable) {
      document.querySelector("#previewFix").disabled = true;
      document.querySelector("#previewFix").textContent = "No automatic fix available";
      App.msg("This finding requires a manual fix. Review the recommendation above.", "error");
    }

    if (finding.fix?.status === "applied") {
      activeFix = finding.fix;
      originalCode = finding.fix.original_content;
      fixedCode = finding.fix.fixed_content;
      renderSideBySideDiff();
      renderDiff(finding.fix.diff);
      document.querySelector("#rollbackFix").hidden = false;
      document.querySelector("#previewFix").hidden = true;
      App.msg("✅ Fix is currently applied. You can roll it back.", "success");
    }
  } catch (err) {
    App.msg(err.message, "error");
  }

  document.querySelector("#previewFix").onclick = generateFixPreview;
  document.querySelector("#applyFix").onclick = applyFix;
  document.querySelector("#rollbackFix").onclick = rollbackFix;
  document.querySelector("#regenerateWithAi").onclick = regenerateWithAI;
  document.querySelector("#useCustomFix").onclick = useCustomFix;
});

async function generateFixPreview(e) {
  const btn = e.currentTarget;
  btn.disabled = true;
  btn.innerHTML = `<span class="spinner"></span> Generating fix with AI...`;
  try {
    const res = await App.api(`/api/findings/${activeFinding.id}/fix-preview`, { method: "POST", body: "{}" });
    activeFix = res.fix;
    originalCode = activeFix.original_content;
    fixedCode = activeFix.fixed_content;
    
    renderSideBySideDiff();
    renderDiff(activeFix.diff);
    document.querySelector("#customFixCode").value = fixedCode;
    document.querySelector("#applyFix").hidden = false;
    App.msg(`✨ ${activeFix.explanation}`, "success");
  } catch (err) {
    App.msg(err.message, "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "🔄 Regenerate";
  }
}

async function applyFix() {
  const btn = document.querySelector("#applyFix");
  if (!activeFix || !activeFix.id) {
    App.msg("No fix preview is available. Generate a fix preview first.", "error");
    return;
  }
  btn.disabled = true;
  btn.innerHTML = `<span class="spinner"></span> Applying...`;
  try {
    const res = await App.api(`/api/fixes/${activeFix.id}/apply`, { method: "POST", body: "{}" });
    activeFix = res.fix;
    btn.hidden = true;
    document.querySelector("#rollbackFix").hidden = false;
    document.querySelector("#previewFix").hidden = true;
    App.msg("✅ Fix applied successfully! A backup was created for rollback.", "success");
  } catch (err) {
    App.msg(err.message, "error");
    btn.disabled = false;
    btn.textContent = "✅ Apply Fix";
  }
}

async function rollbackFix() {
  if (!activeFix || !activeFix.id) {
    App.msg("No applied fix is selected. Generate and apply a fix first.", "error");
    return;
  }
  if (!confirm("⚠ This will restore the original file from backup. Continue?")) return;
  const btn = document.querySelector("#rollbackFix");
  btn.disabled = true;
  try {
    await App.api(`/api/fixes/${activeFix.id}/rollback`, { method: "POST", body: "{}" });
    document.querySelector("#rollbackFix").hidden = true;
    document.querySelector("#previewFix").hidden = false;
    document.querySelector("#applyFix").hidden = true;
    App.msg("↩️ File restored from backup successfully.", "success");
  } catch (err) {
    App.msg(err.message, "error");
    btn.disabled = false;
  }
}

async function regenerateWithAI() {
  const customCode = document.querySelector("#customFixCode").value;
  if (!customCode.trim()) {
    App.msg("Please enter or edit the code first.", "error");
    return;
  }
  
  const btn = document.querySelector("#regenerateWithAi");
  btn.disabled = true;
  btn.innerHTML = `<span class="spinner"></span> AI is improving...`;
  
  try {
    // For now, just use the custom code as the fix
    fixedCode = customCode;
    App.msg("✨ Using your code as the new fix. Click 'Apply Fix' to apply it.", "success");
    // In a real scenario, you'd call an AI refinement API here
  } catch (err) {
    App.msg(err.message, "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "🤖 Ask AI to Improve";
  }
}

function useCustomFix() {
  const customCode = document.querySelector("#customFixCode").value;
  if (!customCode.trim()) {
    App.msg("Please enter the code first.", "error");
    return;
  }
  fixedCode = customCode;
  renderSideBySideDiff();
  App.msg("✅ Custom fix ready. Click 'Apply Fix' to apply your changes.", "success");
}

function renderSideBySideDiff() {
  const originalDiv = document.querySelector("#originalCode");
  const fixedDiv = document.querySelector("#fixedCode");
  
  if (!originalCode || !fixedCode) {
    originalDiv.textContent = "Loading...";
    fixedDiv.textContent = "Loading...";
    return;
  }
  
  const originalLines = originalCode.split('\n');
  const fixedLines = fixedCode.split('\n');
  
  originalDiv.innerHTML = originalLines.map((line, idx) => 
    `<div class="diff-line"><span class="diff-line-num">${idx + 1}</span><span>${escapeHtml(line || ' ')}</span></div>`
  ).join('');
  
  fixedDiv.innerHTML = fixedLines.map((line, idx) => {
    const isChanged = idx >= originalLines.length || line !== (originalLines[idx] || '');
    const className = isChanged ? 'diff-line changed added' : 'diff-line';
    return `<div class="${className}"><span class="diff-line-num">${idx + 1}</span><span>${escapeHtml(line || ' ')}</span></div>`;
  }).join('');
}

function renderDiff(diff) {
  const pre = document.querySelector("#diff");
  if (!diff) { pre.textContent = "No diff generated."; return; }
  pre.innerHTML = diff.split("\n").map(line => {
    if (line.startsWith("+") && !line.startsWith("+++")) return `<span class="add">${escapeHtml(line)}</span>`;
    if (line.startsWith("-") && !line.startsWith("---")) return `<span class="del">${escapeHtml(line)}</span>`;
    return escapeHtml(line);
  }).join("\n");
}

function escapeHtml(s) {
  return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}
