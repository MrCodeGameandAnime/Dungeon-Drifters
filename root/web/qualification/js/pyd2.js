(function () {
  "use strict";

  const PYODIDE_VERSION = "314.0.7";
  const INDEX_URL = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;
  const status = document.getElementById("status");

  function show(message, className) {
    status.textContent = message;
    status.className = className || "";
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

    const bootSource = await (await fetch("python/boot.py")).text();
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
          "PYD2|PASS",
          `Pyodide: ${result.pyodide_version}`,
          `Python: ${result.python_version}`,
          `Route nodes: ${result.route_nodes}`,
          `Encounters: ${result.encounters}`,
          `Rests: ${result.rests}`,
          `Battles: ${result.battles}`,
          `Enemies: ${result.enemies}`,
          `Final node: ${result.final_node}`,
          `Progression: L${result.level} EXP ${result.exp} GP ${result.growth_points} Gold ${result.gold}`,
        ].join("\n"),
        "pass"
      );
    })
    .catch(function (error) {
      show(`PYD2|FAIL|${error.name}|${error.message}`, "fail");
      console.error(error);
    });
})();
