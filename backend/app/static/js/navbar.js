function menu() {
    const menuLists = document.querySelectorAll('.menuList');

    menuLists.forEach(element => {
        const currentDisplay = window.getComputedStyle(element).display;

        if (currentDisplay === "none") {
            element.style.display = "block";
        } else {
            element.style.display = "none";
        }
    });
}

window.addEventListener("scroll", function () {
    const navbar = document.querySelector(".navbar");

    if (window.scrollY > 50) {
        navbar.classList.add("scrolled");
    } else {
        navbar.classList.remove("scrolled");
    }
});