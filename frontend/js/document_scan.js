document.addEventListener("DOMContentLoaded", async () => {
  if (!(await App.setupPage("document-scan"))) return;

  const form = document.querySelector("#docForm");
  const fileInput = document.querySelector("#docFile");

  form.onsubmit = async (e) => {
    e.preventDefault();
    if (!fileInput.files.length) {
      App.msg("Choose a document to scan first.", "error");
      return;
    }

    const btn = document.querySelector("#scanBtn");
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner"></span> Scanning...`;
    App.msg("Analyzing document for malware and indicators...", "success");

    // FormData body — App.api() leaves Content-Type unset (browser sets the multipart
    // boundary) and injects the CSRF token for the POST.
    const body = new FormData();
    body.append("file", fileInput.files[0]);

    try {
      const { scan } = await App.api("/api/docscans", { method: "POST", body });
      window.location.href = `/scan-detail?id=${scan.id}`;
    } catch (err) {
      App.msg(err.message, "error");
      btn.disabled = false;
      btn.textContent = "🔬 Scan Document";
    }
  };
});
