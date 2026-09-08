const API_URL = "https://superjoin-fact-knowledge-api.onrender.com";

const pdfInput = document.getElementById("pdfInput");
const dropZone = document.getElementById("dropZone");
const fileList = document.getElementById("fileList");
const processButton = document.getElementById("processButton");

const resultsSection =
    document.getElementById("resultsSection");

const errorMessage =
    document.getElementById("errorMessage");

const loadingMessage =
    document.getElementById("loadingMessage");

const clearButton =
    document.getElementById("clearButton");

let selectedFiles = [];


/* -----------------------------
   File selection
----------------------------- */

pdfInput.addEventListener("change", function () {

    selectedFiles = Array.from(pdfInput.files);

    validateAndDisplayFiles();

});


/* -----------------------------
   Drag and drop
----------------------------- */

dropZone.addEventListener("dragover", function (event) {

    event.preventDefault();

    dropZone.classList.add("dragover");

});


dropZone.addEventListener("dragleave", function () {

    dropZone.classList.remove("dragover");

});


dropZone.addEventListener("drop", function (event) {

    event.preventDefault();

    dropZone.classList.remove("dragover");

    const droppedFiles =
        Array.from(event.dataTransfer.files);

    selectedFiles = droppedFiles;

    validateAndDisplayFiles();

});


/* -----------------------------
   Validate files
----------------------------- */

function validateAndDisplayFiles() {

    clearError();

    const invalidFiles =
        selectedFiles.filter(
            file => !file.name.toLowerCase().endsWith(".pdf")
        );

    if (invalidFiles.length > 0) {

        showError(
            "Only PDF files are supported."
        );

        selectedFiles = [];

        fileList.innerHTML = "";

        processButton.disabled = true;

        return;
    }

    renderFileList();

    processButton.disabled =
        selectedFiles.length === 0;
}


/* -----------------------------
   Render selected files
----------------------------- */

function renderFileList() {

    fileList.innerHTML = "";

    if (selectedFiles.length === 0) {
        return;
    }

    selectedFiles.forEach(file => {

        const item =
            document.createElement("div");

        item.className = "file-item";

        item.innerHTML = `
            <div>
                <div class="file-name">
                    ${escapeHtml(file.name)}
                </div>

                <div class="file-size">
                    ${formatFileSize(file.size)}
                </div>
            </div>
        `;

        fileList.appendChild(item);

    });
}


/* -----------------------------
   Process documents
----------------------------- */

processButton.addEventListener(
    "click",
    async function () {

        if (selectedFiles.length === 0) {
            return;
        }

        clearError();

        setLoading(true);

        processButton.disabled = true;

        const formData = new FormData();

        selectedFiles.forEach(file => {

            formData.append(
                "files",
                file
            );

        });


        try {

            const response =
                await fetch(
                    `${API_URL}/api/ingest`,
                    {
                        method: "POST",
                        body: formData
                    }
                );


            const data =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    data.detail ||
                    "Document processing failed."
                );

            }


            renderResults(data);

        } catch (error) {

            console.error(error);

            showError(
                error.message ||
                "Could not connect to the backend API."
            );

        } finally {

            setLoading(false);

            processButton.disabled =
                selectedFiles.length === 0;

        }

    }
);


/* -----------------------------
   Render results
----------------------------- */

function renderResults(data) {

    resultsSection.classList.remove("hidden");


    const summary =
        data.summary || {};


    document.getElementById(
        "documentCount"
    ).textContent =
        summary.document_count || 0;


    document.getElementById(
        "factCount"
    ).textContent =
        summary.fact_count || 0;


    document.getElementById(
        "relationshipCount"
    ).textContent =
        summary.relationship_count || 0;


    document.getElementById(
        "factBadge"
    ).textContent =
        `${summary.fact_count || 0} facts`;


    document.getElementById(
        "relationshipBadge"
    ).textContent =
        `${summary.relationship_count || 0} relationships`;


    renderFacts(
        data.facts || []
    );


    renderRelationships(
        data.relationships || []
    );


    resultsSection.scrollIntoView({
        behavior: "smooth"
    });

}


/* -----------------------------
   Render facts
----------------------------- */

function renderFacts(facts) {

    const container =
        document.getElementById(
            "factsContainer"
        );

    container.innerHTML = "";


    if (facts.length === 0) {

        container.innerHTML = `
            <div class="empty-state">
                No verified facts were extracted.
            </div>
        `;

        return;
    }


    facts.forEach(fact => {

        const card =
            document.createElement("div");

        card.className = "fact-card";


        const value =
            fact.value !== null &&
            fact.value !== undefined
                ? formatValue(fact.value, fact.unit_key)
                : "Qualitative";


        const period =
            fact.period_key ||
            "Period not specified";


        const scope =
            fact.scope_key ||
            "Scope not specified";


        const source =
            fact.source_document ||
            "Unknown document";


        const page =
            fact.page_number ||
            "—";


        const evidence =
            fact.evidence ||
            "No evidence available";


        card.innerHTML = `

            <div class="fact-top">

                <div class="fact-metric">
                    ${escapeHtml(
                        fact.metric_key ||
                        "Unnamed metric"
                    )}
                </div>

                <div class="fact-value">
                    ${escapeHtml(value)}
                </div>

            </div>


            <div class="fact-meta">

                <span class="meta-tag">
                    Entity:
                    ${escapeHtml(
                        fact.entity_key ||
                        "Not specified"
                    )}
                </span>

                <span class="meta-tag">
                    Period:
                    ${escapeHtml(period)}
                </span>

                <span class="meta-tag">
                    Scope:
                    ${escapeHtml(scope)}
                </span>

            </div>


            <div class="evidence-box">

                <span class="evidence-label">
                    Source Evidence
                </span>

                <div class="evidence-text">
                    "${escapeHtml(evidence)}"
                </div>

            </div>


            <div class="source-info">

                Source:
                <strong>
                    ${escapeHtml(source)}
                </strong>

                · Page ${escapeHtml(String(page))}

                · Evidence verified:
                <strong>
                    ${fact.evidence_verified
                        ? "Yes"
                        : "No"}
                </strong>

            </div>

        `;


        container.appendChild(card);

    });

}


