import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

// Dynamically use the current browser hostname so requests work on localhost, LAN IP, and mobile devices without reconfiguring .env
export const API_BASE_URL =
  typeof window !== "undefined" && window.location?.hostname
    ? `http://${window.location.hostname}:5000/api/v1`
    : (import.meta.env.VITE_API_BASE_URL as string) || "http://localhost:5000/api/v1";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 120000, // 120s timeout for RAG operations and cold starts
});

// Request interceptor to attach JWT token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem("plantassist_token");
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: unknown) => void;
  reject: (reason?: unknown) => void;
}> = [];

const processQueue = (error: unknown = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve();
    }
  });
  failedQueue = [];
};

// Response interceptor to handle token refresh on 401
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && !originalRequest?._retry) {
      // If we got 401 from refresh or login, do not retry
      if (
        originalRequest.url?.includes("/auth/login") ||
        originalRequest.url?.includes("/auth/refresh")
      ) {
        return Promise.reject(error);
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then(() => apiClient(originalRequest))
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = localStorage.getItem("plantassist_refresh_token");
      if (!refreshToken) {
        localStorage.removeItem("plantassist_token");
        localStorage.removeItem("plantassist_refresh_token");
        localStorage.removeItem("plantassist_user");
        window.location.href = "#/login";
        return Promise.reject(error);
      }

      try {
        const refreshResponse = await axios.post(
          `${API_BASE_URL}/auth/refresh`,
          { refresh_token: refreshToken },
          { headers: { "Content-Type": "application/json" } }
        );

        const newAccessToken = refreshResponse.data?.data?.access_token;
        if (newAccessToken) {
          localStorage.setItem("plantassist_token", newAccessToken);
          if (refreshResponse.data?.data?.refresh_token) {
            localStorage.setItem(
              "plantassist_refresh_token",
              refreshResponse.data.data.refresh_token
            );
          }
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
          }
          processQueue(null);
          return apiClient(originalRequest);
        }
      } catch (refreshErr) {
        processQueue(refreshErr);
        localStorage.removeItem("plantassist_token");
        localStorage.removeItem("plantassist_refresh_token");
        localStorage.removeItem("plantassist_user");
        window.location.href = "#/login";
        return Promise.reject(refreshErr);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;

