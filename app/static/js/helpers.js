async function sendPostRequest(url, data) {
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
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
  