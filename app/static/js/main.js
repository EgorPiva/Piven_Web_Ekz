document.querySelectorAll(".js-markdown-editor").forEach((textarea) => {
    if (window.EasyMDE) {
        new EasyMDE({
            element: textarea,
            spellChecker: false,
            status: false,
        });
    }
});

document.querySelectorAll(".genre-option").forEach((label) => {
    const checkbox = label.querySelector("input[type='checkbox']");
    if (!checkbox) {
        return;
    }

    const syncState = () => {
        label.classList.toggle("is-selected", checkbox.checked);
    };

    checkbox.addEventListener("change", syncState);
    syncState();
});
