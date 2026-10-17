/**
 * Baalaji Pharmacy Management System - API Client
 */

const API_BASE_URL = (
  window.BAALAAJI_API_BASE_URL || window.location.origin
).replace(/\/+$/, "");

const API = {
  getToken() {
    return localStorage.getItem("baalaji_token");
  },

  setToken(token) {
    localStorage.setItem("baalaji_token", token);
  },

  clearToken() {
    localStorage.removeItem("baalaji_token");
    localStorage.removeItem("baalaji_user");
  },

  getUser() {
    try {
      return JSON.parse(localStorage.getItem("baalaji_user")) || null;
    } catch {
      return null;
    }
  },

  setUser(user) {
    localStorage.setItem("baalaji_user", JSON.stringify(user));
  },

  async request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers = options.headers || {};

    const token = this.getToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    if (!headers["Content-Type"] && !(options.body instanceof FormData)) {
      headers["Content-Type"] = "application/json";
    }

    const config = {
      ...options,
      headers
    };

    try {
      const response = await fetch(url, config);

      if (response.status === 401) {
        this.clearToken();
        App.showLogin();
        throw new Error("Session expired. Please log in again.");
      }

      if (!response.ok) {
        let errDetail = "An error occurred";
        try {
          const errData = await response.json();
          errDetail = errData.detail || JSON.stringify(errData);
        } catch {
          errDetail = await response.text();
        }
        throw new Error(errDetail);
      }

      // Handle file downloads
      const disposition = response.headers.get("Content-Disposition");
      if (disposition && disposition.includes("attachment")) {
        return response.blob();
      }

      return await response.json();
    } catch (err) {
      console.error(`API Error on ${endpoint}:`, err);
      throw err;
    }
  },

  get(endpoint) {
    return this.request(endpoint, { method: "GET" });
  },

  post(endpoint, data) {
    return this.request(endpoint, {
      method: "POST",
      body: data instanceof FormData ? data : JSON.stringify(data)
    });
  },

  put(endpoint, data) {
    return this.request(endpoint, {
      method: "PUT",
      body: data instanceof FormData ? data : JSON.stringify(data)
    });
  },

  async download(endpoint, defaultFilename = "download.xlsx") {
    const token = this.getToken();
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: token ? { "Authorization": `Bearer ${token}` } : {}
    });
    if (!response.ok) {
      throw new Error("Download failed");
    }
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = defaultFilename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  }
};
