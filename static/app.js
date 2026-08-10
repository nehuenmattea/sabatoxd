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

    // -----------------------------------------------------------------------
    // Selector visual de libros para una libreta: click para agregar/quitar,
    // se atenúan (con un check) los que ya están agregados. Todo vía AJAX,
    // sin recargar la página.
    // -----------------------------------------------------------------------
    const pickerToggleBtn = document.getElementById("picker-toggle-btn");
    const pickerBox = document.getElementById("book-picker");
    const pickerGrid = document.getElementById("book-picker-grid");

    if (pickerToggleBtn && pickerBox && pickerGrid && Array.isArray(window.PICKER_BOOKS)) {
        const books = window.PICKER_BOOKS;
        const toggleUrlBase = window.PICKER_TOGGLE_URL_BASE.replace(/\/0$/, "");
        let opened = false;
        let dirty = false;

        const renderItem = (b) => {
            const item = document.createElement("button");
            item.type = "button";
            item.className = "picker-item" + (b.in_list ? " picker-item-added" : "");
            item.dataset.bookId = b.id;

            const cover = document.createElement("div");
            cover.className = "picker-item-cover";
            if (b.cover_url) {
                const img = document.createElement("img");
                img.src = b.cover_url;
                img.alt = "";
                cover.appendChild(img);
            } else {
                cover.textContent = (b.title || "?").slice(0, 1).toUpperCase();
            }
            const check = document.createElement("span");
            check.className = "picker-item-check";
            check.textContent = "✓";
            cover.appendChild(check);

            const title = document.createElement("span");
            title.className = "picker-item-title";
            title.textContent = b.title;

            item.appendChild(cover);
            item.appendChild(title);

            item.addEventListener("click", () => {
                item.classList.add("picker-item-loading");
                fetch(toggleUrlBase + "/" + b.id, {
                    method: "POST",
                    headers: { "X-Requested-With": "XMLHttpRequest" },
                })
                    .then((r) => r.json())
                    .then((data) => {
                        item.classList.remove("picker-item-loading");
                        if (data && data.ok) {
                            item.classList.toggle("picker-item-added", data.in_list);
                            dirty = true;
                        }
                    })
                    .catch(() => item.classList.remove("picker-item-loading"));
            });

            return item;
        };

        books.forEach((b) => pickerGrid.appendChild(renderItem(b)));

        pickerToggleBtn.addEventListener("click", () => {
            opened = !opened;
            pickerBox.classList.toggle("hidden", !opened);
            pickerToggleBtn.textContent = opened ? "Ocultar selector" : "Ver todos mis libros y elegir con clicks";
            if (!opened && dirty) {
                // Recargar para reflejar los cambios en la grilla de "libros en esta libreta"
                window.location.reload();
            }
        });
    }

    // -----------------------------------------------------------------------
    // Buscadores de "libro favorito" en el perfil (hasta 4, reusa el mismo patrón
    // que el buscador de libros de una libreta)
    // -----------------------------------------------------------------------
    if (Array.isArray(window.PROFILE_BOOKS)) {
        document.querySelectorAll(".fav-book-picker").forEach((wrap) => {
            const input = wrap.querySelector(".fav-search-input");
            const hidden = wrap.querySelector(".fav-search-id");
            const resultsBox = wrap.querySelector(".fav-search-results");
            const clearBtn = wrap.querySelector(".fav-clear-btn");
            if (!input || !hidden || !resultsBox) return;

            const books = window.PROFILE_BOOKS;

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
                    item.textContent = b.title + (b.author ? " — " + b.author : "");
                    item.addEventListener("click", () => {
                        input.value = b.title + (b.author ? " — " + b.author : "");
                        hidden.value = b.id;
                        resultsBox.classList.remove("active");
                    });
                    resultsBox.appendChild(item);
                });
            };

            input.addEventListener("input", () => {
                const q = input.value.trim().toLowerCase();
                hidden.value = "";
                if (!q) {
                    resultsBox.classList.remove("active");
                    return;
                }
                const matches = books
                    .filter((b) => (b.title || "").toLowerCase().includes(q) || (b.author || "").toLowerCase().includes(q))
                    .slice(0, 8);
                renderResults(matches);
                resultsBox.classList.add("active");
            });

            input.addEventListener("focus", () => {
                if (input.value.trim()) resultsBox.classList.add("active");
            });

            if (clearBtn) {
                clearBtn.addEventListener("click", () => {
                    input.value = "";
                    hidden.value = "";
                    resultsBox.classList.remove("active");
                });
            }

            document.addEventListener("click", (e) => {
                if (!e.target.closest(".fav-book-picker")) {
                    resultsBox.classList.remove("active");
                }
            });
        });
    }

    // -----------------------------------------------------------------------
    // Confirmación explícita para restaurar una copia de seguridad (perfil)
    // -----------------------------------------------------------------------
    const restoreForm = document.getElementById("restore-backup-form");
    if (restoreForm) {
        restoreForm.addEventListener("submit", (e) => {
            const checkbox = document.getElementById("restore-confirm-checkbox");
            const fileInput = document.getElementById("restore-file-input");
            if (!fileInput.value) {
                e.preventDefault();
                alert("Elegí primero un archivo de copia de seguridad.");
                return;
            }
            if (!checkbox.checked) {
                e.preventDefault();
                alert("Tenés que marcar la casilla de confirmación antes de restaurar.");
                return;
            }
            if (!confirm("Esto va a REEMPLAZAR todos los libros, libretas y datos actuales por los del archivo elegido. ¿Continuar?")) {
                e.preventDefault();
            }
        });
    }

    // -----------------------------------------------------------------------
    // Editar una nota rápida de una libreta: el lápiz muestra un input inline
    // -----------------------------------------------------------------------
    document.querySelectorAll(".note-edit-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            const target = document.getElementById(btn.dataset.target);
            if (!target) return;
            target.classList.toggle("hidden");
            if (!target.classList.contains("hidden")) {
                const input = target.querySelector("input[type=text]");
                if (input) {
                    input.focus();
                    input.select();
                }
            }
        });
    });

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
