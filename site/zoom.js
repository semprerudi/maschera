/* MASCHERA — zoom.js: Schirmbilder anklicken, vergrössert in der Mitte zeigen. */
(function () {
  var ruhig = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  var DAUER = ruhig ? 0 : 320, KURVE = "cubic-bezier(.2,.7,.2,1)";
  var offen = null;

  function ziel(img) {
    var w = img.naturalWidth, h = img.naturalHeight;
    var maxW = window.innerWidth * 0.94, maxH = window.innerHeight * 0.9;
    var f = Math.min(1, maxW / w, maxH / h);
    w *= f; h *= f;
    return { left: (window.innerWidth - w) / 2, top: (window.innerHeight - h) / 2, width: w, height: h };
  }

  function oeffnen(img) {
    if (offen || !img.naturalWidth) return;
    var von = img.getBoundingClientRect(), nach = ziel(img);
    var grund = document.createElement("div");
    grund.className = "zoom-grund";
    var gross = document.createElement("img");
    gross.className = "zoom-bild";
    gross.src = img.currentSrc || img.src;
    gross.alt = img.alt || "";
    gross.style.left = nach.left + "px"; gross.style.top = nach.top + "px";
    gross.style.width = nach.width + "px"; gross.style.height = nach.height + "px";
    grund.appendChild(gross);
    document.body.appendChild(grund);
    document.documentElement.classList.add("zoom-offen");
    img.style.visibility = "hidden";
    var sx = von.width / nach.width, sy = von.height / nach.height;
    var dx = von.left - nach.left, dy = von.top - nach.top;
    gross.animate([
      { transform: "translate(" + dx + "px," + dy + "px) scale(" + sx + "," + sy + ")" },
      { transform: "none" }
    ], { duration: DAUER, easing: KURVE });
    grund.animate([{ backgroundColor: "rgba(12,13,11,0)" }, { backgroundColor: "rgba(12,13,11,.72)" }], { duration: DAUER, easing: "ease-out" });
    offen = { img: img, grund: grund, gross: gross };
    grund.addEventListener("click", schliessen);
    grund.setAttribute("role", "dialog");
    grund.setAttribute("aria-modal", "true");
    grund.tabIndex = -1; grund.focus();
  }

  function schliessen() {
    if (!offen) return;
    var o = offen; offen = null;
    var von = o.img.getBoundingClientRect(), nach = o.gross.getBoundingClientRect();
    var sx = von.width / nach.width, sy = von.height / nach.height;
    var dx = von.left - nach.left, dy = von.top - nach.top;
    o.grund.animate([{ backgroundColor: "rgba(12,13,11,.72)" }, { backgroundColor: "rgba(12,13,11,0)" }], { duration: DAUER, easing: "ease-in", fill: "forwards" });
    var a = o.gross.animate([
      { transform: "none" },
      { transform: "translate(" + dx + "px," + dy + "px) scale(" + sx + "," + sy + ")" }
    ], { duration: DAUER, easing: KURVE, fill: "forwards" });
    var fertig = function () {
      o.img.style.visibility = "";
      o.grund.remove();
      document.documentElement.classList.remove("zoom-offen");
      o.img.focus({ preventScroll: true });
    };
    if (DAUER) a.onfinish = fertig; else fertig();
  }

  document.querySelectorAll("img.schirm").forEach(function (img) {
    img.tabIndex = 0;
    img.setAttribute("role", "button");
    img.addEventListener("click", function () { oeffnen(img); });
    img.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); oeffnen(img); }
    });
  });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") schliessen(); });
  window.addEventListener("resize", function () { if (offen) schliessen(); });
})();
