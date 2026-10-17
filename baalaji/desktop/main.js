const { app, BrowserWindow, ipcMain, shell } = require("electron");
const path = require("path");
const http = require("http");
const { spawn } = require("child_process");

let mainWindow = null;
let pythonProcess = null;

const BACKEND_URL = "http://127.0.0.1:8000";

function checkBackendOnline(timeout = 1000) {
  return new Promise((resolve) => {
    const req = http.get(`${BACKEND_URL}/health`, (res) => {
      resolve(res.statusCode === 200);
    });
    req.on("error", () => resolve(false));
    req.setTimeout(timeout, () => {
      req.destroy();
      resolve(false);
    });
  });
}

function startPythonBackend() {
  const rootDir = path.dirname(__dirname);
  console.log("Starting Python FastAPI backend from:", rootDir);

  // Spawn Python backend process
  pythonProcess = spawn("python", ["-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8000"], {
    cwd: rootDir,
    shell: true,
    stdio: "inherit"
  });

  pythonProcess.on("error", (err) => {
    console.error("Failed to start Python backend:", err);
  });
}

async function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1366,
    height: 850,
    minWidth: 1024,
    minHeight: 700,
    title: "Baalaji Pharmacy Management System",
    icon: path.join(__dirname, "../frontend/assets/logo.svg"),
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  mainWindow.setMenuBarVisibility(false);

  // Check if backend is already running; if not, spawn it
  const isOnline = await checkBackendOnline(1000);
  if (!isOnline) {
    startPythonBackend();
    // Wait up to 10 seconds for backend to become ready
    for (let i = 0; i < 20; i++) {
      await new Promise(r => setTimeout(r, 500));
      if (await checkBackendOnline(500)) break;
    }
  }

  // Load the application
  mainWindow.loadURL(BACKEND_URL);

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

// IPC Handlers
ipcMain.handle("get-printers", async () => {
  if (!mainWindow) return [];
  return await mainWindow.webContents.getPrintersAsync();
});

ipcMain.handle("print-direct", async (event, options = {}) => {
  if (!mainWindow) return { success: false };
  return new Promise((resolve) => {
    mainWindow.webContents.print({
      silent: options.silent || false,
      printBackground: true,
      deviceName: options.printerName || ""
    }, (success, failureReason) => {
      resolve({ success, failureReason });
    });
  });
});

ipcMain.handle("open-external", async (event, url) => {
  shell.openExternal(url);
});

app.whenReady().then(createWindow);

app.on("window-all-closed", () => {
  if (pythonProcess) {
    try {
      pythonProcess.kill();
    } catch (e) {
      console.error(e);
    }
  }
  if (process.platform !== "darwin") {
    app.quit();
  }
});
