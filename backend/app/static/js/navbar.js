function menu() {
    const menuButton = document.querySelector(".menu");
    const menuList = document.querySelector(".menuList");

    document.body.classList.toggle("no-scroll");
    menuButton.classList.toggle("open");

    if (window.getComputedStyle(menuList).display === "none") {
        menuList.style.display = "block";
    } else {
        menuList.style.display = "none";
    }
}

window.addEventListener("scroll", function () {
    const navbar = document.querySelector(".navbar");

    if (window.scrollY > 50) {
        navbar.classList.add("scrolled");
    } else {
        navbar.classList.remove("scrolled");
    }
});