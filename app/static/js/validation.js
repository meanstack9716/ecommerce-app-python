// Error message handling functions
function createErrorMessage(message) {
  const errorMessage = document.createElement("p")
  errorMessage.classList.add("text-red-500", "text-sm", "mt-1", "error-message")
  errorMessage.textContent = message
  return errorMessage
}

function showErrorMessage(field, message) {
  removeErrorMessage(field) // Clear any existing error first
  const errorMessage = createErrorMessage(message)
  field.classList.add("border-red-500")
  field.classList.remove("border-gray-300")
  field.parentElement.appendChild(errorMessage)
  field.focus()
}

function removeErrorMessage(field) {
  const errorMessage = field.parentElement.querySelector(".error-message")
  if (errorMessage) {
    errorMessage.remove()
  }
  field.classList.remove("border-red-500")
  field.classList.add("border-gray-300")
}

// Validators with field-specific error messages
const validators = {
  required: (field, fieldName) => {
    if (!field.value.trim()) {
      showErrorMessage(field, `${fieldName} is required`)
      return false
    }
    removeErrorMessage(field)
    return true
  },
  email: (field) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(field.value)) {
      showErrorMessage(field, "Please enter a valid email address")
      return false
    }
    removeErrorMessage(field)
    return true
  },
  phone: (field) => {
    const phoneRegex = /^[0-9]{10,15}$/
    if (!phoneRegex.test(field.value)) {
      showErrorMessage(
        field,
        "Please enter a valid phone number (10-15 digits)"
      )
      return false
    }
    removeErrorMessage(field)
    return true
  },
}

// Validation personal details functions
function validatePersonalInfo() {
  const fields = {
    firstName: document.getElementById("first_name"),
    lastName: document.getElementById("last_name"),
    email: document.getElementById("email"),
    phoneNumber: document.getElementById("phone_number"),
    streetLine1: document.getElementById("street_line1"),
    city: document.getElementById("city"),
    state: document.getElementById("state"),
    pincode: document.getElementById("pincode"),
    country: document.getElementById("country"),
  }

  const isValid = [
    validators.required(fields.firstName, "First name"),
    validators.required(fields.lastName, "Last name"),
    validators.email(fields.email),
    validators.phone(fields.phoneNumber),
    validators.required(fields.streetLine1, "Street address"),
    validators.required(fields.city, "City"),
    validators.required(fields.state, "State"),
    validators.required(fields.pincode, "Pincode"),
    validators.required(fields.country, "Country"),
  ].every((result) => result === true)

  if (!isValid) return false

  return {
    firstName: fields.firstName.value.trim(),
    lastName: fields.lastName.value.trim(),
    email: fields.email.value.trim(),
    phoneNumber: fields.phoneNumber.value.trim(),
    streetLine1: fields.streetLine1.value.trim(),
    streetLine2: document.getElementById("street_line2")?.value.trim() || "",
    city: fields.city.value.trim(),
    state: fields.state.value.trim(),
    pincode: fields.pincode.value.trim(),
    country: fields.country.value.trim(),
  }
}

function validateBusinessInfo() {
  const fields = {
    businessName: document.getElementById("business_name"),
    businessType: document.getElementById("business_type"),
    businessEmail: document.getElementById("business_email"),
    businessMobile: document.getElementById("business_mobile_number"),
    gstNumber: document.getElementById("gst_number"),
    streetLine1: document.getElementById("business_street_line1"),
    streetLine2: document.getElementById("business_street_line2"),
    city: document.getElementById("business_city"),
    state: document.getElementById("business_state"),
    pincode: document.getElementById("business_pincode"),
    country: document.getElementById("business_country"),
  }

  // Validate all required fields
  const isValid = [
    validators.required(fields.businessName, "Business name"),
    validators.required(fields.businessType, "Business type"),
    validators.email(fields.businessEmail, "Business email"),
    validators.phone(fields.businessMobile, "Business mobile number"),
    validators.required(fields.streetLine1, "Street address"),
    validators.required(fields.gstNumber, "GST number"),
    validators.required(fields.city, "City"),
    validators.required(fields.state, "State"),
    validators.required(fields.pincode, "Pincode"),
    validators.required(fields.country, "Country"),
    // GST number validation can be added if needed
    validateGSTNumber(fields.gstNumber),
  ].every((result) => result === true)

  if (!isValid) return false

  // Return the validated data
  return {
    businessName: fields.businessName.value.trim(),
    businessType: fields.businessType.value,
    businessEmail: fields.businessEmail.value.trim(),
    businessMobile: fields.businessMobile.value.trim(),
    gstNumber: fields.gstNumber.value.trim(),
    address: {
      streetLine1: fields.streetLine1.value.trim(),
      streetLine2: fields.streetLine2.value.trim(),
      city: fields.city.value.trim(),
      state: fields.state.value.trim(),
      pincode: fields.pincode.value.trim(),
      country: fields.country.value.trim(),
    },
  }
}

// Optional GST number validation
function validateGSTNumber(field) {
  if (!field.value.trim()) {
    return true
  }
  const gstRegex = /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$/
  if (!gstRegex.test(field.value.trim())) {
    showErrorMessage(field, "Please enter a valid GST number")
    return false
  }

  removeErrorMessage(field)
  return true
}
function validateBusinessDetails() {
  // Add business details validation logic here
  // For now just return empty object
  return {}
}

// Add event listeners to clear errors when user starts typing
function setupFieldValidation(field) {
  field.addEventListener("input", () => {
    if (field.value.trim()) {
      removeErrorMessage(field)
    }
  })
}

// Initialize field validation
function initFieldValidation() {
  const allFields = document.querySelectorAll("input, select")
  allFields.forEach((field) => {
    setupFieldValidation(field)
  })
}
