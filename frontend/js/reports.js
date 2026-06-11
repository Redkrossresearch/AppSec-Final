document.addEventListener("DOMContentLoaded", async () => {
  if (!(await App.setupPage("reports"))) return;
  try {
    const { reports } = await App.api("/api/reports");
    document.querySelector("#reportRows").innerHTML = reports.length
      ? reports.map(r => `
          <tr>
            <td><a href="/scan-detail?id=${r.scan_id}">Scan #${r.scan_id}</a></td>
            <td><span class="badge medium">${r.format.toUpperCase()}</span></td>
            <td style="color:var(--muted);font-size:13px">${new Date(r.created_at).toLocaleString()}</td>
            <td><a href="/api/reports/${r.id}/download" class="button secondary" style="padding:0 12px;min-height:32px;font-size:12px">⬇ Download</a></td>
          </tr>`).join("")
      : `<tr><td colspan="4" class="empty">No reports yet. Generate one from a scan detail page.</td></tr>`;
  } catch (err) {
    App.msg(err.message, "error");
  }
});
