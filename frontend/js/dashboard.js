document.addEventListener("DOMContentLoaded", async () => {
  if (!(await App.setupPage("dashboard"))) return;
  try {
    const data = await App.api("/api/dashboard");
    document.querySelector("#projectsMetric").textContent = data.project_count;
    document.querySelector("#scansMetric").textContent = data.scan_count;
    document.querySelector("#findingsMetric").textContent = data.open_findings;
    document.querySelector("#fixedMetric").textContent = data.fixed_findings;

    const sev = data.severity || {};
    const max = Math.max(...["critical","high","medium","low"].map(k => sev[k]||0), 1);
    document.querySelector("#severityBars").innerHTML = ["critical","high","medium","low"].map(level => {
      const count = sev[level] || 0;
      const h = Math.max(4, Math.round((count / max) * 120));
      return `<div class="severity-bar" data-level="${level}">
        <div style="height:${h}px"></div>
        <span>${level}</span><br><strong>${count}</strong>
      </div>`;
    }).join("");

    const scans = data.recent_scans || [];
    document.querySelector("#recentScans").innerHTML = scans.length
      ? scans.map(s => `
          <tr>
            <td><a href="/scan-detail?id=${s.id}">#${s.id}</a></td>
            <td><span class="badge ${s.status === 'completed' ? 'fixed' : 'open'}">${App.escape(s.status)}</span></td>
            <td>${s.total_files}</td>
            <td>${s.finding_count}</td>
          </tr>`).join("")
      : `<tr><td colspan="4" class="empty">No scans yet. <a href="/projects">Create a project</a> to begin.</td></tr>`;
  } catch (err) {
    App.msg(err.message, "error");
  }
});
