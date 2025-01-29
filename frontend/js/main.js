document.addEventListener("DOMContentLoaded", function () {
  const dropZone = document.querySelector(".drop-zone");
  const fileInput = dropZone.querySelector(".drop-zone__input");
  const form = document.getElementById("uploadForm");
  const resultsSection = document.querySelector(".results-section");
  const loader = document.querySelector(".loader");
  const uploadStatus = document.querySelector(".upload-status");
  const submitBtn = document.getElementById("submitBtn");

  // Drag and drop handlers
  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("drop-zone--over");
  });

  ["dragleave", "dragend"].forEach((type) => {
    dropZone.addEventListener(type, (e) => {
      dropZone.classList.remove("drop-zone--over");
    });
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("drop-zone--over");

    const file = e.dataTransfer.files[0];
    if (file && file.type === "application/pdf") {
      fileInput.files = e.dataTransfer.files;
      updateThumbnail(dropZone, file);
      updateUploadStatus(file.name, true);
    } else {
      updateUploadStatus("Please upload a PDF file", false);
    }
  });

  dropZone.addEventListener("click", () => {
    fileInput.click();
  });

  fileInput.addEventListener("change", () => {
    if (fileInput.files.length) {
      const file = fileInput.files[0];
      if (file.type === "application/pdf") {
        updateThumbnail(dropZone, file);
        updateUploadStatus(file.name, true);
      } else {
        updateUploadStatus("Please upload a PDF file", false);
        fileInput.value = "";
      }
    }
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const formData = new FormData(form);
    if (!formData.get("file")) {
      updateUploadStatus("Please select a PDF file first", false);
      return;
    }

    try {
      submitBtn.disabled = true;
      resultsSection.style.display = "block";
      loader.style.display = "block";
      updateUploadStatus("Processing...", true);

      const response = await fetch("http://localhost:8000/api/v1/pdf/process", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      displayResults(data);
      updateUploadStatus("PDF processed successfully!", true);
    } catch (error) {
      console.error("Error:", error);
      updateUploadStatus("Error processing PDF. Please try again.", false);
    } finally {
      loader.style.display = "none";
      submitBtn.disabled = false;
    }
  });

  function updateUploadStatus(message, isSuccess) {
    uploadStatus.textContent = message;
    uploadStatus.className = `upload-status ${isSuccess ? "success" : "error"}`;
    uploadStatus.style.display = "block";
  }

  function updateThumbnail(dropZone, file) {
    let thumbnailElement = dropZone.querySelector(".drop-zone__thumb");

    if (dropZone.querySelector(".drop-zone__prompt")) {
      dropZone.querySelector(".drop-zone__prompt").remove();
    }

    if (!thumbnailElement) {
      thumbnailElement = document.createElement("div");
      thumbnailElement.classList.add("drop-zone__thumb");
      dropZone.appendChild(thumbnailElement);
    }

    thumbnailElement.innerHTML = `
      <div class="file-info">
        <svg class="file-icon" viewBox="0 0 24 24">
          <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
        </svg>
        <span class="file-name">${file.name}</span>
      </div>
    `;
  }

  function displayResults(data) {
    console.log("Received data:", data);
    const personalInfo = document.getElementById("personalInfo");
    const educationInfo = document.getElementById("educationInfo");
    const skillsInfo = document.getElementById("skillsInfo");
    const projectsInfo = document.getElementById("projectsInfo");

    // Clear previous results
    personalInfo.innerHTML = "";
    educationInfo.innerHTML = "";
    skillsInfo.innerHTML = "";
    projectsInfo.innerHTML = "";

    // Display matched fields
    data.matched_fields.forEach((field) => {
      console.log("Processing field:", field);
      if (field.field_name === "projects") {
        console.log("Found projects:", field.suggested_value);
      }
      // Skip location field
      if (field.field_name === "location") return;

      if (field.field_name === "projects") {
        console.log("Found projects:", field.suggested_value);
        const projectsElement = createProjectsElement(field);
        projectsInfo.appendChild(projectsElement);
      } else {
        const fieldElement = createFieldElement(field);
        switch (field.field_name) {
          case "full_name":
          case "email":
          case "phone":
            personalInfo.appendChild(fieldElement);
            break;
          case "college_name":
          case "course_name":
          case "graduation_year":
            educationInfo.appendChild(fieldElement);
            break;
          case "skills":
          case "languages":
            skillsInfo.appendChild(fieldElement);
            break;
        }
      }
    });
  }

  function createFieldElement(field) {
    const div = document.createElement("div");
    div.className = "field";
    div.innerHTML = `
      <div class="field-label">${formatFieldName(field.field_name)}</div>
      <div class="field-value">${field.suggested_value || "Not found"}</div>
    `;
    return div;
  }

  function createProjectsElement(field) {
    const div = document.createElement("div");
    div.className = "field projects-field";

    if (!field.suggested_value) {
      div.innerHTML = `
            <div class="field-label">Projects</div>
            <div class="field-value">No projects found</div>
        `;
      return div;
    }

    const projects = field.suggested_value.split(" • ").filter(Boolean);
    let projectsHTML = `<div class="projects-list">`;

    projects.forEach((project) => {
      const [title, description] = project.split(": ");
      projectsHTML += `
            <div class="project-item">
                <div class="project-title">${title}</div>
                <div class="project-description">${description}</div>
            </div>
        `;
    });

    projectsHTML += `</div>`;
    div.innerHTML = projectsHTML;
    return div;
  }

  function formatFieldName(name) {
    return name
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  }
});
