document.addEventListener("DOMContentLoaded", async () => {
  await App.session();
  if (App.user) { window.location.href = "/dashboard"; return; }

  const form = document.querySelector("form[data-auth]");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = form.querySelector("button");
    btn.disabled = true;
    btn.textContent = "Please wait...";
    const payload = Object.fromEntries(new FormData(form).entries());
    try {
      const res = await App.api(`/api/auth/${form.dataset.auth}`, {
        method: "POST",
        body: JSON.stringify(payload)
      });
      App.csrf = res.csrf_token;
      window.location.href = "/dashboard";
    } catch (err) {
      App.msg(err.message, "error");
      btn.disabled = false;
      btn.textContent = form.dataset.auth === "login" ? "Log in" : "Create account";
    }
  });
});
