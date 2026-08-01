async function loadFindings() {
  const severity = document.querySelector("#severityFilter")?.value || "";
  const status = document.querySelector("#statusFilter")?.value || "";
  const search = document.querySelector("#searchBox")?.value || "";
  let query = [];
  if (severity) query.push(`severity=${encodeURIComponent(severity)}`);
  if (status) query.push(`status=${encodeURIComponent(status)}`);

  let findings;
  if (search) {
    query.push(`q=${encodeURIComponent(search)}`);
    const qs = "?" + query.join("&");
    const result = await App.api(`/api/findings-search${qs}`);
    findings = result.findings;
  } else {
    const qs = query.length ? "?" + query.join("&") : "";
    const result = await App.api(`/api/findings${qs}`);
    findings = result.findings;
  }

  const count = document.querySelector("#findingCount");
  if (count) count.textContent = `${findings.length} finding${findings.length !== 1 ? "s" : ""}`;

  document.querySelector("#findingRows").innerHTML = findings.length
    ? findings.map(f => `
        <tr>
          <td>${App.badge(f.severity)}</td>
          <td>${App.escape(f.category)}</td>
          <td>
            <strong>${App.escape(f.title)}</strong><br>
            <span style="color:var(--muted);font-size:12px">${App.escape(f.file_path)}${f.line_number ? `:${f.line_number}` : ""}</span>
          </td>
          <td><span class="badge ${f.status}">${App.escape(f.status)}</span></td>
          <td>
            <a href="/fix-preview?finding=${f.id}" style="font-size:13px">
              ${f.fixable ? "🔧 Fix" : "👁 Review"}
            </a>
          </td>
        </tr>`).join("")
    : `<tr><td colspan="5" class="empty">No findings match the current filters.</td></tr>`;
}

function exportFindingsCsv() {
  const severity = document.querySelector("#severityFilter")?.value || "";
  let query = [];
  if (severity) query.push(`severity=${encodeURIComponent(severity)}`);
  const qs = query.length ? "?" + query.join("&") : "";
  window.location.href = `/api/findings-export${qs}`;
}

document.addEventListener("DOMContentLoaded", async () => {
  if (!(await App.setupPage("findings"))) return;
  await loadFindings();
  document.querySelector("#severityFilter").onchange = loadFindings;
  document.querySelector("#statusFilter").onchange = loadFindings;
  document.querySelector("#searchBox").addEventListener("input", () => {
    clearTimeout(window._searchDebounce);
    window._searchDebounce = setTimeout(loadFindings, 400);
  });
  document.querySelector("#exportCsvBtn").onclick = exportFindingsCsv;
});