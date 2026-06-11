async function loadFindings() {
  const severity = document.querySelector("#severityFilter")?.value || "";
  const status = document.querySelector("#statusFilter")?.value || "";
  let query = [];
  if (severity) query.push(`severity=${encodeURIComponent(severity)}`);
  if (status) query.push(`status=${encodeURIComponent(status)}`);
  const qs = query.length ? "?" + query.join("&") : "";
  const { findings } = await App.api(`/api/findings${qs}`);

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

document.addEventListener("DOMContentLoaded", async () => {
  if (!(await App.setupPage("findings"))) return;
  await loadFindings();
  document.querySelector("#severityFilter").onchange = loadFindings;
  document.querySelector("#statusFilter").onchange = loadFindings;
});