/* -----------------------------
   Render relationships
----------------------------- */

function renderRelationships(
    relationships
) {

    const container =
        document.getElementById(
            "relationshipsContainer"
        );

    container.innerHTML = "";


    if (relationships.length === 0) {

        container.innerHTML = `
            <div class="empty-state">
                No cross-document relationships
                were identified.
            </div>
        `;

        return;
    }


    relationships.forEach(
        relationship => {

            const card =
                document.createElement("div");

            card.className =
                "relationship-card";


            const type =
                relationship.relationship ||
                "uncertain";


            const factA =
                relationship.fact_a || {};


            const factB =
                relationship.fact_b || {};


            const reason =
                relationship.reason ||
                "No reasoning explanation available.";


            card.innerHTML = `

                <div class="relationship-header">

                    <span class="relationship-badge ${escapeHtml(type)}">

                        ${escapeHtml(
                            formatRelationshipType(type)
                        )}

                    </span>

                </div>


                <div class="relationship-facts">

                    ${renderRelationshipFact(
                        factA,
                        "Document A"
                    )}

                    ${renderRelationshipFact(
                        factB,
                        "Document B"
                    )}

                </div>


                <div class="relationship-reason">

                    <strong>
                        Reason:
                    </strong>

                    ${escapeHtml(reason)}

                </div>

            `;


            container.appendChild(card);

        }
    );

}


/* -----------------------------
   Relationship fact
----------------------------- */

function renderRelationshipFact(
    fact,
    label
) {

    return `

        <div class="relationship-fact">

            <h4>
                ${label}
            </h4>

            <p>
                <strong>Metric:</strong>
                ${escapeHtml(
                    fact.metric_key ||
                    "—"
                )}
            </p>

            <p>
                <strong>Value:</strong>
                ${escapeHtml(
                    formatValue(
                        fact.value,
                        fact.unit_key
                    )
                )}
            </p>

            <p>
                <strong>Period:</strong>
                ${escapeHtml(
                    fact.period_key ||
                    "—"
                )}
            </p>

            <p>
                <strong>Scope:</strong>
                ${escapeHtml(
                    fact.scope_key ||
                    "—"
                )}
            </p>

            <p>
                <strong>Source:</strong>
                ${escapeHtml(
                    fact.source_document ||
                    "—"
                )}
                · Page
                ${escapeHtml(
                    String(
                        fact.page_number ||
                        "—"
                    )
                )}
            </p>

        </div>

    `;
}


/* -----------------------------
   Format relationship name
----------------------------- */

function formatRelationshipType(type) {

    const names = {

        corroboration:
            "Corroboration",

        contradiction:
            "Contradiction",

        contextual_difference:
            "Contextual Difference",

        uncertain:
            "Uncertain"

    };

    return names[type] || type;

}


/* -----------------------------
   Format value
----------------------------- */

function formatValue(
    value,
    unit
) {

    if (
        value === null ||
        value === undefined
    ) {
        return "—";
    }


    let formatted;


    if (
        typeof value === "number"
    ) {

        formatted =
            value.toLocaleString(
                "en-IN"
            );

    } else {

        formatted = String(value);

    }


    if (unit) {

        return `${formatted} ${unit}`;

    }


    return formatted;

}


/* -----------------------------
   File size
----------------------------- */

function formatFileSize(bytes) {

    if (bytes < 1024) {

        return `${bytes} B`;

    }


    if (bytes < 1024 * 1024) {

        return `${(
            bytes / 1024
        ).toFixed(1)} KB`;

    }


    return `${(
        bytes / (1024 * 1024)
    ).toFixed(1)} MB`;

}


/* -----------------------------
   Loading state
----------------------------- */

function setLoading(isLoading) {

    if (isLoading) {

        loadingMessage.classList.remove(
            "hidden"
        );

    } else {

        loadingMessage.classList.add(
            "hidden"
        );

    }

}


/* -----------------------------
   Errors
----------------------------- */

function showError(message) {

    errorMessage.textContent =
        message;

    errorMessage.classList.remove(
        "hidden"
    );

}


function clearError() {

    errorMessage.textContent = "";

    errorMessage.classList.add(
        "hidden"
    );

}


/* -----------------------------
   Clear results
----------------------------- */

clearButton.addEventListener(
    "click",
    function () {

        resultsSection.classList.add(
            "hidden"
        );

        selectedFiles = [];

        pdfInput.value = "";

        fileList.innerHTML = "";

        processButton.disabled = true;

        clearError();

        window.scrollTo({
            top: 0,
            behavior: "smooth"
        });

    }
);


/* -----------------------------
   HTML escaping
----------------------------- */

function escapeHtml(value) {

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");

}