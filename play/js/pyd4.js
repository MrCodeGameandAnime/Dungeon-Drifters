(function () {
  "use strict";

  const PYODIDE_VERSION = "314.0.7";
  const INDEX_URL = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;
  let pyodide = null;
  let state = null;
  let gameStarted = false;
  let musicStarted = false;
  const orientationQuery = window.matchMedia("(orientation: portrait)");

  const $ = (id) => document.getElementById(id);

  function setText(id, value) {
    $(id).textContent = value == null ? "" : String(value);
  }

  function clear(node) {
    while (node.firstChild) node.removeChild(node.firstChild);
  }

  function showLoading(visible) {
    $("start").disabled = visible;
    setText("start", visible ? "Loading..." : "Start");
    setText("start-status", visible
      ? "Starting the Python runtime..."
      : "Python runtime ready.");
  }

  function showError(error) {
    $("start-screen").hidden = true;
    $("app").hidden = true;
    $("error").hidden = false;
    setText("error-message", `${error.name || "Error"}: ${error.message || error}`);
  }

  function showApp() {
    $("start-screen").hidden = true;
    $("error").hidden = true;
    $("app").hidden = false;
  }

  function updateViewportHeight() {
    document.documentElement.style.setProperty("--app-height", `${window.innerHeight}px`);
  }

  function updateOrientationGuidance() {
    const portrait = orientationQuery.matches;
    const guidance = $("orientation-guidance");
    guidance.hidden = !portrait;
    $("orientation-detail").textContent = portrait
      ? "If automatic rotation is unavailable, use your device's manual rotation control."
      : "";
  }

  function bindViewportAndOrientation() {
    updateViewportHeight();
    updateOrientationGuidance();
    window.addEventListener("resize", function () {
      updateViewportHeight();
      updateOrientationGuidance();
    });
    if (orientationQuery.addEventListener) {
      orientationQuery.addEventListener("change", updateOrientationGuidance);
    } else if (orientationQuery.addListener) {
      orientationQuery.addListener(updateOrientationGuidance);
    }
  }

  function appendStatus(container, label, value) {
    const line = document.createElement("div");
    line.className = "status-line";
    line.textContent = `${label} ${value == null ? "-" : value}`;
    container.append(line);
  }

  function makeButton(label, command, enabled, reason, className) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = className || "battle-option";
    const text = document.createElement("span");
    text.className = "choice-label";
    text.textContent = label;
    button.append(text);
    const available = enabled !== false;
    button.disabled = !available;
    button.setAttribute("aria-disabled", String(!available));
    if (!available && reason) {
      const detail = document.createElement("span");
      detail.className = "option-reason";
      detail.textContent = `Unavailable: ${String(reason).replace(/_/g, " ")}`;
      button.title = detail.textContent;
      button.append(detail);
    }
    if (available && command) {
      button.addEventListener("click", () => send(command));
    }
    return button;
  }

  function renderOptions(container, options, commandFactory, labelFactory, className) {
    clear(container);
    for (const option of options || []) {
      const label = labelFactory(option);
      container.append(
        makeButton(
          label,
          commandFactory(option),
          option.enabled,
          option.disabled_reason,
          className || "battle-option action-option",
        ),
      );
    }
  }

  function renderPlayer(player) {
    const stats = $("player-status");
    const details = $("player-details");
    clear(stats);
    clear(details);
    setText("player-title", player && player.display_name ? player.display_name : "Party");
    if (!player) {
      appendStatus(details, "Status", "Ready for the route");
      return;
    }
    appendStatus(stats, "HP", `${player.hp_current}/${player.hp_maximum}`);
    if (player.mana_current != null) appendStatus(stats, "Mana", `${player.mana_current}/${player.mana_maximum}`);
    if (player.defending) appendStatus(details, "Guarding", "Yes");
    if (player.temporary_labels && player.temporary_labels.length) {
      appendStatus(details, "State", player.temporary_labels.join(", "));
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
      hp.textContent = `HP ${enemy.hp_current}/${enemy.hp_maximum}`;
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

  function formatLogEntry(entry) {
    const actor = entry.actor_name || "Combatant";
    const target = entry.target_name;
    const action = entry.action_name || "action";
    const targetContext = target && target !== actor ? ` against ${target}` : "";
    const lines = [];

    switch (entry.event_type) {
      case "encounter_start":
        lines.push(`A ${target || "foe"} blocks your path!`);
        break;
      case "initiative":
        lines.push(`${actor} will go first.`);
        break;
      case "damage":
        lines.push(`${actor} used ${action}${targetContext}.${entry.critical ? " Critical hit!" : ""} It dealt ${entry.amount} damage.`);
        break;
      case "miss":
        lines.push(`${actor} used ${action}${targetContext}, but missed.`);
        break;
      case "healing":
        lines.push(`${actor} used ${action}${targetContext}. It restored ${entry.amount} health.`);
        break;
      case "defend":
        lines.push(`${actor} used Defend.`);
        break;
      case "utility":
        lines.push(`${actor} used ${action}. It resolved.`);
        break;
      case "action_rejected":
        lines.push(`${actor} used ${action}${targetContext}, but it failed: ${entry.reason || "unavailable"}.`);
        break;
      case "input_rejected":
        lines.push(`That input is not available: ${String(entry.rejection_reason || "unknown").replace(/_/g, " ")}.`);
        break;
      case "victory":
        lines.push(`${actor} is victorious over ${target || "the enemy"}.`);
        break;
      case "defeat":
        lines.push(`${actor} was defeated by ${target || "the enemy"}.`);
        break;
      case "inventory":
        if (entry.accepted === false) lines.push("That inventory action is not available.");
        else if (entry.action_name) lines.push(`${actor} used ${entry.action_name}.`);
        break;
      case "status":
        break;
      default:
        lines.push(String(entry.event_type || "Battle event").replace(/_/g, " "));
    }

    if (entry.resource_spent) lines.push(`Resource spent: ${entry.resource_spent}.`);
    if (entry.statuses_applied && entry.statuses_applied.length) {
      lines.push(`Statuses applied: ${entry.statuses_applied.join(", ")}.`);
    }
    for (const outcome of entry.outcomes || []) {
      let detail = String(outcome.outcome_type).replace(/_/g, " ");
      if (outcome.charge_count != null) detail += ` (${outcome.charge_count}/3)`;
      if (outcome.amount) detail += ` (${outcome.amount})`;
      lines.push(detail.charAt(0).toUpperCase() + detail.slice(1) + ".");
    }
    return lines;
  }

  function renderLog(entries) {
    const container = $("battle-log");
    clear(container);
    for (const entry of entries || []) {
      for (const message of formatLogEntry(entry)) {
        const line = document.createElement("div");
        line.className = "log-entry";
        line.textContent = message;
        container.append(line);
      }
    }
  }

  function appendChoiceDetail(button, className, value) {
    if (!value) return;
    const detail = document.createElement("span");
    detail.className = className;
    detail.textContent = value;
    button.append(detail);
  }

  function renderMoveOptions(container, options, commandKind) {
    clear(container);
    for (const option of options || []) {
      const button = makeButton(
        `${option.number}. ${option.name}`,
        { kind: commandKind, key: option.selection_key },
        option.enabled,
        option.disabled_reason,
        "battle-option battle-choice move-choice",
      );
      const label = document.createElement("span");
      label.className = "choice-label";
      label.textContent = button.textContent;
      button.textContent = "";
      button.append(label);
      const tags = (option.tags || []).filter((tag) => tag !== option.resource_label);
      appendChoiceDetail(button, "choice-meta", tags.join(" | "));
      if (option.resource_label) appendChoiceDetail(button, "choice-cost", option.resource_label);
      appendChoiceDetail(button, "choice-summary", option.rules_summary);
      container.append(button);
    }
    appendBack(container);
  }

  function renderTargets(container, options) {
    clear(container);
    for (const option of options || []) {
      const button = makeButton(
        `${option.number}. ${option.display_label}`,
        { kind: "target", target_id: option.target_id },
        option.enabled,
        option.disabled_reason,
        "battle-option battle-choice target-choice",
      );
      appendChoiceDetail(button, "choice-meta", `HP ${option.hp_current}/${option.hp_maximum}`);
      appendChoiceDetail(button, "choice-state", (option.temporary_labels || []).join(", "));
      const preview = option.move_preview;
      if (preview) {
        const tags = (preview.tags || []).filter((tag) => tag !== preview.resource_label);
        const moveMeta = [tags.join(" | "), preview.resource_label].filter(Boolean).join(" · ");
        appendChoiceDetail(button, "choice-meta", `${preview.name}${moveMeta ? ` · ${moveMeta}` : ""}`);
        appendChoiceDetail(button, "choice-summary", preview.rules_summary);
      }
      container.append(button);
    }
    appendBack(container);
  }

  function appendBack(container) {
    container.append(makeButton("Back", { kind: "back" }, true, null, "battle-option back-option"));
  }

  function renderInventory(container, view) {
    clear(container);
    const phase = view.interaction_phase;
    const heading = document.createElement("h3");
    const message = document.createElement("p");

    if (phase === "inventory") {
      heading.textContent = "Choose an item:";
      container.append(heading);
      if (view.inventory_items && view.inventory_items.length) {
        renderOptions(
          container,
          view.inventory_items,
          (item) => ({ kind: "inventory_item", item_id: item.item_id }),
          (item) => `${item.number}. ${item.display_name} × ${item.quantity}`,
        );
      } else {
        message.textContent = "Your inventory is empty.";
        container.append(message);
      }
    } else if (phase === "inventory_item") {
      heading.textContent = view.selected_inventory_item
        ? `${view.selected_inventory_item.display_name} × ${view.selected_inventory_item.quantity}`
        : "Item";
      container.append(heading);
      renderOptions(
        container,
        view.inventory_commands,
        (option) => ({ kind: "inventory_command", command: option.command }),
        (option) => `${option.number}. ${option.label}`,
      );
    } else if (phase === "inventory_inspect") {
      const inspection = view.inventory_inspection;
      if (inspection) {
        heading.textContent = inspection.display_name;
        message.textContent = inspection.description;
        container.append(heading, message);
      }
    } else if (phase === "inventory_combination") {
      heading.textContent = "Choose a companion item:";
      container.append(heading);
      renderOptions(
        container,
        view.inventory_companions,
        (item) => ({ kind: "inventory_companion", item_id: item.item_id }),
        (item) => `${item.number}. ${item.display_name} × ${item.quantity}`,
      );
    } else if (phase === "inventory_confirmation") {
      const confirmation = view.inventory_confirmation;
      if (confirmation) {
        heading.textContent = `Combine ${confirmation.source_display_name} and ${confirmation.companion_display_name}`;
        message.textContent = `to prepare ${confirmation.result_display_name}?`;
        container.append(heading, message);
        container.append(
          makeButton("Yes", { kind: "inventory_confirm", confirmed: true }, true, null, "battle-option action-option"),
          makeButton("No", { kind: "inventory_confirm", confirmed: false }, true, null, "battle-option action-option"),
        );
      }
    } else {
      return;
    }

    appendBack(container);
  }

  function renderCharacter(view) {
    const character = view.character;
    if (!character) return;
    setText("character-name", `[ ${character.display_name} ]`);
    setText("character-archetype", character.archetype_label);

    const stats = $("character-stats");
    clear(stats);
    for (const stat of character.stats || []) {
      const line = document.createElement("div");
      line.className = "character-stat";
      line.textContent = `${stat.label}: ${stat.value}`;
      stats.append(line);
    }

    setText("character-level", `Level ${character.level}`);
    const resources = $("character-resources");
    clear(resources);
    appendStatus(resources, "HP", `${character.hp_current}/${character.hp_maximum}`);
    appendStatus(resources, "Mana", `${character.mana_current}/${character.mana_maximum}`);
    appendStatus(resources, "Super", `${character.super_current}/${character.super_maximum}`);
    const experience = character.exp_threshold == null
      ? "MAX LEVEL"
      : `${character.exp_current} / ${character.exp_threshold}`;
    setText("experience-value", experience);
    $("experience-progress").hidden = character.exp_threshold == null;
    $("experience-progress").value = character.exp_fill_bps;
    $("experience-progress").setAttribute("aria-valuetext", experience);
    renderOptions(
      $("character-options"),
      view.options,
      (option) => ({ kind: "overworld_action", action: option.action }),
      (option) => option.label,
      "overworld-option",
    );
  }

  function disabledStatLabel(reason) {
    if (reason === "no_growth_points") return "[No Growth Points]";
    if (reason === "stat_at_maximum") return "[Maximum]";
    return "[Unavailable]";
  }

  function renderSkills(view) {
    const skills = view.skills;
    if (!skills) return;
    setText("growth-summary", `Growth Points: ${skills.growth_points_available}`);
    setText("growth-message", skills.growth_message);

    const stats = $("skill-stats");
    clear(stats);
    for (const [index, stat] of (skills.stats || []).entries()) {
      const row = document.createElement("div");
      row.className = "skill-stat";
      const number = document.createElement("span");
      number.className = "skill-number";
      number.textContent = `${index + 1}.`;
      const label = document.createElement("span");
      label.className = "skill-label";
      label.textContent = stat.label;
      const value = document.createElement("span");
      value.className = "skill-value";
      value.textContent = String(stat.value);
      row.append(number, label, value);
      if (stat.increase_visible) {
        row.append(makeButton(
          stat.increase_enabled ? "[+1]" : disabledStatLabel(stat.disabled_reason),
          stat.increase_enabled ? { kind: "stat_increase", stat_name: stat.stat_name } : null,
          stat.increase_enabled,
          null,
          "stat-increase",
        ));
      }
      stats.append(row);
    }

    const attacks = $("skill-attacks");
    clear(attacks);
    for (const move of skills.moves || []) {
      const line = document.createElement("div");
      line.className = "skill-attack";
      line.textContent = move.name;
      attacks.append(line);
    }
    renderOptions(
      $("skills-options"),
      view.options,
      (option) => ({ kind: "overworld_action", action: option.action }),
      (option) => option.label,
      "overworld-option",
    );
  }

  function renderWeapon(view) {
    const weapon = view.weapon;
    if (!weapon) return;
    setText("weapon-name", weapon.name);
    setText("weapon-type", weapon.weapon_type);
    setText("weapon-wielder", `Wielder: ${weapon.intended_wielder}`);
    const bonuses = $("weapon-bonuses");
    clear(bonuses);
    for (const bonus of weapon.bonuses || []) {
      const line = document.createElement("div");
      line.textContent = `${bonus.label} +${bonus.amount}`;
      bonuses.append(line);
    }
    setText("weapon-description", weapon.description);
    renderDetailOptions("weapon-options", view.options);
  }

  function renderEquipment(view) {
    const equipment = view.equipment;
    if (!equipment) return;
    const slots = $("equipment-slots");
    clear(slots);
    for (const slot of [equipment.necklace, equipment.ring]) {
      const line = document.createElement("div");
      line.textContent = `[ ${slot.label} ]  ${slot.item_name}`;
      slots.append(line);
    }
    const benefits = $("equipment-benefits");
    clear(benefits);
    for (const benefit of equipment.benefits || []) {
      const line = document.createElement("div");
      line.textContent = benefit;
      benefits.append(line);
    }
    renderDetailOptions("equipment-options", view.options);
  }

  function renderDetailOptions(containerId, options) {
    renderOptions(
      $(containerId),
      options,
      (option) => ({ kind: "overworld_action", action: option.action }),
      (option) => option.label,
      "overworld-option",
    );
  }

  function renderOverworld(view) {
    const characterMenuScreens = ["character", "skills", "weapon", "equipment"];
    const characterMenuActive = characterMenuScreens.includes(view.screen);
    const mainScreen = view.screen === "main";
    setText("screen-badge", characterMenuActive || mainScreen ? "OVERWORLD" : view.screen);
    setText("location-label", view.location_label);
    setText("adventure-text", view.adventure_text);
    renderPlayer(view.character);
    renderEnemies([]);
    renderLog([]);

    $("route-actions").hidden = characterMenuActive;
    $("overworld-options").hidden = characterMenuActive;
    renderOptions(
      $("route-actions"),
      characterMenuActive || !view.contextual_route_option ? [] : [view.contextual_route_option],
      (option) => ({ kind: "overworld_action", action: option.action }),
      (option) => option.label,
      "overworld-option",
    );
    renderOptions(
      $("overworld-options"),
      view.options,
      (option) => ({ kind: "overworld_action", action: option.action }),
      (option) => option.label,
      "overworld-option",
    );

    $("character-panel").hidden = view.screen !== "character";
    $("skills-panel").hidden = view.screen !== "skills";
    $("weapon-panel").hidden = view.screen !== "weapon";
    $("equipment-panel").hidden = view.screen !== "equipment";
    if (view.screen === "character") renderCharacter(view);
    else if (view.screen === "skills") renderSkills(view);
    else if (view.screen === "weapon") renderWeapon(view);
    else if (view.screen === "equipment") renderEquipment(view);

    renderInventory($("inventory"), view);
    clear($("actions"));
    clear($("moves"));
    clear($("targets"));
    const notice = $("notice");
    notice.hidden = !view.notice;
    notice.textContent = view.notice || "";
  }

  function renderSuperMeter(meter) {
    const current = meter ? meter.current : 0;
    const maximum = meter ? meter.maximum : 0;
    const fill = meter ? meter.fill_bps : 0;
    $("super-progress").value = fill;
    $("super-progress").setAttribute("aria-valuetext", `${current} / ${maximum}`);
    setText("super-value", `${current} / ${maximum}`);
    $("super-ready").hidden = !(meter && meter.activation_offered);
  }

  function renderBattle(view) {
    const phase = view.interaction_phase;
    $("app").dataset.interactionPhase = phase;
    $("battle-screen").dataset.interactionPhase = phase;
    const matchupPlayer = view.visual && view.visual.player_lines && view.visual.player_lines.length
      ? view.visual.player_lines.join(" ")
      : view.player.display_name;
    setText("battle-matchup", `[ ${matchupPlayer} ]   VS   [ ${view.encounter_label} ]`);
    renderPlayer(view.player);
    renderEnemies(view.enemies);
    renderLog(view.log_entries);
    renderSuperMeter(view.super_meter);

    const actions = $("actions");
    const moves = $("moves");
    const targets = $("targets");
    const inventory = $("inventory");
    clear(actions);
    clear(moves);
    clear(targets);
    clear(inventory);

    if (phase === "actions") {
      setText("controls-title", "Actions");
      renderOptions(
        actions,
        view.action_options,
        (option) => ({ kind: "action", intent: option.intent }),
        (option) => option.label,
      );
      if (view.super_meter.activation_offered) {
        actions.append(makeButton("Super", { kind: "action", intent: "super" }, true, null, "battle-option action-option"));
      }
    } else if (phase === "regular_moves" || phase === "healing_moves" || phase === "super_moves") {
      setText("controls-title", phase === "super_moves" ? "Choose a Super:" : "Choose a move:");
      renderMoveOptions(moves, view.move_options, "move");
    } else if (phase === "targets") {
      setText("controls-title", "Choose a target:");
      renderTargets(targets, view.target_options);
    } else {
      const headings = {
        inventory: "Items",
        inventory_item: "Item actions",
        inventory_inspect: "Item details",
        inventory_combination: "Combine items",
        inventory_confirmation: "Confirm combination",
        complete: "Battle complete",
      };
      setText("controls-title", headings[phase] || "Battle");
      renderInventory(inventory, view);
    }
  }

  function render() {
    if (!state) return;
    if (gameStarted) showApp();
    const battle = Boolean(state.interaction_phase);
    $("overworld-screen").hidden = battle;
    $("battle-screen").hidden = !battle;
    if (battle) renderBattle(state);
    else {
      $("app").removeAttribute("data-interaction-phase");
      $("battle-screen").removeAttribute("data-interaction-phase");
      renderOverworld(state);
    }
    const complete = !battle && state.screen === "main" && !state.contextual_route_option;
    $("completion").hidden = !complete;
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
      if (state && state.interaction_phase === "complete") {
        state = await pythonJson("current_view_json()");
      }
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
      if (!document.fullscreenElement && document.documentElement.requestFullscreen) {
        await document.documentElement.requestFullscreen();
      }
      if (screen.orientation && screen.orientation.lock) await screen.orientation.lock("landscape");
    } catch (error) {
      console.info("Fullscreen or orientation enhancement unavailable", error);
    }
  }

  function updateFullscreenButton() {
    const isFullscreen = Boolean(document.fullscreenElement);
    $("immersive").querySelector(".utility-icon").setAttribute(
      "src",
      isFullscreen ? "assets/icons/exit-fullscreen.png" : "assets/icons/fullscreen.png",
    );
  }

  async function toggleImmersion() {
    try {
      if (document.fullscreenElement) {
        if (document.exitFullscreen) await document.exitFullscreen();
        if (screen.orientation && screen.orientation.unlock) screen.orientation.unlock();
      } else {
        await requestImmersion();
      }
    } catch (error) {
      console.info("Fullscreen enhancement unavailable", error);
    }
  }

  function updateMusicButton() {
    const audio = $("theme-music");
    const icon = $("sound-toggle").querySelector(".utility-icon");
    icon.setAttribute("src", !musicStarted || audio.muted
      ? "assets/icons/music-off.png"
      : "assets/icons/music-on.png");
  }

  function startMusic() {
    const audio = $("theme-music");
    musicStarted = true;
    updateMusicButton();
    let playback;
    try {
      playback = audio.play();
    } catch (error) {
      musicStarted = false;
      updateMusicButton();
      console.info("Background music could not start", error);
      return;
    }
    if (playback && typeof playback.catch === "function") {
      playback.catch(function (error) {
        musicStarted = false;
        updateMusicButton();
        console.info("Background music could not start", error);
      });
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
    showLoading(false);
    window.__DD_BROWSER_READY__ = true;
  }

  $("start").addEventListener("click", async function () {
    if (!state || gameStarted) return;
    gameStarted = true;
    $("start").disabled = true;
    startMusic();
    await requestImmersion();
    render();
  });

  $("sound-toggle").addEventListener("click", function () {
    const audio = $("theme-music");
    if (!musicStarted) {
      startMusic();
      return;
    }
    audio.muted = !audio.muted;
    updateMusicButton();
  });

  $("restart").addEventListener("click", async function () {
    await requestImmersion();
    await restart();
  });
  $("immersive").addEventListener("click", toggleImmersion);
  document.addEventListener("fullscreenchange", updateFullscreenButton);
  updateFullscreenButton();
  $("completion-restart").addEventListener("click", restart);
  $("retry").addEventListener("click", function () {
    window.location.reload();
  });

  bindViewportAndOrientation();
  boot().catch(function (error) {
    showError(error);
    console.error(error);
  });
})();
