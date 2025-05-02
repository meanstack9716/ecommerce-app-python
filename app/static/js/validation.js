// Error message handling functions
function createErrorMessage(message) {
  const errorMessage = document.createElement("p")
  errorMessage.classList.add("text-red-500", "text-sm", "mt-1", "error-message")
  errorMessage.textContent = message
  return errorMessage
}

function showErrorMessage(field, message) {
  removeErrorMessage(field)
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
  minLength: function (field, minLength, fieldName) {
    if (field.value.trim().length < minLength) {
      showErrorMessage(
        field,
        `${fieldName} must be at least ${minLength} characters.`
      )
      return false
    }
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
  requiredRadioGroup: function (fieldName, fieldSelector) {
    const field = document.querySelector(fieldSelector)
    const checked = document.querySelector(`input[name="${fieldName}"]:checked`)

    if (!checked) {
      showErrorMessage(field, `${fieldName.replace(/_/g, " ")} is required`)
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
    validators.required(fields.firstName, "First name") &&
      validators.minLength(fields.firstName, 3, "First name"),

    validators.required(fields.lastName, "Last name") &&
      validators.minLength(fields.lastName, 3, "Last name"),

    validators.email(fields.email),
    validators.phone(fields.phoneNumber),

    validators.required(fields.streetLine1, "Street address") &&
      validators.minLength(fields.streetLine1, 8, "Street address"),

    validators.required(fields.city, "City") &&
      validators.minLength(fields.city, 3, "City"),

    validators.required(fields.state, "State") &&
      validators.minLength(fields.state, 3, "State"),

    validators.required(fields.pincode, "Pincode"),

    validators.required(fields.country, "Country") &&
      validators.minLength(fields.country, 3, "Country"),
  ].every((result) => result === true)

  if (!isValid) return false

  return {
    first_name: fields.firstName.value.trim(),
    last_name: fields.lastName.value.trim(),
    email: fields.email.value.trim(),
    phoneNumber: fields.phoneNumber.value.trim(),
    address: {
      streetLine1: fields.streetLine1.value.trim(),
      streetLine2: document.getElementById("street_line2")?.value.trim() || "",
      city: fields.city.value.trim(),
      state: fields.state.value.trim(),
      pincode: fields.pincode.value.trim(),
      country: fields.country.value.trim(),
    },
  }
}

function validateBusinessInfo() {
  const fields = {
    businessName: document.getElementById("business_name"),
    businessType: document.getElementById("business_type"),
    businessEmail: document.getElementById("business_email"),
    businessMobile: document.getElementById("business_mobile_number"),
    gstNumber: document.getElementById("gst_number"),
    businessAddressType: document.querySelector(
      'input[name="business_address_type"]:checked'
    ),
    streetLine1: document.getElementById("business_street_line1"),
    streetLine2: document.getElementById("business_street_line2"),
    city: document.getElementById("business_city"),
    state: document.getElementById("business_state"),
    pincode: document.getElementById("business_pincode"),
    country: document.getElementById("business_country"),
  }

  const isValid = [
    validators.required(fields.businessName, "Business name") &&
      validators.minLength(fields.businessName, 3, "Business name"),

    validators.required(fields.businessType, "Business type"),

    validators.email(fields.businessEmail, "Business email"),

    validators.phone(fields.businessMobile, "Business mobile number"),

    validators.requiredRadioGroup(
      "business_address_type",
      "#business_address_type_container"
    ),

    validators.required(fields.streetLine1, "Street address") &&
      validators.minLength(fields.streetLine1, 8, "Street address"),

    validators.required(fields.gstNumber, "GST number"),

    validators.required(fields.city, "City") &&
      validators.minLength(fields.city, 3, "City"),

    validators.required(fields.state, "State"),

    validators.required(fields.pincode, "Pincode"),

    validators.required(fields.country, "Country") &&
      validators.minLength(fields.country, 3, "Country"),

    // GST number validation (if needed)
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
    businessAddress: {
      streetLine1: fields.streetLine1.value.trim(),
      streetLine2: fields.streetLine2.value.trim(),
      city: fields.city.value.trim(),
      state: fields.state.value.trim(),
      pincode: fields.pincode.value.trim(),
      country: fields.country.value.trim(),
      type: fields.businessAddressType.value.trim(),
    },
  }
}

function validateBusinessDetails() {
  const fields = {
    panNumber: document.getElementById("pan_card_number"),
    panCardFront: document.getElementById("pan_card_front"),
    panCardBack: document.getElementById("pan_card_back"),
    addressProofIdType: document.getElementById("address_proof_id_type"),
    idNumber: document.getElementById("id_number"),
    addressProofFront: document.getElementById("address_proof_front"),
    addressProofBack: document.getElementById("address_proof_back"),
  }

  // Validate required fields
  const isRequiredValid = [
    validators.required(fields.panNumber, "PAN number"),
    validators.required(fields.panCardFront, "PAN Card Front Photo"),
    validators.required(fields.panCardBack, "PAN Card Back Photo"),
    validators.required(fields.addressProofIdType, "Address Proof ID Type"),
    validators.required(fields.idNumber, "ID Number"),
    validators.required(fields.addressProofFront, "Address Proof Front Photo"),
    // validators.required(fields.addressProofBack, "Address Proof Back Photo"),
    validatePANNumber(fields.panNumber),
  ].every((result) => result === true)

  if (!isRequiredValid) return false

  const areImagesValid = [
    validateImage(fields.panCardFront),
    validateImage(fields.panCardBack),
    validateImage(fields.addressProofFront),
    validateImage(fields.addressProofBack),
  ].every((result) => result === true)

  if (!areImagesValid) return false

  // Return validated data
  return {
    panNumber: fields.panNumber.value.trim(),
    panCardFront: fields.panCardFront.files[0] || null,
    panCardBack: fields.panCardBack.files[0] || null,
    idNumber: fields.idNumber.value,
    addressProofIdType: fields.addressProofIdType.value,
    addressProofFront: fields.addressProofFront.files[0] || null,
    addressProofBack: fields.addressProofBack.files[0] || null,
  }
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

function validatePANNumber(field) {
  //   const panRegex = /^[A-Z]{5}[0-9]{4}[A-Z]{1}$/
  //   const value = field.value.trim()

  //   if (!panRegex.test(field)) {
  //     showErrorMessage(field, "Please enter a valid PAN number.")
  //     return false
  //   }
  //   removeErrorMessage(field)
  return true
}

function validateImage(imageField) {
  const file = imageField.files[0]
  if (!file) return false

  const validTypes = ["image/png", "image/jpeg", "image/gif", "image/webp"]
  if (!validTypes.includes(file.type)) {
    showToast("Invalid image type. Only PNG, JPG, or GIF allowed.", "error")
    return false
  }

  const maxSize = 2 * 1024 * 1024
  if (file.size > maxSize) {
    showToast("Image size exceeds 2MB.", "error")
    return false
  }

  return true
}
