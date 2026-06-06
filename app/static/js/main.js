document.querySelectorAll(".js-markdown-editor").forEach((textarea) => {
    if (window.EasyMDE) {
        new EasyMDE({
            element: textarea,
            spellChecker: false,
            status: false,
        });
    }
});
