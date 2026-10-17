const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("electronAPI", {
  isElectron: true,
  getPrinters: () => ipcRenderer.invoke("get-printers"),
  printDirect: (options) => ipcRenderer.invoke("print-direct", options),
  openExternal: (url) => ipcRenderer.invoke("open-external", url)
});
