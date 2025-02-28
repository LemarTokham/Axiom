import {AxiosRequestConfig, AxiosResponse} from "axios";
import {apiClient, ApiResponse} from "./apiClient.ts";
import config from "../config.ts";


class ApiService {

    private static handleResponse<T>(response: AxiosResponse<ApiResponse<T>>): T {

        if (!response || typeof response !== "object") {
            console.error("Invalid response format:", response);
            throw new Error("Unexpected response structure from the API.");
        }

        if (config.app.mode === "development") {
            console.debug("Raw API Response:", response);
        }

        const { data, success, error } = response.data;

        if (!success) {
            console.error("API Error:", error?.message || "Unknown error");
            throw new Error(error?.message || "API request failed.");
        }

        if (data === undefined || data === null) {
            console.error("API returned empty data:", response);
            throw new Error("API response contains no data.");
        }

        if (response.data === null || response.data === undefined) {
            console.error("API returned empty data:", response);
            throw new Error("API response contains no data,");
        }

        return data as T;
    }

    static async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
        const response = await apiClient.get<ApiResponse<T>>(url, config);
        return this.handleResponse<T>(response);
    }

    static async post<T>(url: string, data?: Record<string, unknown> | FormData, config?: AxiosRequestConfig): Promise<T> {
        const response = await apiClient.post<ApiResponse<T>>(url, data, config);
        return this.handleResponse<T>(response);
    }

    static async put<T>(url: string, data?: Record<string, unknown> | FormData, config?: AxiosRequestConfig): Promise<T> {
        const response = await apiClient.put<ApiResponse<T>>(url, data, config);
        return this.handleResponse<T>(response);
    }

    static async del<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
        const response = await apiClient.delete<ApiResponse<T>>(url, config);
        return this.handleResponse<T>(response);
    }
}

export default ApiService;
