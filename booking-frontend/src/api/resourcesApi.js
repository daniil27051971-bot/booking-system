import api from "./axios"

export async function getResources() {
    const response = await api.get("/resources/")
    return response.data
}   