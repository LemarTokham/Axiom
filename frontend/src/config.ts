const ENV = import.meta.env


const apiConfig = {
    apiUrl: ENV.VITE_API_URL || "http://localhost:8000",
    timeout: 10000,
}

const appConfig = {
    appName: "axiom",
    mode: "development",

}

const config = {
    api: apiConfig,
    app: appConfig,
}

export default config