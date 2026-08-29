(() => {
  // Deprecated Google Analytics cookies.
  const legacyCookies = ["_ga", "_ga_9E0WQEN2SV"];

  for (const name of legacyCookies) {
    // Delete a cookie belonging specifically to the current hostname.
    document.cookie = `${name}=; Max-Age=0; Path=/`;

    // Delete the same cookie if it belongs to the parent domain.
    document.cookie =
      `${name}=; Max-Age=0; Path=/; Domain=.aarongraybill.com`;
  }
})();
