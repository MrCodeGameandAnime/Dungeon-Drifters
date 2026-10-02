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
    pyodide.runPython("import sys\nsys.path.insert(0, '/dd_runtime.zip')");

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
          "PYD1|PASS",
          `Pyodide: ${result.pyodide_version}`,
          `Python: ${result.python_version}`,
          `Initial screen: ${result.initial_screen}`,
          `Initial route node: ${result.initial_route_node}`,
          `Encounter entry: ${result.encounter_entry}`,
          `Battle inputs: ${result.battle_inputs}`,
          `Completed encounter: ${result.completed_encounter}`,
        ].join("\n"),
        "pass"
      );
    })
    .catch(function (error) {
      show(`PYD1|FAIL|${error.name}|${error.message}`, "fail");
      console.error(error);
    });
})();
