(function () {
  "use strict";

  const PYODIDE_VERSION = "314.0.7";
  const INDEX_URL = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;
  const status = document.getElementById("status");

  function show(message, className) {
    status.textContent = message;
    status.className = className || "";
  }

  async function fetchText(path) {
    const response = await fetch(path);
    if (!response.ok) {
      throw new Error(`${path} returned HTTP ${response.status}`);
    }
    return response.text();
  }

  async function boot() {
    if (typeof loadPyodide !== "function") {
      throw new Error("Pyodide loader did not initialize");
    }
    const pyodide = await loadPyodide({ indexURL: INDEX_URL });
    const archiveResponse = await fetch("game/dd_runtime.zip");
    if (!archiveResponse.ok) {
      throw new Error(`game/dd_runtime.zip returned HTTP ${archiveResponse.status}`);
    }
    pyodide.FS.writeFile(
      "/dd_runtime.zip",
      new Uint8Array(await archiveResponse.arrayBuffer())
    );
    pyodide.runPython("import sys\nsys.path.insert(0, '/')\nsys.path.insert(0, '/dd_runtime.zip')");
    pyodide.FS.writeFile("/dd_bridge.py", await (await fetch("python/dd_bridge.py")).text());
    const bootSource = await fetchText("python/boot.py");
    const resultProxy = await pyodide.runPythonAsync(`${bootSource}\nboot()`);
    const result = resultProxy && typeof resultProxy.toJs === "function"
      ? resultProxy.toJs()
      : resultProxy;
    if (resultProxy && typeof resultProxy.destroy === "function") {
      resultProxy.destroy();
    }
    return JSON.parse(result);
  }

  boot()
    .then(function (result) {
      show(
        [
          "PYD3|PASS",
          `Initial screen: ${result.initial.screen}`,
          `Initial route action: ${result.initial.contextual_route_option.action}`,
          `Entry phase: ${result.after_entry.interaction_phase}`,
          `Restart screen: ${result.after_restart.screen}`,
          "Bridge: semantic views and inputs",
        ].join("\n"),
        "pass"
      );
    })
    .catch(function (error) {
      show(`PYD3|FAIL|${error.name}|${error.message}`, "fail");
      console.error(error);
    });
})();
