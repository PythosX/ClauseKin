const Auth = (() => {
  const SESSION_KEY = "contractlens_session";
  const USER_KEY = "contractlens_user";

  function login(email, password, remember = true) {
    if (email === "demo@contractlens.ai" && password === "demo123") {
      const user = { email, name: "Demo User" };
      const storage = remember ? localStorage : sessionStorage;
      storage.setItem(SESSION_KEY, "active");
      storage.setItem(USER_KEY, JSON.stringify(user));
      return { ok: true, user };
    }
    return { ok: false, message: "Invalid email or password. Use the demo credentials shown below." };
  }

  function getStorage() {
    if (localStorage.getItem(SESSION_KEY) === "active") return localStorage;
    if (sessionStorage.getItem(SESSION_KEY) === "active") return sessionStorage;
    return null;
  }

  function isLoggedIn() {
    return !!getStorage();
  }

  function user() {
    const storage = getStorage();
    if (!storage) return null;
    try { return JSON.parse(storage.getItem(USER_KEY) || "null"); }
    catch { return null; }
  }

  function logout() {
    localStorage.removeItem(SESSION_KEY);
    localStorage.removeItem(USER_KEY);
    sessionStorage.removeItem(SESSION_KEY);
    sessionStorage.removeItem(USER_KEY);
    location.replace("/pages/login.html");
  }

  function requireLogin() {
    if (!isLoggedIn()) {
      location.replace("/pages/login.html");
      return false;
    }
    return true;
  }

  return { login, logout, isLoggedIn, user, requireLogin };
})();
