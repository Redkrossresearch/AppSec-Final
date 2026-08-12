document.addEventListener("DOMContentLoaded", async () => {
  if (!(await App.setupPage("projects"))) return;

  const projectId = App.query("id");
  const scanId = App.query("scan") || App.query("id");

  // ── Project detail page ──────────────────────────────────────────
  if (document.querySelector("#projectName")) {
    try {
      const { project } = await App.api(`/api/projects/${projectId}`);
      document.querySelector("#projectName").textContent = project.name;
      document.querySelector("#projectPath").textContent = project.path;

      const { scans } = await App.api(`/api/projects/${projectId}/scans`);
      const tbody = document.querySelector("#scanList");
      tbody.innerHTML = scans.length
        ? scans.map(s => {
            const summ = s.summary || {};
            const top = summ.critical ? "critical" : summ.high ? "high" : summ.medium ? "medium" : "low";
            return `
              <tr>
                <td><a href="/scan-detail?id=${s.id}">#${s.id}</a></td>
                <td><span class="badge ${s.status === 'completed' ? 'fixed' : 'open'}">${App.escape(s.status)}</span></td>
                <td>${s.total_files}</td>
                <td>${s.finding_count}</td>
                <td>${s.finding_count ? App.badge(top) : "—"}</td>
                <td>${new Date(s.started_at).toLocaleString()}</td>
              </tr>`;
          }).join("")
        : `<tr><td colspan="6" class="empty">No scans yet. Click "Run Security Scan" to start.</td></tr>`;

      document.querySelector("#startScan").onclick = async (e) => {
        const btn = e.currentTarget;
        btn.disabled = true;
        btn.innerHTML = `<span class="spinner"></span> Scanning...`;
        App.msg("Scanning source files for security issues...", "success");
        try {
          const data = await App.api(`/api/projects/${projectId}/scans`, { method: "POST", body: "{}" });
          window.location.href = `/scan-detail?id=${data.scan.id}`;
        } catch (err) {
          App.msg(err.message, "error");
          btn.disabled = false;
          btn.textContent = "Run Security Scan";
        }
      };
    } catch (err) {
      App.msg(err.message, "error");
    }
  }

  // ── Scan detail page ─────────────────────────────────────────────
  if (document.querySelector("#scanTitle")) {
    try {
      const id = scanId;
      const { scan, findings } = await App.api(`/api/scans/${id}`);
      const summ = scan.summary || {};

      document.querySelector("#scanTitle").textContent = `Scan #${scan.id}`;
      document.querySelector("#scanSummary").textContent =
        `${scan.total_files} files scanned · ${scan.finding_count} findings · Status: ${scan.status}`;

      // Metrics
      document.querySelector("#mTotal").textContent = summ.total || 0;
      document.querySelector("#mCritical").textContent = summ.critical || 0;
      document.querySelector("#mHigh").textContent = summ.high || 0;
      document.querySelector("#mFixed").textContent = findings.filter(f => f.status === "fixed").length;

      // Fix All bar
      const fixable = findings.filter(f => f.fixable && f.status === "open");
      if (fixable.length > 0) {
        document.querySelector("#fixAllBar").style.display = "flex";
        document.querySelector("#fixableCount").textContent = fixable.length;
      }

      // Findings table
      document.querySelector("#scanFindings").innerHTML = findings.length
        ? findings.map(f => `
            <tr>
              <td>${App.badge(f.severity)}</td>
              <td>${App.escape(f.title)}<br>
                <span style="color:var(--muted);font-size:12px">${App.escape(f.description.substring(0,80))}...</span>
              </td>
              <td style="font-size:12px;color:var(--muted)">${App.escape(f.file_path)}${f.line_number ? `:${f.line_number}` : ""}</td>
              <td><span class="badge ${f.status}">${App.escape(f.status)}</span></td>
              <td>
                ${f.fixable ? `<a href="/fix-preview?finding=${f.id}" style="font-size:13px">Fix →</a>` : '<span style="color:var(--muted);font-size:12px">Manual</span>'}
              </td>
            </tr>`).join("")
        : `<tr><td colspan="5" class="empty">🎉 No security findings detected!</td></tr>`;

      // Fix All button
      document.querySelector("#fixAllBtn")?.addEventListener("click", async () => {
        const btn = document.querySelector("#fixAllBtn");
        btn.disabled = true;
        btn.innerHTML = `<span class="spinner"></span> Fixing...`;
        try {
          const result = await App.api(`/api/scans/${id}/fix-all`, { method: "POST", body: "{}" });
          App.msg(`${result.summary}`, "success");
          setTimeout(() => window.location.reload(), 1500);
        } catch (err) {
          App.msg(err.message, "error");
          btn.disabled = false;
          btn.textContent = "Fix All";
        }
      });

      // Download fixed project button
      document.querySelector("#downloadFixed")?.addEventListener("click", async () => {
        const btn = document.querySelector("#downloadFixed");
        const fixed = findings.filter(f => f.status === "fixed").length;
        if (fixed === 0) {
          App.msg("No fixes have been applied yet. Click 'Fix All' first.", "error");
          return;
        }
        btn.disabled = true;
        btn.innerHTML = `<span class="spinner"></span> Downloading...`;
        try {
          window.location.href = `/api/scans/${id}/download-fixed`;
          btn.disabled = false;
          btn.textContent = "⬇ Download Fixed";
        } catch (err) {
          App.msg(err.message, "error");
          btn.disabled = false;
          btn.textContent = "⬇ Download Fixed";
        }
      });

      // Show download button if any fixes applied
      if (findings.some(f => f.status === "fixed")) {
        document.querySelector("#downloadFixed").style.display = "block";
      }

      // ── Sanitization report (document scans only) ──────────────────
      // summary.document.sanitization is written by the docscan adapter; code scans
      // have no document block, so the panel simply stays hidden for them.
      const sanitize = (summ.document || {}).sanitization;
      if (sanitize) {
        const panel = document.querySelector("#sanitizePanel");
        panel.style.display = "block";

        const neutralized = sanitize.removed_count > 0;
        const failed = String(sanitize.status).startsWith("FAILED");
        const color = failed ? "var(--danger)" : neutralized ? "var(--accent)" : "var(--muted)";
        document.querySelector("#sanitizeStatus").innerHTML =
          `Status: <strong style="color:${color}">${App.escape(sanitize.status)}</strong>` +
          ` · <strong>${sanitize.removed_count}</strong> item(s) removed`;

        document.querySelector("#sanitizeRemoved").innerHTML = neutralized
          ? sanitize.removed.map(item => `<li>✓ ${App.escape(item)}</li>`).join("")
          : `<li style="color:var(--muted);list-style:none;margin-left:-18px">No active content was present to remove.</li>`;

        if (sanitize.original_size && sanitize.sanitized_size) {
          document.querySelector("#sanitizeSize").textContent =
            `Original ${sanitize.original_size} bytes → Sanitized ${sanitize.sanitized_size} bytes`;
        }

        // The sanitized copy is stored as a Report row with format "sanitized"; find
        // it by scan so the button can hit the existing download endpoint.
        try {
          const { reports } = await App.api("/api/reports");
          const safe = reports.find(r => r.scan_id === Number(id) && r.format === "sanitized");
          if (safe) {
            const btn = document.querySelector("#downloadSanitized");
            btn.style.display = "block";
            btn.onclick = () => { window.location.href = `/api/reports/${safe.id}/download`; };
          }
        } catch (err) {
          // Non-fatal: the panel still shows what was removed without the download.
        }
      }

      // Report buttons
      for (const fmt of ["csv", "pdf"]) {
        document.querySelector(`#${fmt}Report`)?.addEventListener("click", async () => {
          const btn = document.querySelector(`#${fmt}Report`);
          btn.disabled = true;
          btn.textContent = `${fmt.toUpperCase()}...`;
          try {
            const { report } = await App.api(`/api/reports/scans/${id}/${fmt}`, { method: "POST", body: "{}" });
            App.msg(`${fmt.toUpperCase()} report ready! Downloading...`, "success");
            window.location.href = `/api/reports/${report.id}/download`;
          } catch (err) {
            App.msg(err.message, "error");
          } finally {
            btn.disabled = false;
            btn.textContent = fmt === "csv" ? "📋 CSV" : "📄 PDF";
          }
        });
      }
    } catch (err) {
      App.msg(err.message, "error");
    }
  }
});
