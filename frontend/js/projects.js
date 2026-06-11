async function loadProjects() {
  const data = await App.api("/api/projects");
  const el = document.querySelector("#projectList");
  if (!data.projects.length) {
    el.innerHTML = `<p class="empty">No projects yet. Upload a ZIP or enter a folder path below.</p>`;
    return;
  }
  el.innerHTML = data.projects.map(p => `
    <div class="project-card">
      <div>
        <h3>${App.escape(p.name)}</h3>
        <div class="path">${App.escape(p.path)}</div>
      </div>
      <div class="stack">
        <span style="color:var(--muted);font-size:13px">${p.scan_count} scan${p.scan_count !== 1 ? "s" : ""}</span>
        <a class="button secondary" href="/project-detail?id=${p.id}" style="padding:0 12px;min-height:34px;font-size:13px">Open →</a>
      </div>
    </div>`).join("");
}

document.addEventListener("DOMContentLoaded", async () => {
  if (!(await App.setupPage("projects"))) return;
  await loadProjects();

  // ── ZIP upload drag-and-drop ──
  const zone = document.querySelector("#uploadZone");
  const fileInput = document.querySelector("#fileInput");

  zone.addEventListener("click", () => fileInput.click());
  zone.addEventListener("dragover", e => { e.preventDefault(); zone.classList.add("dragover"); });
  zone.addEventListener("dragleave", () => zone.classList.remove("dragover"));
  zone.addEventListener("drop", e => {
    e.preventDefault();
    zone.classList.remove("dragover");
    const file = e.dataTransfer.files[0];
    if (file) handleZipUpload(file);
  });
  fileInput.addEventListener("change", () => {
    if (fileInput.files[0]) handleZipUpload(fileInput.files[0]);
  });

  async function handleZipUpload(file) {
    if (!file.name.endsWith(".zip")) { App.msg("Please select a .zip file.", "error"); return; }
    const name = document.querySelector("#uploadName").value.trim() || file.name.replace(".zip","");
    if (!name) { App.msg("Enter a project name first.", "error"); return; }

    const uploadBtn = document.querySelector("#uploadBtn");
    uploadBtn.disabled = true;
    uploadBtn.innerHTML = `<span class="spinner"></span> Uploading & extracting...`;
    App.msg("Uploading ZIP file...", "success");

    try {
      const formData = new FormData();
      formData.append("zip", file);
      formData.append("name", name);
      formData.append("description", document.querySelector("#uploadDesc").value.trim());

      const res = await fetch("/api/projects", {
        method: "POST",
        credentials: "same-origin",
        headers: { "X-CSRF-Token": App.csrf },
        body: formData
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Upload failed");

      App.msg(`Project "${data.project.name}" created successfully!`, "success");
      document.querySelector("#uploadName").value = "";
      document.querySelector("#uploadDesc").value = "";
      fileInput.value = "";
      await loadProjects();
    } catch (err) {
      App.msg(err.message, "error");
    } finally {
      uploadBtn.disabled = false;
      uploadBtn.innerHTML = "Upload ZIP";
    }
  }

  // ── Path-based project form ──
  document.querySelector("#pathForm")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = Object.fromEntries(new FormData(e.target).entries());
    try {
      const data = await App.api("/api/projects", {
        method: "POST",
        body: JSON.stringify(payload)
      });
      App.msg(`Project "${data.project.name}" registered.`, "success");
      e.target.reset();
      await loadProjects();
    } catch (err) {
      App.msg(err.message, "error");
    }
  });
});
