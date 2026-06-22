import api from "./axios"

export async function registerUser(data) {
    const response = await api.post("/auth/register", data)
    return response.data
}

export async function loginUser(username, password) {
    const formData = new URLSearchParams()

    formData.append("username", username)
    formData.append("password", password)

    const response = await api.post("/auth/login", formData, {
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        }
    })

    return response.data
}

export function logoutUser() {
    localStorage.removeItem("token")
}