async function sendPostRequest(url, formData) {
  try {
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
      credentials: 'include' 
    });

    const responseData = await response.json();

    if (response.ok) {
      return { success: true, message: responseData.message || 'Request successful' };
    } else {
      return { success: false, errors: responseData.errors || 'Request failed' };
    }
  } catch (err) {
    return { success: false, message: err.message || 'Network error' };
  }
}


async function sendGetRequest(url) {
  try {
    const response = await fetch(url, {
      method: 'GET',
      credentials: 'include', // includes cookies/session if needed
    });

    const responseData = await response.json();

    if (response.ok) {
      return { success: true, data: responseData };
    } else {
      return { success: false, error: responseData.error || 'Request failed' };
    }
  } catch (err) {
    return { success: false, error: err.message || 'Network error' };
  }
}
