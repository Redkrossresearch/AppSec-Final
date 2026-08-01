document.addEventListener("DOMContentLoaded", async () => {
  if (!(await App.setupPage("dashboard"))) return;

  try {
    const data = await App.api("/api/dashboard");

    // Dashboard Metrics
    document.querySelector("#projectsMetric").textContent = data.project_count;
    document.querySelector("#scansMetric").textContent = data.scan_count;
    document.querySelector("#findingsMetric").textContent = data.open_findings;
    document.querySelector("#fixedMetric").textContent = data.fixed_findings;

    // Security Score
    const scoreElement = document.querySelector("#securityScore");
    scoreElement.textContent = data.security_score + "%";

    if (data.security_score >= 80) {
      scoreElement.style.color = "#22c55e";
    } else if (data.security_score >= 50) {
      scoreElement.style.color = "#facc15";
    } else {
      scoreElement.style.color = "#ef4444";
    }

    // ==========================
    // System Health
    // ==========================
    const health = data.system_health;

    document.querySelector("#systemHealth").innerHTML = `
      <p>🟢 <strong>Backend:</strong> ${health.backend}</p>
      <p>🟢 <strong>Database:</strong> ${health.database}</p>
      <p>🟢 <strong>Scanner:</strong> ${health.scanner}</p>
    `;

    // ==========================
    // Severity Breakdown
    // ==========================
    const sev = data.severity || {};

    const max = Math.max(
      ...["critical", "high", "medium", "low"].map(level => sev[level] || 0),
      1
    );

    document.querySelector("#severityBars").innerHTML =
      ["critical", "high", "medium", "low"]
        .map(level => {
          const count = sev[level] || 0;
          const height = Math.max(4, Math.round((count / max) * 120));

          return `
            <div class="severity-bar" data-level="${level}">
              <div style="height:${height}px"></div>
              <span>${level}</span><br>
              <strong>${count}</strong>
            </div>
          `;
        })
        .join("");

    // ==========================
    // Recent Scans
    // ==========================
    const scans = data.recent_scans || [];

    document.querySelector("#recentScans").innerHTML = scans.length
      ? scans
          .map(
            s => `
              <tr>
                <td><a href="/scan-detail?id=${s.id}">#${s.id}</a></td>
                <td>
                  <span class="badge ${s.status === "completed" ? "fixed" : "open"}">
                    ${App.escape(s.status)}
                  </span>
                </td>
                <td>${s.total_files}</td>
                <td>${s.finding_count}</td>
              </tr>
            `
          )
          .join("")
      : `
          <tr>
            <td colspan="4" class="empty">
              No scans yet.
              <a href="/projects">Create a project</a> to begin.
            </td>
          </tr>
        `;

  } catch (err) {
    App.msg(err.message, "error");
  }
});
