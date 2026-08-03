const button = document.querySelector(".menu-button");
const links = document.querySelector(".nav-links");
if (button && links) {
  button.addEventListener("click", () => {
    const open = button.getAttribute("aria-expanded") === "true";
    button.setAttribute("aria-expanded", String(!open));
    links.classList.toggle("open", !open);
  });
}
