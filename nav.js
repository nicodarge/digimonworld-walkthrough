// Mobile nav toggle, wide-table scroll wrapping, and the back-to-top button.
(function () {
  var btn = document.querySelector(".nav-toggle");
  var nav = document.querySelector(".site-nav");
  if (btn && nav) {
    btn.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      btn.setAttribute("aria-expanded", open ? "true" : "false");
    });
    // Escape closes the panel and hands focus back to the control that opened it.
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && nav.classList.contains("open")) {
        nav.classList.remove("open");
        btn.setAttribute("aria-expanded", "false");
        btn.focus();
      }
    });
  }

  // Make wide tables scrollable instead of breaking the layout. Tables the build
  // turned into a card list handle narrow screens on their own.
  document.querySelectorAll("main table").forEach(function (t) {
    // A card's own table is small by construction and already inside a box the
    // grid sizes; wrapping it adds a scroll container that can only ever be a
    // nuisance.
    if (t.closest(".table-scroll") || t.closest(".card") ||
        t.classList.contains("t-cards")) return;
    var w = document.createElement("div");
    w.className = "table-scroll";
    if (t.dataset.scrollHint) {
      w.setAttribute("role", "region");
      w.setAttribute("aria-label", t.dataset.scrollHint);
      w.tabIndex = 0;
    }
    t.parentNode.insertBefore(w, t);
    w.appendChild(t);
  });

  // One back-to-top control, in place of the arrow the archive repeated after
  // every section banner.
  var label = document.documentElement.lang === "fr" ? "Retour en haut" : "Back to top";
  var top = document.createElement("button");
  top.type = "button";
  top.className = "to-top-btn";
  top.textContent = "↑ " + label;
  document.body.appendChild(top);
  top.addEventListener("click", function () {
    window.scrollTo({ top: 0, behavior: "smooth" });
    var main = document.getElementById("content");
    if (main) main.focus({ preventScroll: true });
  });
  var ticking = false;
  window.addEventListener("scroll", function () {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(function () {
      top.classList.toggle("show", window.scrollY > 600);
      ticking = false;
    });
  }, { passive: true });
})();
