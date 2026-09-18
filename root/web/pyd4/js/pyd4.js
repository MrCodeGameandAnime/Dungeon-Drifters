(function () {
  "use strict";

  const PYODIDE_VERSION = "314.0.7";
  const INDEX_URL = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;
  let pyodide = null;
  let state = null;

  const $ = (id) => document.getElementById(id);

  function setText(id, value) {
    $(id).textContent = value == null ? "" : String(value);
  }

  function clear(node) {
    while (node.firstChild) node.removeChild(node.firstChild);
  }

  function showLoading(visible) {
    $("loading").hidden = !visible;
  }

  function showError(error) {
    showLoading(false);
    $("app").hidden = true;
    $("error").hidden = false;
    setText("error-message", `${error.name || "Error"}: ${error.message || error}`);
  }

  function showApp() {
    showLoading(false);
    $("error").hidden = true;
    $("app").hidden = false;
  }

  function appendStat(container, label, value) {
    const stat = document.createElement("div");
    stat.className = "stat";
    const name = document.createElement("span");
    name.className = "stat-label";
    name.textContent = label;
    const content = document.createElement("span");
    content.className = "stat-value";
    content.textContent = value == null ? "-" : String(value);
    stat.append(name, content);
    container.append(stat);
  }

  function appendDetail(container, label, value) {
    const row = document.createElement("div");
    row.className = "detail-row";
    const name = document.createElement("span");
    name.textContent = label;
    const content = document.createElement("strong");
    content.textContent = value == null ? "-" : String(value);
    row.append(name, content);
    container.append(row);
  }

  function makeButton(label, command, enabled, reason) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    const available = enabled !== false;
    button.disabled = !available;
    button.setAttribute("aria-disabled", String(!available));
    if (!available && reason) button.title = String(reason);
    if (available && command) {
      button.addEventListener("click", () => send(command));
    }
    return button;
  }

  function renderOptions(container, options, commandFactory, labelFactory) {
    clear(container);
    for (const option of options || []) {
      const label = labelFactory(option);
      container.append(
        makeButton(
          label,
          commandFactory(option),
          option.enabled,
          option.disabled_reason,
        ),
      );
    }
  }

  function renderPlayer(player) {
    const stats = $("player-status");
    const details = $("player-details");
    clear(stats);
    clear(details);
    if (!player) {
      appendDetail(details, "Status", "Ready for the route");
      return;
    }
    appendStat(stats, "HP", `${player.hp_current} / ${player.hp_maximum}`);
    appendStat(stats, "Mana", `${player.mana_current} / ${player.mana_maximum}`);
    appendStat(stats, "Super", `${player.super_current} / ${player.super_maximum}`);
    appendDetail(details, "Name", player.display_name);
    if (player.defending != null) appendDetail(details, "Guarding", player.defending ? "Yes" : "No");
    if (player.temporary_labels && player.temporary_labels.length) {
      appendDetail(details, "Statuses", player.temporary_labels.join(", "));
    }
  }

  function renderEnemies(enemies) {
    const container = $("enemies");
    clear(container);
    for (const enemy of enemies || []) {
      const card = document.createElement("div");
      card.className = `enemy${enemy.defeated ? " defeated" : ""}`;
      const head = document.createElement("div");
      head.className = "enemy-head";
      const name = document.createElement("span");
      name.textContent = enemy.display_label;
      const hp = document.createElement("span");
      hp.textContent = `${enemy.hp_current} / ${enemy.hp_maximum}`;
      head.append(name, hp);
      card.append(head);
      if (enemy.temporary_labels && enemy.temporary_labels.length) {
        const meta = document.createElement("div");
        meta.className = "enemy-meta";
        meta.textContent = enemy.temporary_labels.join(", ");
        card.append(meta);
      }
      container.append(card);
    }
  }

  function renderLog(entries) {
    const container = $("battle-log");
    clear(container);
    for (const entry of (entries || []).slice(-10)) {
      const line = document.createElement("div");
      line.className = "log-entry";
      const actor = entry.actor_name || "Battle";
      const target = entry.target_name ? ` → ${entry.target_name}` : "";
      const action = entry.action_name ? `: ${entry.action_name}` : "";
      const amount = entry.amount ? ` (${entry.amount})` : "";
      line.innerHTML = "";
      const strong = document.createElement("strong");
      strong.textContent = actor;
      line.append(strong, document.createTextNode(`${target}${action}${amount}`));
      container.append(line);
    }
  }

  function renderInventory(container, view) {
    clear(container);
    const inventory = view.inventory;
    if (inventory && inventory.items && inventory.items.length) {
      const heading = document.createElement("h3");
      heading.textContent = "Inventory";
      container.append(heading);
      renderOptions(
        container,
        inventory.items,
        (item) => ({ kind: "overworld_item", selection_key: item.selection_key }),
        (item) => `${item.display_name} × ${item.quantity}`,
      );
    }
    if (view.inventory_items && view.inventory_items.length) {
      const heading = document.createElement("h3");
      heading.textContent = "Battle items";
      container.append(heading);
      renderOptions(
        container,
        view.inventory_items,
        (item) => ({ kind: "inventory_item", item_id: item.item_id }),
        (item) => `${item.display_name} × ${item.quantity}`,
      );
    }
    if (view.inventory_commands && view.inventory_commands.length) {
      const heading = document.createElement("h3");
      heading.textContent = "Item commands";
      container.append(heading);
      renderOptions(
        container,
        view.inventory_commands,
        (option) => ({ kind: "inventory_command", command: option.command }),
        (option) => option.label,
      );
    }
    if (view.inventory_companions && view.inventory_companions.length) {
      const heading = document.createElement("h3");
      heading.textContent = "Companion items";
      container.append(heading);
      renderOptions(
        container,
        view.inventory_companions,
        (item) => ({ kind: "inventory_companion", item_id: item.item_id }),
        (item) => `${item.display_name} × ${item.quantity}`,
      );
    }
    if (view.inventory_confirmation) {
      const heading = document.createElement("h3");
      heading.textContent = `Confirm ${view.inventory_confirmation.result_display_name}`;
      container.append(heading);
      container.append(makeButton("Confirm", { kind: "inventory_confirm", confirmed: true }));
      container.append(makeButton("Cancel", { kind: "inventory_confirm", confirmed: false }));
    }
    if (view.interaction_phase && view.interaction_phase !== "actions") {
      container.append(makeButton("Back", { kind: "back" }));
    }
  }

  function renderOverworld(view) {
    setText("screen-badge", view.screen);
    setText("phase-badge", "");
    setText("location-label", view.location_label);
    setText("adventure-text", view.adventure_text);
    renderPlayer(view.character);
    renderEnemies([]);
    renderLog([]);
    renderOptions(
      $("route-actions"),
      view.contextual_route_option ? [view.contextual_route_option] : [],
      (option) => ({ kind: "overworld_action", action: option.action }),
      (option) => option.label,
    );
    renderOptions(
      $("overworld-options"),
      view.options,
      (option) => ({ kind: "overworld_action", action: option.action }),
      (option) => option.label,
    );
    renderInventory($("inventory"), view);
    clear($("actions"));
    clear($("moves"));
    clear($("targets"));
    const notice = $("notice");
    notice.hidden = !view.notice;
    notice.textContent = view.notice || "";
  }

  function renderBattle(view) {
    setText("screen-badge", "battle");
    setText("phase-badge", view.interaction_phase);
    setText("location-label", view.encounter_label);
    setText("adventure-text", "Choose from the actions offered by the battle view.");
    renderPlayer(view.player);
    renderEnemies(view.enemies);
    renderLog(view.log_entries);
    clear($("route-actions"));
    clear($("overworld-options"));
    clear($("notice"));
    $("notice").hidden = true;
    renderOptions(
      $("actions"),
      view.action_options,
      (option) => ({ kind: "action", intent: option.intent }),
      (option) => option.label,
    );
    renderOptions(
      $("moves"),
      view.move_options,
      (option) => ({ kind: "move", key: option.selection_key }),
      (option) => `${option.name}${option.resource_label ? ` · ${option.resource_label}` : ""}`,
    );
    renderOptions(
      $("targets"),
      view.target_options,
      (option) => ({ kind: "target", target_id: option.target_id }),
      (option) => `${option.display_label} · ${option.hp_current} / ${option.hp_maximum}`,
    );
    renderInventory($("inventory"), view);
    clear($("overworld-options"));
  }

  function render() {
    if (!state) return;
    showApp();
    const battle = Boolean(state.interaction_phase);
    $("enemy-panel").hidden = !battle;
    $("controls-panel").hidden = false;
    if (battle) renderBattle(state);
    else renderOverworld(state);
    const complete = !battle && state.screen === "main" && !state.contextual_route_option;
    $("completion").hidden = !complete;
    setText("runtime-status", complete ? "Route complete" : "Python runtime ready");
  }

  function unwrap(proxy) {
    const value = proxy && typeof proxy.toJs === "function" ? proxy.toJs() : proxy;
    if (proxy && typeof proxy.destroy === "function") proxy.destroy();
    return value;
  }

  async function pythonJson(expression) {
    const result = unwrap(await pyodide.runPythonAsync(expression));
    return JSON.parse(result);
  }

  async function send(command) {
    try {
      pyodide.globals.set("_browser_command_json", JSON.stringify(command));
      state = await pythonJson("submit_json(_browser_command_json)");
      render();
    } catch (error) {
      showError(error);
      console.error(error);
    }
  }

  async function restart() {
    try {
      state = await pythonJson("restart_game_json()");
      render();
    } catch (error) {
      showError(error);
      console.error(error);
    }
  }

  async function requestImmersion() {
    try {
      if (document.documentElement.requestFullscreen) await document.documentElement.requestFullscreen();
      if (screen.orientation && screen.orientation.lock) await screen.orientation.lock("landscape");
    } catch (error) {
      console.info("Fullscreen or orientation enhancement unavailable", error);
    }
  }

  async function boot() {
    showLoading(true);
    if (typeof loadPyodide !== "function") throw new Error("Pyodide loader did not initialize");
    pyodide = await loadPyodide({ indexURL: INDEX_URL });
    const archiveResponse = await fetch("game/dd_runtime.zip");
    if (!archiveResponse.ok) throw new Error(`game/dd_runtime.zip returned HTTP ${archiveResponse.status}`);
    pyodide.FS.writeFile("/dd_runtime.zip", new Uint8Array(await archiveResponse.arrayBuffer()));
    pyodide.runPython("import sys\nsys.path.insert(0, '/')\nsys.path.insert(0, '/dd_runtime.zip')");
    const bridgeResponse = await fetch("python/dd_bridge.py");
    if (!bridgeResponse.ok) throw new Error(`python/dd_bridge.py returned HTTP ${bridgeResponse.status}`);
    pyodide.FS.writeFile("/dd_bridge.py", await bridgeResponse.text());
    const bootResponse = await fetch("python/boot.py");
    if (!bootResponse.ok) throw new Error(`python/boot.py returned HTTP ${bootResponse.status}`);
    await pyodide.runPythonAsync(await bootResponse.text());
    await pythonJson("boot()");
    state = await pythonJson("current_view_json()");
    render();
    window.__DD_BROWSER_READY__ = true;
  }

  $("restart").addEventListener("click", async function () {
    await requestImmersion();
    await restart();
  });
  $("completion-restart").addEventListener("click", restart);
  $("retry").addEventListener("click", function () {
    window.location.reload();
  });

  boot().catch(function (error) {
    showError(error);
    console.error(error);
  });
})();
