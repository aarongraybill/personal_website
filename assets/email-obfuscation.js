(() => {
  const target = document.getElementById("email-conversion");

  if (!target) {
    return;
  }

  const encoded = [
    108, 109, 127, 125, 125, 62, 120, 125, 109, 134, 112, 120, 124, 125,
    75, 127, 129, 111, 125, 118, 128, 125, 112, 59, 115, 115, 133
  ];

  const email = encoded
    .map((code, index) => String.fromCharCode(code - (index % 7) - 11))
    .join("");

  const emailBlock = document.createElement("div");
  emailBlock.id = target.id;
  emailBlock.className = "email-copy-block";

  const emailText = document.createElement("span");
  emailText.className = "email-copy-text";
  emailText.textContent = email;

  const copyButton = document.createElement("button");
  copyButton.className = "email-copy-button";
  copyButton.type = "button";
  copyButton.setAttribute("aria-label", "Copy email address");
  copyButton.title = "Copy email address";

  const copyIcon = document.createElement("i");
  copyIcon.className = "fa fa-clipboard email-copy-icon";
  copyIcon.setAttribute("aria-hidden", "true");

  const copyStatus = document.createElement("span");
  copyStatus.className = "email-copy-status";
  copyStatus.setAttribute("aria-live", "polite");
  copyStatus.setAttribute("role", "status");

  copyButton.append(copyIcon);
  emailBlock.append(emailText, copyButton, copyStatus);

  copyButton.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(email);
      copyButton.classList.add("copied");
      copyButton.setAttribute("aria-label", "Email address copied");
      copyButton.title = "Email address copied";
      copyStatus.textContent = "Email address copied";
      setTimeout(() => {
        copyButton.classList.remove("copied");
        copyButton.setAttribute("aria-label", "Copy email address");
        copyButton.title = "Copy email address";
        copyStatus.textContent = "";
      }, 1200);
    } catch {
      window.prompt("Copy email address", email);
    }
  });

  target.replaceWith(emailBlock);
})();
