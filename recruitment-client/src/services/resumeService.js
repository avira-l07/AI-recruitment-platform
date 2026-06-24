import api from './api';

const resumeService = {
  /**
   * Uploads a user's resume.
   * @param {string|number} userId - The ID of the user.
   * @param {File} file - The resume file to upload.
   * @returns {Promise<Object>} The server response data.
   */
  uploadResume: async (userId, file) => {
    if (!userId) {
      throw new Error('User ID is missing. Please logout and login again.');
    }
    if (!file) {
      throw new Error('Resume file is missing.');
    }

    const formData = new FormData();

    // Backend Swagger expects: user_id and file
    formData.append('user_id', userId);
    formData.append('file', file);

    // Do not manually set Content-Type.
    // Axios automatically sets multipart/form-data with the correct boundary.
    const response = await api.post('/resumes/upload', formData);

    return response.data;
  },

  /**
   * Retrieves and parses a user's resume data.
   * @param {string|number} userId - The ID of the user.
   * @returns {Promise<Object>} The parsed resume data.
   */
  getResume: async (userId) => {
    // FIXED: Wrapped the URL in backticks for string interpolation
    const response = await api.get(`/resumes/${userId}`);
    const data = response.data;
    let parsedObj = {};

    if (data.parsed_data) {
      try {
        parsedObj =
          typeof data.parsed_data === 'string'
            ? JSON.parse(data.parsed_data)
            : data.parsed_data;
      } catch (error) {
        console.warn('Failed to parse resume data:', error);
      }
    }

    return {
      ...data,
      ...parsedObj,
      parsed_data: parsedObj,
    };
  },

  /**
   * Fetches career suggestions based on the user's resume.
   * @param {string|number} userId - The ID of the user.
   * @returns {Promise<Object>} The career suggestions data.
   */
  getCareerSuggestions: async (userId) => {
    // FIXED: Wrapped the URL in backticks for string interpolation
    const response = await api.get(`/resumes/${userId}/career-suggestions`);
    return response.data;
  },
};

export default resumeService;