// ---------------------------------------------------------------------------
// Widget de calificación por estrellas (con medias estrellas)
// ---------------------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
    const widget = document.getElementById("rating-widget");
    if (widget) {
        const stars = Array.from(widget.querySelectorAll(".star"));
        const hidden = document.getElementById("rating-value");
        const clearBtn = document.getElementById("rating-clear");
        const label = document.getElementById("rating-label");

        const valueFromEvent = (starEl, evt) => {
            const rect = starEl.getBoundingClientRect();
            const idx = parseInt(starEl.dataset.val, 10);
            const clientX = evt.touches ? evt.touches[0].clientX : evt.clientX;
            const frac = (clientX - rect.left) / rect.width;
            return frac <= 0.5 ? idx - 0.5 : idx;
        };

        const paint = (val) => {
            val = parseFloat(val) || 0;
            stars.forEach((s) => {
                const idx = parseInt(s.dataset.val, 10);
                const fill = s.querySelector(".star-fill");
                let pct = 0;
                if (val >= idx) pct = 100;
                else if (val >= idx - 0.5) pct = 50;
                fill.style.width = pct + "%";
            });
            if (label) {
                label.textContent = val > 0 ? val + " / 5" : "Sin calificar";
            }
        };

        paint(hidden.value);

        stars.forEach((s) => {
            s.addEventListener("mousemove", (e) => paint(valueFromEvent(s, e)));
            s.addEventListener("mouseleave", () => paint(hidden.value));
            s.addEventListener("click", (e) => {
                hidden.value = valueFromEvent(s, e);
                paint(hidden.value);
            });
        });

        if (clearBtn) {
            clearBtn.addEventListener("click", () => {
                hidden.value = 0;
                paint(0);
            });
        }
    }

    // -----------------------------------------------------------------------
    // Selector de géneros (máximo configurable, ver data-max)
    // -----------------------------------------------------------------------
    const genreBox = document.getElementById("genre-selector");
    if (genreBox) {
        const max = parseInt(genreBox.dataset.max, 10) || 5;
        const checkboxes = Array.from(genreBox.querySelectorAll('input[type="checkbox"]'));
        const counter = document.getElementById("genre-counter");
        const newGenresInput = document.getElementById("new-genres-input");

        const countNewGenres = () => {
            if (!newGenresInput || !newGenresInput.value.trim()) return 0;
            return newGenresInput.value.split(",").map((s) => s.trim()).filter(Boolean).length;
        };

        const updateState = () => {
            const checkedCount = checkboxes.filter((c) => c.checked).length;
            const total = checkedCount + countNewGenres();

            if (counter) {
                counter.textContent = `${total} / ${max} géneros seleccionados`;
                counter.classList.toggle("over-limit", total > max);
            }

            checkboxes.forEach((c) => {
                if (!c.checked) {
                    c.disabled = total >= max;
                }
            });
        };

        checkboxes.forEach((c) => c.addEventListener("change", updateState));
        if (newGenresInput) newGenresInput.addEventListener("input", updateState);

        updateState();
    }

    // -----------------------------------------------------------------------
    // Buscador de libros existentes (para agregarlos a una libreta)
    // -----------------------------------------------------------------------
    const searchInput = document.getElementById("book-search-input");
    if (searchInput && Array.isArray(window.AVAILABLE_BOOKS)) {
        const hiddenId = document.getElementById("book-search-id");
        const resultsBox = document.getElementById("book-search-results");
        const addBtn = document.getElementById("add-existing-btn");
        const books = window.AVAILABLE_BOOKS;

        const renderResults = (matches) => {
            resultsBox.innerHTML = "";
            if (matches.length === 0) {
                const empty = document.createElement("div");
                empty.className = "search-item search-item-empty";
                empty.textContent = "Sin resultados";
                resultsBox.appendChild(empty);
                return;
            }
            matches.forEach((b) => {
                const item = document.createElement("div");
                item.className = "search-item";
                const label = b.title + " — " + (b.author || "Autor desconocido") + (b.year ? " (" + b.year + ")" : "");
                item.textContent = label;
                item.addEventListener("click", () => {
                    searchInput.value = label;
                    hiddenId.value = b.id;
                    addBtn.disabled = false;
                    resultsBox.classList.remove("active");
                });
                resultsBox.appendChild(item);
            });
        };

        searchInput.addEventListener("input", () => {
            const q = searchInput.value.trim().toLowerCase();
            hiddenId.value = "";
            addBtn.disabled = true;

            if (!q) {
                resultsBox.classList.remove("active");
                return;
            }

            const matches = books
                .filter((b) => {
                    const t = (b.title || "").toLowerCase();
                    const a = (b.author || "").toLowerCase();
                    return t.includes(q) || a.includes(q);
                })
                .slice(0, 8);

            renderResults(matches);
            resultsBox.classList.add("active");
        });

        searchInput.addEventListener("focus", () => {
            if (searchInput.value.trim()) resultsBox.classList.add("active");
        });

        document.addEventListener("click", (e) => {
            if (!e.target.closest(".search-select")) {
                resultsBox.classList.remove("active");
            }
        });
    }

    // Confirmar antes de subir una fecha de lectura futura (respaldo del atributo max)
    const dateInput = document.getElementById("date_read");
    if (dateInput) {
        const todayStr = dateInput.getAttribute("max");
        dateInput.addEventListener("change", () => {
            if (todayStr && dateInput.value > todayStr) {
                dateInput.value = todayStr;
            }
        });
    }

    // Auto-ocultar mensajes flash
    document.querySelectorAll(".flash").forEach((el) => {
        setTimeout(() => {
            el.style.opacity = "0";
            setTimeout(() => el.remove(), 400);
        }, 4000);
    });
});
