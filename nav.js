// Mobile nav toggle + wrap wide legacy tables for horizontal scrolling.
(function () {
  var btn = document.querySelector(".nav-toggle");
  var nav = document.querySelector(".site-nav");
  if (btn && nav) {
    btn.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      btn.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }
  // Make wide tables scrollable instead of breaking the layout.
  document.querySelectorAll("main table").forEach(function (t) {
    if (t.closest(".table-scroll")) return;
    var w = document.createElement("div");
    w.className = "table-scroll";
    t.parentNode.insertBefore(w, t);
    w.appendChild(t);
  });
})();
