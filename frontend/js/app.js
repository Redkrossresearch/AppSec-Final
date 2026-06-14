window.App = {
  user: null,
  csrf: null,

  escape(v) {
    return String(v ?? "").replace(/[&<>"']/g, c =>
      ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  },

  query(name) {
    return new URLSearchParams(window.location.search).get(name);
  },

  async api(path, options = {}) {
    const settings = { credentials: "same-origin", ...options };
    settings.headers = {
      ...(options.body && typeof options.body === "string" ? { "Content-Type": "application/json" } : {}),
      ...(options.headers || {})
    };
    if (this.csrf && ["POST","PATCH","DELETE"].includes((settings.method||"GET").toUpperCase())) {
      settings.headers["X-CSRF-Token"] = this.csrf;
    }
    const res = await fetch(path, settings);
    const ct = res.headers.get("content-type") || "";
    const data = ct.includes("json") ? await res.json() : null;
    if (!res.ok) {
      const message = data?.error || data?.explanation || data?.message || `Request failed (${res.status})`;
      throw new Error(message);
    }
    return data;
  },

  async session() {
    try {
      const data = await this.api("/api/auth/me");
      this.user = data.user;
      this.csrf = data.csrf_token;
      return data.user;
    } catch(e) {
      return null;
    }
  },

  msg(text, type = "success") {
    const el = document.querySelector("#message");
    if (!el) return;
    el.textContent = text;
    el.className = `alert ${type} show`;
    if (text) setTimeout(() => el.classList.remove("show"), 6000);
  },

  badge(level) {
    return `<span class="badge ${this.escape(level)}">${this.escape(level)}</span>`;
  },

  shell(active) {
    const sidebar = document.querySelector("#sidebar");
    const bar = document.querySelector("#appbar");
    if (sidebar) {
      const links = [
        ["dashboard","Dashboard","🛡"],
        ["projects","Projects","📁"],
        ["findings","Findings","🔍"],
        ["document-scan","Documents","📑"],
        ["reports","Reports","📄"],
        ["settings","Settings","⚙"],
      ];
      sidebar.innerHTML = `
        <a class="brand" href="/dashboard">
          <svg viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="36" height="36" rx="9" fill="#20d39b"/>
            <path d="M18 7l9 4v8c0 5-4 9-9 10-5-1-9-5-9-10v-8l9-4z" fill="#051510" opacity=".9"/>
            <path d="M14 18l3 3 5-5" stroke="#20d39b" stroke-width="2" stroke-linecap="round"/>
          </svg>
          <span>AppSec<br><strong>Orchestrator</strong></span>
        </a>
        <nav style="margin-top:8px">
          ${links.map(([href,label,icon]) => `
            <a class="menu ${active===href?"active":""}" href="/${href}">
              <span>${icon}</span>${label}
            </a>`).join("")}
        </nav>`;
    }
    if (bar) {
      bar.innerHTML = `
        <small>Automated source-code security & remediation</small>
        <div class="stack">
          <span style="color:var(--muted);font-size:13px">${this.escape(this.user?.name || "")}</span>
          <button class="secondary" id="logoutBtn" style="padding:0 12px;min-height:34px;font-size:13px">Log out</button>
        </div>`;
      document.querySelector("#logoutBtn").onclick = async () => {
        await this.api("/api/auth/logout", { method: "POST" });
        window.location.href = "/login";
      };
    }
  },

  async setupPage(active) {
    await this.session();
    if (!this.user) {
      window.location.href = "/login";
      return false;
    }
    this.shell(active);
    return true;
  }
};
