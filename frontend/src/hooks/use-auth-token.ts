export function useAuthToken() {

    const getAuthToken = () => localStorage.getItem('authToken');

    const setAuthToken = (token: string) => localStorage.setItem('authToken', token);

    const removeAuthToken = () => localStorage.removeItem('authToken');

    const isAuthenticated = () => !!getAuthToken();

    return {
        getAuthToken,
        setAuthToken,
        removeAuthToken,
        isAuthenticated,
    }
}