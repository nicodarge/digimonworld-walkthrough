// Language chooser for the root page: send a reader to fr/ or en/ on their
// browser's preference, falling back to English.
//
// A file rather than an inline <script>, so the Content-Security-Policy the
// vhost sends can say script-src 'self' instead of 'unsafe-inline'. It was the
// only inline script on the whole site.
//
// The page keeps two visible links for anyone this never runs for -- scripting
// off, or a crawler -- so nothing here is load-bearing for reaching the site.
(function () {
  var lang = (navigator.language || "en").toLowerCase().indexOf("fr") === 0 ? "fr" : "en";
  // replace, not assign: the chooser holds nothing worth a back-button stop.
  location.replace(lang + "/");
})();
